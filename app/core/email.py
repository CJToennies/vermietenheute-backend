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


def send_password_reset_email(to: str, token: str, name: str) -> bool:
    """
    Sendet eine Passwort-Reset-E-Mail.

    Args:
        to: E-Mail-Adresse des Empfängers
        token: Reset-Token
        name: Name des Benutzers

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"

    if not settings.RESEND_API_KEY:
        print(f"[DEV] Passwort-Reset-Email an {to}: {reset_url}")
        return True

    init_resend()

    try:
        resend.Emails.send({
            "from": "VermietenHeute <noreply@vermietenheute.de>",
            "to": to,
            "subject": "Passwort zurücksetzen",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Passwort zurücksetzen</h2>
                <p>Hallo {name},</p>
                <p>Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt. Klicken Sie auf den Button unten, um ein neues Passwort zu setzen.</p>
                <p style="margin: 30px 0;">
                    <a href="{reset_url}"
                       style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Passwort zurücksetzen
                    </a>
                </p>
                <p style="color: #666; font-size: 14px;">
                    Dieser Link ist 24 Stunden gültig. Falls Sie keine Passwort-Zurücksetzung angefordert haben, können Sie diese E-Mail ignorieren.
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


def send_new_application_notification(
    to: str,
    landlord_name: str,
    property_title: str,
    applicant_name: str,
    applicant_email: str,
    applicant_phone: str | None,
    applicant_message: str | None,
    property_id: str
) -> bool:
    """
    Sendet eine Benachrichtigung an den Vermieter über eine neue Bewerbung.

    Args:
        to: E-Mail-Adresse des Vermieters
        landlord_name: Name des Vermieters
        property_title: Titel der Immobilie
        applicant_name: Name des Bewerbers
        applicant_email: E-Mail des Bewerbers
        applicant_phone: Telefon des Bewerbers (optional)
        applicant_message: Nachricht des Bewerbers (optional)
        property_id: ID der Immobilie (für Link)

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    dashboard_url = f"{settings.FRONTEND_URL}/properties/{property_id}"

    if not settings.RESEND_API_KEY:
        print(f"[DEV] Neue-Bewerbung-Email an {to}:")
        print(f"  - Bewerber: {applicant_name}")
        print(f"  - Property: {property_title}")
        print(f"  - Dashboard: {dashboard_url}")
        return True

    init_resend()

    # Telefon-Zeile nur wenn vorhanden
    phone_html = ""
    if applicant_phone:
        phone_html = f'<p style="margin: 5px 0;"><strong>Telefon:</strong> {applicant_phone}</p>'

    # Nachricht nur wenn vorhanden
    message_html = ""
    if applicant_message:
        message_html = f'''
        <div style="margin-top: 15px; padding: 15px; background-color: #f9fafb; border-radius: 6px; border-left: 4px solid #2563eb;">
            <p style="margin: 0 0 5px 0; font-weight: bold; color: #374151;">Nachricht:</p>
            <p style="margin: 0; color: #4b5563; white-space: pre-wrap;">{applicant_message}</p>
        </div>
        '''

    try:
        resend.Emails.send({
            "from": "VermietenHeute <noreply@vermietenheute.de>",
            "to": to,
            "subject": f"Neue Bewerbung für: {property_title}",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Neue Bewerbung eingegangen!</h2>
                <p>Hallo {landlord_name},</p>
                <p>Sie haben eine neue Bewerbung für Ihre Immobilie erhalten:</p>

                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0; font-weight: bold; font-size: 16px;">{property_title}</p>
                </div>

                <h3 style="color: #374151; margin-top: 25px;">Bewerber-Informationen</h3>
                <div style="background-color: #ffffff; border: 1px solid #e5e7eb; padding: 15px; border-radius: 6px;">
                    <p style="margin: 5px 0;"><strong>Name:</strong> {applicant_name}</p>
                    <p style="margin: 5px 0;"><strong>E-Mail:</strong> <a href="mailto:{applicant_email}">{applicant_email}</a></p>
                    {phone_html}
                </div>

                {message_html}

                <p style="margin: 30px 0;">
                    <a href="{dashboard_url}"
                       style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Bewerbung ansehen
                    </a>
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


def send_landlord_to_applicant_email(
    to: str,
    applicant_name: str,
    subject: str,
    message: str,
    landlord_name: str,
    property_title: str
) -> bool:
    """
    Sendet eine E-Mail vom Vermieter an den Bewerber.

    Args:
        to: E-Mail-Adresse des Bewerbers
        applicant_name: Name des Bewerbers
        subject: Betreff der E-Mail
        message: Nachricht (kann mehrzeilig sein)
        landlord_name: Name des Vermieters
        property_title: Titel der Immobilie

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    if not settings.RESEND_API_KEY:
        print(f"[DEV] Vermieter-Email an {to}:")
        print(f"  - Betreff: {subject}")
        print(f"  - Von: {landlord_name}")
        print(f"  - Nachricht: {message[:100]}...")
        return True

    init_resend()

    # Nachricht für HTML formatieren (Zeilenumbrüche zu <br>)
    message_html = message.replace("\n", "<br>")

    try:
        resend.Emails.send({
            "from": "VermietenHeute <noreply@vermietenheute.de>",
            "to": to,
            "subject": subject,
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 6px 6px 0 0; margin-bottom: 0;">
                    <p style="margin: 0; font-size: 14px; color: #6b7280;">
                        Nachricht zu Ihrer Bewerbung für:
                    </p>
                    <p style="margin: 5px 0 0 0; font-weight: bold; color: #111827;">
                        {property_title}
                    </p>
                </div>

                <div style="border: 1px solid #e5e7eb; border-top: none; padding: 20px; border-radius: 0 0 6px 6px;">
                    <p>Hallo {applicant_name},</p>

                    <div style="margin: 20px 0; line-height: 1.6;">
                        {message_html}
                    </div>

                    <p style="margin-top: 30px;">
                        Mit freundlichen Grüßen<br>
                        <strong>{landlord_name}</strong>
                    </p>
                </div>

                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">
                    Diese E-Mail wurde über VermietenHeute versendet.
                </p>
            </div>
            """
        })
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {e}")
        return False


def send_email_change_email(to: str, token: str, name: str) -> bool:
    """
    Sendet eine E-Mail zur Bestätigung der neuen E-Mail-Adresse.

    Args:
        to: Neue E-Mail-Adresse des Empfängers
        token: Bestätigungs-Token
        name: Name des Benutzers

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    verification_url = f"{settings.FRONTEND_URL}/verify-email-change/{token}"

    if not settings.RESEND_API_KEY:
        print(f"[DEV] Email-Änderung-Email an {to}: {verification_url}")
        return True

    init_resend()

    try:
        resend.Emails.send({
            "from": "VermietenHeute <noreply@vermietenheute.de>",
            "to": to,
            "subject": "Neue E-Mail-Adresse bestätigen",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Neue E-Mail-Adresse bestätigen</h2>
                <p>Hallo {name},</p>
                <p>Sie haben die Änderung Ihrer E-Mail-Adresse angefordert. Bitte bestätigen Sie diese neue E-Mail-Adresse, indem Sie auf den Button unten klicken.</p>
                <p style="margin: 30px 0;">
                    <a href="{verification_url}"
                       style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        E-Mail-Adresse bestätigen
                    </a>
                </p>
                <p style="color: #666; font-size: 14px;">
                    Dieser Link ist 24 Stunden gültig. Falls Sie keine E-Mail-Änderung angefordert haben, können Sie diese E-Mail ignorieren.
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
