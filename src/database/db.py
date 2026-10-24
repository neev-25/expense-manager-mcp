"""
db.py — Database connection and initialisation helpers.

Key patterns used here:
  - psycopg2.extras.RealDictCursor so query results behave like dicts.
  - A single `init_db()` function creates all tables on server start.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from src.config import NEON_DATABASE_URL
from src.database.models import ALL_TABLES


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
