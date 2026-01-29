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
from app.core.email import send_verification_email
from app.core.rate_limit import limiter, RATE_LIMIT_REGISTER, RATE_LIMIT_LOGIN, RATE_LIMIT_RESEND
from app.config import settings
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserResponse, Token, LoginRequest,
    ResendVerificationRequest, VerificationResponse
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
