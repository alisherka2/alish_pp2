import psycopg2
from config import DB_CONFIG


def get_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Could not connect to database: {e}")
        raise


def create_table():
    """Apply the extended schema (idempotent)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Base contacts table (Practice 7 compatible)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id          SERIAL PRIMARY KEY,
            username    VARCHAR(50)  UNIQUE NOT NULL,
            first_name  VARCHAR(50),
            last_name   VARCHAR(50),
            phone       VARCHAR(20)  NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Groups
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id   SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL
        );
    """)
    cursor.execute("""
        INSERT INTO groups (name) VALUES ('Family'),('Work'),('Friend'),('Other')
        ON CONFLICT DO NOTHING;
    """)

    # New columns on contacts (safe)
    for col, definition in [
        ("email",    "VARCHAR(100)"),
        ("birthday", "DATE"),
        ("group_id", "INTEGER REFERENCES groups(id)"),
    ]:
        cursor.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='contacts' AND column_name='{col}'
                ) THEN
                    ALTER TABLE contacts ADD COLUMN {col} {definition};
                END IF;
            END;
            $$;
        """)

    # Phones table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phones (
            id         SERIAL PRIMARY KEY,
            contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
            phone      VARCHAR(20) NOT NULL,
            type       VARCHAR(10) CHECK (type IN ('home','work','mobile'))
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("[OK] Schema is ready.")
