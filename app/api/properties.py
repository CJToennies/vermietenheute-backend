"""
API-Endpoints für Immobilien (Properties).
CRUD-Operationen und Bewerbungs-Abruf.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.property import Property
from app.models.application import Application
from app.schemas.property import (
    PropertyCreate, PropertyUpdate, PropertyResponse, PropertyListResponse, PropertyPublicResponse
)
from app.schemas.application import ApplicationResponse, ApplicationListResponse, application_to_response


router = APIRouter()


def property_to_public_response(property_obj: Property) -> dict:
    """Konvertiert Property zu öffentlicher Response mit optionaler Adress-Maskierung."""
    response = {
        "id": property_obj.id,
        "title": property_obj.title,
        "type": property_obj.type,
        "description": property_obj.description,
        "city": property_obj.city,
        "rent": property_obj.rent,
        "deposit": property_obj.deposit,
        "size": property_obj.size,
        "rooms": property_obj.rooms,
        "available_from": property_obj.available_from,
        "furnished": property_obj.furnished,
        "pets_allowed": property_obj.pets_allowed,
        "listing_url": property_obj.listing_url,
        "show_address_publicly": property_obj.show_address_publicly,
        "is_active": property_obj.is_active,
        "created_at": property_obj.created_at,
    }

    # Adresse nur anzeigen wenn show_address_publicly = True
    if property_obj.show_address_publicly:
        response["address"] = property_obj.address
        response["zip_code"] = property_obj.zip_code
    else:
        response["address"] = None  # Frontend zeigt "Adresse auf Anfrage"
        response["zip_code"] = None

    return response


@router.get("", response_model=PropertyListResponse)
def list_properties(
    landlord_id: Optional[UUID] = Query(None, description="Filter nach Vermieter-ID"),
    city: Optional[str] = Query(None, description="Filter nach Stadt"),
    type: Optional[str] = Query(None, description="Filter nach Immobilientyp"),
    min_rent: Optional[float] = Query(None, ge=0, description="Minimale Miete"),
    max_rent: Optional[float] = Query(None, ge=0, description="Maximale Miete"),
    furnished: Optional[bool] = Query(None, description="Nur möbliert"),
    pets_allowed: Optional[bool] = Query(None, description="Haustiere erlaubt"),
    include_inactive: Optional[bool] = Query(False, description="Auch inaktive anzeigen"),
    page: int = Query(1, ge=1, description="Seite"),
    per_page: int = Query(20, ge=1, le=100, description="Einträge pro Seite"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Listet Immobilien mit optionalen Filtern.

    Args:
        landlord_id: Optional - Filtert nach Vermieter
        city: Optional - Filtert nach Stadt
        type: Optional - Filtert nach Typ (wohnung, haus, etc.)
        min_rent: Optional - Minimale Kaltmiete
        max_rent: Optional - Maximale Kaltmiete
        furnished: Optional - Nur möblierte Objekte
        pets_allowed: Optional - Nur mit Haustiererlaubnis
        include_inactive: Auch inaktive Properties anzeigen (Standard: False)
        page: Seitennummer (Standard: 1)
        per_page: Einträge pro Seite (Standard: 20)
        db: Datenbank-Session

    Returns:
        Paginierte Liste von Immobilien
    """
    query = db.query(Property)

    # Nur aktive anzeigen, außer include_inactive ist True oder landlord_id ist gesetzt
    if not include_inactive and not landlord_id:
        query = query.filter(Property.is_active == True)

    # Filter anwenden
    if landlord_id:
        query = query.filter(Property.landlord_id == landlord_id)
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if type:
        query = query.filter(Property.type == type)
    if min_rent is not None:
        query = query.filter(Property.rent >= min_rent)
    if max_rent is not None:
        query = query.filter(Property.rent <= max_rent)
    if furnished is not None:
        query = query.filter(Property.furnished == furnished)
    if pets_allowed is not None:
        query = query.filter(Property.pets_allowed == pets_allowed)

    # Gesamtanzahl
    total = query.count()

    # Pagination
    offset = (page - 1) * per_page
    properties = query.order_by(Property.created_at.desc()).offset(offset).limit(per_page).all()

    return {
        "items": properties,
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.post("", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_property(
    property_data: PropertyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Property:
    """
    Erstellt eine neue Immobilie für den aktuellen Vermieter.

    Args:
        property_data: Immobiliendaten
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Die erstellte Immobilie
    """
    property_obj = Property(
        landlord_id=current_user.id,
        **property_data.model_dump()
    )

    db.add(property_obj)
    db.commit()
    db.refresh(property_obj)

    return property_obj


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Property:
    """
    Ruft eine einzelne Immobilie ab (für eingeloggte Vermieter).
    Zeigt alle Details inkl. Adresse.

    Args:
        property_id: UUID der Immobilie
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Die Immobilie

    Raises:
        HTTPException 404: Wenn Immobilie nicht gefunden
        HTTPException 403: Wenn keine Berechtigung
    """
    property_obj = db.query(Property).filter(Property.id == property_id).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht gefunden"
        )

    # Nur eigene Properties oder Admin dürfen volle Details sehen
    if property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Immobilie"
        )

    return property_obj


@router.get("/{property_id}/public", response_model=PropertyPublicResponse)
def get_property_public(
    property_id: UUID,
    db: Session = Depends(get_db)
) -> dict:
    """
    Ruft eine einzelne Immobilie ab (öffentlich, ohne Auth).
    Adresse wird nur angezeigt wenn show_address_publicly = True.

    Args:
        property_id: UUID der Immobilie
        db: Datenbank-Session

    Returns:
        Die Immobilie (mit maskierter Adresse falls nicht öffentlich)

    Raises:
        HTTPException 404: Wenn Immobilie nicht gefunden oder nicht aktiv
    """
    property_obj = db.query(Property).filter(Property.id == property_id).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht gefunden"
        )

    if not property_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht mehr verfügbar"
        )

    return property_to_public_response(property_obj)


