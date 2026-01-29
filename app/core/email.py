"""
Email Service - E-Mail-Versand über Resend.
"""
import resend
from app.config import settings


def init_resend():
    """Initialisiert den Resend-Client."""
    if settings.RESEND_API_KEY:
        resend.api_key = settings.RESEND_API_KEY


def send_verification_email(to: str, token: str, name: str) -> bool:
    """
    Sendet eine Verifizierungs-E-Mail an einen neuen Vermieter.

    Args:
        to: E-Mail-Adresse des Empfängers
        token: Verifizierungstoken
        name: Name des Benutzers

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    if not settings.RESEND_API_KEY:
        print(f"[DEV] Verifizierungs-Email an {to}: {settings.FRONTEND_URL}/verify-email/{token}")
        return True

    init_resend()

    verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"

    try:
        resend.Emails.send({
            "from": "VermietenHeute <noreply@vermietenheute.de>",
            "to": to,
            "subject": "Bitte bestätigen Sie Ihre E-Mail-Adresse",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Willkommen bei VermietenHeute!</h2>
                <p>Hallo {name},</p>
                <p>vielen Dank für Ihre Registrierung. Bitte bestätigen Sie Ihre E-Mail-Adresse, um Ihr Konto zu aktivieren.</p>
                <p style="margin: 30px 0;">
                    <a href="{verification_url}"
                       style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        E-Mail bestätigen
                    </a>
                </p>
                <p style="color: #666; font-size: 14px;">
                    Dieser Link ist 24 Stunden gültig. Falls Sie sich nicht bei VermietenHeute registriert haben, können Sie diese E-Mail ignorieren.
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">
                    VermietenHeute - Die Plattform für Vermieter
                </p>
            </div>
            """
        })
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {e}")
        return False


def send_application_verification_email(to: str, token: str, property_title: str, applicant_name: str) -> bool:
    """
    Sendet eine Verifizierungs-E-Mail an einen Bewerber.

    Args:
        to: E-Mail-Adresse des Bewerbers
        token: Verifizierungstoken
        property_title: Titel der Immobilie
        applicant_name: Name des Bewerbers

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    if not settings.RESEND_API_KEY:
        print(f"[DEV] Bewerber-Verifizierungs-Email an {to}: {settings.FRONTEND_URL}/bewerben/verify/{token}")
        return True

    init_resend()

    verification_url = f"{settings.FRONTEND_URL}/bewerben/verify/{token}"

    try:
        resend.Emails.send({
            "from": "VermietenHeute <noreply@vermietenheute.de>",
            "to": to,
            "subject": f"Bitte bestätigen Sie Ihre Bewerbung für: {property_title}",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Bewerbung eingegangen!</h2>
                <p>Hallo {applicant_name},</p>
                <p>vielen Dank für Ihre Bewerbung auf:</p>
                <p style="background-color: #f3f4f6; padding: 15px; border-radius: 6px; font-weight: bold;">
                    {property_title}
                </p>
                <p>Bitte bestätigen Sie Ihre E-Mail-Adresse, um Ihre Bewerbung zu verifizieren.
                   Dies erhöht Ihre Chancen beim Vermieter.</p>
                <p style="margin: 30px 0;">
                    <a href="{verification_url}"
                       style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        E-Mail bestätigen
                    </a>
                </p>
                <p style="color: #666; font-size: 14px;">
                    Ihre Bewerbung wurde bereits an den Vermieter übermittelt. Die Bestätigung ist optional,
                    zeigt dem Vermieter aber, dass Ihre E-Mail-Adresse gültig ist.
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">
                    VermietenHeute - Die Plattform für Vermieter
                </p>
            </div>
            """
        })
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {e}")
        return False


def send_application_confirmed_email(to: str, property_title: str, applicant_name: str) -> bool:
    """
    Sendet eine Bestätigungs-E-Mail nach erfolgreicher Verifizierung.

    Args:
        to: E-Mail-Adresse des Bewerbers
        property_title: Titel der Immobilie
        applicant_name: Name des Bewerbers

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    if not settings.RESEND_API_KEY:
        print(f"[DEV] Bestätigungs-Email an {to} für {property_title}")
        return True

    init_resend()

    try:
        resend.Emails.send({
            "from": "VermietenHeute <noreply@vermietenheute.de>",
            "to": to,
            "subject": f"E-Mail bestätigt - Bewerbung für: {property_title}",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #16a34a;">E-Mail erfolgreich bestätigt!</h2>
                <p>Hallo {applicant_name},</p>
                <p>Ihre E-Mail-Adresse wurde erfolgreich bestätigt. Der Vermieter kann nun sehen,
                   dass Ihre Kontaktdaten verifiziert sind.</p>
                <p style="background-color: #f0fdf4; padding: 15px; border-radius: 6px; border-left: 4px solid #16a34a;">
                    <strong>Bewerbung für:</strong> {property_title}
                </p>
                <p>Der Vermieter wird sich bei Interesse bei Ihnen melden.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">
                    VermietenHeute - Die Plattform für Vermieter
                </p>
            </div>
            """
        })
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {e}")
        return False
