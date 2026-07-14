"""
tools/category_tools.py — MCP tools for dynamic category and subcategory management.
"""
from __future__ import annotations
from typing import Optional

from src.database.db import get_connection
from src.schemas.category import CategoryCreate, CategoryUpdate, SubcategoryCreate


def register(mcp):

    @mcp.tool()
    def list_categories() -> list[dict]:
        """List all categories with their subcategories."""
        with get_connection() as conn:
            cats = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
            result = []
            for cat in cats:
                subs = conn.execute(
                    "SELECT id, name FROM subcategories WHERE category_id=? ORDER BY name",
                    (cat["id"],)
                ).fetchall()
                result.append({
                    "id": cat["id"],
                    "name": cat["name"],
                    "icon": cat["icon"],
                    "subcategories": [dict(s) for s in subs],
                })
        return result

    @mcp.tool()
    def create_category(name: str, icon: str = "💰") -> dict:
        """Create a new top-level expense category. Example: name='Fashion', icon='👗'"""
        data = CategoryCreate(name=name, icon=icon)
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO categories(name, icon) VALUES (?,?)",
                (data.name, data.icon)
            )
        return {"status": "ok", "id": cur.lastrowid, "name": name}

    @mcp.tool()
    def update_category(
        category_id: int,
        name: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> dict:
        """Rename a category or change its icon."""
        data = CategoryUpdate(name=name, icon=icon)
        fields = {k: v for k, v in data.model_dump().items() if v is not None}
        if not fields:
            return {"status": "nothing to update"}
        set_clause = ", ".join(f"{k}=?" for k in fields)
        with get_connection() as conn:
            conn.execute(
                f"UPDATE categories SET {set_clause} WHERE id=?",
                (*fields.values(), category_id)
            )
        return {"status": "ok", "category_id": category_id}

    @mcp.tool()
    def delete_category(category_id: int) -> dict:
        """Delete a category. Subcategories are removed automatically (CASCADE)."""
        with get_connection() as conn:
            conn.execute("DELETE FROM categories WHERE id=?", (category_id,))
        return {"status": "deleted", "category_id": category_id}

    @mcp.tool()
    def create_subcategory(category_id: int, name: str) -> dict:
        """Add a subcategory to an existing category. Example: category_id=1, name='Biryani'"""
        data = SubcategoryCreate(category_id=category_id, name=name)
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO subcategories(category_id, name) VALUES (?,?)",
                (data.category_id, data.name)
            )
        return {"status": "ok", "id": cur.lastrowid, "name": name}

    @mcp.tool()
    def move_subcategory(subcategory_id: int, new_category_id: int) -> dict:
        """Move a subcategory to a different parent category."""
        with get_connection() as conn:
            conn.execute(
                "UPDATE subcategories SET category_id=? WHERE id=?",
                (new_category_id, subcategory_id)
            )
        return {"status": "ok"}
