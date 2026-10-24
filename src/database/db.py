"""
db.py — Database connection and initialisation helpers.

Key patterns used here:
  - psycopg2.extras.RealDictCursor so query results behave like dicts.
  - A single `init_db()` function creates all tables on server start.
  - A ContextVar stores the current user_id per request (set by auth middleware).
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from contextvars import ContextVar

from src.config import NEON_DATABASE_URL
from src.database.models import ALL_TABLES

# Per-request context variable holding the resolved user_id.
# Set by the auth middleware before any tool executes.
_current_user_id: ContextVar[int | None] = ContextVar("_current_user_id", default=None)


def get_current_user_id() -> int:
    """Return the user_id for the current MCP request. Raises if not set."""
    uid = _current_user_id.get()
    if uid is None:
        raise ValueError(
            "No authenticated user found. "
            "Please add the header X-User-Email: your@email.com to your connector settings."
        )
    return uid


def set_current_user_id(uid: int) -> None:
    """Called by auth middleware to bind a user_id to the current async context."""
    _current_user_id.set(uid)


class PostgresConnWrapper:
    def __init__(self, c):
        self.conn = c

    def execute(self, query, params=None):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur
        
    def commit(self):
        self.conn.commit()
    
    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def cursor(self):
        return self.conn.cursor()

@contextmanager
def get_connection():
    """
    Context-manager that yields an open Postgres connection wrapper.
    Automatically commits on success and rolls back on any exception.
    """
    if not NEON_DATABASE_URL:
        raise ValueError("NEON_DATABASE_URL environment variable is not set.")
    
    conn = psycopg2.connect(NEON_DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield PostgresConnWrapper(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Create all tables (idempotent — safe to call on every server start).
    Tables are created in the order defined in models.ALL_TABLES.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            for stmt in ALL_TABLES:
                cur.execute(stmt)
    print(f"[DB] Connected to Neon Postgres database")
