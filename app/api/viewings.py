"""
API-Endpoints für Besichtigungstermine (Viewings), Buchungen und Einladungen.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.core.rate_limit import limiter, RATE_LIMIT_BOOKING
from app.core.email import (
    send_viewing_invitation_email,
    send_viewing_confirmation_email,
    send_viewing_cancelled_email,
    send_viewing_rescheduled_email,
)
from app.core.ics import generate_ics, format_datetime_german
from app.models.user import User
from app.models.property import Property
from app.models.application import Application
from app.models.viewing import ViewingSlot
from app.models.viewing_invitation import ViewingInvitation
from app.models.booking import Booking
from app.schemas.viewing import (
    ViewingSlotCreate,
    ViewingSlotBulkCreate,
    ViewingSlotUpdate,
    ViewingSlotResponse,
    ViewingSlotListResponse,
    ViewingInviteRequest,
    ViewingInvitationResponse,
    ViewingInvitationWithDetails,
    ViewingInvitationRespondRequest,
)
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingListResponse,
    BookingCancelResponse,
)


router = APIRouter()


# ============================================
# Helper Functions
# ============================================

def get_slot_response(slot: ViewingSlot, db: Session) -> dict:
    """Erstellt ein Response-Dict für einen ViewingSlot."""
    confirmed_count = db.query(Booking).filter(
        Booking.slot_id == slot.id,
        Booking.confirmed == True,
        Booking.cancelled_at == None
    ).count()

    invitations_count = db.query(ViewingInvitation).filter(
        ViewingInvitation.slot_id == slot.id
    ).count()

    return {
        "id": slot.id,
        "property_id": slot.property_id,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "slot_type": slot.slot_type,
        "access_type": slot.access_type,
        "max_attendees": slot.max_attendees,
        "notes": slot.notes,
        "available_spots": slot.max_attendees - confirmed_count,
        "bookings_count": confirmed_count,
        "invitations_count": invitations_count,
        "created_at": slot.created_at,
        "updated_at": slot.updated_at
    }


def verify_property_owner(
    property_id: UUID,
    user_id: UUID,
    db: Session
) -> Property:
    """Verifiziert, dass der Benutzer Eigentümer der Immobilie ist und diese aktiv ist."""
    property_obj = db.query(Property).filter(Property.id == property_id).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht gefunden"
        )

    if not property_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht mehr aktiv"
        )

    if property_obj.landlord_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Immobilie"
        )

    return property_obj


# ============================================
# ViewingSlot Endpoints
# ============================================

@router.get("", response_model=ViewingSlotListResponse)
def list_viewing_slots(
    property_id: Optional[UUID] = Query(None, description="Filter nach Immobilie"),
    slot_type: Optional[str] = Query(None, description="Filter nach Slot-Typ"),
    access_type: Optional[str] = Query(None, description="Filter nach Zugangsart"),
    upcoming_only: bool = Query(False, description="Nur zukünftige Termine"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Listet alle Besichtigungstermine des eingeloggten Vermieters.

    Args:
        property_id: Optional - Filter nach Immobilien-ID
        slot_type: Optional - Filter nach Slot-Typ (individual/group)
        access_type: Optional - Filter nach Zugangsart (public/invited)
        upcoming_only: Nur zukünftige Termine anzeigen
        db: Datenbank-Session
        current_user: Authentifizierter Benutzer

    Returns:
        Liste der Besichtigungstermine
    """
    # Nur Slots für eigene, aktive Properties
    query = db.query(ViewingSlot).join(Property).filter(
        Property.landlord_id == current_user.id,
        Property.is_active == True
    )

    if property_id:
        query = query.filter(ViewingSlot.property_id == property_id)

    if slot_type:
        query = query.filter(ViewingSlot.slot_type == slot_type)

    if access_type:
        query = query.filter(ViewingSlot.access_type == access_type)

    if upcoming_only:
        query = query.filter(ViewingSlot.start_time >= datetime.utcnow())

    slots = query.order_by(ViewingSlot.start_time).all()

    result = [get_slot_response(slot, db) for slot in slots]

    return {
        "items": result,
        "total": len(result)
    }


