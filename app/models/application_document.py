"""
ApplicationDocument Model - Dokumente für Bewerbungen.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ApplicationDocument(Base):
    """
    Dokumente-Tabelle für Bewerbungen.

    Attributes:
        id: Eindeutige UUID des Dokuments
        application_id: Fremdschlüssel zur Bewerbung
        filename: Originaler Dateiname
        display_name: Anzeigename (bei Kategorie "sonstiges")
        category: Dokumentkategorie
        filepath: Pfad zur gespeicherten Datei
        file_size: Dateigröße in Bytes
        created_at: Erstellungszeitpunkt
    """

    __tablename__ = "application_documents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    filename = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)  # Für "sonstiges" Kategorie
    category = Column(String(50), nullable=False)  # gehaltsnachweis, schufa, ausweis, mietschuldenfreiheit, arbeitsvertrag, sonstiges
    filepath = Column(String(500), nullable=False)  # Pfad in Supabase Storage
    url = Column(String(1000), nullable=True)  # Öffentliche URL (Supabase Storage)
    file_size = Column(Integer, nullable=False)  # in Bytes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Beziehungen
    application = relationship("Application", back_populates="documents")

    def __repr__(self) -> str:
        return f"<ApplicationDocument {self.category}: {self.filename}>"
