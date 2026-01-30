"""
API-Endpoints für das Bewerber-Portal.
Ermöglicht Bewerbern ihre Bewerbung zu verwalten.
"""
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.core.storage import delete_folder
from app.models.application import Application
from app.models.application_document import ApplicationDocument
from app.models.property import Property
from app.models.self_disclosure import SelfDisclosure
from app.schemas.application_document import CATEGORY_LABELS


router = APIRouter()


def format_file_size(size_bytes: int) -> str:
    """Formatiert Dateigröße lesbar."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


# Response Schemas
class PropertyInfo(BaseModel):
    """Kurzinfo zur Immobilie."""
    id: UUID
    title: str
    address: str
    city: str
    zip_code: str
    rent: float


class DocumentInfo(BaseModel):
    """Dokumentinfo für Portal."""
    id: UUID
    filename: str
    display_name: Optional[str]
    category: str
    category_label: str
    url: str
    file_size: int
    file_size_formatted: str
    created_at: datetime


class SelfDisclosureInfo(BaseModel):
    """Selbstauskunft-Status."""
    exists: bool
    completed_fields: int
    total_fields: int


class PortalResponse(BaseModel):
    """Vollständige Portal-Response."""
    # Bewerbungsdaten
    application_id: UUID
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    message: Optional[str]
    status: str
    is_email_verified: bool
    created_at: datetime

    # Immobilie
    property: PropertyInfo

    # Selbstauskunft
    self_disclosure: SelfDisclosureInfo

    # Dokumente
    documents: List[DocumentInfo]
    documents_total_size: int
    documents_total_size_formatted: str
    documents_max_size: int
    documents_remaining_size: int


class ApplicationUpdateRequest(BaseModel):
    """Schema für Bewerbungs-Update durch Bewerber."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    message: Optional[str] = None


class ApplicationUpdateResponse(BaseModel):
    """Response für Bewerbungs-Update."""
    message: str
    application_id: UUID
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]


MAX_TOTAL_SIZE = 30 * 1024 * 1024  # 30 MB


def get_application_by_access_token(db: Session, access_token: str) -> Application:
    """Holt Application anhand des access_token."""
    application = db.query(Application).filter(
        Application.access_token == access_token
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bewerbung nicht gefunden oder ungültiger Link"
        )

    return application


def count_self_disclosure_fields(sd: SelfDisclosure) -> tuple:
    """Zählt ausgefüllte Felder in der Selbstauskunft."""
    if not sd:
        return (0, 20)

    fields = [
        sd.geburtsname, sd.staatsangehoerigkeit, sd.familienstand,
        sd.arbeitgeber_name, sd.arbeitgeber_adresse, sd.beschaeftigt_als,
        sd.beschaeftigt_seit, sd.aktueller_vermieter_name,
        sd.aktueller_vermieter_adresse, sd.aktueller_vermieter_telefon,
        sd.nettoeinkommen
    ]

    # Boolean Felder zählen immer als ausgefüllt
    bool_fields = 9  # Die ganzen Ja/Nein Felder

    completed = sum(1 for f in fields if f) + bool_fields
    total = len(fields) + bool_fields

    return (completed, total)


@router.get("/portal/{access_token}", response_model=PortalResponse)
def get_portal_data(
    access_token: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Ruft alle Daten für das Bewerber-Portal ab.

    Args:
        access_token: Zugangstoken der Bewerbung
        db: Datenbank-Session

    Returns:
        Alle relevanten Daten für das Portal
    """
    application = get_application_by_access_token(db, access_token)

    # Property laden
    property_obj = db.query(Property).filter(
        Property.id == application.property_id
    ).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht gefunden"
        )

    # Dokumente laden
    documents = db.query(ApplicationDocument).filter(
        ApplicationDocument.application_id == application.id
    ).order_by(ApplicationDocument.created_at.desc()).all()

    total_size = sum(doc.file_size for doc in documents)

    # Selbstauskunft prüfen
    self_disclosure = application.self_disclosure
    completed, total = count_self_disclosure_fields(self_disclosure)

    return {
        "application_id": application.id,
        "first_name": application.first_name,
        "last_name": application.last_name,
        "email": application.email,
        "phone": application.phone,
        "message": application.message,
        "status": application.status,
        "is_email_verified": application.is_email_verified,
        "created_at": application.created_at,
        "property": {
            "id": property_obj.id,
            "title": property_obj.title,
            "address": property_obj.address,
            "city": property_obj.city,
            "zip_code": property_obj.zip_code,
            "rent": property_obj.rent
        },
        "self_disclosure": {
            "exists": self_disclosure is not None,
            "completed_fields": completed,
            "total_fields": total
        },
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "display_name": doc.display_name,
                "category": doc.category,
                "category_label": CATEGORY_LABELS.get(doc.category, doc.category),
                "url": doc.url,  # Direkte Supabase Storage URL
                "file_size": doc.file_size,
                "file_size_formatted": format_file_size(doc.file_size),
                "created_at": doc.created_at
            }
            for doc in documents
        ],
        "documents_total_size": total_size,
        "documents_total_size_formatted": format_file_size(total_size),
        "documents_max_size": MAX_TOTAL_SIZE,
        "documents_remaining_size": MAX_TOTAL_SIZE - total_size
    }


@router.patch("/portal/{access_token}", response_model=ApplicationUpdateResponse)
def update_application(
    access_token: str,
    data: ApplicationUpdateRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Aktualisiert die Bewerbungsdaten.

    Args:
        access_token: Zugangstoken der Bewerbung
        data: Zu aktualisierende Felder
        db: Datenbank-Session

    Returns:
        Aktualisierte Bewerbungsdaten
    """
    application = get_application_by_access_token(db, access_token)

    # Nur gesetzte Felder aktualisieren
    update_data = data.model_dump(exclude_unset=True)

    # Email-Änderung: Email-Verifizierung zurücksetzen
    if "email" in update_data and update_data["email"] != application.email:
        application.is_email_verified = False
        # TODO: Neue Verifizierungs-Email senden

    for field, value in update_data.items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)

    return {
        "message": "Bewerbung erfolgreich aktualisiert",
        "application_id": application.id,
        "first_name": application.first_name,
        "last_name": application.last_name,
        "email": application.email,
        "phone": application.phone
    }


class DeleteConfirmationRequest(BaseModel):
    """Schema für Lösch-Bestätigung."""
    confirm: bool = False


class DeleteResponse(BaseModel):
    """Schema für Lösch-Response."""
    message: str
    deleted: bool


@router.delete("/portal/{access_token}", response_model=DeleteResponse)
def delete_application(
    access_token: str,
    confirmation: DeleteConfirmationRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Löscht die Bewerbung inkl. aller Dokumente und Selbstauskunft.
    DSGVO-konform: Bewerber kann seine Daten löschen.

    Args:
        access_token: Zugangstoken der Bewerbung
        confirmation: Bestätigung (confirm=True erforderlich)
        db: Datenbank-Session

    Returns:
        Bestätigung der Löschung

    Raises:
        HTTPException 400: Wenn Bestätigung fehlt
        HTTPException 404: Wenn Bewerbung nicht gefunden
    """
    if not confirmation.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bitte bestätigen Sie die Löschung mit confirm=true"
        )

    application = get_application_by_access_token(db, access_token)

    # Dokument-Dateien aus Supabase Storage löschen
    delete_folder(str(application.id))

    # Bewerbung löschen (Cascade löscht Dokumente und Selbstauskunft in DB)
    db.delete(application)
    db.commit()

    return {
        "message": "Bewerbung und alle zugehörigen Daten wurden gelöscht",
        "deleted": True
    }
