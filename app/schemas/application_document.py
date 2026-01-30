"""
Pydantic Schemas für ApplicationDocument/Bewerber-Dokumente.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# Erlaubte Dokument-Kategorien
DOCUMENT_CATEGORIES = [
    "gehaltsnachweis",
    "schufa",
    "ausweis",
    "mietschuldenfreiheit",
    "arbeitsvertrag",
    "sonstiges"
]

CATEGORY_LABELS = {
    "gehaltsnachweis": "Gehaltsnachweis",
    "schufa": "SCHUFA-Auskunft",
    "ausweis": "Personalausweis/Reisepass",
    "mietschuldenfreiheit": "Mietschuldenfreiheitsbescheinigung",
    "arbeitsvertrag": "Arbeitsvertrag",
    "sonstiges": "Sonstiges"
}


class ApplicationDocumentBase(BaseModel):
    """Basis-Schema für Dokument-Daten."""
    category: str = Field(..., pattern="^(gehaltsnachweis|schufa|ausweis|mietschuldenfreiheit|arbeitsvertrag|sonstiges)$")
    display_name: Optional[str] = Field(None, max_length=255)


class ApplicationDocumentCreate(ApplicationDocumentBase):
    """Schema für Dokument-Upload (wird aus Form-Data erstellt)."""
    pass


class ApplicationDocumentResponse(BaseModel):
    """Schema für Dokument-Response."""
    id: UUID
    application_id: UUID
    filename: str
    display_name: Optional[str] = None
    category: str
    category_label: str
    filepath: str
    url: str
    file_size: int
    file_size_formatted: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationDocumentListResponse(BaseModel):
    """Schema für Dokument-Listen-Response."""
    items: List[ApplicationDocumentResponse]
    total: int
    total_size: int  # Gesamtgröße in Bytes
    total_size_formatted: str
    max_size: int  # Max erlaubte Größe
    remaining_size: int  # Verbleibende Größe


class DocumentUploadResponse(BaseModel):
    """Schema für Upload-Response."""
    message: str
    document: ApplicationDocumentResponse
