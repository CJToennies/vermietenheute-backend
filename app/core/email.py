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


def send_application_portal_email(
    to: str,
    verification_token: str,
    access_token: str,
    property_title: str,
    applicant_name: str
) -> bool:
    """
    Sendet eine E-Mail an einen Bewerber mit Portal-Link.

    Args:
        to: E-Mail-Adresse des Bewerbers
        verification_token: Token zur Email-Verifizierung
        access_token: Token für Portal-Zugang
        property_title: Titel der Immobilie
        applicant_name: Name des Bewerbers

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    verification_url = f"{settings.FRONTEND_URL}/bewerben/verify/{verification_token}"
    portal_url = f"{settings.FRONTEND_URL}/bewerben/portal/{access_token}"

    if not settings.RESEND_API_KEY:
        print(f"[DEV] Bewerber-Portal-Email an {to}:")
        print(f"  - Verifizierung: {verification_url}")
        print(f"  - Portal: {portal_url}")
        return True

    init_resend()

    try:
        resend.Emails.send({
            "from": "VermietenHeute <noreply@vermietenheute.de>",
            "to": to,
            "subject": f"Ihre Bewerbung für: {property_title}",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Bewerbung erfolgreich gesendet!</h2>
                <p>Hallo {applicant_name},</p>
                <p>vielen Dank für Ihre Bewerbung auf:</p>
                <p style="background-color: #f3f4f6; padding: 15px; border-radius: 6px; font-weight: bold;">
                    {property_title}
                </p>

                <h3 style="color: #374151; margin-top: 30px;">1. E-Mail bestätigen</h3>
                <p>Bitte bestätigen Sie Ihre E-Mail-Adresse. Dies zeigt dem Vermieter, dass Ihre Kontaktdaten echt sind.</p>
                <p style="margin: 20px 0;">
                    <a href="{verification_url}"
                       style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        E-Mail bestätigen
                    </a>
                </p>

                <h3 style="color: #374151; margin-top: 30px;">2. Ihre Bewerbung verwalten</h3>
                <p>Über Ihr persönliches Bewerber-Portal können Sie:</p>
                <ul style="color: #666;">
                    <li>Ihre Bewerbungsdaten bearbeiten</li>
                    <li>Eine Selbstauskunft ausfüllen</li>
                    <li>Dokumente hochladen (Gehaltsnachweis, SCHUFA, etc.)</li>
                </ul>
                <p style="margin: 20px 0;">
                    <a href="{portal_url}"
                       style="background-color: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Zum Bewerber-Portal
                    </a>
                </p>

                <p style="color: #666; font-size: 14px; margin-top: 30px; padding: 15px; background-color: #fef3c7; border-radius: 6px;">
                    <strong>Wichtig:</strong> Speichern Sie diese E-Mail! Der Portal-Link ist Ihr persönlicher Zugang zu Ihrer Bewerbung.
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
