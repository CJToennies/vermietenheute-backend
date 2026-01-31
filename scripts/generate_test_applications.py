"""
Script zum Generieren von Test-Bewerbungen.

Usage:
    python scripts/generate_test_applications.py <property_id>

Oder ohne Argument - zeigt verfügbare Properties an.
"""
import sys
import os
import uuid
import random
from datetime import datetime, timedelta, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Property, Application


# Testdaten
FIRST_NAMES = [
    "Max", "Anna", "Felix", "Laura", "Jonas", "Emma", "Lukas", "Mia",
    "Leon", "Sophie", "Paul", "Marie", "Tim", "Lena", "David", "Julia",
    "Niklas", "Sarah", "Tom", "Lisa", "Jan", "Nina", "Moritz", "Hannah", "Ben"
]

LAST_NAMES = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner",
    "Becker", "Schulz", "Hoffmann", "Koch", "Richter", "Bauer", "Klein",
    "Wolf", "Schröder", "Neumann", "Schwarz", "Braun", "Zimmermann",
    "Krüger", "Hartmann", "Lange", "Werner", "Peters"
]

MESSAGES = [
    "Ich interessiere mich sehr für Ihre Wohnung und würde mich über eine Besichtigung freuen.",
    "Die Wohnung entspricht genau meinen Vorstellungen. Ich bin berufstätig und zuverlässig.",
    "Als langjähriger Mieter meiner aktuellen Wohnung suche ich nun etwas Größeres.",
    "Ich bin Nichtraucher, habe keine Haustiere und bin sehr ordentlich.",
    "Die Lage und Größe der Wohnung passen perfekt zu meinen Anforderungen.",
    "Ich kann alle erforderlichen Unterlagen zeitnah bereitstellen.",
    "Über eine positive Rückmeldung würde ich mich sehr freuen!",
    "Ich bin finanziell solvent und habe ein stabiles Einkommen.",
]


def generate_application(property_id: uuid.UUID, index: int) -> Application:
    """Generiert eine einzelne Test-Bewerbung."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)

    # Zufälliges Datum in den letzten 30 Tagen
    days_ago = random.randint(0, 30)
    now = datetime.now(timezone.utc)
    created_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))

    return Application(
        id=uuid.uuid4(),
        property_id=property_id,
        first_name=first_name,
        last_name=last_name,
        email=f"test.bewerber{index}@example.com",
        phone=f"0170-{random.randint(1000000, 9999999)}",
        message=random.choice(MESSAGES),
        status="neu",
        is_email_verified=False,  # Unverifiziert!
        access_token=str(uuid.uuid4()),
        created_at=created_at,
        updated_at=created_at,
    )


def main():
    db = SessionLocal()

    try:
        # Property-ID als Argument oder anzeigen
        if len(sys.argv) < 2:
            print("\n📋 Verfügbare Properties:\n")
            properties = db.query(Property).all()

            if not properties:
                print("❌ Keine Properties gefunden. Erstelle zuerst ein Objekt im Dashboard.")
                return

            for p in properties:
                app_count = db.query(Application).filter(Application.property_id == p.id).count()
                print(f"  • {p.id}")
                print(f"    {p.title} ({p.city})")
                print(f"    Bewerbungen: {app_count}")
                print()

            print("\nUsage: python scripts/generate_test_applications.py <property_id>")
            return

        property_id = uuid.UUID(sys.argv[1])

        # Property prüfen
        property = db.query(Property).filter(Property.id == property_id).first()
        if not property:
            print(f"❌ Property mit ID {property_id} nicht gefunden.")
            return

        print(f"\n🏠 Property: {property.title}")
        print(f"📍 {property.address}, {property.zip_code} {property.city}")

        # Bestehende Bewerbungen zählen
        existing_count = db.query(Application).filter(
            Application.property_id == property_id
        ).count()
        print(f"\n📊 Bestehende Bewerbungen: {existing_count}")

        # 25 neue Bewerbungen generieren
        print(f"\n🔄 Generiere 25 Test-Bewerbungen...")

        applications = []
        for i in range(25):
            app = generate_application(property_id, existing_count + i + 1)
            applications.append(app)
            db.add(app)

        db.commit()

        # Neue Gesamtzahl
        new_count = db.query(Application).filter(
            Application.property_id == property_id
        ).count()

        print(f"\n✅ 25 Bewerbungen erfolgreich erstellt!")
        print(f"📊 Neue Gesamtzahl: {new_count} Bewerbungen")

        if new_count > 20:
            print(f"\n⚠️  Limit überschritten! ({new_count}/20)")
            print("   → 'Unbegrenzte Bewerbungen' Upgrade sollte angezeigt werden")

    except ValueError as e:
        print(f"❌ Ungültige UUID: {sys.argv[1]}")
    except Exception as e:
        print(f"❌ Fehler: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