@router.patch("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: UUID,
    property_data: PropertyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Property:
    """
    Aktualisiert eine Immobilie.
    Nur der Eigentümer kann seine Immobilien bearbeiten.

    Args:
        property_id: UUID der Immobilie
        property_data: Zu aktualisierende Felder
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Die aktualisierte Immobilie

    Raises:
        HTTPException 404: Wenn Immobilie nicht gefunden
        HTTPException 403: Wenn Benutzer nicht Eigentümer
    """
    property_obj = db.query(Property).filter(Property.id == property_id).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht gefunden"
        )

    # Berechtigung prüfen
    if property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Immobilie"
        )

    # Nur gesetzte Felder aktualisieren
    update_data = property_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(property_obj, field, value)

    db.commit()
    db.refresh(property_obj)

    return property_obj


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    property_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Löscht eine Immobilie (Soft-Delete durch is_active=False).

    Args:
        property_id: UUID der Immobilie
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Raises:
        HTTPException 404: Wenn Immobilie nicht gefunden
        HTTPException 403: Wenn Benutzer nicht Eigentümer
    """
    property_obj = db.query(Property).filter(Property.id == property_id).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht gefunden"
        )

    # Berechtigung prüfen
    if property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Immobilie"
        )

    # Soft-Delete
    property_obj.is_active = False
    db.commit()


@router.get("/{property_id}/applications", response_model=ApplicationListResponse)
def list_property_applications(
    property_id: UUID,
    status_filter: Optional[str] = Query(None, description="Filter nach Status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Listet alle Bewerbungen für eine Immobilie.
    Nur der Eigentümer kann die Bewerbungen sehen.

    Args:
        property_id: UUID der Immobilie
        status_filter: Optional - Filter nach Bewerbungsstatus
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Liste der Bewerbungen

    Raises:
        HTTPException 404: Wenn Immobilie nicht gefunden
        HTTPException 403: Wenn Benutzer nicht Eigentümer
    """
    property_obj = db.query(Property).filter(Property.id == property_id).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht gefunden"
        )

    # Berechtigung prüfen
    if property_obj.landlord_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für diese Immobilie"
        )

    # Bewerbungen abfragen mit Eager Loading der Relationships
    query = db.query(Application).options(
        joinedload(Application.documents),
        joinedload(Application.self_disclosure)
    ).filter(Application.property_id == property_id)

    if status_filter:
        query = query.filter(Application.status == status_filter)

    applications = query.order_by(Application.created_at.desc()).all()

    return {
        "items": [application_to_response(app) for app in applications],
        "total": len(applications)
    }
