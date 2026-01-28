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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Beziehungen
    viewing_slot = relationship("ViewingSlot", back_populates="bookings")

    def __repr__(self) -> str:
        return f"<Booking {self.first_name} {self.last_name}>"
