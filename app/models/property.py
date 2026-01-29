"""
Property Model - Immobilien/Mietobjekte.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Property(Base):
    """
    Immobilien-Tabelle für Mietobjekte.

    Attributes:
        id: Eindeutige UUID der Immobilie
        landlord_id: Fremdschlüssel zum Vermieter
        title: Titel der Anzeige
        type: Art der Immobilie (wohnung, haus, zimmer, etc.)
        description: Ausführliche Beschreibung
        address: Straße und Hausnummer
        city: Stadt
        zip_code: Postleitzahl
        rent: Monatliche Kaltmiete
        deposit: Kaution
        size: Größe in Quadratmetern
        rooms: Anzahl der Zimmer
        available_from: Verfügbar ab Datum
        furnished: Möbliert ja/nein
        pets_allowed: Haustiere erlaubt
        is_active: Anzeige aktiv/sichtbar
        created_at: Erstellungszeitpunkt
        updated_at: Letzter Änderungszeitpunkt
    """

    __tablename__ = "properties"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    landlord_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # wohnung, haus, zimmer, etc.
    description = Column(Text, nullable=True)
    address = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    zip_code = Column(String(10), nullable=False)
    rent = Column(Numeric(10, 2), nullable=False)  # Kaltmiete
    deposit = Column(Numeric(10, 2), nullable=True)  # Kaution
    size = Column(Numeric(8, 2), nullable=True)  # qm
    rooms = Column(Numeric(4, 1), nullable=True)  # z.B. 2.5 Zimmer
    available_from = Column(Date, nullable=True)
    furnished = Column(Boolean, default=False, nullable=False)
    pets_allowed = Column(Boolean, default=False, nullable=False)
    listing_url = Column(String(500), nullable=True)  # Externe Anzeigen-URL (ImmobilienScout, etc.)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Beziehungen
    landlord = relationship("User", back_populates="properties")
    applications = relationship(
        "Application",
        back_populates="property",
        cascade="all, delete-orphan"
    )
    viewing_slots = relationship(
        "ViewingSlot",
        back_populates="property",
        cascade="all, delete-orphan"
    )
    images = relationship(
        "PropertyImage",
        back_populates="property",
        cascade="all, delete-orphan",
        order_by="PropertyImage.order"
    )

    def __repr__(self) -> str:
        return f"<Property {self.title}>"
