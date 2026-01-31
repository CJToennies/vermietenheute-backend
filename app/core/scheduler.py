"""
Background Scheduler für automatische Erinnerungen.

Sendet Erinnerungs-E-Mails an Bewerber:
- 24 Stunden vor dem Termin
- 1 Stunde vor dem Termin
"""
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.booking import Booking
from app.models.viewing import ViewingSlot
from app.models.property import Property
from app.models.application import Application
from app.core.email import send_viewing_reminder_email
from app.core.ics import generate_ics


# Globaler Scheduler
scheduler = AsyncIOScheduler()


def get_db_session() -> Session:
    """Erstellt eine neue Datenbank-Session."""
    return SessionLocal()


async def send_reminders():
    """
    Sendet Erinnerungs-E-Mails an alle Bewerber mit anstehenden Terminen.

    - 24h vorher: reminder_24h_sent = False, start_time zwischen 23-25h
    - 1h vorher: reminder_1h_sent = False, start_time zwischen 50-70 Minuten
    """
    db = get_db_session()
    try:
        now = datetime.utcnow()

        # ========================================
        # 24-Stunden-Erinnerungen
        # ========================================
        upcoming_24h = db.query(Booking).join(ViewingSlot).filter(
            ViewingSlot.start_time.between(
                now + timedelta(hours=23),
                now + timedelta(hours=25)
            ),
            Booking.reminder_24h_sent == False,
            Booking.confirmed == True,
            Booking.cancelled_at == None
        ).all()

        for booking in upcoming_24h:
            try:
                slot = booking.viewing_slot
                property_obj = db.query(Property).filter(
                    Property.id == slot.property_id
                ).first()

                if not property_obj:
                    continue

                # Portal-Token holen
                portal_token = ""
                if booking.application_id:
                    app = db.query(Application).filter(
                        Application.id == booking.application_id
                    ).first()
                    if app and app.access_token:
                        portal_token = app.access_token

                # ICS generieren
                ics_data = generate_ics(
                    slot_id=slot.id,
                    property_title=property_obj.title,
                    property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                )

                # E-Mail senden
                success = send_viewing_reminder_email(
                    to=booking.email,
                    applicant_name=f"{booking.first_name} {booking.last_name}",
                    property_title=property_obj.title,
                    property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
                    viewing_date=slot.start_time.strftime("%d.%m.%Y"),
                    viewing_time=slot.start_time.strftime("%H:%M"),
                    reminder_type="24h",
                    portal_token=portal_token,
                    ics_data=ics_data
                )

                if success:
                    booking.reminder_24h_sent = True
                    print(f"[Scheduler] 24h-Erinnerung gesendet an {booking.email}")

            except Exception as e:
                print(f"[Scheduler] Fehler bei 24h-Erinnerung für {booking.email}: {e}")

        # ========================================
        # 1-Stunden-Erinnerungen
        # ========================================
        upcoming_1h = db.query(Booking).join(ViewingSlot).filter(
            ViewingSlot.start_time.between(
                now + timedelta(minutes=50),
                now + timedelta(minutes=70)
            ),
            Booking.reminder_1h_sent == False,
            Booking.confirmed == True,
            Booking.cancelled_at == None
        ).all()

        for booking in upcoming_1h:
            try:
                slot = booking.viewing_slot
                property_obj = db.query(Property).filter(
                    Property.id == slot.property_id
                ).first()

                if not property_obj:
                    continue

                # Portal-Token holen
                portal_token = ""
                if booking.application_id:
                    app = db.query(Application).filter(
                        Application.id == booking.application_id
                    ).first()
                    if app and app.access_token:
                        portal_token = app.access_token

                # ICS generieren
                ics_data = generate_ics(
                    slot_id=slot.id,
                    property_title=property_obj.title,
                    property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                )

                # E-Mail senden
                success = send_viewing_reminder_email(
                    to=booking.email,
                    applicant_name=f"{booking.first_name} {booking.last_name}",
                    property_title=property_obj.title,
                    property_address=f"{property_obj.address}, {property_obj.zip_code} {property_obj.city}",
                    viewing_date=slot.start_time.strftime("%d.%m.%Y"),
                    viewing_time=slot.start_time.strftime("%H:%M"),
                    reminder_type="1h",
                    portal_token=portal_token,
                    ics_data=ics_data
                )

                if success:
                    booking.reminder_1h_sent = True
                    print(f"[Scheduler] 1h-Erinnerung gesendet an {booking.email}")

            except Exception as e:
                print(f"[Scheduler] Fehler bei 1h-Erinnerung für {booking.email}: {e}")

        # Änderungen speichern
        db.commit()

    except Exception as e:
        print(f"[Scheduler] Fehler beim Senden von Erinnerungen: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Startet den Background-Scheduler."""
    # Erinnerungen alle 15 Minuten prüfen
    scheduler.add_job(
        send_reminders,
        trigger=IntervalTrigger(minutes=15),
        id="viewing_reminders",
        name="Besichtigungstermin-Erinnerungen",
        replace_existing=True
    )

    scheduler.start()
    print("[Scheduler] Background-Scheduler gestartet (Erinnerungen alle 15 Min)")


def stop_scheduler():
    """Stoppt den Background-Scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[Scheduler] Background-Scheduler gestoppt")
