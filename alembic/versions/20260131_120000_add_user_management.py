"""Add user management: password reset and email change columns

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-01-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h8i9j0k1l2m3'
down_revision: Union[str, None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Add password_reset_token column (IF NOT EXISTS)
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'password_reset_token'
    """))
    if not result.fetchone():
        op.add_column('users', sa.Column('password_reset_token', sa.String(255), nullable=True))

    # 2. Add password_reset_token_expires column (IF NOT EXISTS)
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'password_reset_token_expires'
    """))
    if not result.fetchone():
        op.add_column('users', sa.Column('password_reset_token_expires', sa.DateTime(), nullable=True))

    # 3. Add pending_email column (IF NOT EXISTS)
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'pending_email'
    """))
    if not result.fetchone():
        op.add_column('users', sa.Column('pending_email', sa.String(255), nullable=True))

    # 4. Add email_change_token column (IF NOT EXISTS)
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'email_change_token'
    """))
    if not result.fetchone():
        op.add_column('users', sa.Column('email_change_token', sa.String(255), nullable=True))

    # 5. Add email_change_token_expires column (IF NOT EXISTS)
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'email_change_token_expires'
    """))
    if not result.fetchone():
        op.add_column('users', sa.Column('email_change_token_expires', sa.DateTime(), nullable=True))

    # 6. Create index on password_reset_token (IF NOT EXISTS)
    result = conn.execute(sa.text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'users' AND indexname = 'ix_users_password_reset_token'
    """))
    if not result.fetchone():
        op.create_index('ix_users_password_reset_token', 'users', ['password_reset_token'])

    # 7. Create index on email_change_token (IF NOT EXISTS)
    result = conn.execute(sa.text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'users' AND indexname = 'ix_users_email_change_token'
    """))
    if not result.fetchone():
        op.create_index('ix_users_email_change_token', 'users', ['email_change_token'])


def downgrade() -> None:
    conn = op.get_bind()

    # Drop indexes first
    result = conn.execute(sa.text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'users' AND indexname = 'ix_users_email_change_token'
    """))
    if result.fetchone():
        op.drop_index('ix_users_email_change_token', table_name='users')

    result = conn.execute(sa.text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'users' AND indexname = 'ix_users_password_reset_token'
    """))
    if result.fetchone():
        op.drop_index('ix_users_password_reset_token', table_name='users')

    # Drop columns
    columns = [
        'email_change_token_expires',
        'email_change_token',
        'pending_email',
        'password_reset_token_expires',
        'password_reset_token',
    ]

    for column in columns:
        result = conn.execute(sa.text(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = '{column}'
        """))
        if result.fetchone():
            op.drop_column('users', column)
