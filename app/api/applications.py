"""
API-Endpoints für Bewerbungen (Applications).
Erstellen und Verwalten von Mietbewerbungen mit E-Mail-Verifizierung.
"""
import secrets
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.core.email import send_application_portal_email
from app.core.rate_limit import limiter, RATE_LIMIT_APPLICATION
from app.config import settings
from app.models.user import User
from app.models.property import Property
from app.models.application import Application
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse, ApplicationCreateResponse, ApplicationVerificationResponse
)


router = APIRouter()


@router.post("", response_model=ApplicationCreateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMIT_APPLICATION)
def create_application(
    request: Request,
    application_data: ApplicationCreate,
    db: Session = Depends(get_db)
) -> Application:
    """
    Erstellt eine neue Bewerbung für eine Immobilie.
    Öffentlicher Endpoint - keine Authentifizierung erforderlich.
    Sendet eine Verifizierungs-E-Mail an den Bewerber.

    Args:
        request: FastAPI Request (für Rate Limiting)
        application_data: Bewerbungsdaten inkl. property_id
        db: Datenbank-Session

    Returns:
        Die erstellte Bewerbung

    Raises:
        HTTPException 404: Wenn Immobilie nicht gefunden
        HTTPException 400: Wenn Immobilie nicht verfügbar
    """
    # Prüfen ob Immobilie existiert und aktiv ist
    property_obj = db.query(Property).filter(
        Property.id == application_data.property_id
    ).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht gefunden"
        )

    if not property_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Immobilie ist nicht mehr verfügbar"
        )

    # Prüfen ob bereits eine Bewerbung mit dieser E-Mail existiert
    existing = db.query(Application).filter(
        Application.property_id == application_data.property_id,
        Application.email == application_data.email
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sie haben sich bereits für diese Immobilie beworben"
        )

    # Tokens generieren
    verification_token = secrets.token_urlsafe(32)
    access_token = secrets.token_urlsafe(32)
    token_expires = datetime.utcnow() + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)

    # Bewerbung erstellen
    application = Application(
        **application_data.model_dump(),
        is_email_verified=False,
        email_verification_token=verification_token,
        email_verification_expires=token_expires,
        access_token=access_token
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    # Portal-E-Mail senden (mit Verifizierungslink und Portal-Link)
    applicant_name = f"{application.first_name} {application.last_name}"
    send_application_portal_email(
        to=application.email,
        verification_token=verification_token,
        access_token=access_token,
        property_title=property_obj.title,
        applicant_name=applicant_name
    )

    return application


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Application:
    """
    Ruft eine einzelne Bewerbung ab.
    Nur der Eigentümer der zugehörigen Immobilie kann die Bewerbung sehen.

    Args:
        application_id: UUID der Bewerbung
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Die Bewerbung

    Raises:
        HTTPException 404: Wenn Bewerbung nicht gefunden
        HTTPException 403: Wenn keine Berechtigung
    """
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bewerbung nicht gefunden"
        )

    # Prüfen ob Benutzer Eigentümer der Immobilie ist
    property_obj = db.query(Property).filter(
        Property.id == application.property_id
    ).first()

    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Bewerbung"
        )

    return application


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: UUID,
    application_data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Application:
    """
    Aktualisiert eine Bewerbung (Notizen, Rating, Status).
    Nur der Eigentümer der zugehörigen Immobilie kann die Bewerbung bearbeiten.

    Args:
        application_id: UUID der Bewerbung
        application_data: Zu aktualisierende Felder
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Die aktualisierte Bewerbung

    Raises:
        HTTPException 404: Wenn Bewerbung nicht gefunden
        HTTPException 403: Wenn keine Berechtigung
    """
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bewerbung nicht gefunden"
        )

    # Prüfen ob Benutzer Eigentümer der Immobilie ist
    property_obj = db.query(Property).filter(
        Property.id == application.property_id
    ).first()

    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Bewerbung"
        )

    # Nur gesetzte Felder aktualisieren
    update_data = application_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)

    return application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Löscht eine Bewerbung.
    Nur der Eigentümer der zugehörigen Immobilie kann die Bewerbung löschen.

    Args:
        application_id: UUID der Bewerbung
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Raises:
        HTTPException 404: Wenn Bewerbung nicht gefunden
        HTTPException 403: Wenn keine Berechtigung
    """
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bewerbung nicht gefunden"
        )

    # Prüfen ob Benutzer Eigentümer der Immobilie ist
    property_obj = db.query(Property).filter(
        Property.id == application.property_id
    ).first()

    if not property_obj or property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Bewerbung"
        )

    db.delete(application)
    db.commit()


@router.get("/verify/{token}", response_model=ApplicationVerificationResponse)
def verify_application_email(
    token: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Verifiziert die E-Mail-Adresse eines Bewerbers.

    Args:
        token: Verifizierungstoken aus der E-Mail
        db: Datenbank-Session

    Returns:
        Erfolgsmeldung mit Immobilientitel

    Raises:
        HTTPException 400: Wenn Token ungültig oder abgelaufen
    """
    # Bewerbung mit Token suchen
    application = db.query(Application).filter(
        Application.email_verification_token == token
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger Verifizierungslink"
        )

    # Immobilie für Titel laden
    property_obj = db.query(Property).filter(
        Property.id == application.property_id
    ).first()
    property_title = property_obj.title if property_obj else "Unbekannt"

    # Prüfen ob bereits verifiziert
    if application.is_email_verified:
        return {
            "message": "E-Mail-Adresse wurde bereits verifiziert",
            "success": True,
            "property_title": property_title
        }

    # Prüfen ob Token abgelaufen
    if application.email_verification_expires and application.email_verification_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verifizierungslink ist abgelaufen"
        )

    # Bewerbung verifizieren
    application.is_email_verified = True
    application.email_verification_token = None
    application.email_verification_expires = None

    db.commit()

    return {
        "message": "E-Mail-Adresse erfolgreich verifiziert",
        "success": True,
        "property_title": property_title
    }
