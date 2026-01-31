"""
Pydantic Schemas für Booking/Buchungen.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class BookingBase(BaseModel):
    """Basis-Schema für Buchungs-Daten."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)


class BookingCreate(BookingBase):
    """Schema für Buchungs-Erstellung (öffentlich)."""
    application_id: Optional[UUID] = None  # Optional: Verknüpfung mit Bewerbung


class BookingFromInvitation(BaseModel):
    """Schema für Buchung über Einladung."""
    # Keine zusätzlichen Daten nötig - werden aus Einladung übernommen
    pass


class BookingResponse(BookingBase):
    """Schema für Buchungs-Response."""
    id: UUID
    slot_id: UUID
    confirmed: bool
    application_id: Optional[UUID] = None
    invitation_id: Optional[UUID] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingWithSlotInfo(BookingResponse):
    """Schema für Buchung mit Slot-Informationen."""
    slot_start_time: datetime
    slot_end_time: datetime
    property_title: str
    property_address: str


class BookingListResponse(BaseModel):
    """Schema für Buchungs-Listen-Response."""
    items: list[BookingResponse]
    total: int


class BookingCancelResponse(BaseModel):
    """Schema für Stornierungsbestätigung."""
    success: bool
    message: str
    booking_id: UUID
    cancelled_at: datetime
