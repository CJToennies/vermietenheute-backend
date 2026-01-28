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
    """Schema für Buchungs-Erstellung."""
    pass


class BookingResponse(BookingBase):
    """Schema für Buchungs-Response."""
    id: UUID
    slot_id: UUID
    confirmed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    """Schema für Buchungs-Listen-Response."""
    items: list[BookingResponse]
    total: int
