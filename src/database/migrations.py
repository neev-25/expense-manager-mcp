"""
migrations.py — Seed data for categories/subcategories.

Run this once after init_db() to populate sensible defaults.
The function is idempotent — calling it twice won't duplicate data
because of the INSERT OR IGNORE pattern and the UNIQUE constraint.
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


def seed_categories() -> None:
    """Insert default categories and subcategories if they don't exist yet."""
    with get_connection() as conn:
        for cat in DEFAULT_CATEGORIES:
            conn.execute(
                "INSERT INTO categories(name, icon) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
                (cat["name"], cat["icon"])
            )
            row = conn.execute(
                "SELECT id FROM categories WHERE name = %s", (cat["name"],)
            ).fetchone()
            cat_id = row["id"]

            for sub in cat["subs"]:
                conn.execute(
                    "INSERT INTO subcategories(category_id, name) VALUES (%s, %s) ON CONFLICT (category_id, name) DO NOTHING",
                    (cat_id, sub)
                )
    print("[DB] Default categories seeded.")


def run_migrations() -> None:
    """Entry point — run all migrations in order."""
    seed_categories()
