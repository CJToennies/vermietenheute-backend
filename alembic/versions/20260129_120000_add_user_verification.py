"""Add user verification fields

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-01-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification fields to users table
    op.add_column(
        'users',
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'users',
        sa.Column('verification_token', sa.String(255), nullable=True)
    )
    op.add_column(
        'users',
        sa.Column('verification_token_expires', sa.DateTime(), nullable=True)
    )

    # Create index on verification_token for faster lookups
    op.create_index(
        'ix_users_verification_token',
        'users',
        ['verification_token']
    )


def downgrade() -> None:
    op.drop_index('ix_users_verification_token', table_name='users')
    op.drop_column('users', 'verification_token_expires')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'is_verified')