@router.post("", response_model=ViewingSlotResponse, status_code=status.HTTP_201_CREATED)
def create_viewing_slot(
    slot_data: ViewingSlotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Erstellt einen neuen Besichtigungstermin.

    Args:
        slot_data: Termindaten inkl. property_id
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Der erstellte Termin
    """
    # Berechtigung prüfen
    verify_property_owner(slot_data.property_id, current_user.id, db)

    # max_attendees für Einzeltermine auf 1 setzen
    max_attendees = slot_data.max_attendees
    if slot_data.slot_type == "individual":
        max_attendees = 1

    # Termin erstellen
    slot = ViewingSlot(
        property_id=slot_data.property_id,
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
        slot_type=slot_data.slot_type,
        access_type=slot_data.access_type,
        max_attendees=max_attendees,
        notes=slot_data.notes
    )

    db.add(slot)
    db.commit()
    db.refresh(slot)

    return get_slot_response(slot, db)


@router.post("/bulk", response_model=ViewingSlotListResponse, status_code=status.HTTP_201_CREATED)
def create_bulk_slots(
    data: ViewingSlotBulkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Erstellt mehrere Slots aus einem Zeitbereich.

    Args:
        data: Bulk-Erstellungsdaten mit Datum, Zeitbereich und Konfiguration
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Liste der erstellten Termine

    Beispiel:
        date: "2026-02-15"
        time_start: "14:00"
        time_end: "18:00"
        slot_duration_minutes: 30

        Generiert: 14:00-14:30, 14:30-15:00, ..., 17:30-18:00 (8 Slots)
    """
    # Berechtigung prüfen
    verify_property_owner(data.property_id, current_user.id, db)

    # Zeiten parsen
    start_hour, start_minute = map(int, data.time_start.split(":"))
    end_hour, end_minute = map(int, data.time_end.split(":"))

    base_date = datetime.combine(data.date, datetime.min.time())
    period_start = base_date.replace(hour=start_hour, minute=start_minute)
    period_end = base_date.replace(hour=end_hour, minute=end_minute)

    created_slots = []

    # max_attendees für Einzeltermine auf 1 setzen
    max_attendees = data.max_attendees
    if data.slot_type == "individual":
        max_attendees = 1

    if data.slot_duration_minutes == 0:
        # Ein offener Slot für den gesamten Zeitraum
        slot = ViewingSlot(
            property_id=data.property_id,
            start_time=period_start,
            end_time=period_end,
            slot_type=data.slot_type,
            access_type=data.access_type,
            max_attendees=max_attendees,
            notes=data.notes
        )
        db.add(slot)
        created_slots.append(slot)
    else:
        # Mehrere Slots generieren
        current_start = period_start
        slot_duration = timedelta(minutes=data.slot_duration_minutes)

        while current_start + slot_duration <= period_end:
            slot = ViewingSlot(
                property_id=data.property_id,
                start_time=current_start,
                end_time=current_start + slot_duration,
                slot_type=data.slot_type,
                access_type=data.access_type,
                max_attendees=max_attendees,
                notes=data.notes
            )
            db.add(slot)
            created_slots.append(slot)
            current_start += slot_duration

    db.commit()

    # Slots refreshen
    for slot in created_slots:
        db.refresh(slot)

    result = [get_slot_response(slot, db) for slot in created_slots]

    return {
        "items": result,
        "total": len(result)
    }


@router.get("/{slot_id}", response_model=ViewingSlotResponse)
def get_viewing_slot(
    slot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Ruft einen einzelnen Besichtigungstermin ab.

    Args:
        slot_id: UUID des Termins
        db: Datenbank-Session
        current_user: Authentifizierter Benutzer

    Returns:
        Der Termin
    """
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    # Berechtigung prüfen (muss Eigentümer sein)
    property_obj = db.query(Property).filter(Property.id == slot.property_id).first()
    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diesen Termin"
        )

    return get_slot_response(slot, db)


@router.patch("/{slot_id}", response_model=ViewingSlotResponse)
def update_viewing_slot(
    slot_id: UUID,
    slot_data: ViewingSlotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Aktualisiert einen Besichtigungstermin.
    Bei Zeitänderung werden alle Buchenden benachrichtigt.

    Args:
        slot_id: UUID des Termins
        slot_data: Zu aktualisierende Felder
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Der aktualisierte Termin
    """
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    # Berechtigung prüfen
    property_obj = db.query(Property).filter(Property.id == slot.property_id).first()
    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diesen Termin"
        )

    # Alte Zeiten speichern für Vergleich
    old_start = slot.start_time
    old_end = slot.end_time
    time_changed = False

    # Nur gesetzte Felder aktualisieren
    update_data = slot_data.model_dump(exclude_unset=True)

    # Prüfen ob Zeiten geändert werden
    if "start_time" in update_data or "end_time" in update_data:
        new_start = update_data.get("start_time", slot.start_time)
        new_end = update_data.get("end_time", slot.end_time)
        if new_start != old_start or new_end != old_end:
            time_changed = True

    for field, value in update_data.items():
        setattr(slot, field, value)

    db.commit()
    db.refresh(slot)

    # Bei Zeitänderung: Buchende benachrichtigen
    if time_changed:
        bookings = db.query(Booking).filter(
            Booking.slot_id == slot_id,
            Booking.confirmed == True,
            Booking.cancelled_at == None
        ).all()

        for booking in bookings:
            # Application für Portal-Token holen
            portal_token = None
            if booking.application_id:
                app = db.query(Application).filter(
                    Application.id == booking.application_id
                ).first()
                if app:
                    portal_token = app.access_token

            # ICS generieren
            ics_data = generate_ics(
                slot_id=slot.id,
                property_title=property_obj.title,
                property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
                start_time=slot.start_time,
                end_time=slot.end_time,
            )

            # E-Mail senden
            send_viewing_rescheduled_email(
                to=booking.email,
                applicant_name=f"{booking.first_name} {booking.last_name}",
                property_title=property_obj.title,
                property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
                old_date=old_start.strftime("%d.%m.%Y"),
                old_time=old_start.strftime("%H:%M"),
                new_date=slot.start_time.strftime("%d.%m.%Y"),
                new_time=slot.start_time.strftime("%H:%M"),
                portal_token=portal_token or "",
                ics_data=ics_data
            )

    return get_slot_response(slot, db)


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_viewing_slot(
    slot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Löscht einen Besichtigungstermin.
    Alle Buchenden werden per E-Mail benachrichtigt.

    Args:
        slot_id: UUID des Termins
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session
    """
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    # Berechtigung prüfen
    property_obj = db.query(Property).filter(Property.id == slot.property_id).first()
    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diesen Termin"
        )

    # Alle Buchenden benachrichtigen
    bookings = db.query(Booking).filter(
        Booking.slot_id == slot_id,
        Booking.confirmed == True,
        Booking.cancelled_at == None
    ).all()

    for booking in bookings:
        send_viewing_cancelled_email(
            to=booking.email,
            applicant_name=f"{booking.first_name} {booking.last_name}",
            property_title=property_obj.title,
            property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
            viewing_date=slot.start_time.strftime("%d.%m.%Y"),
            viewing_time=slot.start_time.strftime("%H:%M"),
            cancelled_by="landlord"
        )

    # Auch Eingeladene (die noch nicht gebucht haben) benachrichtigen
    invitations = db.query(ViewingInvitation).filter(
        ViewingInvitation.slot_id == slot_id,
        ViewingInvitation.status == "pending"
    ).all()

    for invitation in invitations:
        app = db.query(Application).filter(
            Application.id == invitation.application_id
        ).first()
        if app:
            send_viewing_cancelled_email(
                to=app.email,
                applicant_name=f"{app.first_name} {app.last_name}",
                property_title=property_obj.title,
                property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
                viewing_date=slot.start_time.strftime("%d.%m.%Y"),
                viewing_time=slot.start_time.strftime("%H:%M"),
                cancelled_by="landlord"
            )

    db.delete(slot)
    db.commit()


# ============================================
# Booking Endpoints
# ============================================

@router.get("/{slot_id}/bookings", response_model=BookingListResponse)
def get_slot_bookings(
    slot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Ruft alle Buchungen für einen Slot ab.

    Args:
        slot_id: UUID des Termins
        db: Datenbank-Session
        current_user: Authentifizierter Benutzer

    Returns:
        Liste der Buchungen
    """
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    # Berechtigung prüfen
    property_obj = db.query(Property).filter(Property.id == slot.property_id).first()
    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diesen Termin"
        )

    bookings = db.query(Booking).filter(
        Booking.slot_id == slot_id
    ).order_by(Booking.created_at).all()

    return {
        "items": bookings,
        "total": len(bookings)
    }


@router.post("/{slot_id}/book", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMIT_BOOKING)
def book_viewing_slot(
    request: Request,
    slot_id: UUID,
    booking_data: BookingCreate,
    db: Session = Depends(get_db)
) -> Booking:
    """
    Bucht einen Platz für einen öffentlichen Besichtigungstermin.
    Öffentlicher Endpoint - keine Authentifizierung erforderlich.

    Args:
        request: FastAPI Request (für Rate Limiting)
        slot_id: UUID des Termins
        booking_data: Buchungsdaten
        db: Datenbank-Session

    Returns:
        Die erstellte Buchung
    """
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    # Prüfen ob Termin öffentlich ist
    if slot.access_type != "public":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dieser Termin ist nur für eingeladene Bewerber verfügbar"
        )

    # Prüfen ob noch Plätze verfügbar
    confirmed_count = db.query(Booking).filter(
        Booking.slot_id == slot_id,
        Booking.confirmed == True,
        Booking.cancelled_at == None
    ).count()

    if confirmed_count >= slot.max_attendees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keine Plätze mehr verfügbar"
        )

    # Prüfen ob E-Mail bereits gebucht hat
    existing = db.query(Booking).filter(
        Booking.slot_id == slot_id,
        Booking.email == booking_data.email,
        Booking.cancelled_at == None
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sie haben diesen Termin bereits gebucht"
        )

    # Prüfen ob Termin nicht in der Vergangenheit liegt
    if slot.start_time < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dieser Termin liegt bereits in der Vergangenheit"
        )

    # Buchung erstellen
    booking = Booking(
        slot_id=slot_id,
        first_name=booking_data.first_name,
        last_name=booking_data.last_name,
        email=booking_data.email,
        phone=booking_data.phone,
        application_id=booking_data.application_id
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Bestätigungs-E-Mail senden
    property_obj = db.query(Property).filter(Property.id == slot.property_id).first()
    if property_obj:
        # ICS generieren
        ics_data = generate_ics(
            slot_id=slot.id,
            property_title=property_obj.title,
            property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
            start_time=slot.start_time,
            end_time=slot.end_time,
        )

        # Portal-Token holen wenn Bewerbung verknüpft
        portal_token = ""
        if booking.application_id:
            app = db.query(Application).filter(
                Application.id == booking.application_id
            ).first()
            if app:
                portal_token = app.access_token or ""

        send_viewing_confirmation_email(
            to=booking.email,
            applicant_name=f"{booking.first_name} {booking.last_name}",
            property_title=property_obj.title,
            property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
            viewing_date=slot.start_time.strftime("%d.%m.%Y"),
            viewing_time=slot.start_time.strftime("%H:%M"),
            portal_token=portal_token,
            ics_data=ics_data
        )

    return booking


@router.delete("/{slot_id}/bookings/{booking_id}", response_model=BookingCancelResponse)
def cancel_booking(
    slot_id: UUID,
    booking_id: UUID,
    db: Session = Depends(get_db)
) -> dict:
    """
    Storniert eine Buchung (1 Stunde vor Termin Frist).
    Öffentlicher Endpoint.

    Args:
        slot_id: UUID des Termins
        booking_id: UUID der Buchung
        db: Datenbank-Session

    Returns:
        Stornierungsbestätigung
    """
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.slot_id == slot_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buchung nicht gefunden"
        )

    if booking.cancelled_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Buchung wurde bereits storniert"
        )

    # Slot für Fristprüfung laden
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    # Frist prüfen (1 Stunde vor Termin)
    cancellation_deadline = slot.start_time - timedelta(hours=1)
    if datetime.utcnow() > cancellation_deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stornierung nicht mehr möglich (weniger als 1 Stunde vor Termin)"
        )

    # Buchung stornieren
    booking.cancel()
    db.commit()
    db.refresh(booking)

    # Vermieter benachrichtigen
    property_obj = db.query(Property).filter(Property.id == slot.property_id).first()
    if property_obj and property_obj.landlord_id:
        landlord = db.query(User).filter(User.id == property_obj.landlord_id).first()
        if landlord:
            send_viewing_cancelled_email(
                to=landlord.email,
                applicant_name=f"{booking.first_name} {booking.last_name}",
                property_title=property_obj.title,
                property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
                viewing_date=slot.start_time.strftime("%d.%m.%Y"),
                viewing_time=slot.start_time.strftime("%H:%M"),
                cancelled_by="applicant"
            )

    return {
        "success": True,
        "message": "Buchung erfolgreich storniert",
        "booking_id": booking.id,
        "cancelled_at": booking.cancelled_at
    }


