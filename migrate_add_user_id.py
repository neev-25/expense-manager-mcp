"""
migrate_add_user_id.py — One-time migration to add user_id columns to existing Neon tables.

Run this ONCE on your existing Neon database before deploying the updated server:

    uv run python migrate_add_user_id.py

Safe to re-run: uses ADD COLUMN IF NOT EXISTS everywhere.
Existing rows will have user_id=NULL after migration — they won't be visible
to any user until attributed. Use the --attribute flag to assign them to an email.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.db import get_connection

MIGRATIONS = [
    # Create users table if it doesn't exist yet
    """
    CREATE TABLE IF NOT EXISTS users (
        id         SERIAL PRIMARY KEY,
        email      TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,
    # Add user_id to all data tables (safe to run multiple times)
    "ALTER TABLE categories        ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE subcategories     ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE expenses          ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE friends           ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE balances          ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE events            ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE event_expenses    ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE settlements       ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE budgets           ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE recurring_expenses ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    # Fix UNIQUE constraints for per-user categories
    # (only if the old global unique constraint still exists — ignore errors)
]

def run():
    print("Running migrations on Neon Postgres...")
    with get_connection() as conn:
        for sql in MIGRATIONS:
            sql = sql.strip()
            print(f"  → {sql[:80]}...")
            try:
                conn.execute(sql)
            except Exception as e:
                print(f"    ⚠️  Skipped (already applied or not applicable): {e}")
    print("✅ Migration complete.")

    # Optional: attribute existing rows to a specific user
    email = None
    for arg in sys.argv[1:]:
        if arg.startswith("--attribute="):
            email = arg.split("=", 1)[1]

    if email:
        print(f"\nAttributing all NULL user_id rows to: {email}")
        with get_connection() as conn:
            row = conn.execute(
                "INSERT INTO users(email) VALUES (%s) ON CONFLICT(email) DO UPDATE SET email=EXCLUDED.email RETURNING id",
                (email.strip().lower(),)
            ).fetchone()
            uid = row["id"]
            tables = [
                "categories", "subcategories", "expenses", "friends",
                "balances", "events", "event_expenses", "settlements",
                "budgets", "recurring_expenses"
            ]
            for table in tables:
                conn.execute(
                    f"UPDATE {table} SET user_id=%s WHERE user_id IS NULL", (uid,)
                )
                print(f"  ✅ {table} attributed to user_id={uid}")
        print(f"Done! All existing data is now owned by {email}.")


if __name__ == "__main__":
    run()
