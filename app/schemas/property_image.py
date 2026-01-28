"""
Pydantic Schemas für PropertyImage/Bilder.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class PropertyImageBase(BaseModel):
    """Basis-Schema für Bilder."""
    filename: str
    order: int = 0


class PropertyImageCreate(PropertyImageBase):
    """Schema für Bild-Erstellung (intern verwendet)."""
    filepath: str
    property_id: UUID


class PropertyImageResponse(BaseModel):
    """Schema für Bild-Response."""
    id: UUID
    property_id: UUID
    filename: str
    filepath: str
    url: str  # Vollständige URL zum Bild
    order: int
    created_at: datetime

    class Config:
        from_attributes = True


class PropertyImageListResponse(BaseModel):
    """Schema für Bilder-Listen-Response."""
    items: list[PropertyImageResponse]
    total: int
