"""
Pydantic Schemas für Request/Response Validierung.
"""
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, Token, TokenData
)
from app.schemas.property import (
    PropertyCreate, PropertyUpdate, PropertyResponse
)
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse
)
from app.schemas.viewing import (
    ViewingSlotCreate, ViewingSlotUpdate, ViewingSlotResponse
)
from app.schemas.booking import (
    BookingCreate, BookingResponse
)

__all__ = [
    # User
    "UserCreate", "UserUpdate", "UserResponse", "Token", "TokenData",
    # Property
    "PropertyCreate", "PropertyUpdate", "PropertyResponse",
    # Application
    "ApplicationCreate", "ApplicationUpdate", "ApplicationResponse",
    # Viewing
    "ViewingSlotCreate", "ViewingSlotUpdate", "ViewingSlotResponse",
    # Booking
    "BookingCreate", "BookingResponse",
]
