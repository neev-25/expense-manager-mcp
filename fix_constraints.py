"""fix_constraints.py — Drop old global UNIQUE constraints and add per-user ones."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.database.db import get_connection

steps = [
    # categories: drop old UNIQUE(name), add UNIQUE(user_id, name)
    "ALTER TABLE categories DROP CONSTRAINT IF EXISTS categories_name_key",
    "ALTER TABLE categories ADD CONSTRAINT IF NOT EXISTS categories_user_id_name_key UNIQUE (user_id, name)",
    # subcategories: drop old UNIQUE(category_id, name), add UNIQUE(user_id, category_id, name)
    "ALTER TABLE subcategories DROP CONSTRAINT IF EXISTS subcategories_category_id_name_key",
    "ALTER TABLE subcategories ADD CONSTRAINT IF NOT EXISTS subcategories_user_cat_name_key UNIQUE (user_id, category_id, name)",
    # budgets: drop old UNIQUE(category_id, month, year), add UNIQUE(user_id, category_id, month, year)
    "ALTER TABLE budgets DROP CONSTRAINT IF EXISTS budgets_category_id_month_year_key",
    "ALTER TABLE budgets ADD CONSTRAINT IF NOT EXISTS budgets_user_cat_month_year_key UNIQUE (user_id, category_id, month, year)",
]

with get_connection() as conn:
    for sql in steps:
        try:
            conn.execute(sql)
            print(f"  OK: {sql[:70]}")
        except Exception as e:
            print(f"  SKIP ({e.__class__.__name__}): {sql[:60]}")

print("Done.")
