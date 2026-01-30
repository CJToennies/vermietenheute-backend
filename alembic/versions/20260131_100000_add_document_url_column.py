"""Add url column to application_documents for Supabase Storage

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-01-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, None] = 'f6g7h8i9j0k1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add url column to application_documents table."""
    conn = op.get_bind()

    # Check if column already exists
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'application_documents' AND column_name = 'url'
    """))

    if not result.fetchone():
        op.add_column(
            'application_documents',
            sa.Column('url', sa.String(1000), nullable=True)
        )


def downgrade() -> None:
    """Remove url column from application_documents table."""
    op.drop_column('application_documents', 'url')
