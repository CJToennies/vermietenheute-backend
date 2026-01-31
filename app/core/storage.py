"""
Supabase Storage Service.
Verwaltet Datei-Uploads und -Downloads.
Nutzt private Buckets mit Signed URLs für Sicherheit.
"""
import uuid
from typing import Optional, Tuple
from supabase import create_client, Client
from app.config import settings


# Supabase Client (lazy initialization)
_supabase_client: Optional[Client] = None

# Signed URL Gültigkeit in Sekunden (1 Stunde)
SIGNED_URL_EXPIRY = 3600


def get_supabase_client() -> Client:
    """
    Gibt den Supabase Client zurück.
    Initialisiert ihn bei Bedarf.
    """
    global _supabase_client

    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise ValueError(
                "SUPABASE_URL und SUPABASE_SERVICE_KEY müssen gesetzt sein"
            )
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )

    return _supabase_client


def get_signed_url(storage_path: str, expiry_seconds: int = SIGNED_URL_EXPIRY) -> str:
    """
    Generiert eine URL für eine Datei.
    Versucht zuerst signed URL, dann public URL als Fallback.

    Args:
        storage_path: Pfad in Storage (z.B. "folder/file.pdf")
        expiry_seconds: Gültigkeit in Sekunden (default: 1 Stunde)

    Returns:
        URL zur Datei

    Raises:
        Exception: Bei Fehler
    """
    client = get_supabase_client()
    bucket = settings.SUPABASE_STORAGE_BUCKET

    # Methode 1: Versuche signed URL (für private buckets)
    try:
        result = client.storage.from_(bucket).create_signed_url(
            path=storage_path,
            expires_in=expiry_seconds
        )

        # Handle verschiedene Response-Formate
        signed_url = None
        if isinstance(result, dict):
            signed_url = result.get("signedURL") or result.get("signedUrl") or result.get("data", {}).get("signedUrl")
        elif hasattr(result, 'signed_url'):
            signed_url = result.signed_url
        elif isinstance(result, str):
            signed_url = result

        if signed_url:
            return signed_url
    except Exception as e:
        print(f"Signed URL Fehler (normal bei public bucket): {e}")

    # Methode 2: Public URL (für public buckets)
    try:
        public_url = client.storage.from_(bucket).get_public_url(storage_path)
        if public_url:
            return public_url
    except Exception as e:
        print(f"Public URL Fehler: {e}")

    # Methode 3: URL manuell bauen
    base_url = settings.SUPABASE_URL.rstrip('/')
    return f"{base_url}/storage/v1/object/public/{bucket}/{storage_path}"


def upload_file(
    file_content: bytes,
    filename: str,
    folder: str,
    content_type: str = "application/octet-stream"
) -> Tuple[str, str]:
    """
    Lädt eine Datei zu Supabase Storage hoch.
    Nutzt private Bucket - URLs werden bei Bedarf signiert.

    Args:
        file_content: Dateiinhalt als Bytes
        filename: Originaler Dateiname (für Extension)
        folder: Unterordner (z.B. application_id)
        content_type: MIME-Type der Datei

    Returns:
        Tuple aus (storage_path, signed_url)
        Die signed_url ist 1 Stunde gültig.

    Raises:
        Exception: Bei Upload-Fehler
    """
    client = get_supabase_client()
    bucket = settings.SUPABASE_STORAGE_BUCKET

    # Eindeutigen Dateinamen generieren
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    unique_name = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
    storage_path = f"{folder}/{unique_name}"

    # Upload zu Supabase Storage
    try:
        result = client.storage.from_(bucket).upload(
            path=storage_path,
            file=file_content,
            file_options={"contentType": content_type}
        )
    except Exception as e:
        error_msg = str(e)
        if "Bucket not found" in error_msg or "bucket" in error_msg.lower():
            raise Exception(
                f"Supabase Storage Bucket '{bucket}' nicht gefunden. "
                "Bitte erstellen Sie den Bucket im Supabase Dashboard unter Storage."
            )
        raise Exception(f"Upload fehlgeschlagen: {error_msg}")

    # Signierte URL generieren (für sofortige Anzeige nach Upload)
    signed_url = get_signed_url(storage_path)

    return storage_path, signed_url


def delete_file(storage_path: str) -> bool:
    """
    Löscht eine Datei aus Supabase Storage.

    Args:
        storage_path: Pfad in Storage (z.B. "folder/file.pdf")

    Returns:
        True wenn erfolgreich, False wenn Datei nicht existiert
    """
    client = get_supabase_client()
    bucket = settings.SUPABASE_STORAGE_BUCKET

    try:
        client.storage.from_(bucket).remove([storage_path])
        return True
    except Exception:
        return False


def delete_folder(folder: str) -> bool:
    """
    Löscht alle Dateien in einem Ordner.

    Args:
        folder: Ordnername (z.B. application_id)

    Returns:
        True wenn erfolgreich
    """
    client = get_supabase_client()
    bucket = settings.SUPABASE_STORAGE_BUCKET

    try:
        # Alle Dateien im Ordner auflisten
        files = client.storage.from_(bucket).list(folder)

        if files:
            # Pfade für Löschung vorbereiten
            paths = [f"{folder}/{f['name']}" for f in files]
            client.storage.from_(bucket).remove(paths)

        return True
    except Exception:
        return False


def get_content_type(filename: str) -> str:
    """
    Ermittelt den MIME-Type anhand der Dateiendung.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    content_types = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    return content_types.get(ext, "application/octet-stream")
