"""
Pydantic Schemas für Application/Bewerbungen.
"""
from datetime import datetime
from typing import Optional
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


class ApplicationResponse(ApplicationBase):
    """Schema für Bewerbungs-Response."""
    id: UUID
    property_id: UUID
    landlord_notes: Optional[str] = None
    rating: Optional[int] = None
    status: str
    is_email_verified: bool = False
    has_self_disclosure: bool = False
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
