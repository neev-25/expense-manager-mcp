"""
auth/user_context.py — Look up or create a user row by email.

Called once per request by the FastMCP middleware before any tool runs.
"""
from src.database.db import get_connection, set_current_user_id
from src.database.migrations import seed_categories


def get_or_create_user(email: str) -> int:
    """
    Return the user_id for the given email address.
    If no row exists yet, insert one and seed default categories for that user.
    """
    email = email.strip().lower()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE email = %s", (email,)
        ).fetchone()
        if row:
            return row["id"]

        # New user — insert and seed
        new_row = conn.execute(
            "INSERT INTO users(email) VALUES (%s) RETURNING id", (email,)
        ).fetchone()
        uid = new_row["id"]

    # Seed default categories outside the transaction above so the
    # user row is committed before the category inserts FK-reference it.
    seed_categories(uid)
    return uid


def resolve_user(email: str) -> None:
    """Resolve email → user_id and store it in the per-request ContextVar."""
    uid = get_or_create_user(email)
    set_current_user_id(uid)
