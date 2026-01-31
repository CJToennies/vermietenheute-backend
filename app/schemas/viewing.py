"""
Pydantic Schemas für ViewingSlot/Besichtigungstermine.
"""
from datetime import datetime, date, time
from typing import Optional, Literal, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# Typen für Slot- und Zugangsart
SlotType = Literal["individual", "group"]
AccessType = Literal["public", "invited"]
InvitationStatus = Literal["pending", "accepted", "declined"]


class ViewingSlotBase(BaseModel):
    """Basis-Schema für Besichtigungstermin-Daten."""
    start_time: datetime
    end_time: datetime
    slot_type: SlotType = "individual"
    access_type: AccessType = "public"
    max_attendees: int = Field(default=1, ge=1, le=100)
    notes: Optional[str] = None

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        """Validiert, dass Endzeit nach Startzeit liegt."""
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError("Endzeit muss nach Startzeit liegen")
        return v

    @field_validator("max_attendees")
    @classmethod
    def validate_max_attendees(cls, v: int, info) -> int:
        """Validiert max_attendees basierend auf slot_type."""
        slot_type = info.data.get("slot_type", "individual")
        if slot_type == "individual" and v > 1:
            # Für Einzeltermine max 1 Teilnehmer erlauben
            return 1
        return v


class ViewingSlotCreate(ViewingSlotBase):
    """Schema für Besichtigungstermin-Erstellung."""
    property_id: UUID


class ViewingSlotBulkCreate(BaseModel):
    """Schema für Bulk-Erstellung von Besichtigungsterminen."""
    property_id: UUID
    date: date  # Datum (YYYY-MM-DD)
    time_start: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # "HH:MM"
    time_end: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # "HH:MM"
    slot_duration_minutes: int = Field(default=30, ge=0, le=480)  # 0 = ein offener Slot
    slot_type: SlotType = "individual"
    access_type: AccessType = "public"
    max_attendees: int = Field(default=1, ge=1, le=100)
    notes: Optional[str] = None

    @field_validator("time_end")
    @classmethod
    def end_after_start(cls, v: str, info) -> str:
        """Validiert, dass Endzeit nach Startzeit liegt."""
        start = info.data.get("time_start")
        if start and v <= start:
            raise ValueError("Endzeit muss nach Startzeit liegen")
        return v


class ViewingSlotUpdate(BaseModel):
    """Schema für Besichtigungstermin-Aktualisierung."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    slot_type: Optional[SlotType] = None
    access_type: Optional[AccessType] = None
    max_attendees: Optional[int] = Field(None, ge=1, le=100)
    notes: Optional[str] = None


class ViewingSlotResponse(BaseModel):
    """Schema für Besichtigungstermin-Response."""
    id: UUID
    property_id: UUID
    start_time: datetime
    end_time: datetime
    slot_type: SlotType
    access_type: AccessType
    max_attendees: int
    notes: Optional[str] = None
    available_spots: int
    bookings_count: int = 0
    invitations_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ViewingSlotListResponse(BaseModel):
    """Schema für Besichtigungstermin-Listen-Response."""
    items: list[ViewingSlotResponse]
    total: int


class ViewingSlotWithProperty(ViewingSlotResponse):
    """Schema für Besichtigungstermin mit Property-Infos."""
    property_title: str
    property_address: str
    property_city: str


# ============================================
# Einladungs-Schemas
# ============================================

class ViewingInviteRequest(BaseModel):
    """Schema für Einladung eines Bewerbers."""
    application_id: UUID
    send_email: bool = True


class ViewingInvitationResponse(BaseModel):
    """Schema für Einladungs-Response."""
    id: UUID
    slot_id: UUID
    application_id: UUID
    status: InvitationStatus
    invited_at: datetime
    responded_at: Optional[datetime] = None
    invitation_token: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ViewingInvitationWithDetails(ViewingInvitationResponse):
    """Schema für Einladung mit Details."""
    applicant_name: str
    applicant_email: str
    slot_start_time: datetime
    slot_end_time: datetime


class ViewingInvitationRespondRequest(BaseModel):
    """Schema für Antwort auf Einladung."""
    response: Literal["accept", "decline"]


# ============================================
# Public Viewing Schemas (für Bewerber-Portal)
# ============================================

class PublicViewingSlot(BaseModel):
    """Öffentliches Schema für Besichtigungstermine (im Bewerber-Portal)."""
    id: UUID
    start_time: datetime
    end_time: datetime
    slot_type: SlotType
    available_spots: int
    is_fully_booked: bool

    class Config:
        from_attributes = True


class PortalViewingInvitation(BaseModel):
    """Schema für Einladungen im Bewerber-Portal."""
    id: UUID
    status: InvitationStatus
    invited_at: datetime
    responded_at: Optional[datetime] = None
    viewing_slot: PublicViewingSlot
    property_title: str
    property_address: str

    class Config:
        from_attributes = True


class PortalViewingBooking(BaseModel):
    """Schema für Buchungen im Bewerber-Portal."""
    id: UUID
    slot_id: UUID
    confirmed: bool
    cancelled_at: Optional[datetime] = None
    viewing_slot: PublicViewingSlot
    property_title: str
    property_address: str
    created_at: datetime

    class Config:
        from_attributes = True
