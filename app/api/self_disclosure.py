"""
API-Endpoints für Selbstauskunft.
Erstellen, Abrufen und Aktualisieren von Mieter-Selbstauskünften.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.self_disclosure import SelfDisclosure
from app.schemas.self_disclosure import (
    SelfDisclosureCreate,
    SelfDisclosureUpdate,
    SelfDisclosureResponse
)


router = APIRouter()


@router.post(
    "/{application_id}/self-disclosure",
    response_model=SelfDisclosureResponse,
    status_code=status.HTTP_201_CREATED
)
def create_self_disclosure(
    application_id: uuid.UUID,
    data: SelfDisclosureCreate,
    db: Session = Depends(get_db)
) -> SelfDisclosure:
    """
    Erstellt eine Selbstauskunft für eine Bewerbung.

    Öffentlicher Endpoint - keine Authentifizierung erforderlich.
    Der Interessent kann seine Selbstauskunft nach der Bewerbung ausfüllen.

    Args:
        application_id: UUID der Bewerbung
        data: Selbstauskunft-Daten
        db: Datenbank-Session

    Returns:
        Erstellte Selbstauskunft

    Raises:
        HTTPException 404: Wenn Bewerbung nicht gefunden
        HTTPException 400: Wenn bereits eine Selbstauskunft existiert
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

    # Prüfen ob bereits eine Selbstauskunft existiert
    existing = db.query(SelfDisclosure).filter(
        SelfDisclosure.application_id == application_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Für diese Bewerbung existiert bereits eine Selbstauskunft"
        )

    # Selbstauskunft erstellen
    self_disclosure = SelfDisclosure(
        application_id=application_id,
        **data.model_dump()
    )

    db.add(self_disclosure)
    db.commit()
    db.refresh(self_disclosure)

    return self_disclosure


@router.get(
    "/{application_id}/self-disclosure",
    response_model=SelfDisclosureResponse
)
def get_self_disclosure(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SelfDisclosure:
    """
    Ruft die Selbstauskunft einer Bewerbung ab.

    Nur der Vermieter der zugehörigen Immobilie kann die Selbstauskunft einsehen.

    Args:
        application_id: UUID der Bewerbung
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Selbstauskunft

    Raises:
        HTTPException 404: Wenn Bewerbung oder Selbstauskunft nicht gefunden
        HTTPException 403: Wenn keine Berechtigung
    """
    # Bewerbung mit Property laden
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bewerbung nicht gefunden"
        )

    # Berechtigung prüfen (nur Vermieter der Immobilie)
    if application.property.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Bewerbung"
        )

    # Selbstauskunft abrufen
    self_disclosure = db.query(SelfDisclosure).filter(
        SelfDisclosure.application_id == application_id
    ).first()

    if not self_disclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keine Selbstauskunft vorhanden"
        )

    return self_disclosure


@router.patch(
    "/{application_id}/self-disclosure",
    response_model=SelfDisclosureResponse
)
def update_self_disclosure(
    application_id: uuid.UUID,
    data: SelfDisclosureUpdate,
    db: Session = Depends(get_db)
) -> SelfDisclosure:
    """
    Aktualisiert eine Selbstauskunft.

    Öffentlicher Endpoint - keine Authentifizierung erforderlich.
    Der Interessent kann seine Selbstauskunft nachträglich bearbeiten.

    Args:
        application_id: UUID der Bewerbung
        data: Update-Daten
        db: Datenbank-Session

    Returns:
        Aktualisierte Selbstauskunft

    Raises:
        HTTPException 404: Wenn Selbstauskunft nicht gefunden
    """
    # Selbstauskunft suchen
    self_disclosure = db.query(SelfDisclosure).filter(
        SelfDisclosure.application_id == application_id
    ).first()

    if not self_disclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keine Selbstauskunft vorhanden"
        )

    # Nur gesetzte Felder aktualisieren
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(self_disclosure, field, value)

    db.commit()
    db.refresh(self_disclosure)

    return self_disclosure


@router.get(
    "/{application_id}/self-disclosure/exists"
)
def check_self_disclosure_exists(
    application_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> dict:
    """
    Prüft ob eine Selbstauskunft für eine Bewerbung existiert.

    Öffentlicher Endpoint - für den Interessenten zum Prüfen.

    Args:
        application_id: UUID der Bewerbung
        db: Datenbank-Session

    Returns:
        {"exists": true/false}
    """
    exists = db.query(SelfDisclosure).filter(
        SelfDisclosure.application_id == application_id
    ).first() is not None

    return {"exists": exists}
