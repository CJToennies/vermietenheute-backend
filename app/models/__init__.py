"""
SQLAlchemy Models für Vermietenheute.
Importiert alle Models für einfachen Zugriff.
"""
from app.models.user import User
from app.models.property import Property
from app.models.property_image import PropertyImage
from app.models.application import Application
from app.models.application_document import ApplicationDocument
from app.models.self_disclosure import SelfDisclosure
from app.models.viewing import ViewingSlot
from app.models.viewing_invitation import ViewingInvitation
from app.models.booking import Booking

# Alle Models für Alembic-Migrationen exportieren
__all__ = [
    "User",
    "Property",
    "PropertyImage",
    "Application",
    "ApplicationDocument",
    "SelfDisclosure",
    "ViewingSlot",
    "ViewingInvitation",
    "Booking"
]
