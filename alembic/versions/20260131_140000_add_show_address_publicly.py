"""Add show_address_publicly to properties.

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-01-31 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j0k1l2m3n4o5'
down_revision: Union[str, None] = 'i9j0k1l2m3n4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Prüfen ob Spalte bereits existiert
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('properties')]

    if 'show_address_publicly' not in columns:
        op.add_column(
            'properties',
            sa.Column('show_address_publicly', sa.Boolean(), nullable=False, server_default='true')
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('properties')]

    if 'show_address_publicly' in columns:
        op.drop_column('properties', 'show_address_publicly')
