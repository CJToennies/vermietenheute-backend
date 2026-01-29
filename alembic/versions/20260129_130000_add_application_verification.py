"""Add application email verification fields

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-01-29 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email verification fields to applications table
    op.add_column(
        'applications',
        sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'applications',
        sa.Column('email_verification_token', sa.String(255), nullable=True)
    )
    op.add_column(
        'applications',
        sa.Column('email_verification_expires', sa.DateTime(), nullable=True)
    )

    # Create index on email_verification_token for faster lookups
    op.create_index(
        'ix_applications_email_verification_token',
        'applications',
        ['email_verification_token']
    )


def downgrade() -> None:
    op.drop_index('ix_applications_email_verification_token', table_name='applications')
    op.drop_column('applications', 'email_verification_expires')
    op.drop_column('applications', 'email_verification_token')
    op.drop_column('applications', 'is_email_verified')
