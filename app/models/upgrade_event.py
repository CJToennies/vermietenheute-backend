"""
UpgradeEvent Model - Trackt Upgrade-Interesse für Analytics.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class UpgradeEvent(Base):
    """
    Trackt Upgrade-Interesse für Analytics.

    Wichtig für: Conversion-Messung, Preisfindung.
    Speichert wann User auf "Upgrade" geklickt haben,
    auch wenn es in der Beta kostenlos freigeschaltet wird.

    Attributes:
        id: Eindeutige UUID des Events
        user_id: Benutzer der das Upgrade angefordert hat
        feature: Name des Features (multi_property, unlimited_applications, frequent_listings)
        trigger_context: Wo wurde das Modal gezeigt (property_creation, application_list)
        is_beta: War es ein Beta-Upgrade (kostenlos)
        would_pay_amount: Betrag in Cent den der User zahlen würde (590 = 5,90€)
        shown_at: Wann wurde das Modal gezeigt
        unlocked_at: Wann hat der User geklickt
        time_to_decision_seconds: Zeit zwischen Modal-Anzeige und Klick
        created_at: Erstellungszeitpunkt
    """

    __tablename__ = "upgrade_events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Feature-Details
    feature = Column(String(50), nullable=False, index=True)
    trigger_context = Column(String(100), nullable=True)

    # Beta vs. Paid
    is_beta = Column(Boolean, default=True, nullable=False)
    would_pay_amount = Column(Integer, nullable=True)  # Cent (590 = 5,90€)

    # Timing
    shown_at = Column(DateTime, nullable=True)
    unlocked_at = Column(DateTime, nullable=True)
    time_to_decision_seconds = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Beziehungen
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<UpgradeEvent {self.feature} by {self.user_id}>"
