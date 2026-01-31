"""
Application Model - Bewerbungen für Mietobjekte.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.database import Base


class Application(Base):
    """
    Bewerbungs-Tabelle für Mietinteressenten.

    Attributes:
        id: Eindeutige UUID der Bewerbung
        property_id: Fremdschlüssel zur Immobilie
        first_name: Vorname des Bewerbers
        last_name: Nachname des Bewerbers
        email: E-Mail-Adresse
        phone: Telefonnummer
        message: Nachricht/Anschreiben des Bewerbers
        landlord_notes: Notizen des Vermieters
        rating: Bewertung durch Vermieter (1-5)
        status: Status der Bewerbung (neu, in_pruefung, akzeptiert, abgelehnt)
        created_at: Erstellungszeitpunkt
        updated_at: Letzter Änderungszeitpunkt
    """

    __tablename__ = "applications"

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
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    landlord_notes = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 Sterne
    status = Column(
        String(50),
        default="neu",
        nullable=False
    )  # neu, in_pruefung, akzeptiert, abgelehnt
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True, index=True)
    email_verification_expires = Column(DateTime, nullable=True)
    access_token = Column(String(255), nullable=True, unique=True, index=True)  # Für Bewerber-Portal
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Beziehungen
    property = relationship("Property", back_populates="applications")
    self_disclosure = relationship(
        "SelfDisclosure",
        back_populates="application",
        uselist=False,
        cascade="all, delete-orphan"
    )
    documents = relationship(
        "ApplicationDocument",
        back_populates="application",
        cascade="all, delete-orphan"
    )
    viewing_invitations = relationship(
        "ViewingInvitation",
        back_populates="application",
        cascade="all, delete-orphan"
    )
    viewing_bookings = relationship(
        "Booking",
        back_populates="application"
    )

    @hybrid_property
    def has_self_disclosure(self) -> bool:
        """Prüft ob eine Selbstauskunft vorhanden ist."""
        return self.self_disclosure is not None

    def __repr__(self) -> str:
        return f"<Application {self.first_name} {self.last_name}>"
