"""
PropertyImage Model - Bilder für Immobilien.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class PropertyImage(Base):
    """
    Bilder-Tabelle für Immobilien.

    Attributes:
        id: Eindeutige UUID des Bildes
        property_id: Fremdschlüssel zur Immobilie
        filename: Originaler Dateiname
        filepath: Pfad zur gespeicherten Datei
        order: Reihenfolge der Bilder (für Sortierung)
        created_at: Erstellungszeitpunkt
    """

    __tablename__ = "property_images"

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
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Beziehungen
    property = relationship("Property", back_populates="images")

    def __repr__(self) -> str:
        return f"<PropertyImage {self.filename}>"
