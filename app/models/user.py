"""
User Model - Vermieter/Nutzer der Plattform.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """
    Benutzer-Tabelle für Vermieter.

    Attributes:
        id: Eindeutige UUID des Benutzers
        email: E-Mail-Adresse (einzigartig)
        password_hash: Gehashtes Passwort
        name: Anzeigename des Benutzers
        is_active: Ob der Account aktiv ist
        is_verified: Ob die E-Mail verifiziert ist
        verification_token: Token zur E-Mail-Verifizierung
        verification_token_expires: Ablaufzeit des Tokens
        password_reset_token: Token zum Passwort-Reset
        password_reset_token_expires: Ablaufzeit des Reset-Tokens
        pending_email: Neue E-Mail-Adresse (noch nicht bestätigt)
        email_change_token: Token zur E-Mail-Änderung
        email_change_token_expires: Ablaufzeit des Email-Change-Tokens
        created_at: Erstellungszeitpunkt
        updated_at: Letzter Änderungszeitpunkt
    """

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True, index=True)
    verification_token_expires = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True, index=True)
    password_reset_token_expires = Column(DateTime, nullable=True)
    pending_email = Column(String(255), nullable=True)
    email_change_token = Column(String(255), nullable=True, index=True)
    email_change_token_expires = Column(DateTime, nullable=True)

    # Feature-Flags (Monetarisierung)
    feature_multi_property = Column(Boolean, default=False, nullable=False)
    feature_unlimited_applications = Column(Boolean, default=False, nullable=False)
    feature_frequent_listings = Column(Boolean, default=False, nullable=False)

    # Stripe-Vorbereitung (für spätere Zahlungsintegration)
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    subscription_status = Column(String(50), default="free", nullable=False)  # free, beta, active, cancelled
    subscription_plan = Column(String(50), nullable=True)  # null, "pro", "business"
    subscription_ends_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Beziehungen
    properties = relationship("Property", back_populates="landlord")

    def __repr__(self) -> str:
        return f"<User {self.email}>"
