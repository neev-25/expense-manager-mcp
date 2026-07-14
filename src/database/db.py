"""
db.py — Database connection and initialisation helpers.

Key patterns used here:
  - `sqlite3.Row` as row_factory so query results behave like dicts
    (access columns by name: row["amount"] instead of row[1]).
  - PRAGMA foreign_keys = ON so our REFERENCES constraints are enforced.
  - A single `init_db()` function creates all tables on server start.
"""
import sqlite3
from contextlib import contextmanager

from src.config import DB_PATH
from src.database.models import ALL_TABLES


@contextmanager
def get_connection():
    """
    Context-manager that yields an open SQLite connection.

    Usage:
        with get_connection() as conn:
            conn.execute("SELECT ...")

    Automatically commits on success and rolls back on any exception.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # rows are dict-like
    conn.execute("PRAGMA foreign_keys = ON")  # enforce FK constraints
    conn.execute("PRAGMA journal_mode = WAL")  # better concurrency
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Create all tables (idempotent — safe to call on every server start).
    Tables are created in the order defined in models.ALL_TABLES so that
    foreign-key dependencies are always satisfied.
    """
    with get_connection() as conn:
        for stmt in ALL_TABLES:
            conn.execute(stmt)
    print(f"[DB] Database ready at: {DB_PATH}")
