"""
FastAPI Dependencies für Authentifizierung und Autorisierung.
"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from app.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User


# OAuth2 Schema für Token-Extraktion aus Header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db() -> Generator:
    """
    Dependency: Erstellt eine Datenbank-Session pro Request.
    Die Session wird automatisch geschlossen nach dem Request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency: Extrahiert und validiert den aktuellen Benutzer aus dem JWT Token.

    Args:
        db: Datenbank-Session
        token: JWT Token aus dem Authorization Header

    Returns:
        Das User-Objekt des authentifizierten Benutzers

    Raises:
        HTTPException 401: Wenn Token ungültig oder Benutzer nicht gefunden
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ungültige Anmeldedaten",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Benutzer aus Datenbank laden
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Benutzer ist deaktiviert"
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency: Stellt sicher, dass der Benutzer aktiv ist.

    Args:
        current_user: Der aktuelle Benutzer

    Returns:
        Der aktive Benutzer

    Raises:
        HTTPException 403: Wenn Benutzer deaktiviert
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Benutzer ist deaktiviert"
        )
    return current_user
