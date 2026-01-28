"""Add income fields to self_disclosure

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-27 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add miete_zahlbar column
    op.add_column(
        'self_disclosures',
        sa.Column('miete_zahlbar', sa.Boolean(), nullable=False, server_default='false')
    )
    # Add nettoeinkommen column
    op.add_column(
        'self_disclosures',
        sa.Column('nettoeinkommen', sa.String(100), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('self_disclosures', 'nettoeinkommen')
    op.drop_column('self_disclosures', 'miete_zahlbar')
