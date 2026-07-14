"""
services/expense_service.py — All expense CRUD and the filtering engine.

The filtering engine is the most interesting part here: it builds a SQL
WHERE clause dynamically based on whatever filters the caller provides.
This supports 15+ filter dimensions without any hard-coded query branches.
"""
from __future__ import annotations
from typing import Optional
from datetime import datetime

from src.database.db import get_connection
from src.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseFilters


def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


# ── Create ────────────────────────────────────────────────────────────────────
def create_expense(data: ExpenseCreate) -> dict:
    sql = """
        INSERT INTO expenses
            (title, amount, description, category_id, subcategory_id, merchant,
             payment_method, currency, location, expense_date, receipt_url, tags, notes)
        VALUES
            (:title, :amount, :description, :category_id, :subcategory_id, :merchant,
             :payment_method, :currency, :location, :expense_date, :receipt_url, :tags, :notes)
    """
    with get_connection() as conn:
        cur = conn.execute(sql, data.model_dump())
        new_id = cur.lastrowid
    return get_expense(new_id)


# ── Read ──────────────────────────────────────────────────────────────────────
def get_expense(expense_id: int) -> dict:
    sql = """
        SELECT e.*, c.name AS category_name, s.name AS subcategory_name
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        LEFT JOIN subcategories s ON e.subcategory_id = s.id
        WHERE e.id = ?
    """
    with get_connection() as conn:
        row = conn.execute(sql, (expense_id,)).fetchone()
    if not row:
        raise ValueError(f"Expense with id={expense_id} not found.")
    return _row_to_dict(row)


# ── Update ────────────────────────────────────────────────────────────────────
def update_expense(expense_id: int, data: ExpenseUpdate) -> dict:
    # Only update fields that were actually provided (not None)
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    if not fields:
        raise ValueError("No fields provided for update.")

    fields["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{col} = :{col}" for col in fields)
    fields["id"] = expense_id

    with get_connection() as conn:
        conn.execute(f"UPDATE expenses SET {set_clause} WHERE id = :id", fields)
    return get_expense(expense_id)


# ── Soft Delete / Restore ─────────────────────────────────────────────────────
def delete_expense(expense_id: int) -> dict:
    """Soft delete — marks is_deleted=1 so it can be restored later."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE expenses SET is_deleted=1, updated_at=? WHERE id=?",
            (datetime.now().isoformat(), expense_id)
        )
    return {"status": "deleted", "id": expense_id}


def restore_expense(expense_id: int) -> dict:
    """Restore a soft-deleted expense."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE expenses SET is_deleted=0, updated_at=? WHERE id=?",
            (datetime.now().isoformat(), expense_id)
        )
    return get_expense(expense_id)


# ── Powerful Filtering Engine ─────────────────────────────────────────────────
def list_expenses(filters: Optional[ExpenseFilters] = None) -> list[dict]:
    """
    Build a dynamic SQL query from an ExpenseFilters object.

    Design pattern: Accumulate conditions in a list, then join with AND.
    This keeps the code readable and avoids nested if-else chains.
    """
    if filters is None:
        filters = ExpenseFilters()

    conditions: list[str] = []
    params: dict = {}

    # Soft-delete filter (default: hide deleted)
    if not filters.include_deleted:
        conditions.append("e.is_deleted = 0")

    # Date range
    if filters.start_date:
        conditions.append("e.expense_date >= :start_date")
        params["start_date"] = filters.start_date
    if filters.end_date:
        conditions.append("e.expense_date <= :end_date")
        params["end_date"] = filters.end_date

    # Month / Year shortcut
    if filters.year:
        conditions.append("strftime('%Y', e.expense_date) = :year")
        params["year"] = str(filters.year)
    if filters.month:
        conditions.append("strftime('%m', e.expense_date) = :month")
        params["month"] = f"{filters.month:02d}"

    # Category / Subcategory
    if filters.category_id:
        conditions.append("e.category_id = :category_id")
        params["category_id"] = filters.category_id
    if filters.subcategory_id:
        conditions.append("e.subcategory_id = :subcategory_id")
        params["subcategory_id"] = filters.subcategory_id

    # Amount range
    if filters.min_amount is not None:
        conditions.append("e.amount >= :min_amount")
        params["min_amount"] = filters.min_amount
    if filters.max_amount is not None:
        conditions.append("e.amount <= :max_amount")
        params["max_amount"] = filters.max_amount

    # Text search (partial LIKE matches)
    if filters.merchant:
        conditions.append("e.merchant LIKE :merchant")
        params["merchant"] = f"%{filters.merchant}%"
    if filters.location:
        conditions.append("e.location LIKE :location")
        params["location"] = f"%{filters.location}%"
    if filters.tags:
        conditions.append("e.tags LIKE :tags")
        params["tags"] = f"%{filters.tags}%"
    if filters.notes:
        conditions.append("e.notes LIKE :notes")
        params["notes"] = f"%{filters.notes}%"

    # Payment method / Currency
    if filters.payment_method:
        conditions.append("e.payment_method = :payment_method")
        params["payment_method"] = filters.payment_method
    if filters.currency:
        conditions.append("e.currency = :currency")
        params["currency"] = filters.currency

    # Event filter
    if filters.event_id:
        conditions.append("""
            e.id IN (SELECT expense_id FROM event_expenses WHERE event_id = :event_id)
        """)
        params["event_id"] = filters.event_id

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    sql = f"""
        SELECT e.*,
               c.name  AS category_name,
               s.name  AS subcategory_name
        FROM expenses e
        LEFT JOIN categories   c ON e.category_id    = c.id
        LEFT JOIN subcategories s ON e.subcategory_id = s.id
        {where_clause}
        ORDER BY e.expense_date DESC, e.id DESC
    """

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]
