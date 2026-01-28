"""
API-Endpoints für Property-Bilder.
Upload, Abruf und Löschung von Immobilienbildern.
"""
import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.property import Property
from app.models.property_image import PropertyImage
from app.config import settings


router = APIRouter()

# Upload-Verzeichnis
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "properties")

# Erlaubte Dateitypen
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def get_file_extension(filename: str) -> str:
    """Gibt die Dateiendung zurück."""
    return os.path.splitext(filename)[1].lower()


def is_allowed_file(filename: str) -> bool:
    """Prüft ob Dateityp erlaubt ist."""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


@router.post("/{property_id}/images", status_code=status.HTTP_201_CREATED)
async def upload_images(
    property_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Lädt ein oder mehrere Bilder für eine Immobilie hoch.

    Args:
        property_id: UUID der Immobilie
        files: Liste von Bilddateien
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Liste der hochgeladenen Bilder

    Raises:
        HTTPException 404: Wenn Immobilie nicht gefunden
        HTTPException 403: Wenn keine Berechtigung
        HTTPException 400: Wenn Dateityp nicht erlaubt
    """
    # Property prüfen
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

    # Upload-Verzeichnis erstellen
    property_upload_dir = os.path.join(UPLOAD_DIR, str(property_id))
    os.makedirs(property_upload_dir, exist_ok=True)

    # Aktuelle höchste Reihenfolge ermitteln
    max_order = db.query(PropertyImage).filter(
        PropertyImage.property_id == property_id
    ).count()

    uploaded_images = []

    for i, file in enumerate(files):
        # Dateityp prüfen
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dateityp nicht erlaubt: {file.filename}. Erlaubt: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Dateigröße prüfen
        file.file.seek(0, 2)  # Zum Ende
        file_size = file.file.tell()
        file.file.seek(0)  # Zurück zum Anfang

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Datei zu groß: {file.filename}. Maximal {MAX_FILE_SIZE // (1024*1024)} MB erlaubt."
            )

        # Eindeutigen Dateinamen generieren
        file_ext = get_file_extension(file.filename)
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        filepath = os.path.join(property_upload_dir, unique_filename)

        # Datei speichern
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Relativen Pfad für DB speichern
        relative_path = f"uploads/properties/{property_id}/{unique_filename}"

        # Datenbank-Eintrag erstellen
        image = PropertyImage(
            property_id=property_id,
            filename=file.filename,
            filepath=relative_path,
            order=max_order + i
        )

        db.add(image)
        uploaded_images.append({
            "id": str(image.id),
            "filename": image.filename,
            "filepath": image.filepath,
            "url": f"/static/{relative_path}",
            "order": image.order
        })

    db.commit()

    return {
        "message": f"{len(uploaded_images)} Bild(er) erfolgreich hochgeladen",
        "images": uploaded_images
    }


@router.get("/{property_id}/images")
def list_images(
    property_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> dict:
    """
    Listet alle Bilder einer Immobilie.

    Args:
        property_id: UUID der Immobilie
        db: Datenbank-Session

    Returns:
        Liste der Bilder
    """
    # Property prüfen
    property_obj = db.query(Property).filter(Property.id == property_id).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Immobilie nicht gefunden"
        )

    images = db.query(PropertyImage).filter(
        PropertyImage.property_id == property_id
    ).order_by(PropertyImage.order).all()

    return {
        "items": [
            {
                "id": str(img.id),
                "property_id": str(img.property_id),
                "filename": img.filename,
                "filepath": img.filepath,
                "url": f"/static/{img.filepath}",
                "order": img.order,
                "created_at": img.created_at.isoformat()
            }
            for img in images
        ],
        "total": len(images)
    }


@router.delete("/{property_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    property_id: uuid.UUID,
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Löscht ein Bild einer Immobilie.

    Args:
        property_id: UUID der Immobilie
        image_id: UUID des Bildes
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Raises:
        HTTPException 404: Wenn Bild nicht gefunden
        HTTPException 403: Wenn keine Berechtigung
    """
    # Property prüfen
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

    # Bild suchen
    image = db.query(PropertyImage).filter(
        PropertyImage.id == image_id,
        PropertyImage.property_id == property_id
    ).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bild nicht gefunden"
        )

    # Datei löschen
    full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), image.filepath)
    if os.path.exists(full_path):
        os.remove(full_path)

    # Datenbank-Eintrag löschen
    db.delete(image)
    db.commit()


@router.patch("/{property_id}/images/{image_id}/order")
def update_image_order(
    property_id: uuid.UUID,
    image_id: uuid.UUID,
    order: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Ändert die Reihenfolge eines Bildes.

    Args:
        property_id: UUID der Immobilie
        image_id: UUID des Bildes
        order: Neue Reihenfolge
        current_user: Authentifizierter Benutzer
        db: Datenbank-Session

    Returns:
        Aktualisiertes Bild
    """
    # Property prüfen
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

    # Bild suchen
    image = db.query(PropertyImage).filter(
        PropertyImage.id == image_id,
        PropertyImage.property_id == property_id
    ).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bild nicht gefunden"
        )

    image.order = order
    db.commit()

    return {
        "id": str(image.id),
        "property_id": str(image.property_id),
        "filename": image.filename,
        "url": f"/static/{image.filepath}",
        "order": image.order
    }
