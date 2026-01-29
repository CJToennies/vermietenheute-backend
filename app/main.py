"""
Vermietenheute Backend - Hauptanwendung.
FastAPI-Anwendung mit CORS, Rate Limiting und allen Routen.
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.api import api_router
from app.core.rate_limit import limiter


# FastAPI-Anwendung erstellen
app = FastAPI(
    title="Vermietenheute API",
    description="Backend API für die Vermietungsplattform Vermietenheute",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Rate Limiter konfigurieren
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """
    Dynamische CORS-Middleware.
    Erlaubt explizite Origins und Wildcard-Patterns (*.vercel.app, *.railway.app).
    """

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")

        # Preflight-Request (OPTIONS)
        if request.method == "OPTIONS":
            response = Response(status_code=200)
            if origin and settings.is_origin_allowed(origin):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept"
            return response

        # Normale Requests
        response = await call_next(request)

        if origin and settings.is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


# Dynamische CORS-Middleware hinzufügen
app.add_middleware(DynamicCORSMiddleware)

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
