"""
SelfDisclosure Model - Digitale Mieter-Selbstauskunft.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class SelfDisclosure(Base):
    """
    Selbstauskunft-Tabelle für Mietinteressenten.

    Attributes:
        id: Eindeutige UUID
        application_id: Fremdschlüssel zur Bewerbung

        PERSÖNLICHE DATEN:
        geburtsname: Geburtsname (falls abweichend)
        staatsangehoerigkeit: Staatsangehörigkeit
        familienstand: ledig/verheiratet/geschieden/verwitwet

        ARBEITGEBER:
        arbeitgeber_name: Name des Arbeitgebers
        arbeitgeber_adresse: Adresse des Arbeitgebers
        beschaeftigt_als: Position/Beruf
        beschaeftigt_seit: Beschäftigt seit Datum
        arbeitsverhaeltnis_ungekuendigt: Ist das Arbeitsverhältnis ungekündigt?

        AKTUELLER VERMIETER:
        aktueller_vermieter_name: Name des aktuellen Vermieters
        aktueller_vermieter_adresse: Adresse
        aktueller_vermieter_telefon: Telefon

        WEITERE PERSONEN:
        weitere_personen: JSON Array mit Personen im Haushalt

        FINANZIELLE/RECHTLICHE FRAGEN:
        mietrueckstaende: Bestehen Mietrückstände?
        raeumungsklage: War eine Räumungsklage anhängig?
        raeumungsklage_datum: Wann?
        zwangsvollstreckung: Wurde Zwangsvollstreckung betrieben?
        zwangsvollstreckung_datum: Wann?
        eidesstattliche_versicherung: Wurde eidesstattl. Versicherung abgegeben?
        eidesstattliche_versicherung_datum: Wann?
        insolvenzverfahren: Läuft ein Insolvenzverfahren?
        insolvenzverfahren_datum: Seit wann?
        lohn_pfaendung: Besteht eine Lohnpfändung?
        vorstrafen_mietverhaeltnis: Vorstrafen im Zusammenhang mit Mietverhältnis?
        vorstrafen_datum: Wann?
        sozialleistungen: Werden Sozialleistungen bezogen?
        sozialleistungen_art: Welche Art?
        gewerbliche_nutzung: Ist gewerbliche Nutzung geplant?
        gewerbliche_nutzung_zweck: Welcher Zweck?
        tierhaltung: Sollen Tiere gehalten werden?
        tierhaltung_details: Welche Tiere?
        kaution_buergschaft: Kann Kaution/Bürgschaft gestellt werden?

        EINWILLIGUNGEN:
        schufa_einwilligung: Einwilligung zur SCHUFA-Abfrage
        vollstaendig_wahrheitsgemaess: Bestätigung der Richtigkeit

        created_at: Erstellungszeitpunkt
    """

    __tablename__ = "self_disclosures"

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
        unique=True,
        index=True
    )

    # Persönliche Daten
    geburtsname = Column(String(100), nullable=True)
    staatsangehoerigkeit = Column(String(100), nullable=True)
    familienstand = Column(String(50), nullable=True)  # ledig, verheiratet, geschieden, verwitwet

    # Arbeitgeber
    arbeitgeber_name = Column(String(200), nullable=True)
    arbeitgeber_adresse = Column(Text, nullable=True)
    beschaeftigt_als = Column(String(200), nullable=True)
    beschaeftigt_seit = Column(Date, nullable=True)
    arbeitsverhaeltnis_ungekuendigt = Column(Boolean, nullable=True)

    # Aktueller Vermieter
    aktueller_vermieter_name = Column(String(200), nullable=True)
    aktueller_vermieter_adresse = Column(Text, nullable=True)
    aktueller_vermieter_telefon = Column(String(50), nullable=True)

    # Weitere Personen im Haushalt (JSON Array)
    weitere_personen = Column(JSON, nullable=True, default=list)

    # Finanzielle/Rechtliche Fragen
    mietrueckstaende = Column(Boolean, default=False, nullable=False)

    raeumungsklage = Column(Boolean, default=False, nullable=False)
    raeumungsklage_datum = Column(Date, nullable=True)

    zwangsvollstreckung = Column(Boolean, default=False, nullable=False)
    zwangsvollstreckung_datum = Column(Date, nullable=True)

    eidesstattliche_versicherung = Column(Boolean, default=False, nullable=False)
    eidesstattliche_versicherung_datum = Column(Date, nullable=True)

    insolvenzverfahren = Column(Boolean, default=False, nullable=False)
    insolvenzverfahren_datum = Column(Date, nullable=True)

    lohn_pfaendung = Column(Boolean, default=False, nullable=False)

    vorstrafen_mietverhaeltnis = Column(Boolean, default=False, nullable=False)
    vorstrafen_datum = Column(Date, nullable=True)

    sozialleistungen = Column(Boolean, default=False, nullable=False)
    sozialleistungen_art = Column(String(200), nullable=True)

    gewerbliche_nutzung = Column(Boolean, default=False, nullable=False)
    gewerbliche_nutzung_zweck = Column(String(200), nullable=True)

    tierhaltung = Column(Boolean, default=False, nullable=False)
    tierhaltung_details = Column(String(200), nullable=True)

    kaution_buergschaft = Column(Boolean, default=True, nullable=False)

    # Einkommen und Mietzahlung
    miete_zahlbar = Column(Boolean, default=False, nullable=False)  # Bestätigung: Miete kann gezahlt werden
    nettoeinkommen = Column(String(100), nullable=True)  # Freiwillige Angabe des Nettoeinkommens

    # Einwilligungen
    schufa_einwilligung = Column(Boolean, default=False, nullable=False)
    vollstaendig_wahrheitsgemaess = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Beziehungen
    application = relationship("Application", back_populates="self_disclosure")

    def __repr__(self) -> str:
        return f"<SelfDisclosure {self.id}>"