# ============================================
# Invitation Endpoints
# ============================================

@router.post("/{slot_id}/invite", response_model=ViewingInvitationResponse)
def invite_applicant(
    slot_id: UUID,
    data: ViewingInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ViewingInvitation:
    """
    Lädt einen Bewerber zu einem Termin ein.

    Args:
        slot_id: UUID des Termins
        data: Einladungsdaten (application_id, send_email)
        db: Datenbank-Session
        current_user: Authentifizierter Benutzer

    Returns:
        Die erstellte Einladung
    """
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    # Berechtigung prüfen
    property_obj = db.query(Property).filter(Property.id == slot.property_id).first()
    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diesen Termin"
        )

    # Application prüfen
    application = db.query(Application).filter(
        Application.id == data.application_id,
        Application.property_id == slot.property_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bewerbung nicht gefunden"
        )

    # Prüfen ob bereits eingeladen
    existing = db.query(ViewingInvitation).filter(
        ViewingInvitation.slot_id == slot_id,
        ViewingInvitation.application_id == data.application_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bewerber wurde bereits zu diesem Termin eingeladen"
        )

    # Einladung erstellen
    invitation = ViewingInvitation(
        slot_id=slot_id,
        application_id=data.application_id
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # E-Mail senden wenn gewünscht
    if data.send_email:
        # ICS generieren
        ics_data = generate_ics(
            slot_id=slot.id,
            property_title=property_obj.title,
            property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
            start_time=slot.start_time,
            end_time=slot.end_time,
            status="TENTATIVE"
        )

        send_viewing_invitation_email(
            to=application.email,
            applicant_name=f"{application.first_name} {application.last_name}",
            property_title=property_obj.title,
            property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
            viewing_date=slot.start_time.strftime("%d.%m.%Y"),
            viewing_time=slot.start_time.strftime("%H:%M"),
            invitation_token=invitation.invitation_token,
            portal_token=application.access_token or "",
            landlord_name=current_user.name,
            ics_data=ics_data
        )

    return invitation


@router.get("/{slot_id}/invitations", response_model=List[ViewingInvitationWithDetails])
def get_slot_invitations(
    slot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[dict]:
    """
    Ruft alle Einladungen für einen Slot ab, inkl. Bewerber-Details.

    Args:
        slot_id: UUID des Termins
        db: Datenbank-Session
        current_user: Authentifizierter Benutzer

    Returns:
        Liste der Einladungen mit Bewerber-Namen
    """
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    # Berechtigung prüfen
    property_obj = db.query(Property).filter(Property.id == slot.property_id).first()
    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diesen Termin"
        )

    invitations = db.query(ViewingInvitation).filter(
        ViewingInvitation.slot_id == slot_id
    ).order_by(ViewingInvitation.invited_at).all()

    # Bewerber-Details hinzufügen
    result = []
    for inv in invitations:
        application = db.query(Application).filter(
            Application.id == inv.application_id
        ).first()

        result.append({
            "id": inv.id,
            "slot_id": inv.slot_id,
            "application_id": inv.application_id,
            "status": inv.status,
            "invited_at": inv.invited_at,
            "responded_at": inv.responded_at,
            "invitation_token": inv.invitation_token,
            "created_at": inv.created_at,
            "updated_at": inv.updated_at,
            "applicant_name": f"{application.first_name} {application.last_name}" if application else "Unbekannt",
            "applicant_email": application.email if application else "",
            "slot_start_time": slot.start_time,
            "slot_end_time": slot.end_time,
        })

    return result


@router.get("/application/{application_id}/invitations")
def get_application_invitations(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[dict]:
    """
    Ruft alle Einladungen für eine Bewerbung ab.

    Args:
        application_id: UUID der Bewerbung
        db: Datenbank-Session
        current_user: Authentifizierter Benutzer

    Returns:
        Liste der Einladungen mit Termin-Details
    """
    # Bewerbung prüfen
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bewerbung nicht gefunden"
        )

    # Berechtigung prüfen (muss Eigentümer der Property sein)
    property_obj = db.query(Property).filter(
        Property.id == application.property_id
    ).first()

    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Bewerbung"
        )

    invitations = db.query(ViewingInvitation).filter(
        ViewingInvitation.application_id == application_id
    ).order_by(ViewingInvitation.invited_at.desc()).all()

    result = []
    for inv in invitations:
        slot = db.query(ViewingSlot).filter(
            ViewingSlot.id == inv.slot_id
        ).first()

        if slot:
            result.append({
                "id": str(inv.id),
                "slot_id": str(inv.slot_id),
                "status": inv.status,
                "invited_at": inv.invited_at.isoformat(),
                "responded_at": inv.responded_at.isoformat() if inv.responded_at else None,
                "slot_start_time": slot.start_time.isoformat(),
                "slot_end_time": slot.end_time.isoformat(),
                "slot_type": slot.slot_type,
            })

    return result


