"""
API-Endpoints für Authentifizierung.
Registrierung und Login.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from app.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, LoginRequest


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> User:
    """
    Registriert einen neuen Benutzer (Vermieter).

    Args:
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

    # Neuen Benutzer erstellen
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> dict:
    """
    Authentifiziert einen Benutzer und gibt einen JWT Token zurück.

    Args:
        form_data: OAuth2 Formular mit username (E-Mail) und password
        db: Datenbank-Session

    Returns:
        JWT Access Token

    Raises:
        HTTPException 401: Wenn Anmeldedaten ungültig
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

    # Token erstellen
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/json", response_model=Token)
def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Alternative Login-Route mit JSON Body statt Form Data.

    Args:
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
