"""
Pydantic Schemas für Application/Bewerbungen.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class ApplicationBase(BaseModel):
    """Basis-Schema für Bewerbungs-Daten."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    message: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    """Schema für Bewerbungs-Erstellung."""
    property_id: UUID


class ApplicationUpdate(BaseModel):
    """
    Schema für Bewerbungs-Aktualisierung.
    Nur Vermieter können diese Felder ändern.
    """
    landlord_notes: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)  # 1-5 Sterne
    status: Optional[str] = Field(
        None,
        pattern="^(neu|in_pruefung|akzeptiert|abgelehnt)$"
    )


class ApplicationDocumentInfo(BaseModel):
    """Dokument-Info für Vermieter-Ansicht."""
    id: UUID
    filename: str
    display_name: Optional[str] = None
    category: str
    category_label: str
    url: str
    file_size: int
    file_size_formatted: str
    created_at: datetime


class ApplicationResponse(ApplicationBase):
    """Schema für Bewerbungs-Response."""
    id: UUID
    property_id: UUID
    landlord_notes: Optional[str] = None
    rating: Optional[int] = None
    status: str
    is_email_verified: bool = False
    has_self_disclosure: bool = False
    documents: List[ApplicationDocumentInfo] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationCreateResponse(ApplicationBase):
    """
    Schema für Bewerbungs-Erstellungs-Response.
    Enthält zusätzlich den access_token für das Bewerber-Portal.
    """
    id: UUID
    property_id: UUID
    status: str
    is_email_verified: bool = False
    access_token: str  # Für Bewerber-Portal-Zugang
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationVerificationResponse(BaseModel):
    """Schema für Bewerbungs-Verifizierungs-Response."""
    message: str
    success: bool
    property_title: Optional[str] = None


class ApplicationListResponse(BaseModel):
    """Schema für Bewerbungs-Listen-Response."""
    items: list[ApplicationResponse]
    total: int


# Kategorie-Labels für Dokumente
DOCUMENT_CATEGORY_LABELS = {
    "gehaltsnachweis": "Gehaltsnachweis",
    "schufa": "SCHUFA-Auskunft",
    "ausweis": "Personalausweis/Reisepass",
    "mietschuldenfreiheit": "Mietschuldenfreiheitsbescheinigung",
    "arbeitsvertrag": "Arbeitsvertrag",
    "sonstiges": "Sonstiges"
}


def format_file_size(size_bytes: int) -> str:
    """Formatiert Dateigröße lesbar."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def application_to_response(application) -> dict:
    """Konvertiert Application Model zu Response dict mit Dokumenten."""
    documents = []
    if hasattr(application, 'documents') and application.documents:
        for doc in application.documents:
            documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "display_name": doc.display_name,
                "category": doc.category,
                "category_label": DOCUMENT_CATEGORY_LABELS.get(doc.category, doc.category),
                "url": f"/static/{doc.filepath}",
                "file_size": doc.file_size,
                "file_size_formatted": format_file_size(doc.file_size),
                "created_at": doc.created_at
            })

    return {
        "id": application.id,
        "property_id": application.property_id,
        "first_name": application.first_name,
        "last_name": application.last_name,
        "email": application.email,
        "phone": application.phone,
        "message": application.message,
        "landlord_notes": application.landlord_notes,
        "rating": application.rating,
        "status": application.status,
        "is_email_verified": application.is_email_verified,
        "has_self_disclosure": application.self_disclosure is not None,
        "documents": documents,
        "created_at": application.created_at,
        "updated_at": application.updated_at
    }
