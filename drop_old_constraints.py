"""drop_old_constraints.py — Force drop the old global unique constraints from Neon."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.database.db import get_connection

# These are the OLD constraints to drop. They enforce uniqueness globally,
# preventing two different users from having categories/subcategories with the same name.
drops = [
    ("categories",    "categories_name_key"),
    ("subcategories", "subcategories_category_id_name_key"),
    ("budgets",       "budgets_category_id_month_year_key"),
]

with get_connection() as conn:
    for table, constraint in drops:
        try:
            conn.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "{constraint}"')
            print(f"  ✅ Dropped {constraint}")
        except Exception as e:
            print(f"  ⚠  {constraint}: {e}")

    # Verify remaining constraints
    rows = conn.execute("""
        SELECT table_name, constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name IN ('categories','subcategories','budgets')
          AND constraint_type IN ('UNIQUE','PRIMARY KEY')
        ORDER BY table_name, constraint_name
    """).fetchall()
    print("\nRemaining constraints:")
    for r in rows:
        print(f"  {r['table_name']}: {r['constraint_name']} ({r['constraint_type']})")

print("\nDone.")
