# db.py — PostgreSQL persistence layer (psycopg2)
#
# All DB calls are wrapped in try/except so the game runs
# gracefully even when no database is configured.

import datetime

try:
    import psycopg2
    import psycopg2.extras
    _PSYCOPG2_AVAILABLE = True
except ImportError:
    _PSYCOPG2_AVAILABLE = False

# ── Connection settings ───────────────────────────────────────────────────────
# Change these to match your PostgreSQL installation.
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "snake",
    "user":     "postgres",
    "password": "AliLoh123",
}

_conn = None   # module-level cached connection


def _get_conn():
    global _conn
    if not _PSYCOPG2_AVAILABLE:
        return None
    try:
        if _conn is None or _conn.closed:
            _conn = psycopg2.connect(**DB_CONFIG)
        return _conn
    except Exception as e:
        print(f"[DB] Connection failed: {e}")
        return None


def init_db():
    """Create tables if they don't exist yet."""
    conn = _get_conn()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id       SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id            SERIAL PRIMARY KEY,
                    player_id     INTEGER REFERENCES players(id),
                    score         INTEGER   NOT NULL,
                    level_reached INTEGER   NOT NULL,
                    played_at     TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB] init_db error: {e}")
        conn.rollback()
        return False


def get_or_create_player(username: str) -> int | None:
    """Return the player's id, inserting a new row if needed."""
    conn = _get_conn()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO players (username) VALUES (%s) "
                "ON CONFLICT (username) DO UPDATE SET username=EXCLUDED.username "
                "RETURNING id",
                (username,)
            )
            row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
    except Exception as e:
        print(f"[DB] get_or_create_player error: {e}")
        conn.rollback()
        return None


def save_session(player_id: int, score: int, level: int):
    """Persist one game result."""
    conn = _get_conn()
    if conn is None or player_id is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO game_sessions (player_id, score, level_reached) "
                "VALUES (%s, %s, %s)",
                (player_id, score, level)
            )
        conn.commit()
    except Exception as e:
        print(f"[DB] save_session error: {e}")
        conn.rollback()


def get_top10() -> list[dict]:
    """Return top-10 all-time scores."""
    conn = _get_conn()
    if conn is None:
        return []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT p.username, gs.score, gs.level_reached,
                       gs.played_at::date AS played_date
                FROM   game_sessions gs
                JOIN   players p ON p.id = gs.player_id
                ORDER  BY gs.score DESC
                LIMIT  10
            """)
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        print(f"[DB] get_top10 error: {e}")
        return []


def get_personal_best(player_id: int) -> int:
    """Return the highest score ever achieved by this player."""
    conn = _get_conn()
    if conn is None or player_id is None:
        return 0
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(score), 0) FROM game_sessions "
                "WHERE player_id = %s",
                (player_id,)
            )
            row = cur.fetchone()
        return row[0] if row else 0
    except Exception as e:
        print(f"[DB] get_personal_best error: {e}")
        return 0
