"""Change properties.landlord_id to nullable with SET NULL

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-01-31 13:00:00.000000

This migration changes the foreign key constraint on properties.landlord_id
from CASCADE to SET NULL, allowing properties to become "orphaned" when
a landlord deletes their account. This is necessary for DSGVO compliance:
applicant data (applications, documents) should not be immediately deleted
when a landlord deletes their account.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i9j0k1l2m3n4'
down_revision: Union[str, None] = 'h8i9j0k1l2m3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    1. Make landlord_id nullable
    2. Drop existing CASCADE foreign key
    3. Create new SET NULL foreign key
    """
    conn = op.get_bind()

    # Step 1: Make column nullable (if not already)
    # PostgreSQL: ALTER COLUMN ... DROP NOT NULL
    conn.execute(sa.text("""
        ALTER TABLE properties
        ALTER COLUMN landlord_id DROP NOT NULL
    """))

    # Step 2: Find and drop the existing foreign key constraint
    # First, get the constraint name
    result = conn.execute(sa.text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'properties'
        AND constraint_type = 'FOREIGN KEY'
        AND constraint_name LIKE '%landlord_id%'
    """))
    row = result.fetchone()

    if row:
        constraint_name = row[0]
        conn.execute(sa.text(f"""
            ALTER TABLE properties
            DROP CONSTRAINT "{constraint_name}"
        """))

    # If no constraint found by name pattern, try the default naming
    else:
        result = conn.execute(sa.text("""
            SELECT tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'properties'
            AND tc.constraint_type = 'FOREIGN KEY'
            AND kcu.column_name = 'landlord_id'
        """))
        row = result.fetchone()
        if row:
            constraint_name = row[0]
            conn.execute(sa.text(f"""
                ALTER TABLE properties
                DROP CONSTRAINT "{constraint_name}"
            """))

    # Step 3: Create new foreign key with SET NULL
    conn.execute(sa.text("""
        ALTER TABLE properties
        ADD CONSTRAINT fk_properties_landlord_id
        FOREIGN KEY (landlord_id)
        REFERENCES users(id)
        ON DELETE SET NULL
    """))


def downgrade() -> None:
    """
    Revert to CASCADE delete (WARNING: will fail if orphaned properties exist!)
    """
    conn = op.get_bind()

    # First, delete any orphaned properties (landlord_id IS NULL)
    conn.execute(sa.text("""
        DELETE FROM properties WHERE landlord_id IS NULL
    """))

    # Drop the SET NULL constraint
    conn.execute(sa.text("""
        ALTER TABLE properties
        DROP CONSTRAINT IF EXISTS fk_properties_landlord_id
    """))

    # Make column NOT NULL again
    conn.execute(sa.text("""
        ALTER TABLE properties
        ALTER COLUMN landlord_id SET NOT NULL
    """))

    # Recreate with CASCADE
    conn.execute(sa.text("""
        ALTER TABLE properties
        ADD CONSTRAINT fk_properties_landlord_id
        FOREIGN KEY (landlord_id)
        REFERENCES users(id)
        ON DELETE CASCADE
    """))
