"""add_self_disclosure

Revision ID: a1b2c3d4e5f6
Revises: 9a1b2c3d4e5f
Create Date: 2026-01-27 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# Revision Identifier
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade-Migration ausführen."""
    op.create_table('self_disclosures',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),

        # Persönliche Daten
        sa.Column('geburtsname', sa.String(length=100), nullable=True),
        sa.Column('staatsangehoerigkeit', sa.String(length=100), nullable=True),
        sa.Column('familienstand', sa.String(length=50), nullable=True),

        # Arbeitgeber
        sa.Column('arbeitgeber_name', sa.String(length=200), nullable=True),
        sa.Column('arbeitgeber_adresse', sa.Text(), nullable=True),
        sa.Column('beschaeftigt_als', sa.String(length=200), nullable=True),
        sa.Column('beschaeftigt_seit', sa.Date(), nullable=True),
        sa.Column('arbeitsverhaeltnis_ungekuendigt', sa.Boolean(), nullable=True),

        # Aktueller Vermieter
        sa.Column('aktueller_vermieter_name', sa.String(length=200), nullable=True),
        sa.Column('aktueller_vermieter_adresse', sa.Text(), nullable=True),
        sa.Column('aktueller_vermieter_telefon', sa.String(length=50), nullable=True),

        # Weitere Personen im Haushalt (JSON)
        sa.Column('weitere_personen', sa.JSON(), nullable=True),

        # Finanzielle/Rechtliche Fragen
        sa.Column('mietrueckstaende', sa.Boolean(), nullable=False, server_default='false'),

        sa.Column('raeumungsklage', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('raeumungsklage_datum', sa.Date(), nullable=True),

        sa.Column('zwangsvollstreckung', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('zwangsvollstreckung_datum', sa.Date(), nullable=True),

        sa.Column('eidesstattliche_versicherung', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('eidesstattliche_versicherung_datum', sa.Date(), nullable=True),

        sa.Column('insolvenzverfahren', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('insolvenzverfahren_datum', sa.Date(), nullable=True),

        sa.Column('lohn_pfaendung', sa.Boolean(), nullable=False, server_default='false'),

        sa.Column('vorstrafen_mietverhaeltnis', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('vorstrafen_datum', sa.Date(), nullable=True),

        sa.Column('sozialleistungen', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sozialleistungen_art', sa.String(length=200), nullable=True),

        sa.Column('gewerbliche_nutzung', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('gewerbliche_nutzung_zweck', sa.String(length=200), nullable=True),

        sa.Column('tierhaltung', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tierhaltung_details', sa.String(length=200), nullable=True),

        sa.Column('kaution_buergschaft', sa.Boolean(), nullable=False, server_default='true'),

        # Einwilligungen
        sa.Column('schufa_einwilligung', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('vollstaendig_wahrheitsgemaess', sa.Boolean(), nullable=False, server_default='false'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id')
    )
    op.create_index(op.f('ix_self_disclosures_id'), 'self_disclosures', ['id'], unique=False)
    op.create_index(op.f('ix_self_disclosures_application_id'), 'self_disclosures', ['application_id'], unique=True)


def downgrade() -> None:
    """Downgrade-Migration ausführen."""
    op.drop_index(op.f('ix_self_disclosures_application_id'), table_name='self_disclosures')
    op.drop_index(op.f('ix_self_disclosures_id'), table_name='self_disclosures')
    op.drop_table('self_disclosures')
