# Vermietenheute Backend

FastAPI Backend für die Vermietungsplattform Vermietenheute.

## Features

- JWT-basierte Authentifizierung
- Multi-Tenant Architektur (landlord_id)
- CRUD-Operationen für Immobilien
- Bewerbungsverwaltung
- Besichtigungstermine und Buchungen
- PostgreSQL Datenbank mit Alembic Migrationen

## Voraussetzungen

- Python 3.10+
- PostgreSQL 14+
- pip oder pipenv

## Installation

### 1. Repository klonen und Virtual Environment erstellen

```bash
cd vermietenheute-backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 3. Umgebungsvariablen konfigurieren

```bash
# .env.example kopieren
cp .env.example .env

# .env bearbeiten und Werte anpassen
```

Wichtige Variablen:
- `DATABASE_URL`: PostgreSQL Verbindungs-URL
- `SECRET_KEY`: Geheimer Schlüssel für JWT (mindestens 32 Zeichen)

### 4. Datenbank erstellen

```sql
-- In PostgreSQL
CREATE DATABASE vermietenheute;
```

### 5. Migrationen ausführen

```bash
# Initiale Migration erstellen
alembic revision --autogenerate -m "initial"

# Migrationen anwenden
alembic upgrade head
```

### 6. Server starten

```bash
# Entwicklungsserver
uvicorn app.main:app --reload --port 8000

# Produktionsserver
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API-Dokumentation

Nach dem Start ist die Dokumentation verfügbar unter:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## API-Endpoints

### Authentifizierung

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| POST | `/api/auth/register` | Neuen Benutzer registrieren |
| POST | `/api/auth/login` | Einloggen (OAuth2 Form) |
| POST | `/api/auth/login/json` | Einloggen (JSON Body) |

### Immobilien

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/api/properties` | Alle Immobilien auflisten |
| POST | `/api/properties` | Neue Immobilie erstellen |
| GET | `/api/properties/{id}` | Immobilie abrufen |
| PATCH | `/api/properties/{id}` | Immobilie aktualisieren |
| DELETE | `/api/properties/{id}` | Immobilie löschen |
| GET | `/api/properties/{id}/applications` | Bewerbungen abrufen |

### Bewerbungen

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| POST | `/api/applications` | Bewerbung einreichen |
| GET | `/api/applications/{id}` | Bewerbung abrufen |
| PATCH | `/api/applications/{id}` | Bewerbung aktualisieren |
| DELETE | `/api/applications/{id}` | Bewerbung löschen |

### Besichtigungen

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/api/viewings` | Alle Termine auflisten |
| POST | `/api/viewings` | Neuen Termin erstellen |
| GET | `/api/viewings/{id}` | Termin abrufen |
| PATCH | `/api/viewings/{id}` | Termin aktualisieren |
| DELETE | `/api/viewings/{id}` | Termin löschen |
| POST | `/api/viewings/{id}/book` | Termin buchen |

## Projekt-Struktur

```
vermietenheute-backend/
├── alembic/                  # Datenbank-Migrationen
│   ├── versions/            # Migration-Dateien
│   ├── env.py               # Alembic Konfiguration
│   └── script.py.mako       # Migration Template
├── app/
│   ├── api/                 # API-Routes
│   │   ├── __init__.py      # Router-Sammlung
│   │   ├── auth.py          # Authentifizierung
│   │   ├── properties.py    # Immobilien
│   │   ├── applications.py  # Bewerbungen
│   │   └── viewings.py      # Besichtigungen
│   ├── core/                # Kern-Module
│   │   ├── deps.py          # Dependencies
│   │   └── security.py      # JWT & Passwort
│   ├── models/              # SQLAlchemy Models
│   │   ├── user.py
│   │   ├── property.py
│   │   ├── application.py
│   │   ├── viewing.py
│   │   └── booking.py
│   ├── schemas/             # Pydantic Schemas
│   │   ├── user.py
│   │   ├── property.py
│   │   ├── application.py
│   │   ├── viewing.py
│   │   └── booking.py
│   ├── config.py            # Konfiguration
│   ├── database.py          # DB-Verbindung
│   └── main.py              # FastAPI App
├── .env.example             # Beispiel-Umgebungsvariablen
├── alembic.ini              # Alembic Konfiguration
├── requirements.txt         # Python-Abhängigkeiten
└── README.md               # Diese Datei
```

## Datenbank-Schema

### Users
- Vermieter-Accounts mit E-Mail/Passwort Authentifizierung

### Properties
- Immobilien mit Adresse, Preis, Größe etc.
- Gehören zu einem Vermieter (landlord_id)

### Applications
- Mietbewerbungen für Immobilien
- Status: neu, in_pruefung, akzeptiert, abgelehnt

### ViewingSlots
- Besichtigungstermine für Immobilien
- Begrenzte Teilnehmerzahl

### Bookings
- Buchungen für Besichtigungstermine

## Lizenz

Proprietär - Alle Rechte vorbehalten
