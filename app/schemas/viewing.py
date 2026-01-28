"""
Pydantic Schemas für ViewingSlot/Besichtigungstermine.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ViewingSlotBase(BaseModel):
    """Basis-Schema für Besichtigungstermin-Daten."""
    start_time: datetime
    end_time: datetime
    max_attendees: int = Field(default=10, ge=1, le=100)

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        """Validiert, dass Endzeit nach Startzeit liegt."""
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError("Endzeit muss nach Startzeit liegen")
        return v


class ViewingSlotCreate(ViewingSlotBase):
    """Schema für Besichtigungstermin-Erstellung."""
    property_id: UUID


class ViewingSlotUpdate(BaseModel):
    """Schema für Besichtigungstermin-Aktualisierung."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_attendees: Optional[int] = Field(None, ge=1, le=100)


class ViewingSlotResponse(ViewingSlotBase):
    """Schema für Besichtigungstermin-Response."""
    id: UUID
    property_id: UUID
    available_spots: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ViewingSlotListResponse(BaseModel):
    """Schema für Besichtigungstermin-Listen-Response."""
    items: list[ViewingSlotResponse]
    total: int
