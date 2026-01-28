"""
Pydantic Schemas für SelfDisclosure/Selbstauskunft.
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class WeiterePersonSchema(BaseModel):
    """Schema für eine weitere Person im Haushalt."""
    name: str
    geburtsdatum: Optional[str] = None
    verhaeltnis: str  # z.B. "Ehepartner", "Kind", "Lebensgefährte"


class SelfDisclosureBase(BaseModel):
    """Basis-Schema für Selbstauskunft."""

    # Persönliche Daten
    geburtsname: Optional[str] = None
    staatsangehoerigkeit: Optional[str] = None
    familienstand: Optional[str] = None

    # Arbeitgeber
    arbeitgeber_name: Optional[str] = None
    arbeitgeber_adresse: Optional[str] = None
    beschaeftigt_als: Optional[str] = None
    beschaeftigt_seit: Optional[date] = None
    arbeitsverhaeltnis_ungekuendigt: Optional[bool] = None

    # Aktueller Vermieter
    aktueller_vermieter_name: Optional[str] = None
    aktueller_vermieter_adresse: Optional[str] = None
    aktueller_vermieter_telefon: Optional[str] = None

    # Weitere Personen im Haushalt
    weitere_personen: Optional[List[WeiterePersonSchema]] = Field(default_factory=list)

    # Finanzielle/Rechtliche Fragen
    mietrueckstaende: bool = False

    raeumungsklage: bool = False
    raeumungsklage_datum: Optional[date] = None

    zwangsvollstreckung: bool = False
    zwangsvollstreckung_datum: Optional[date] = None

    eidesstattliche_versicherung: bool = False
    eidesstattliche_versicherung_datum: Optional[date] = None

    insolvenzverfahren: bool = False
    insolvenzverfahren_datum: Optional[date] = None

    lohn_pfaendung: bool = False

    vorstrafen_mietverhaeltnis: bool = False
    vorstrafen_datum: Optional[date] = None

    sozialleistungen: bool = False
    sozialleistungen_art: Optional[str] = None

    gewerbliche_nutzung: bool = False
    gewerbliche_nutzung_zweck: Optional[str] = None

    tierhaltung: bool = False
    tierhaltung_details: Optional[str] = None

    kaution_buergschaft: bool = True

    # Einkommen und Mietzahlung
    miete_zahlbar: bool = False  # Bestätigung: Ich kann die Miete zahlen
    nettoeinkommen: Optional[str] = None  # Freiwillige Angabe

    # Einwilligungen
    schufa_einwilligung: bool = False
    vollstaendig_wahrheitsgemaess: bool = False

    @field_validator('familienstand')
    @classmethod
    def validate_familienstand(cls, v):
        if v is not None:
            valid_values = ['ledig', 'verheiratet', 'geschieden', 'verwitwet', 'eingetragene_lebenspartnerschaft']
            if v.lower() not in valid_values:
                raise ValueError(f'Familienstand muss einer von {valid_values} sein')
        return v


class SelfDisclosureCreate(SelfDisclosureBase):
    """Schema für Selbstauskunft-Erstellung."""
    vollstaendig_wahrheitsgemaess: bool = Field(
        ...,
        description="Muss true sein - Bestätigung der Richtigkeit aller Angaben"
    )

    @field_validator('vollstaendig_wahrheitsgemaess')
    @classmethod
    def validate_wahrheitsgemaess(cls, v):
        if not v:
            raise ValueError('Sie müssen bestätigen, dass alle Angaben vollständig und wahrheitsgemäß sind')
        return v


class SelfDisclosureUpdate(BaseModel):
    """Schema für Selbstauskunft-Update."""

    # Persönliche Daten
    geburtsname: Optional[str] = None
    staatsangehoerigkeit: Optional[str] = None
    familienstand: Optional[str] = None

    # Arbeitgeber
    arbeitgeber_name: Optional[str] = None
    arbeitgeber_adresse: Optional[str] = None
    beschaeftigt_als: Optional[str] = None
    beschaeftigt_seit: Optional[date] = None
    arbeitsverhaeltnis_ungekuendigt: Optional[bool] = None

    # Aktueller Vermieter
    aktueller_vermieter_name: Optional[str] = None
    aktueller_vermieter_adresse: Optional[str] = None
    aktueller_vermieter_telefon: Optional[str] = None

    # Weitere Personen im Haushalt
    weitere_personen: Optional[List[WeiterePersonSchema]] = None

    # Finanzielle/Rechtliche Fragen
    mietrueckstaende: Optional[bool] = None
    raeumungsklage: Optional[bool] = None
    raeumungsklage_datum: Optional[date] = None
    zwangsvollstreckung: Optional[bool] = None
    zwangsvollstreckung_datum: Optional[date] = None
    eidesstattliche_versicherung: Optional[bool] = None
    eidesstattliche_versicherung_datum: Optional[date] = None
    insolvenzverfahren: Optional[bool] = None
    insolvenzverfahren_datum: Optional[date] = None
    lohn_pfaendung: Optional[bool] = None
    vorstrafen_mietverhaeltnis: Optional[bool] = None
    vorstrafen_datum: Optional[date] = None
    sozialleistungen: Optional[bool] = None
    sozialleistungen_art: Optional[str] = None
    gewerbliche_nutzung: Optional[bool] = None
    gewerbliche_nutzung_zweck: Optional[str] = None
    tierhaltung: Optional[bool] = None
    tierhaltung_details: Optional[str] = None
    kaution_buergschaft: Optional[bool] = None

    # Einkommen und Mietzahlung
    miete_zahlbar: Optional[bool] = None
    nettoeinkommen: Optional[str] = None

    # Einwilligungen
    schufa_einwilligung: Optional[bool] = None
    vollstaendig_wahrheitsgemaess: Optional[bool] = None


class SelfDisclosureResponse(SelfDisclosureBase):
    """Schema für Selbstauskunft-Response."""
    id: UUID
    application_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
