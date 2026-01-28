"""
Konfiguration für die Vermietenheute Anwendung.
Lädt Umgebungsvariablen aus .env Datei.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Anwendungs-Einstellungen mit Pydantic."""

    # Datenbank
    DATABASE_URL: str

    # JWT Authentifizierung
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Umgebung
    ENVIRONMENT: str = "development"

    @property
    def cors_origins_list(self) -> List[str]:
        """Gibt CORS Origins als Liste zurück."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Globale Settings-Instanz
settings = Settings()
