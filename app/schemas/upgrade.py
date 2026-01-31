"""
Pydantic Schemas für Upgrade/Monetarisierung.
"""
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel


# Feature-Typen
FeatureType = Literal["multi_property", "unlimited_applications", "frequent_listings"]


class UserFeaturesResponse(BaseModel):
    """Response mit den freigeschalteten Features des Users."""
    multi_property: bool = False
    unlimited_applications: bool = False
    frequent_listings: bool = False


class LimitInfo(BaseModel):
    """Informationen zu einem einzelnen Limit."""
    current: int
    limit: int
    exceeded: bool


class FrequencyLimitInfo(BaseModel):
    """Informationen zum Frequenz-Limit."""
    days_since_last: Optional[int] = None
    limit_days: int = 90
    exceeded: bool = False


class UserLimitsResponse(BaseModel):
    """Response mit den aktuellen Limits des Users."""
    properties: LimitInfo
    applications: LimitInfo
    frequency: FrequencyLimitInfo


class UpgradeRequest(BaseModel):
    """Request für Feature-Freischaltung."""
    trigger_context: Optional[str] = None  # Wo wurde das Upgrade getriggert


class UpgradeResponse(BaseModel):
    """Response nach Feature-Freischaltung."""
    success: bool
    feature: str
    message: str


class UpgradeEventResponse(BaseModel):
    """Response für ein Upgrade-Event."""
    id: UUID
    user_id: UUID
    feature: str
    trigger_context: Optional[str] = None
    is_beta: bool = True
    would_pay_amount: Optional[int] = None
    unlocked_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
