"""
Pydantic Schemas für User/Authentifizierung.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Basis-Schema für User-Daten."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema für Benutzer-Registrierung."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema für Benutzer-Aktualisierung."""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema für User-Response."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema für JWT Token Response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema für Token-Payload."""
    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema für Login-Request."""
    email: EmailStr
    password: str
