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
    """Create the contacts table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
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
    conn.commit()
    cursor.close()
    conn.close()
    print("[OK] Table 'contacts' is ready.")
