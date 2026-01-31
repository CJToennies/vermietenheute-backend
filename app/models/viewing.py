"""
ViewingSlot Model - Besichtigungstermine für Immobilien.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ViewingSlot(Base):
    """
    Besichtigungstermin-Tabelle.

    Attributes:
        id: Eindeutige UUID des Termins
        property_id: Fremdschlüssel zur Immobilie
        start_time: Startzeitpunkt der Besichtigung
        end_time: Endzeitpunkt der Besichtigung
        slot_type: Art des Termins ("individual" = Einzeltermin, "group" = Sammelbesichtigung)
        access_type: Zugangsbeschränkung ("public" = öffentlich, "invited" = nur eingeladene)
        max_attendees: Maximale Anzahl Teilnehmer
        notes: Interne Notizen für den Vermieter
        created_at: Erstellungszeitpunkt
        updated_at: Letzter Änderungszeitpunkt
    """

    __tablename__ = "viewing_slots"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # Slot-Konfiguration
    slot_type = Column(
        String(20),
        default="individual",
        nullable=False
    )  # "individual" oder "group"
    access_type = Column(
        String(20),
        default="public",
        nullable=False
    )  # "public" oder "invited"
    max_attendees = Column(Integer, default=1, nullable=False)
    notes = Column(Text, nullable=True)  # Interne Notizen

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Beziehungen
    property = relationship("Property", back_populates="viewing_slots")
    bookings = relationship(
        "Booking",
        back_populates="viewing_slot",
        cascade="all, delete-orphan"
    )
    invitations = relationship(
        "ViewingInvitation",
        back_populates="viewing_slot",
        cascade="all, delete-orphan"
    )

    def get_available_spots(self) -> int:
        """Berechnet verfügbare Plätze."""
        confirmed_bookings = sum(1 for b in self.bookings if b.confirmed and not b.cancelled_at)
        return self.max_attendees - confirmed_bookings

    def get_confirmed_bookings_count(self) -> int:
        """Gibt die Anzahl bestätigter Buchungen zurück."""
        return sum(1 for b in self.bookings if b.confirmed and not b.cancelled_at)

    def is_fully_booked(self) -> bool:
        """Prüft ob der Termin ausgebucht ist."""
        return self.get_available_spots() <= 0

    def __repr__(self) -> str:
        return f"<ViewingSlot {self.start_time} ({self.slot_type})>"
