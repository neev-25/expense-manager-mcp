"""
tools/analytics_tools.py — MCP tools for analytics, budgets, and recurring expenses.
"""
from __future__ import annotations
from typing import Optional
from datetime import date

from src.services import analytics_service as svc
from src.database.db import get_connection
from src.config import RECURRING_FREQUENCIES


def register(mcp):

    @mcp.tool()
    def expense_summary(year: Optional[int] = None, month: Optional[int] = None) -> list[dict]:
        """
        Category-wise spending summary.
        Leave year/month empty for all-time totals.
        """
        return svc.category_summary(year=year, month=month)

    @mcp.tool()
    def monthly_summary(year: int, month: int) -> dict:
        """
        Full monthly report: total, by category (with %), by payment method, top merchant.
        Example: year=2026, month=7
        """
        return svc.monthly_summary(year=year, month=month)

    @mcp.tool()
    def yearly_summary(year: int) -> dict:
        """Month-by-month spending breakdown for an entire year."""
        return svc.yearly_summary(year=year)

    @mcp.tool()
    def payment_summary(year: Optional[int] = None, month: Optional[int] = None) -> list[dict]:
        """Breakdown of spending by payment method (UPI, Cash, Card, etc.)."""
        return svc.payment_summary(year=year, month=month)

    @mcp.tool()
    def budget_summary(year: int, month: int) -> list[dict]:
        """
        Budget vs actual for all categories with budgets set.
        Returns alert level: 🟢 ok / 🟡 warning (≥80%) / 🔴 danger (≥100%)
        """
        return svc.budget_summary(year=year, month=month)

    @mcp.tool()
    def set_budget(category_id: int, month: int, year: int, amount: float) -> dict:
        """Set or update a spending budget for a category in a specific month/year."""
        return svc.set_budget(category_id=category_id, month=month, year=year, amount=amount)

    # ── Recurring Expenses ────────────────────────────────────────────────────
    @mcp.tool()
    def add_recurring(
        title: str,
        amount: float,
        frequency: str,
        next_due_date: str,
        category_id: Optional[int] = None,
        payment_method: str = "Cash",
    ) -> dict:
        """
        Add a recurring expense that auto-creates entries when due.
        frequency: 'daily' | 'weekly' | 'monthly' | 'yearly'
        next_due_date: YYYY-MM-DD

        Examples: Netflix monthly ₹199, Gym monthly ₹1500, Rent monthly ₹8000
        """
        if frequency not in RECURRING_FREQUENCIES:
            raise ValueError(f"frequency must be one of {RECURRING_FREQUENCIES}")
        with get_connection() as conn:
            cur = conn.execute("""
                INSERT INTO recurring_expenses
                    (title, amount, category_id, payment_method, frequency, next_due_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, amount, category_id, payment_method, frequency, next_due_date))
        return {"status": "ok", "id": cur.lastrowid, "title": title}

    @mcp.tool()
    def list_recurring() -> list[dict]:
        """List all active recurring expenses."""
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT r.*, c.name AS category_name
                FROM recurring_expenses r
                LEFT JOIN categories c ON r.category_id = c.id
                WHERE r.is_active=1 ORDER BY r.next_due_date
            """).fetchall()
        return [dict(r) for r in rows]

    @mcp.tool()
    def process_recurring() -> dict:
        """
        Process all overdue recurring expenses — creates actual expense entries
        for each one and updates next_due_date.
        Call this daily or at server startup.
        """
        from dateutil.relativedelta import relativedelta
        today = date.today()
        today_str = today.isoformat()
        created = []

        with get_connection() as conn:
            due = conn.execute("""
                SELECT * FROM recurring_expenses
                WHERE is_active=1 AND next_due_date <= ?
            """, (today_str,)).fetchall()

            for r in due:
                # Create the expense
                conn.execute("""
                    INSERT INTO expenses
                        (title, amount, category_id, payment_method, expense_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (r["title"], r["amount"], r["category_id"],
                      r["payment_method"], r["next_due_date"],
                      f"Auto-created from recurring rule #{r['id']}"))

                # Advance next_due_date
                from datetime import datetime
                due_date = datetime.strptime(r["next_due_date"], "%Y-%m-%d").date()
                freq = r["frequency"]
                if freq == "daily":
                    next_due = due_date + relativedelta(days=1)
                elif freq == "weekly":
                    next_due = due_date + relativedelta(weeks=1)
                elif freq == "monthly":
                    next_due = due_date + relativedelta(months=1)
                else:  # yearly
                    next_due = due_date + relativedelta(years=1)

                conn.execute(
                    "UPDATE recurring_expenses SET next_due_date=? WHERE id=?",
                    (next_due.isoformat(), r["id"])
                )
                created.append({"title": r["title"], "date": r["next_due_date"]})

        return {"created": created, "count": len(created)}
