"""Add Bewerber-Portal: access_token and application_documents table

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-01-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f6g7h8i9j0k1'
down_revision: Union[str, None] = 'e5f6g7h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Add access_token column to applications (IF NOT EXISTS)
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'applications' AND column_name = 'access_token'
    """))
    if not result.fetchone():
        op.add_column('applications', sa.Column('access_token', sa.String(255), nullable=True))

    # 2. Create unique index on access_token (IF NOT EXISTS)
    result = conn.execute(sa.text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'applications' AND indexname = 'ix_applications_access_token'
    """))
    if not result.fetchone():
        op.create_index('ix_applications_access_token', 'applications', ['access_token'], unique=True)

    # 3. Create application_documents table (IF NOT EXISTS)
    result = conn.execute(sa.text("""
        SELECT table_name FROM information_schema.tables
        WHERE table_name = 'application_documents'
    """))
    if not result.fetchone():
        op.create_table(
            'application_documents',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=False),
            sa.Column('filename', sa.String(255), nullable=False),
            sa.Column('display_name', sa.String(255), nullable=True),
            sa.Column('category', sa.String(50), nullable=False),
            sa.Column('filepath', sa.String(500), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        )

    # 4. Create index on application_id (IF NOT EXISTS)
    result = conn.execute(sa.text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'application_documents' AND indexname = 'ix_application_documents_application_id'
    """))
    if not result.fetchone():
        op.create_index('ix_application_documents_application_id', 'application_documents', ['application_id'])


def downgrade() -> None:
    # Drop in reverse order
    conn = op.get_bind()

    # Check and drop index
    result = conn.execute(sa.text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'application_documents' AND indexname = 'ix_application_documents_application_id'
    """))
    if result.fetchone():
        op.drop_index('ix_application_documents_application_id', table_name='application_documents')

    # Check and drop table
    result = conn.execute(sa.text("""
        SELECT table_name FROM information_schema.tables
        WHERE table_name = 'application_documents'
    """))
    if result.fetchone():
        op.drop_table('application_documents')

    # Check and drop access_token index
    result = conn.execute(sa.text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'applications' AND indexname = 'ix_applications_access_token'
    """))
    if result.fetchone():
        op.drop_index('ix_applications_access_token', table_name='applications')

    # Check and drop access_token column
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'applications' AND column_name = 'access_token'
    """))
    if result.fetchone():
        op.drop_column('applications', 'access_token')
