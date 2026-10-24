"""
migrations.py — Seed data for categories/subcategories.

Seed is now per-user: each new user gets their own copy of the default
categories / subcategories. Calling it twice for the same user is safe
because of ON CONFLICT DO NOTHING.
"""
from src.database.db import get_connection

# Default categories with icons and their subcategories
DEFAULT_CATEGORIES: list[dict] = [
    {
        "name": "Food", "icon": "🍔",
        "subs": ["Restaurant", "Fast Food", "Cafe", "Snacks", "Groceries", "Sweets"]
    },
    {
        "name": "Travel", "icon": "✈️",
        "subs": ["Bus", "Metro", "Cab", "Train", "Flight", "Fuel", "Parking", "Toll"]
    },
    {
        "name": "Entertainment", "icon": "🎬",
        "subs": ["Movies", "OTT", "Gaming", "Events", "Sports"]
    },
    {
        "name": "Shopping", "icon": "🛍️",
        "subs": ["Clothes", "Electronics", "Books", "Shoes", "Online"]
    },
    {
        "name": "Health", "icon": "🏥",
        "subs": ["Medicine", "Doctor", "Lab Tests", "Gym", "Pharmacy"]
    },
    {
        "name": "Bills & Utilities", "icon": "📄",
        "subs": ["Electricity", "Water", "Internet", "Mobile", "Gas", "Rent"]
    },
    {
        "name": "Education", "icon": "📚",
        "subs": ["Tuition", "Books", "Courses", "Stationery"]
    },
    {
        "name": "Subscriptions", "icon": "🔄",
        "subs": ["Netflix", "Spotify", "YouTube Premium", "Amazon Prime", "Other"]
    },
    {
        "name": "Personal Care", "icon": "💅",
        "subs": ["Haircut", "Salon", "Cosmetics"]
    },
    {
        "name": "Miscellaneous", "icon": "📦",
        "subs": ["Gifts", "Donations", "Other"]
    },
]


def seed_categories(user_id: int) -> None:
    """Insert default categories and subcategories for a user if they don't exist yet."""
    with get_connection() as conn:
        for cat in DEFAULT_CATEGORIES:
            # Check if this category already exists for this user
            existing = conn.execute(
                "SELECT id FROM categories WHERE user_id = %s AND name = %s",
                (user_id, cat["name"])
            ).fetchone()
            if existing:
                cat_id = existing["id"]
            else:
                row = conn.execute(
                    "INSERT INTO categories(user_id, name, icon) VALUES (%s, %s, %s) RETURNING id",
                    (user_id, cat["name"], cat["icon"])
                ).fetchone()
                cat_id = row["id"]

            for sub in cat["subs"]:
                sub_exists = conn.execute(
                    "SELECT id FROM subcategories WHERE user_id=%s AND category_id=%s AND name=%s",
                    (user_id, cat_id, sub)
                ).fetchone()
                if not sub_exists:
                    conn.execute(
                        "INSERT INTO subcategories(user_id, category_id, name) VALUES (%s, %s, %s)",
                        (user_id, cat_id, sub)
                    )
    print(f"[DB] Default categories seeded for user_id={user_id}.")


def run_migrations() -> None:
    """Entry point — run all structural migrations in order."""
    # Per-user seeding now happens in auth/user_context.py when a new user logs in.
    # Nothing global to seed here anymore.
    print("[DB] Migrations complete.")