# ============================================
# Public Invitation Response Endpoints
# ============================================

@router.get("/invitation/{token}")
def get_invitation_by_token(
    token: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Ruft eine Einladung über den Token ab (öffentlich).

    Args:
        token: Einladungs-Token
        db: Datenbank-Session

    Returns:
        Einladungsdetails
    """
    invitation = db.query(ViewingInvitation).filter(
        ViewingInvitation.invitation_token == token
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Einladung nicht gefunden oder ungültig"
        )

    slot = db.query(ViewingSlot).filter(ViewingSlot.id == invitation.slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Termin nicht mehr verfügbar"
        )

    property_obj = db.query(Property).filter(Property.id == slot.property_id).first()

    return {
        "invitation_id": invitation.id,
        "status": invitation.status,
        "viewing_slot": {
            "id": slot.id,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "slot_type": slot.slot_type
        },
        "property": {
            "title": property_obj.title if property_obj else "Unbekannt",
            "address": f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}" if property_obj else "Unbekannt"
        }
    }


@router.post("/invitation/{token}/respond", response_model=BookingResponse)
def respond_to_invitation(
    token: str,
    data: ViewingInvitationRespondRequest,
    db: Session = Depends(get_db)
) -> Booking | dict:
    """
    Antwortet auf eine Besichtigungseinladung (öffentlich).

    Args:
        token: Einladungs-Token
        data: Response (accept/decline)
        db: Datenbank-Session

    Returns:
        Bei accept: Die erstellte Buchung
        Bei decline: Bestätigung
    """
    invitation = db.query(ViewingInvitation).filter(
        ViewingInvitation.invitation_token == token
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Einladung nicht gefunden oder ungültig"
        )

    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Einladung wurde bereits {invitation.status}"
        )

    slot = db.query(ViewingSlot).filter(ViewingSlot.id == invitation.slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Termin nicht mehr verfügbar"
        )

    # Prüfen ob Termin nicht in der Vergangenheit liegt
    if slot.start_time < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dieser Termin liegt bereits in der Vergangenheit"
        )

    application = db.query(Application).filter(
        Application.id == invitation.application_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bewerbung nicht mehr verfügbar"
        )

    if data.response == "decline":
        invitation.decline()
        db.commit()
        # Return a minimal response for decline
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Einladung abgelehnt"
        )

    # Accept: Prüfen ob noch Plätze verfügbar
    confirmed_count = db.query(Booking).filter(
        Booking.slot_id == slot.id,
        Booking.confirmed == True,
        Booking.cancelled_at == None
    ).count()

    if confirmed_count >= slot.max_attendees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leider sind keine Plätze mehr verfügbar"
        )

    # Einladung annehmen
    invitation.accept()

    # Buchung erstellen
    booking = Booking(
        slot_id=slot.id,
        first_name=application.first_name,
        last_name=application.last_name,
        email=application.email,
        phone=application.phone,
        application_id=application.id,
        invitation_id=invitation.id
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Bestätigungs-E-Mail senden
    property_obj = db.query(Property).filter(Property.id == slot.property_id).first()
    if property_obj:
        ics_data = generate_ics(
            slot_id=slot.id,
            property_title=property_obj.title,
            property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
            start_time=slot.start_time,
            end_time=slot.end_time,
        )

        send_viewing_confirmation_email(
            to=application.email,
            applicant_name=f"{application.first_name} {application.last_name}",
            property_title=property_obj.title,
            property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
            viewing_date=slot.start_time.strftime("%d.%m.%Y"),
            viewing_time=slot.start_time.strftime("%H:%M"),
            portal_token=application.access_token or "",
            ics_data=ics_data
        )

    return booking
