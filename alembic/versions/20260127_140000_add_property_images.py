"""add_property_images

Revision ID: 9a1b2c3d4e5f
Revises: 78cfefc28123
Create Date: 2026-01-27 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# Revision Identifier
revision: str = '9a1b2c3d4e5f'
down_revision: Union[str, None] = '78cfefc28123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade-Migration ausführen."""
    op.create_table('property_images',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('property_id', sa.UUID(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('filepath', sa.String(length=500), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_property_images_id'), 'property_images', ['id'], unique=False)
    op.create_index(op.f('ix_property_images_property_id'), 'property_images', ['property_id'], unique=False)


def downgrade() -> None:
    """Downgrade-Migration ausführen."""
    op.drop_index(op.f('ix_property_images_property_id'), table_name='property_images')
    op.drop_index(op.f('ix_property_images_id'), table_name='property_images')
    op.drop_table('property_images')
