"""
API-Endpunkte für Upgrade/Monetarisierung.

Provides endpoints for:
- Getting user's unlocked features
- Getting user's current limits and usage
- Unlocking features (beta: free, later: Stripe)
"""
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Property, Application, UpgradeEvent
from app.schemas.upgrade import (
    UserFeaturesResponse,
    UserLimitsResponse,
    LimitInfo,
    FrequencyLimitInfo,
    UpgradeRequest,
    UpgradeResponse,
)
from app.core.deps import get_current_user
from app.core.email import send_upgrade_notification_email
from app.config import settings


router = APIRouter(prefix="/upgrades", tags=["upgrades"])


# Feature-Typ Definition
FeatureType = Literal["multi_property", "unlimited_applications", "frequent_listings"]


@router.get("/features", response_model=UserFeaturesResponse)
def get_user_features(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Gibt die freigeschalteten Features des Users zurück.

    Returns:
        UserFeaturesResponse mit den Feature-Flags
    """
    return {
        "multi_property": current_user.feature_multi_property,
        "unlimited_applications": current_user.feature_unlimited_applications,
        "frequent_listings": current_user.feature_frequent_listings,
    }


@router.get("/limits", response_model=UserLimitsResponse)
def get_user_limits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Gibt aktuelle Nutzung und Limits zurück.

    Returns:
        UserLimitsResponse mit Properties, Applications und Frequency Limits
    """
    # Anzahl aktiver Properties
    active_properties = db.query(Property).filter(
        Property.landlord_id == current_user.id,
        Property.is_active == True
    ).count()

    # Letztes Property-Erstellungsdatum
    last_property = db.query(Property).filter(
        Property.landlord_id == current_user.id
    ).order_by(Property.created_at.desc()).first()

    days_since_last = None
    frequency_exceeded = False
    if last_property:
        days_since_last = (datetime.utcnow() - last_property.created_at).days
        frequency_exceeded = days_since_last < 90

    # Max Bewerbungen pro Property
    max_applications_query = db.query(
        func.count(Application.id).label('count')
    ).join(Property).filter(
        Property.landlord_id == current_user.id
    ).group_by(Application.property_id).order_by(
        func.count(Application.id).desc()
    ).first()

    max_applications = max_applications_query.count if max_applications_query else 0

    return {
        "properties": {
            "current": active_properties,
            "limit": 1,
            "exceeded": active_properties >= 1,
        },
        "applications": {
            "current": max_applications,
            "limit": 20,
            "exceeded": max_applications > 20,
        },
        "frequency": {
            "days_since_last": days_since_last,
            "limit_days": 90,
            "exceeded": frequency_exceeded,
        }
    }


@router.post("/unlock/{feature}", response_model=UpgradeResponse)
def unlock_feature(
    feature: FeatureType,
    data: UpgradeRequest = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Schaltet ein Feature frei.

    In der Beta-Phase: Kostenlos freigeschaltet.
    Später: Stripe-Checkout Session erstellen.

    Args:
        feature: multi_property, unlimited_applications oder frequent_listings
        data: Optional - Trigger-Kontext

    Returns:
        UpgradeResponse mit Erfolg/Fehler
    """
    trigger_context = data.trigger_context if data else None

    # User frisch aus der DB laden (innerhalb dieser Session)
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User nicht gefunden")

    # Prüfen ob Feature bereits freigeschaltet
    feature_flags = {
        "multi_property": user.feature_multi_property,
        "unlimited_applications": user.feature_unlimited_applications,
        "frequent_listings": user.feature_frequent_listings,
    }

    if feature_flags.get(feature):
        return {
            "success": True,
            "feature": feature,
            "message": "Feature bereits freigeschaltet"
        }

    # Feature freischalten
    if feature == "multi_property":
        user.feature_multi_property = True
    elif feature == "unlimited_applications":
        user.feature_unlimited_applications = True
    elif feature == "frequent_listings":
        user.feature_frequent_listings = True

    # Subscription-Status auf Beta setzen (wenn noch free)
    if user.subscription_status == "free":
        user.subscription_status = "beta"

    # Upgrade-Event loggen
    upgrade_event = UpgradeEvent(
        user_id=user.id,
        feature=feature,
        trigger_context=trigger_context,
        is_beta=settings.BETA_MODE,
        would_pay_amount=590,  # 5,90€ in Cent
        unlocked_at=datetime.utcnow()
    )
    db.add(upgrade_event)

    # Alle Änderungen speichern
    db.commit()

    # Admin benachrichtigen
    properties_count = db.query(Property).filter(
        Property.landlord_id == user.id
    ).count()

    send_upgrade_notification_email(
        user_email=user.email,
        user_name=user.name,
        feature=feature,
        properties_count=properties_count,
        trigger_context=trigger_context
    )

    feature_names = {
        "multi_property": "Mehrere Objekte",
        "unlimited_applications": "Unbegrenzte Bewerbungen",
        "frequent_listings": "Häufige Inserate"
    }

    return {
        "success": True,
        "feature": feature,
        "message": f"'{feature_names.get(feature, feature)}' erfolgreich freigeschaltet"
    }


@router.get("/check/{feature}")
def check_feature_required(
    feature: FeatureType,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Prüft ob ein Feature-Upgrade erforderlich ist.

    Args:
        feature: multi_property, unlimited_applications oder frequent_listings

    Returns:
        Dict mit required (bool), unlocked (bool), limit_info
    """
    # Feature-Status prüfen
    feature_flags = {
        "multi_property": current_user.feature_multi_property,
        "unlimited_applications": current_user.feature_unlimited_applications,
        "frequent_listings": current_user.feature_frequent_listings,
    }

    is_unlocked = feature_flags.get(feature, False)

    # Limit-Status prüfen
    limits = get_user_limits(current_user, db)

    limit_exceeded = False
    if feature == "multi_property":
        limit_exceeded = limits["properties"]["exceeded"]
    elif feature == "unlimited_applications":
        limit_exceeded = limits["applications"]["exceeded"]
    elif feature == "frequent_listings":
        limit_exceeded = limits["frequency"]["exceeded"]

    return {
        "feature": feature,
        "unlocked": is_unlocked,
        "limit_exceeded": limit_exceeded,
        "upgrade_required": limit_exceeded and not is_unlocked,
        "beta_mode": settings.BETA_MODE
    }
