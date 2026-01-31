"""
Booking Model - Buchungen für Besichtigungstermine.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Booking(Base):
    """
    Buchungs-Tabelle für Besichtigungstermine.

    Attributes:
        id: Eindeutige UUID der Buchung
        slot_id: Fremdschlüssel zum Besichtigungstermin
        first_name: Vorname des Interessenten
        last_name: Nachname des Interessenten
        email: E-Mail-Adresse
        phone: Telefonnummer
        confirmed: Buchung bestätigt ja/nein
        application_id: Optional - Verknüpfung mit Bewerbung
        invitation_id: Optional - Verknüpfung mit Einladung
        reminder_24h_sent: Ob 24h-Erinnerung gesendet wurde
        reminder_1h_sent: Ob 1h-Erinnerung gesendet wurde
        cancelled_at: Zeitpunkt der Stornierung (null wenn aktiv)
        created_at: Erstellungszeitpunkt
        updated_at: Letzter Änderungszeitpunkt
    """

    __tablename__ = "bookings"

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
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    confirmed = Column(Boolean, default=True, nullable=False)

    # Verknüpfung mit Bewerbung (optional)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    # Verknüpfung mit Einladung (optional)
    invitation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("viewing_invitations.id", ondelete="SET NULL"),
        nullable=True
    )

    # Erinnerungs-Flags
    reminder_24h_sent = Column(Boolean, default=False, nullable=False)
    reminder_1h_sent = Column(Boolean, default=False, nullable=False)

    # Stornierung
    cancelled_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Beziehungen
    viewing_slot = relationship("ViewingSlot", back_populates="bookings")
    application = relationship("Application", back_populates="viewing_bookings")
    invitation = relationship("ViewingInvitation", backref="booking")

    def cancel(self) -> None:
        """Storniert die Buchung."""
        self.cancelled_at = datetime.utcnow()
        self.confirmed = False

    def is_cancelled(self) -> bool:
        """Prüft ob die Buchung storniert wurde."""
        return self.cancelled_at is not None

    def __repr__(self) -> str:
        status = "cancelled" if self.is_cancelled() else "active"
        return f"<Booking {self.first_name} {self.last_name} ({status})>"
