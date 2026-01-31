"""
API-Router für alle Endpoints.
"""
from fastapi import APIRouter
from app.api import auth, properties, applications, viewings, images, self_disclosure, portal, documents, upgrades

# Haupt-API-Router
api_router = APIRouter()

# Alle Sub-Router einbinden
api_router.include_router(auth.router, prefix="/auth", tags=["Authentifizierung"])
api_router.include_router(properties.router, prefix="/properties", tags=["Immobilien"])
api_router.include_router(images.router, prefix="/properties", tags=["Bilder"])
api_router.include_router(applications.router, prefix="/applications", tags=["Bewerbungen"])
api_router.include_router(self_disclosure.router, prefix="/applications", tags=["Selbstauskunft"])
api_router.include_router(viewings.router, prefix="/viewings", tags=["Besichtigungen"])
api_router.include_router(portal.router, prefix="/applicant", tags=["Bewerber-Portal"])
api_router.include_router(documents.router, prefix="/applicant", tags=["Bewerber-Dokumente"])
api_router.include_router(upgrades.router, tags=["Upgrade/Monetarisierung"])
