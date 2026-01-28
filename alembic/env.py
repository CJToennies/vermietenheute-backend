"""
Alembic Migration Environment.
Konfiguriert Alembic für Datenbank-Migrationen.
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Projekt-Root zum Pfad hinzufügen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Umgebungsvariablen laden
from dotenv import load_dotenv
load_dotenv()

# Alembic Config Objekt
config = context.config

# Datenbank-URL aus Umgebungsvariable setzen
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", ""))

# Logging konfigurieren
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Models importieren für Autogenerate
from app.database import Base
from app.models import User, Property, Application, ViewingSlot, Booking

# Target Metadata für Autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Führt Migrationen im 'offline' Modus aus.
    Generiert SQL-Statements ohne Datenbankverbindung.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Führt Migrationen im 'online' Modus aus.
    Verbindet sich mit der Datenbank und wendet Änderungen an.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


# Migration-Modus bestimmen
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
