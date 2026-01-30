"""
API-Endpoints für Bewerber-Dokumente.
Upload, Abruf und Löschung von Bewerbungsdokumenten.
Nutzt Supabase Storage für persistente Dateispeicherung.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.core.storage import upload_file, delete_file, get_content_type
from app.models.application import Application
from app.models.application_document import ApplicationDocument
from app.schemas.application_document import (
    ApplicationDocumentResponse,
    ApplicationDocumentListResponse,
    DocumentUploadResponse,
    DOCUMENT_CATEGORIES,
    CATEGORY_LABELS
)


router = APIRouter()

# Erlaubte Dateitypen
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".docx", ".doc"}
MAX_TOTAL_SIZE = 30 * 1024 * 1024  # 30 MB gesamt
MAX_DOCUMENTS = 10


def get_file_extension(filename: str) -> str:
    """Gibt die Dateiendung zurück."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return f".{ext}" if ext else ""


def is_allowed_file(filename: str) -> bool:
    """Prüft ob Dateityp erlaubt ist."""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def format_file_size(size_bytes: int) -> str:
    """Formatiert Dateigröße lesbar."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_application_by_access_token(db: Session, access_token: str) -> Application:
    """Holt Application anhand des access_token."""
    application = db.query(Application).filter(
        Application.access_token == access_token
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bewerbung nicht gefunden"
        )

    return application


def get_total_documents_size(db: Session, application_id: uuid.UUID) -> int:
    """Berechnet die Gesamtgröße aller Dokumente einer Bewerbung."""
    documents = db.query(ApplicationDocument).filter(
        ApplicationDocument.application_id == application_id
    ).all()
    return sum(doc.file_size for doc in documents)


def document_to_response(doc: ApplicationDocument) -> dict:
    """Konvertiert ein Document Model zu Response dict."""
    return {
        "id": doc.id,
        "application_id": doc.application_id,
        "filename": doc.filename,
        "display_name": doc.display_name,
        "category": doc.category,
        "category_label": CATEGORY_LABELS.get(doc.category, doc.category),
        "filepath": doc.filepath,
        "url": doc.url,  # Direkte Supabase Storage URL
        "file_size": doc.file_size,
        "file_size_formatted": format_file_size(doc.file_size),
        "created_at": doc.created_at
    }


@router.post("/portal/{access_token}/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    access_token: str,
    file: UploadFile = File(...),
    category: str = Form(...),
    display_name: str = Form(None),
    db: Session = Depends(get_db)
) -> dict:
    """
    Lädt ein Dokument für eine Bewerbung hoch.
    Öffentlicher Endpoint - Zugriff über access_token.

    Args:
        access_token: Zugangstoken der Bewerbung
        file: Die hochzuladende Datei
        category: Dokumentkategorie
        display_name: Optionaler Anzeigename (für "sonstiges")
        db: Datenbank-Session

    Returns:
        Das hochgeladene Dokument

    Raises:
        HTTPException 400: Wenn Limit überschritten oder Dateityp nicht erlaubt
        HTTPException 404: Wenn Bewerbung nicht gefunden
    """
    # Bewerbung laden
    application = get_application_by_access_token(db, access_token)

    # Kategorie validieren
    if category not in DOCUMENT_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ungültige Kategorie. Erlaubt: {', '.join(DOCUMENT_CATEGORIES)}"
        )

    # Bei "sonstiges" muss display_name angegeben werden
    if category == "sonstiges" and not display_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bei 'Sonstiges' muss ein Dokumentname angegeben werden"
        )

    # Dateityp prüfen
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dateityp nicht erlaubt. Erlaubt: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Dateigröße ermitteln
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    # Anzahl Dokumente prüfen
    doc_count = db.query(ApplicationDocument).filter(
        ApplicationDocument.application_id == application.id
    ).count()

    if doc_count >= MAX_DOCUMENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximale Anzahl von {MAX_DOCUMENTS} Dokumenten erreicht"
        )

    # Gesamtgröße prüfen
    current_total = get_total_documents_size(db, application.id)
    if current_total + file_size > MAX_TOTAL_SIZE:
        remaining = MAX_TOTAL_SIZE - current_total
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Speicherlimit überschritten. Verfügbar: {format_file_size(remaining)}"
        )

    # Datei-Inhalt lesen
    file_content = await file.read()

    # Zu Supabase Storage hochladen
    content_type = get_content_type(file.filename)
    folder = str(application.id)

    try:
        storage_path, public_url = upload_file(
            file_content=file_content,
            filename=file.filename,
            folder=folder,
            content_type=content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Hochladen: {str(e)}"
        )

    # Datenbank-Eintrag erstellen
    document = ApplicationDocument(
        application_id=application.id,
        filename=file.filename,
        display_name=display_name if category == "sonstiges" else None,
        category=category,
        filepath=storage_path,
        url=public_url,
        file_size=file_size
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "message": "Dokument erfolgreich hochgeladen",
        "document": document_to_response(document)
    }


@router.get("/portal/{access_token}/documents", response_model=ApplicationDocumentListResponse)
def list_documents(
    access_token: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Listet alle Dokumente einer Bewerbung.
    Öffentlicher Endpoint - Zugriff über access_token.

    Args:
        access_token: Zugangstoken der Bewerbung
        db: Datenbank-Session

    Returns:
        Liste der Dokumente mit Größeninfo
    """
    application = get_application_by_access_token(db, access_token)

    documents = db.query(ApplicationDocument).filter(
        ApplicationDocument.application_id == application.id
    ).order_by(ApplicationDocument.created_at.desc()).all()

    total_size = sum(doc.file_size for doc in documents)

    return {
        "items": [document_to_response(doc) for doc in documents],
        "total": len(documents),
        "total_size": total_size,
        "total_size_formatted": format_file_size(total_size),
        "max_size": MAX_TOTAL_SIZE,
        "remaining_size": MAX_TOTAL_SIZE - total_size
    }


@router.delete("/portal/{access_token}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    access_token: str,
    document_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> None:
    """
    Löscht ein Dokument.
    Öffentlicher Endpoint - Zugriff über access_token.

    Args:
        access_token: Zugangstoken der Bewerbung
        document_id: UUID des Dokuments
        db: Datenbank-Session

    Raises:
        HTTPException 404: Wenn Dokument nicht gefunden
    """
    application = get_application_by_access_token(db, access_token)

    document = db.query(ApplicationDocument).filter(
        ApplicationDocument.id == document_id,
        ApplicationDocument.application_id == application.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )

    # Datei aus Supabase Storage löschen
    if document.filepath:
        delete_file(document.filepath)

    # Datenbank-Eintrag löschen
    db.delete(document)
    db.commit()
