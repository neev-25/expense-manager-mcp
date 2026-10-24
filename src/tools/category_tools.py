"""
tools/category_tools.py — MCP tools for dynamic category and subcategory management.
All DB operations are now scoped to the current user_id.
"""
from __future__ import annotations
from typing import Optional

from src.database.db import get_connection, get_current_user_id
from src.schemas.category import CategoryCreate, CategoryUpdate, SubcategoryCreate


def register(mcp):

    @mcp.tool()
    def list_categories() -> list[dict]:
        """List all categories with their subcategories."""
        uid = get_current_user_id()
        with get_connection() as conn:
            cats = conn.execute(
                "SELECT * FROM categories WHERE user_id=%s ORDER BY name", (uid,)
            ).fetchall()
            result = []
            for cat in cats:
                subs = conn.execute(
                    "SELECT id, name FROM subcategories WHERE category_id=%s AND user_id=%s ORDER BY name",
                    (cat["id"], uid)
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
        uid = get_current_user_id()
        data = CategoryCreate(name=name, icon=icon)
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM categories WHERE user_id=%s AND name=%s",
                (uid, data.name)
            ).fetchone()
            if existing:
                return {"status": "exists", "id": existing["id"], "name": name}
            cur = conn.execute(
                "INSERT INTO categories(user_id, name, icon) VALUES (%s,%s,%s) RETURNING id",
                (uid, data.name, data.icon)
            )
            row = cur.fetchone()
        return {"status": "ok", "id": row["id"], "name": name}

    @mcp.tool()
    def update_category(
        category_id: int,
        name: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> dict:
        """Rename a category or change its icon."""
        uid = get_current_user_id()
        data = CategoryUpdate(name=name, icon=icon)
        fields = {k: v for k, v in data.model_dump().items() if v is not None}
        if not fields:
            return {"status": "nothing to update"}
        set_clause = ", ".join(f"{k}=%s" for k in fields)
        with get_connection() as conn:
            conn.execute(
                f"UPDATE categories SET {set_clause} WHERE id=%s AND user_id=%s",
                (*fields.values(), category_id, uid)
            )
        return {"status": "ok", "category_id": category_id}

    @mcp.tool()
    def delete_category(category_id: int) -> dict:
        """Delete a category. Subcategories are removed automatically (CASCADE)."""
        uid = get_current_user_id()
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM categories WHERE id=%s AND user_id=%s", (category_id, uid)
            )
        return {"status": "deleted", "category_id": category_id}

    @mcp.tool()
    def create_subcategory(category_id: int, name: str) -> dict:
        """Add a subcategory to an existing category. Example: category_id=1, name='Biryani'"""
        uid = get_current_user_id()
        data = SubcategoryCreate(category_id=category_id, name=name)
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM subcategories WHERE user_id=%s AND category_id=%s AND name=%s",
                (uid, data.category_id, data.name)
            ).fetchone()
            if existing:
                return {"status": "exists", "id": existing["id"], "name": name}
            cur = conn.execute(
                "INSERT INTO subcategories(user_id, category_id, name) VALUES (%s,%s,%s) RETURNING id",
                (uid, data.category_id, data.name)
            )
            row = cur.fetchone()
        return {"status": "ok", "id": row["id"], "name": name}

    @mcp.tool()
    def move_subcategory(subcategory_id: int, new_category_id: int) -> dict:
        """Move a subcategory to a different parent category."""
        uid = get_current_user_id()
        with get_connection() as conn:
            conn.execute(
                "UPDATE subcategories SET category_id=%s WHERE id=%s AND user_id=%s",
                (new_category_id, subcategory_id, uid)
            )
        return {"status": "ok"}
