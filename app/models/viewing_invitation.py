"""
ViewingInvitation Model - Einladungen für Besichtigungstermine.
"""
import uuid
import secrets
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ViewingInvitation(Base):
    """
    Einladungs-Tabelle für Besichtigungstermine.

    Ermöglicht es Vermietern, Bewerber zu bestimmten Terminen einzuladen.
    Bewerber können die Einladung annehmen oder ablehnen.

    Attributes:
        id: Eindeutige UUID der Einladung
        slot_id: Fremdschlüssel zum Besichtigungstermin
        application_id: Fremdschlüssel zur Bewerbung
        status: Status der Einladung (pending, accepted, declined)
        invited_at: Zeitpunkt der Einladung
        responded_at: Zeitpunkt der Antwort
        invitation_token: Einzigartiger Token für direkten Zugriff
        created_at: Erstellungszeitpunkt
        updated_at: Letzter Änderungszeitpunkt
    """

    __tablename__ = "viewing_invitations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    slot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("viewing_slots.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status = Column(
        String(20),
        default="pending",
        nullable=False
    )  # pending, accepted, declined
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)
    invitation_token = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: secrets.token_urlsafe(32)
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Beziehungen
    viewing_slot = relationship("ViewingSlot", back_populates="invitations")
    application = relationship("Application", back_populates="viewing_invitations")

    def accept(self) -> None:
        """Einladung annehmen."""
        self.status = "accepted"
        self.responded_at = datetime.utcnow()

    def decline(self) -> None:
        """Einladung ablehnen."""
        self.status = "declined"
        self.responded_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<ViewingInvitation {self.status} for slot {self.slot_id}>"
