"""
Extend Viewing Management - slot_type, access_type, invitations, reminders

Revision ID: 20260131_150000
Revises: j0k1l2m3n4o5
Create Date: 2026-01-31

Features:
- viewing_slots: slot_type, access_type
- viewing_invitations: new table for invited applicants
- bookings: application_id, invitation_id, reminder flags
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '20260131_150000'
down_revision = 'j0k1l2m3n4o5'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = '{table_name}' AND column_name = '{column_name}'
    """))
    return result.fetchone() is not None


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"""
        SELECT table_name FROM information_schema.tables
        WHERE table_name = '{table_name}'
    """))
    return result.fetchone() is not None


def upgrade() -> None:
    # ========================================
    # 1. Extend viewing_slots table
    # ========================================

    # Add slot_type column (individual or group)
    if not column_exists('viewing_slots', 'slot_type'):
        op.add_column('viewing_slots', sa.Column(
            'slot_type',
            sa.String(20),
            nullable=False,
            server_default='individual'
        ))

    # Add access_type column (public or invited)
    if not column_exists('viewing_slots', 'access_type'):
        op.add_column('viewing_slots', sa.Column(
            'access_type',
            sa.String(20),
            nullable=False,
            server_default='public'
        ))

    # Add notes column for landlord notes on the slot
    if not column_exists('viewing_slots', 'notes'):
        op.add_column('viewing_slots', sa.Column(
            'notes',
            sa.Text,
            nullable=True
        ))

    # ========================================
    # 2. Create viewing_invitations table
    # ========================================

    if not table_exists('viewing_invitations'):
        op.create_table(
            'viewing_invitations',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('slot_id', UUID(as_uuid=True), sa.ForeignKey('viewing_slots.id', ondelete='CASCADE'), nullable=False),
            sa.Column('application_id', UUID(as_uuid=True), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=False),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('invited_at', sa.DateTime, nullable=False),
            sa.Column('responded_at', sa.DateTime, nullable=True),
            sa.Column('invitation_token', sa.String(64), nullable=False, unique=True),
            sa.Column('created_at', sa.DateTime, nullable=False),
            sa.Column('updated_at', sa.DateTime, nullable=False),
        )

        # Create indexes
        op.create_index('ix_viewing_invitations_slot_id', 'viewing_invitations', ['slot_id'])
        op.create_index('ix_viewing_invitations_application_id', 'viewing_invitations', ['application_id'])
        op.create_index('ix_viewing_invitations_invitation_token', 'viewing_invitations', ['invitation_token'])

    # ========================================
    # 3. Extend bookings table
    # ========================================

    # Add application_id (link to application if booked by applicant)
    if not column_exists('bookings', 'application_id'):
        op.add_column('bookings', sa.Column(
            'application_id',
            UUID(as_uuid=True),
            sa.ForeignKey('applications.id', ondelete='SET NULL'),
            nullable=True
        ))
        op.create_index('ix_bookings_application_id', 'bookings', ['application_id'])

    # Add invitation_id (link to invitation if booked via invitation)
    if not column_exists('bookings', 'invitation_id'):
        op.add_column('bookings', sa.Column(
            'invitation_id',
            UUID(as_uuid=True),
            sa.ForeignKey('viewing_invitations.id', ondelete='SET NULL'),
            nullable=True
        ))

    # Add reminder flags
    if not column_exists('bookings', 'reminder_24h_sent'):
        op.add_column('bookings', sa.Column(
            'reminder_24h_sent',
            sa.Boolean,
            nullable=False,
            server_default='false'
        ))

    if not column_exists('bookings', 'reminder_1h_sent'):
        op.add_column('bookings', sa.Column(
            'reminder_1h_sent',
            sa.Boolean,
            nullable=False,
            server_default='false'
        ))

    # Add cancellation timestamp (for tracking when cancelled)
    if not column_exists('bookings', 'cancelled_at'):
        op.add_column('bookings', sa.Column(
            'cancelled_at',
            sa.DateTime,
            nullable=True
        ))


def downgrade() -> None:
    # Remove bookings columns
    if column_exists('bookings', 'cancelled_at'):
        op.drop_column('bookings', 'cancelled_at')
    if column_exists('bookings', 'reminder_1h_sent'):
        op.drop_column('bookings', 'reminder_1h_sent')
    if column_exists('bookings', 'reminder_24h_sent'):
        op.drop_column('bookings', 'reminder_24h_sent')
    if column_exists('bookings', 'invitation_id'):
        op.drop_column('bookings', 'invitation_id')
    if column_exists('bookings', 'application_id'):
        op.drop_index('ix_bookings_application_id', 'bookings')
        op.drop_column('bookings', 'application_id')

    # Drop viewing_invitations table
    if table_exists('viewing_invitations'):
        op.drop_index('ix_viewing_invitations_invitation_token', 'viewing_invitations')
        op.drop_index('ix_viewing_invitations_application_id', 'viewing_invitations')
        op.drop_index('ix_viewing_invitations_slot_id', 'viewing_invitations')
        op.drop_table('viewing_invitations')

    # Remove viewing_slots columns
    if column_exists('viewing_slots', 'notes'):
        op.drop_column('viewing_slots', 'notes')
    if column_exists('viewing_slots', 'access_type'):
        op.drop_column('viewing_slots', 'access_type')
    if column_exists('viewing_slots', 'slot_type'):
        op.drop_column('viewing_slots', 'slot_type')
