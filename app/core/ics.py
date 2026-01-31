"""
ICS Calendar Service - Generierung von Kalendereinträgen.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from icalendar import Calendar, Event, Alarm, vText
import pytz


def generate_ics(
    slot_id: UUID,
    property_title: str,
    property_address: str,
    start_time: datetime,
    end_time: datetime,
    description: Optional[str] = None,
    status: str = "CONFIRMED",
    organizer_name: Optional[str] = None,
    organizer_email: Optional[str] = None,
) -> bytes:
    """
    Generiert eine ICS-Datei für einen Besichtigungstermin.

    Args:
        slot_id: UUID des Termins (wird als UID verwendet)
        property_title: Titel der Immobilie
        property_address: Adresse der Immobilie
        start_time: Startzeit des Termins
        end_time: Endzeit des Termins
        description: Optionale Beschreibung
        status: Status (CONFIRMED, TENTATIVE, CANCELLED)
        organizer_name: Name des Organisators
        organizer_email: E-Mail des Organisators

    Returns:
        ICS-Datei als Bytes
    """
    cal = Calendar()
    cal.add("prodid", "-//VermietenHeute//Besichtigung//DE")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "REQUEST" if status == "TENTATIVE" else "PUBLISH")

    event = Event()

    # Basis-Informationen
    event.add("summary", f"Besichtigung: {property_title}")
    event.add("dtstart", start_time)
    event.add("dtend", end_time)
    event.add("dtstamp", datetime.utcnow())

    # Eindeutige ID
    event.add("uid", f"{slot_id}@vermietenheute.de")

    # Ort
    event.add("location", property_address)

    # Beschreibung
    if description:
        event.add("description", description)
    else:
        event.add(
            "description",
            f"Besichtigungstermin für: {property_title}\n\n"
            f"Adresse: {property_address}\n\n"
            "Bitte erscheinen Sie pünktlich zum Termin."
        )

    # Status
    event.add("status", status)

    # Organizer
    if organizer_email:
        organizer = vText(f"mailto:{organizer_email}")
        if organizer_name:
            organizer.params["CN"] = organizer_name
        event.add("organizer", organizer)

    # Erinnerung 1 Stunde vorher
    alarm = Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add("trigger", timedelta(hours=-1))  # 1 Stunde vorher
    alarm.add("description", f"Besichtigung in 1 Stunde: {property_title}")
    event.add_component(alarm)

    cal.add_component(event)

    return cal.to_ical()


def generate_cancellation_ics(
    slot_id: UUID,
    property_title: str,
    property_address: str,
    start_time: datetime,
    end_time: datetime,
) -> bytes:
    """
    Generiert eine ICS-Datei für die Absage eines Termins.

    Args:
        slot_id: UUID des Termins
        property_title: Titel der Immobilie
        property_address: Adresse der Immobilie
        start_time: Startzeit des Termins
        end_time: Endzeit des Termins

    Returns:
        ICS-Datei als Bytes (mit STATUS:CANCELLED)
    """
    return generate_ics(
        slot_id=slot_id,
        property_title=property_title,
        property_address=property_address,
        start_time=start_time,
        end_time=end_time,
        description=f"ABGESAGT: Besichtigung für {property_title}",
        status="CANCELLED",
    )


def generate_rescheduled_ics(
    slot_id: UUID,
    property_title: str,
    property_address: str,
    new_start_time: datetime,
    new_end_time: datetime,
    old_start_time: datetime,
    old_end_time: datetime,
) -> bytes:
    """
    Generiert eine ICS-Datei für einen verschobenen Termin.

    Args:
        slot_id: UUID des Termins
        property_title: Titel der Immobilie
        property_address: Adresse der Immobilie
        new_start_time: Neue Startzeit
        new_end_time: Neue Endzeit
        old_start_time: Alte Startzeit
        old_end_time: Alte Endzeit

    Returns:
        ICS-Datei als Bytes
    """
    # Formatierung der alten Zeit
    old_time_str = old_start_time.strftime("%d.%m.%Y %H:%M")
    new_time_str = new_start_time.strftime("%d.%m.%Y %H:%M")

    description = (
        f"VERSCHOBEN: Besichtigung für {property_title}\n\n"
        f"Alter Termin: {old_time_str} (ABGESAGT)\n"
        f"Neuer Termin: {new_time_str}\n\n"
        f"Adresse: {property_address}\n\n"
        "Bitte erscheinen Sie pünktlich zum neuen Termin."
    )

    return generate_ics(
        slot_id=slot_id,
        property_title=property_title,
        property_address=property_address,
        start_time=new_start_time,
        end_time=new_end_time,
        description=description,
        status="CONFIRMED",
    )


def format_datetime_german(dt: datetime) -> str:
    """
    Formatiert ein Datum/Zeit im deutschen Format.

    Args:
        dt: Datetime-Objekt

    Returns:
        Formatierter String (z.B. "Sa, 15.02.2026 14:00 Uhr")
    """
    weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    weekday = weekdays[dt.weekday()]
    return f"{weekday}, {dt.strftime('%d.%m.%Y %H:%M')} Uhr"
