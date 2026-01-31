"""
Konfiguration für die Vermietenheute Anwendung.
Lädt Umgebungsvariablen aus .env Datei.
"""
import re
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Anwendungs-Einstellungen mit Pydantic."""

    # Datenbank
    DATABASE_URL: str

    # JWT Authentifizierung
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 4320  # 72 Stunden (3 Tage)

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Umgebung
    ENVIRONMENT: str = "development"

    # Email (Resend)
    RESEND_API_KEY: str = ""
    FRONTEND_URL: str = "https://vermietenheute-frontend.vercel.app"
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    # Supabase Storage
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "documents"

    # Monetarisierung
    BETA_MODE: bool = True  # Auf False setzen wenn Stripe aktiv
    ADMIN_EMAIL: str = ""  # Email für Upgrade-Benachrichtigungen

    # Dynamische CORS-Patterns (Vercel, Railway, etc.)
    CORS_ALLOW_PATTERNS: List[str] = [
        r"https://.*\.vercel\.app",
        r"https://.*\.railway\.app",
    ]

    @property
    def cors_origins_list(self) -> List[str]:
        """Gibt CORS Origins als Liste zurück."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    def is_origin_allowed(self, origin: str) -> bool:
        """
        Prüft ob ein Origin erlaubt ist.
        Erlaubt explizite Origins und dynamische Patterns.
        """
        # Explizite Origins prüfen
        if origin in self.cors_origins_list:
            return True

        # Dynamische Patterns prüfen (Vercel, Railway, etc.)
        for pattern in self.CORS_ALLOW_PATTERNS:
            if re.match(pattern, origin):
                return True

        return False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Globale Settings-Instanz
settings = Settings()
