"""Fix database: Add missing columns and tables for Bewerber-Portal."""
from app.database import engine
from sqlalchemy import text

print(f"Connecting to: {engine.url}")

with engine.connect() as conn:
    # 1. Check/add access_token column
    print("\n1. Checking access_token column...")
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'applications' AND column_name = 'access_token'
    """))
    if result.fetchone():
        print("   Column 'access_token' already exists!")
    else:
        print("   Adding 'access_token' column...")
        conn.execute(text('ALTER TABLE applications ADD COLUMN access_token VARCHAR(255)'))
        conn.commit()
        print("   Column added!")

    # 2. Check/create access_token index
    print("\n2. Checking access_token index...")
    result = conn.execute(text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'applications' AND indexname = 'ix_applications_access_token'
    """))
    if result.fetchone():
        print("   Index already exists!")
    else:
        print("   Creating index...")
        conn.execute(text('CREATE UNIQUE INDEX ix_applications_access_token ON applications(access_token)'))
        conn.commit()
        print("   Index created!")

    # 3. Check/create application_documents table
    print("\n3. Checking application_documents table...")
    result = conn.execute(text("""
        SELECT table_name FROM information_schema.tables
        WHERE table_name = 'application_documents'
    """))
    if result.fetchone():
        print("   Table 'application_documents' already exists!")
    else:
        print("   Creating 'application_documents' table...")
        conn.execute(text('''
            CREATE TABLE application_documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
                filename VARCHAR(255) NOT NULL,
                display_name VARCHAR(255),
                category VARCHAR(50) NOT NULL,
                filepath VARCHAR(500) NOT NULL,
                file_size INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        '''))
        conn.commit()
        print("   Table created!")

    # 4. Check/create indexes on application_documents
    print("\n4. Checking application_documents indexes...")
    result = conn.execute(text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'application_documents' AND indexname = 'ix_application_documents_application_id'
    """))
    if result.fetchone():
        print("   Index already exists!")
    else:
        print("   Creating index...")
        conn.execute(text('CREATE INDEX ix_application_documents_application_id ON application_documents(application_id)'))
        conn.commit()
        print("   Index created!")

print("\n✓ Done! Restart the server now.")
