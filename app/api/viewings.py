"""
API-Endpoints für Besichtigungstermine (Viewings) und Buchungen.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.core.rate_limit import limiter, RATE_LIMIT_BOOKING
from app.models.user import User
from app.models.property import Property
from app.models.viewing import ViewingSlot
from app.models.booking import Booking
from app.schemas.viewing import (
    ViewingSlotCreate, ViewingSlotUpdate, ViewingSlotResponse, ViewingSlotListResponse
)
from app.schemas.booking import BookingCreate, BookingResponse


router = APIRouter()


@router.get("", response_model=ViewingSlotListResponse)
def list_viewing_slots(
    property_id: Optional[UUID] = Query(None, description="Filter nach Immobilie"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Listet alle Besichtigungstermine.

    Args:
        property_id: Optional - Filter nach Immobilien-ID
        db: Datenbank-Session

    Returns:
        Liste der Besichtigungstermine
    """
    query = db.query(ViewingSlot)

    if property_id:
        query = query.filter(ViewingSlot.property_id == property_id)

    slots = query.order_by(ViewingSlot.start_time).all()

    # Verfügbare Plätze berechnen
    result = []
    for slot in slots:
        confirmed_count = db.query(Booking).filter(
            Booking.slot_id == slot.id,
            Booking.confirmed == True
        ).count()
        slot_dict = {
            "id": slot.id,
            "property_id": slot.property_id,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "max_attendees": slot.max_attendees,
            "available_spots": slot.max_attendees - confirmed_count,
            "created_at": slot.created_at,
            "updated_at": slot.updated_at
        }
        result.append(slot_dict)

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
    Nur der Eigentümer der Immobilie kann Termine erstellen.

    Args:
        slot_data: Termindaten inkl. property_id
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Der erstellte Termin

    Raises:
        HTTPException 404: Wenn Immobilie nicht gefunden
        HTTPException 403: Wenn keine Berechtigung
    """
    # Prüfen ob Immobilie existiert und Benutzer Eigentümer ist
    property_obj = db.query(Property).filter(
        Property.id == slot_data.property_id
    ).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht gefunden"
        )

    if property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Immobilie"
        )

    # Termin erstellen
    slot = ViewingSlot(**slot_data.model_dump())

    db.add(slot)
    db.commit()
    db.refresh(slot)

    return {
        "id": slot.id,
        "property_id": slot.property_id,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "max_attendees": slot.max_attendees,
        "available_spots": slot.max_attendees,
        "created_at": slot.created_at,
        "updated_at": slot.updated_at
    }


@router.get("/{slot_id}", response_model=ViewingSlotResponse)
def get_viewing_slot(
    slot_id: UUID,
    db: Session = Depends(get_db)
) -> dict:
    """
    Ruft einen einzelnen Besichtigungstermin ab.

    Args:
        slot_id: UUID des Termins
        db: Datenbank-Session

    Returns:
        Der Termin

    Raises:
        HTTPException 404: Wenn Termin nicht gefunden
    """
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    confirmed_count = db.query(Booking).filter(
        Booking.slot_id == slot.id,
        Booking.confirmed == True
    ).count()

    return {
        "id": slot.id,
        "property_id": slot.property_id,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "max_attendees": slot.max_attendees,
        "available_spots": slot.max_attendees - confirmed_count,
        "created_at": slot.created_at,
        "updated_at": slot.updated_at
    }


@router.patch("/{slot_id}", response_model=ViewingSlotResponse)
def update_viewing_slot(
    slot_id: UUID,
    slot_data: ViewingSlotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Aktualisiert einen Besichtigungstermin.

    Args:
        slot_id: UUID des Termins
        slot_data: Zu aktualisierende Felder
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Der aktualisierte Termin

    Raises:
        HTTPException 404: Wenn Termin nicht gefunden
        HTTPException 403: Wenn keine Berechtigung
    """
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    # Berechtigung prüfen
    property_obj = db.query(Property).filter(
        Property.id == slot.property_id
    ).first()

    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diesen Termin"
        )

    # Nur gesetzte Felder aktualisieren
    update_data = slot_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(slot, field, value)

    db.commit()
    db.refresh(slot)

    confirmed_count = db.query(Booking).filter(
        Booking.slot_id == slot.id,
        Booking.confirmed == True
    ).count()

    return {
        "id": slot.id,
        "property_id": slot.property_id,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "max_attendees": slot.max_attendees,
        "available_spots": slot.max_attendees - confirmed_count,
        "created_at": slot.created_at,
        "updated_at": slot.updated_at
    }


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_viewing_slot(
    slot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Löscht einen Besichtigungstermin.

    Args:
        slot_id: UUID des Termins
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Raises:
        HTTPException 404: Wenn Termin nicht gefunden
        HTTPException 403: Wenn keine Berechtigung
    """
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    # Berechtigung prüfen
    property_obj = db.query(Property).filter(
        Property.id == slot.property_id
    ).first()

    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diesen Termin"
        )

    db.delete(slot)
    db.commit()


@router.post("/{slot_id}/book", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMIT_BOOKING)
def book_viewing_slot(
    request: Request,
    slot_id: UUID,
    booking_data: BookingCreate,
    db: Session = Depends(get_db)
) -> Booking:
    """
    Bucht einen Platz für einen Besichtigungstermin.
    Öffentlicher Endpoint - keine Authentifizierung erforderlich.

    Args:
        request: FastAPI Request (für Rate Limiting)
        slot_id: UUID des Termins
        booking_data: Buchungsdaten
        db: Datenbank-Session

    Returns:
        Die erstellte Buchung

    Raises:
        HTTPException 404: Wenn Termin nicht gefunden
        HTTPException 400: Wenn keine Plätze mehr verfügbar
    """
    slot = db.query(ViewingSlot).filter(ViewingSlot.id == slot_id).first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Besichtigungstermin nicht gefunden"
        )

    # Prüfen ob noch Plätze verfügbar
    confirmed_count = db.query(Booking).filter(
        Booking.slot_id == slot_id,
        Booking.confirmed == True
    ).count()

    if confirmed_count >= slot.max_attendees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keine Plätze mehr verfügbar"
        )

    # Prüfen ob E-Mail bereits gebucht hat
    existing = db.query(Booking).filter(
        Booking.slot_id == slot_id,
        Booking.email == booking_data.email
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sie haben diesen Termin bereits gebucht"
        )

    # Buchung erstellen
    booking = Booking(
        slot_id=slot_id,
        **booking_data.model_dump()
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return booking
