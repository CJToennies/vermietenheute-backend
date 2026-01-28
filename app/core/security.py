"""
Sicherheitsfunktionen für Authentifizierung.
JWT Token-Erstellung und Passwort-Hashing.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from app.config import settings


# Passwort-Hashing Kontext mit bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Überprüft ein Klartext-Passwort gegen den Hash.

    Args:
        plain_password: Das eingegebene Passwort
        hashed_password: Der gespeicherte Hash

    Returns:
        True wenn das Passwort korrekt ist
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Erstellt einen sicheren Hash für ein Passwort.

    Args:
        password: Das zu hashende Passwort

    Returns:
        Der bcrypt-Hash des Passworts
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Erstellt einen JWT Access Token.

    Args:
        data: Die Daten die im Token gespeichert werden
        expires_delta: Optional - Gültigkeitsdauer des Tokens

    Returns:
        Der encoded JWT Token als String
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Dekodiert und validiert einen JWT Token.

    Args:
        token: Der zu dekodierende Token

    Returns:
        Die Token-Payload oder None bei Fehler
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.JWTError:
        return None
