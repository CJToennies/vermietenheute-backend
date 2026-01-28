"""
Datenbank-Konfiguration mit SQLAlchemy.
Erstellt Engine, SessionLocal und Base für Models.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings


# Datenbank-Engine erstellen
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verbindung vor Nutzung prüfen
    pool_size=10,
    max_overflow=20
)

# Session-Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Basis-Klasse für alle Models
Base = declarative_base()


def get_db():
    """
    Dependency für Datenbank-Session.
    Wird automatisch geschlossen nach Request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
