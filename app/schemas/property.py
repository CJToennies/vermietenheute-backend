"""
Pydantic Schemas für Property/Immobilien.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PropertyBase(BaseModel):
    """Basis-Schema für Immobilien-Daten."""
    title: str = Field(..., min_length=1, max_length=200)
    type: str = Field(..., min_length=1, max_length=50)  # wohnung, haus, zimmer
    description: Optional[str] = None
    address: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    zip_code: str = Field(..., min_length=1, max_length=10)
    rent: Decimal = Field(..., gt=0, decimal_places=2)
    deposit: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    size: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    rooms: Optional[Decimal] = Field(None, gt=0, decimal_places=1)
    available_from: Optional[date] = None
    furnished: bool = False
    pets_allowed: bool = False
    listing_url: Optional[str] = Field(None, max_length=500)


class PropertyCreate(PropertyBase):
    """Schema für Immobilien-Erstellung."""
    pass


class PropertyUpdate(BaseModel):
    """Schema für Immobilien-Aktualisierung."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    address: Optional[str] = Field(None, min_length=1, max_length=200)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    zip_code: Optional[str] = Field(None, min_length=1, max_length=10)
    rent: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    deposit: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    size: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    rooms: Optional[Decimal] = Field(None, gt=0, decimal_places=1)
    available_from: Optional[date] = None
    furnished: Optional[bool] = None
    pets_allowed: Optional[bool] = None
    listing_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class PropertyResponse(PropertyBase):
    """Schema für Immobilien-Response."""
    id: UUID
    landlord_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    """Schema für Immobilien-Listen-Response mit Pagination."""
    items: list[PropertyResponse]
    total: int
    page: int
    per_page: int
