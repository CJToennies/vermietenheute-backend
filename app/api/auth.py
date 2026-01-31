"""
API-Endpoints für Authentifizierung.
Registrierung und Login mit E-Mail-Verifizierung.
"""
import secrets
from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from app.core.email import send_verification_email, send_password_reset_email, send_email_change_email
from app.core.rate_limit import (
    limiter,
    RATE_LIMIT_REGISTER,
    RATE_LIMIT_LOGIN,
    RATE_LIMIT_RESEND,
    RATE_LIMIT_FORGOT_PASSWORD,
    RATE_LIMIT_RESET_PASSWORD,
    RATE_LIMIT_CHANGE_EMAIL,
    RATE_LIMIT_CHANGE_PASSWORD,
    RATE_LIMIT_DELETE_ACCOUNT,
)
from app.config import settings
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserResponse, Token, LoginRequest,
    ResendVerificationRequest, VerificationResponse,
    ForgotPasswordRequest, ResetPasswordRequest,
    ChangePasswordRequest, ChangeEmailRequest, DeleteAccountRequest,
)


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMIT_REGISTER)
def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> User:
    """
    Registriert einen neuen Benutzer (Vermieter).
    Sendet eine Verifizierungs-E-Mail.

    Args:
        request: FastAPI Request (für Rate Limiting)
        user_data: Registrierungsdaten (E-Mail, Name, Passwort)
        db: Datenbank-Session

    Returns:
        Der erstellte Benutzer

    Raises:
        HTTPException 400: Wenn E-Mail bereits existiert
    """
    # Prüfen ob E-Mail bereits registriert
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-Mail-Adresse ist bereits registriert"
        )

    # Verifizierungstoken generieren
    verification_token = secrets.token_urlsafe(32)
    token_expires = datetime.utcnow() + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)

    # Neuen Benutzer erstellen
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires=token_expires
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Verifizierungs-E-Mail senden
    send_verification_email(user.email, verification_token, user.name)

    return user


