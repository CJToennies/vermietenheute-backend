"""
Add Monetization - Feature flags, Stripe preparation, Upgrade events

Revision ID: 20260131_160000
Revises: 20260131_150000
Create Date: 2026-01-31

Features:
- users: feature_multi_property, feature_unlimited_applications, feature_frequent_listings
- users: stripe_customer_id, subscription_status, subscription_plan, subscription_ends_at
- upgrade_events: new table for tracking upgrade interest
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '20260131_160000'
down_revision = '20260131_150000'
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


def index_exists(index_name: str) -> bool:
    """Check if an index exists."""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"""
        SELECT indexname FROM pg_indexes
        WHERE indexname = '{index_name}'
    """))
    return result.fetchone() is not None


def upgrade():
    # ============================================
    # User Feature-Flags
    # ============================================
    if not column_exists('users', 'feature_multi_property'):
        op.add_column('users', sa.Column(
            'feature_multi_property',
            sa.Boolean(),
            server_default='false',
            nullable=False
        ))

    if not column_exists('users', 'feature_unlimited_applications'):
        op.add_column('users', sa.Column(
            'feature_unlimited_applications',
            sa.Boolean(),
            server_default='false',
            nullable=False
        ))

    if not column_exists('users', 'feature_frequent_listings'):
        op.add_column('users', sa.Column(
            'feature_frequent_listings',
            sa.Boolean(),
            server_default='false',
            nullable=False
        ))

    # ============================================
    # Stripe-Vorbereitung
    # ============================================
    if not column_exists('users', 'stripe_customer_id'):
        op.add_column('users', sa.Column(
            'stripe_customer_id',
            sa.String(255),
            nullable=True
        ))
        if not index_exists('ix_users_stripe_customer_id'):
            op.create_index(
                'ix_users_stripe_customer_id',
                'users',
                ['stripe_customer_id']
            )

    if not column_exists('users', 'subscription_status'):
        op.add_column('users', sa.Column(
            'subscription_status',
            sa.String(50),
            server_default='free',
            nullable=False
        ))

    if not column_exists('users', 'subscription_plan'):
        op.add_column('users', sa.Column(
            'subscription_plan',
            sa.String(50),
            nullable=True
        ))

    if not column_exists('users', 'subscription_ends_at'):
        op.add_column('users', sa.Column(
            'subscription_ends_at',
            sa.DateTime(),
            nullable=True
        ))

    # ============================================
    # Upgrade Events Tabelle
    # ============================================
    if not table_exists('upgrade_events'):
        op.create_table(
            'upgrade_events',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('feature', sa.String(50), nullable=False),
            sa.Column('trigger_context', sa.String(100), nullable=True),
            sa.Column('is_beta', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('would_pay_amount', sa.Integer(), nullable=True),
            sa.Column('shown_at', sa.DateTime(), nullable=True),
            sa.Column('unlocked_at', sa.DateTime(), nullable=True),
            sa.Column('time_to_decision_seconds', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_upgrade_events_user_id', 'upgrade_events', ['user_id'])
        op.create_index('ix_upgrade_events_feature', 'upgrade_events', ['feature'])


def downgrade():
    # Upgrade Events
    if table_exists('upgrade_events'):
        op.drop_table('upgrade_events')

    # Stripe-Vorbereitung
    if column_exists('users', 'subscription_ends_at'):
        op.drop_column('users', 'subscription_ends_at')

    if column_exists('users', 'subscription_plan'):
        op.drop_column('users', 'subscription_plan')

    if column_exists('users', 'subscription_status'):
        op.drop_column('users', 'subscription_status')

    if index_exists('ix_users_stripe_customer_id'):
        op.drop_index('ix_users_stripe_customer_id', 'users')

    if column_exists('users', 'stripe_customer_id'):
        op.drop_column('users', 'stripe_customer_id')

    # Feature-Flags
    if column_exists('users', 'feature_frequent_listings'):
        op.drop_column('users', 'feature_frequent_listings')

    if column_exists('users', 'feature_unlimited_applications'):
        op.drop_column('users', 'feature_unlimited_applications')

    if column_exists('users', 'feature_multi_property'):
        op.drop_column('users', 'feature_multi_property')
