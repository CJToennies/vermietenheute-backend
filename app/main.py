"""
Vermietenheute Backend - Hauptanwendung.
FastAPI-Anwendung mit CORS und allen Routen.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api import api_router


# FastAPI-Anwendung erstellen
app = FastAPI(
    title="Vermietenheute API",
    description="Backend API für die Vermietungsplattform Vermietenheute",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS-Middleware konfigurieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload-Verzeichnis erstellen und statische Dateien mounten
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "properties"), exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# Haupt-API-Router einbinden
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["Status"])
def root():
    """
    Root-Endpoint - Gibt API-Status zurück.
    """
    return {
        "name": "Vermietenheute API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/api/docs"
    }


@app.get("/health", tags=["Status"])
def health_check():
    """
    Health-Check Endpoint für Monitoring.
    """
    return {"status": "healthy"}


# Startup-Event
@app.on_event("startup")
async def startup_event():
    """
    Wird beim Start der Anwendung ausgeführt.
    """
    print("Vermietenheute API gestartet")
    print("Dokumentation: http://localhost:8000/api/docs")


# Shutdown-Event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Wird beim Beenden der Anwendung ausgeführt.
    """
    print("Vermietenheute API wird beendet")