@router.post("/login", response_model=Token)
@limiter.limit(RATE_LIMIT_LOGIN)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> dict:
    """
    Authentifiziert einen Benutzer und gibt einen JWT Token zurück.
    Erfordert verifizierte E-Mail-Adresse.

    Args:
        request: FastAPI Request (für Rate Limiting)
        form_data: OAuth2 Formular mit username (E-Mail) und password
        db: Datenbank-Session

    Returns:
        JWT Access Token

    Raises:
        HTTPException 401: Wenn Anmeldedaten ungültig
        HTTPException 403: Wenn E-Mail nicht verifiziert
    """
    # Benutzer suchen
    user = db.query(User).filter(User.email == form_data.username).first()

    # Passwort verifizieren
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-Mail oder Passwort ist falsch",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Prüfen ob Benutzer aktiv
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Benutzer ist deaktiviert"
        )

    # Prüfen ob E-Mail verifiziert
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="E-Mail-Adresse ist nicht verifiziert. Bitte bestätigen Sie Ihre E-Mail."
        )

    # Token erstellen
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/json", response_model=Token)
@limiter.limit(RATE_LIMIT_LOGIN)
def login_json(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Alternative Login-Route mit JSON Body statt Form Data.
    Erfordert verifizierte E-Mail-Adresse.

    Args:
        request: FastAPI Request (für Rate Limiting)
        login_data: JSON mit E-Mail und Passwort
        db: Datenbank-Session

    Returns:
        JWT Access Token
    """
    # Benutzer suchen
    user = db.query(User).filter(User.email == login_data.email).first()

    # Passwort verifizieren
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-Mail oder Passwort ist falsch",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Prüfen ob Benutzer aktiv
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Benutzer ist deaktiviert"
        )

    # Prüfen ob E-Mail verifiziert
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="E-Mail-Adresse ist nicht verifiziert. Bitte bestätigen Sie Ihre E-Mail."
        )

    # Token erstellen
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Gibt den aktuell eingeloggten Benutzer zurück.

    Args:
        current_user: Der authentifizierte Benutzer (aus JWT Token)

    Returns:
        Die Benutzerdaten
    """
    return current_user


@router.get("/verify-email/{token}", response_model=VerificationResponse)
def verify_email(
    token: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Verifiziert die E-Mail-Adresse eines Benutzers.

    Args:
        token: Verifizierungstoken aus der E-Mail
        db: Datenbank-Session

    Returns:
        Erfolgsmeldung

    Raises:
        HTTPException 400: Wenn Token ungültig oder abgelaufen
    """
    # Benutzer mit Token suchen
    user = db.query(User).filter(User.verification_token == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger Verifizierungslink"
        )

    # Prüfen ob bereits verifiziert
    if user.is_verified:
        return {"message": "E-Mail-Adresse wurde bereits verifiziert", "success": True}

    # Prüfen ob Token abgelaufen
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verifizierungslink ist abgelaufen. Bitte fordern Sie einen neuen an."
        )

    # Benutzer verifizieren
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None

    db.commit()

    return {"message": "E-Mail-Adresse erfolgreich verifiziert. Sie können sich jetzt anmelden.", "success": True}


@router.post("/resend-verification", response_model=VerificationResponse)
@limiter.limit(RATE_LIMIT_RESEND)
def resend_verification(
    request: Request,
    data: ResendVerificationRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Sendet die Verifizierungs-E-Mail erneut.

    Args:
        request: FastAPI Request (für Rate Limiting)
        data: E-Mail-Adresse
        db: Datenbank-Session

    Returns:
        Erfolgsmeldung
    """
    # Benutzer suchen
    user = db.query(User).filter(User.email == data.email).first()

    # Immer Erfolg zurückgeben (kein Leak ob E-Mail existiert)
    if not user:
        return {"message": "Falls ein Konto mit dieser E-Mail existiert, wurde eine neue Verifizierungs-E-Mail gesendet.", "success": True}

    # Prüfen ob bereits verifiziert
    if user.is_verified:
        return {"message": "E-Mail-Adresse ist bereits verifiziert.", "success": True}

    # Neuen Token generieren
    verification_token = secrets.token_urlsafe(32)
    token_expires = datetime.utcnow() + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)

    user.verification_token = verification_token
    user.verification_token_expires = token_expires

    db.commit()

    # E-Mail senden
    send_verification_email(user.email, verification_token, user.name)

    return {"message": "Falls ein Konto mit dieser E-Mail existiert, wurde eine neue Verifizierungs-E-Mail gesendet.", "success": True}


# ============================================
# Passwort-Reset Endpoints
# ============================================

@router.post("/forgot-password", response_model=VerificationResponse)
@limiter.limit(RATE_LIMIT_FORGOT_PASSWORD)
def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Fordert einen Passwort-Reset-Link an.
    Sendet eine E-Mail mit Reset-Link falls das Konto existiert.

    Args:
        request: FastAPI Request (für Rate Limiting)
        data: E-Mail-Adresse
        db: Datenbank-Session

    Returns:
        Erfolgsmeldung (verrät nicht ob E-Mail existiert)
    """
    # Benutzer suchen
    user = db.query(User).filter(User.email == data.email).first()

    # Immer gleiche Nachricht (Privacy: nicht verraten ob Email existiert)
    success_message = "Falls ein Konto mit dieser E-Mail existiert, wurde ein Passwort-Reset-Link gesendet."

    if not user:
        return {"message": success_message, "success": True}

    if not user.is_active:
        return {"message": success_message, "success": True}

    # Reset-Token generieren
    reset_token = secrets.token_urlsafe(32)
    token_expires = datetime.utcnow() + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)

    user.password_reset_token = reset_token
    user.password_reset_token_expires = token_expires

    db.commit()

    # E-Mail senden
    send_password_reset_email(user.email, reset_token, user.name)

    return {"message": success_message, "success": True}


@router.get("/reset-password/{token}/verify", response_model=VerificationResponse)
def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Validiert einen Passwort-Reset-Token.
    Wird vom Frontend aufgerufen um zu prüfen ob der Link gültig ist.

    Args:
        token: Reset-Token aus der E-Mail
        db: Datenbank-Session

    Returns:
        Erfolgsmeldung

    Raises:
        HTTPException 400: Wenn Token ungültig oder abgelaufen
    """
    user = db.query(User).filter(User.password_reset_token == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger oder abgelaufener Reset-Link"
        )

    if user.password_reset_token_expires and user.password_reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Der Reset-Link ist abgelaufen. Bitte fordern Sie einen neuen an."
        )

    return {"message": "Token ist gültig", "success": True}


@router.post("/reset-password/{token}", response_model=VerificationResponse)
@limiter.limit(RATE_LIMIT_RESET_PASSWORD)
def reset_password(
    request: Request,
    token: str,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Setzt das Passwort mit einem gültigen Reset-Token zurück.

    Args:
        request: FastAPI Request (für Rate Limiting)
        token: Reset-Token aus der E-Mail
        data: Neues Passwort
        db: Datenbank-Session

    Returns:
        Erfolgsmeldung

    Raises:
        HTTPException 400: Wenn Token ungültig oder abgelaufen
    """
    user = db.query(User).filter(User.password_reset_token == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger oder abgelaufener Reset-Link"
        )

    if user.password_reset_token_expires and user.password_reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Der Reset-Link ist abgelaufen. Bitte fordern Sie einen neuen an."
        )

    # Neues Passwort setzen
    user.password_hash = get_password_hash(data.password)
    user.password_reset_token = None
    user.password_reset_token_expires = None

    db.commit()

    return {"message": "Passwort wurde erfolgreich geändert. Sie können sich jetzt anmelden.", "success": True}


# ============================================
# Passwort ändern (eingeloggt)
# ============================================

@router.post("/change-password", response_model=VerificationResponse)
@limiter.limit(RATE_LIMIT_CHANGE_PASSWORD)
def change_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Ändert das Passwort des eingeloggten Benutzers.

    Args:
        request: FastAPI Request (für Rate Limiting)
        data: Aktuelles und neues Passwort
        current_user: Der authentifizierte Benutzer
        db: Datenbank-Session

    Returns:
        Erfolgsmeldung

    Raises:
        HTTPException 400: Wenn aktuelles Passwort falsch
    """
    # Aktuelles Passwort verifizieren
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aktuelles Passwort ist falsch"
        )

    # Neues Passwort setzen
    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()

    return {"message": "Passwort wurde erfolgreich geändert.", "success": True}


# ============================================
# E-Mail ändern
# ============================================

@router.post("/change-email", response_model=VerificationResponse)
@limiter.limit(RATE_LIMIT_CHANGE_EMAIL)
def change_email(
    request: Request,
    data: ChangeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Fordert eine E-Mail-Änderung an.
    Sendet eine Bestätigungs-E-Mail an die neue Adresse.

    Args:
        request: FastAPI Request (für Rate Limiting)
        data: Neue E-Mail-Adresse und Passwort-Bestätigung
        current_user: Der authentifizierte Benutzer
        db: Datenbank-Session

    Returns:
        Erfolgsmeldung

    Raises:
        HTTPException 400: Wenn Passwort falsch oder E-Mail bereits verwendet
    """
    # Passwort verifizieren
    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwort ist falsch"
        )

    # Prüfen ob neue E-Mail gleich der aktuellen ist
    if data.new_email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Die neue E-Mail-Adresse ist identisch mit der aktuellen"
        )

    # Prüfen ob E-Mail bereits von anderem Benutzer verwendet wird
    existing_user = db.query(User).filter(User.email == data.new_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Diese E-Mail-Adresse wird bereits verwendet"
        )

    # Token generieren
    change_token = secrets.token_urlsafe(32)
    token_expires = datetime.utcnow() + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)

    current_user.pending_email = data.new_email
    current_user.email_change_token = change_token
    current_user.email_change_token_expires = token_expires

    db.commit()

    # Bestätigungs-E-Mail an NEUE Adresse senden
    send_email_change_email(data.new_email, change_token, current_user.name)

    return {"message": "Bestätigungs-E-Mail wurde an die neue Adresse gesendet.", "success": True}


@router.get("/verify-email-change/{token}", response_model=VerificationResponse)
def verify_email_change(
    token: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Bestätigt die E-Mail-Änderung.
    Ändert die E-Mail-Adresse des Benutzers.

    Args:
        token: Bestätigungs-Token aus der E-Mail
        db: Datenbank-Session

    Returns:
        Erfolgsmeldung

    Raises:
        HTTPException 400: Wenn Token ungültig oder abgelaufen
    """
    user = db.query(User).filter(User.email_change_token == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger oder abgelaufener Bestätigungslink"
        )

    if user.email_change_token_expires and user.email_change_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Der Bestätigungslink ist abgelaufen. Bitte fordern Sie eine neue E-Mail-Änderung an."
        )

    if not user.pending_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keine ausstehende E-Mail-Änderung gefunden"
        )

    # Nochmal prüfen ob neue E-Mail inzwischen verwendet wird
    existing_user = db.query(User).filter(User.email == user.pending_email).first()
    if existing_user:
        user.pending_email = None
        user.email_change_token = None
        user.email_change_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Diese E-Mail-Adresse wird bereits verwendet"
        )

    # E-Mail ändern
    user.email = user.pending_email
    user.pending_email = None
    user.email_change_token = None
    user.email_change_token_expires = None

    db.commit()

    return {"message": "E-Mail-Adresse wurde erfolgreich geändert.", "success": True}


# ============================================
# Account löschen
# ============================================

@router.delete("/account", response_model=VerificationResponse)
@limiter.limit(RATE_LIMIT_DELETE_ACCOUNT)
def delete_account(
    request: Request,
    data: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Löscht den Account des Vermieters (DSGVO-konform).

    Properties werden "verwaist" (landlord_id = NULL) statt gelöscht.
    Bewerbungen und Dokumente der Bewerber bleiben erhalten.
    Ein Cleanup-Job löscht diese nach 6 Monaten automatisch.

    Args:
        request: FastAPI Request (für Rate Limiting)
        data: Passwort-Bestätigung
        current_user: Der authentifizierte Benutzer
        db: Datenbank-Session

    Returns:
        Erfolgsmeldung

    Raises:
        HTTPException 400: Wenn Passwort falsch
    """
    # Passwort verifizieren
    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwort ist falsch"
        )

    # User löschen
    # FK SET NULL setzt Properties.landlord_id automatisch auf NULL
    # Bewerbungen und Dokumente der Bewerber bleiben erhalten
    db.delete(current_user)
    db.commit()

    return {"message": "Ihr Konto wurde gelöscht. Bewerberdaten werden nach 6 Monaten automatisch entfernt.", "success": True}
