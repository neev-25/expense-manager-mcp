"""
services/analytics_service.py — Spending analytics and budget tracking.
"""
from __future__ import annotations
from datetime import datetime

from src.database.db import get_connection
from src.config import BUDGET_WARNING_PCT, BUDGET_DANGER_PCT


def _row_to_dict(row) -> dict:
    return dict(row)


# ── Monthly Summary ───────────────────────────────────────────────────────────
def monthly_summary(year: int, month: int) -> dict:
    """Full breakdown for a given month: total, by category, by payment method."""
    m_str = f"{month:02d}"
    y_str = str(year)

    with get_connection() as conn:
        # Overall totals
        totals = conn.execute("""
            SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE is_deleted=0
              AND strftime('%Y', expense_date) = ?
              AND strftime('%m', expense_date) = ?
        """, (y_str, m_str)).fetchone()

        # Days in month for avg calculation
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]

        # By category
        by_cat = conn.execute("""
            SELECT COALESCE(c.name, 'Uncategorized') AS category,
                   SUM(e.amount) AS total,
                   COUNT(*) AS count
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE e.is_deleted=0
              AND strftime('%Y', e.expense_date) = ?
              AND strftime('%m', e.expense_date) = ?
            GROUP BY category
            ORDER BY total DESC
        """, (y_str, m_str)).fetchall()

        # By payment method
        by_pay = conn.execute("""
            SELECT payment_method, SUM(amount) AS total, COUNT(*) AS count
            FROM expenses
            WHERE is_deleted=0
              AND strftime('%Y', expense_date) = ?
              AND strftime('%m', expense_date) = ?
            GROUP BY payment_method
            ORDER BY total DESC
        """, (y_str, m_str)).fetchall()

        # Top merchant
        top_merchant = conn.execute("""
            SELECT merchant, SUM(amount) AS total
            FROM expenses
            WHERE is_deleted=0 AND merchant != ''
              AND strftime('%Y', expense_date) = ?
              AND strftime('%m', expense_date) = ?
            GROUP BY merchant
            ORDER BY total DESC
            LIMIT 1
        """, (y_str, m_str)).fetchone()

    grand_total = totals["total"] or 0
    category_list = []
    for r in by_cat:
        category_list.append({
            "category": r["category"],
            "total": round(r["total"], 2),
            "count": r["count"],
            "percentage": round((r["total"] / grand_total * 100) if grand_total else 0, 1)
        })

    return {
        "year": year,
        "month": month,
        "total": round(grand_total, 2),
        "count": totals["count"],
        "avg_per_day": round(grand_total / days_in_month, 2),
        "by_category": category_list,
        "by_payment_method": [_row_to_dict(r) for r in by_pay],
        "top_merchant": top_merchant["merchant"] if top_merchant else None,
    }


# ── Yearly Summary ────────────────────────────────────────────────────────────
def yearly_summary(year: int) -> dict:
    """Month-by-month breakdown for a full year."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT strftime('%m', expense_date) AS month,
                   SUM(amount) AS total,
                   COUNT(*) AS count
            FROM expenses
            WHERE is_deleted=0
              AND strftime('%Y', expense_date) = ?
            GROUP BY month
            ORDER BY month
        """, (str(year),)).fetchall()

    months_data = {str(i).zfill(2): {"total": 0, "count": 0} for i in range(1, 13)}
    for r in rows:
        months_data[r["month"]] = {"total": round(r["total"], 2), "count": r["count"]}

    annual_total = sum(v["total"] for v in months_data.values())
    return {
        "year": year,
        "annual_total": round(annual_total, 2),
        "months": months_data,
    }


# ── Category Summary ──────────────────────────────────────────────────────────
def category_summary(year: int | None = None, month: int | None = None) -> list[dict]:
    """Spending per category, optionally filtered by year/month."""
    conditions = ["e.is_deleted = 0"]
    params: list = []

    if year:
        conditions.append("strftime('%Y', e.expense_date) = ?")
        params.append(str(year))
    if month:
        conditions.append("strftime('%m', e.expense_date) = ?")
        params.append(f"{month:02d}")

    where = "WHERE " + " AND ".join(conditions)
    sql = f"""
        SELECT COALESCE(c.name, 'Uncategorized') AS category,
               COALESCE(c.icon, '📦') AS icon,
               SUM(e.amount) AS total,
               COUNT(*) AS count,
               AVG(e.amount) AS avg_amount
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        {where}
        GROUP BY category
        ORDER BY total DESC
    """
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── Payment Method Summary ────────────────────────────────────────────────────
def payment_summary(year: int | None = None, month: int | None = None) -> list[dict]:
    conditions = ["is_deleted = 0"]
    params: list = []
    if year:
        conditions.append("strftime('%Y', expense_date) = ?")
        params.append(str(year))
    if month:
        conditions.append("strftime('%m', expense_date) = ?")
        params.append(f"{month:02d}")

    where = "WHERE " + " AND ".join(conditions)
    sql = f"""
        SELECT payment_method, SUM(amount) AS total, COUNT(*) AS count
        FROM expenses {where}
        GROUP BY payment_method ORDER BY total DESC
    """
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── Budget Utilization ─────────────────────────────────────────────────────────
def budget_summary(year: int, month: int) -> list[dict]:
    """
    Compare actual spending against budgets for a given month.
    Returns alert levels: 'ok', 'warning' (≥80%), 'danger' (≥100%).
    """
    m_str = f"{month:02d}"
    y_str = str(year)

    with get_connection() as conn:
        budgets = conn.execute("""
            SELECT b.id, b.amount AS budget_amount, c.name AS category, b.category_id
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            WHERE b.month=? AND b.year=?
        """, (month, year)).fetchall()

        results = []
        for b in budgets:
            spent_row = conn.execute("""
                SELECT COALESCE(SUM(amount), 0) AS spent
                FROM expenses
                WHERE is_deleted=0
                  AND category_id=?
                  AND strftime('%Y', expense_date) = ?
                  AND strftime('%m', expense_date) = ?
            """, (b["category_id"], y_str, m_str)).fetchone()

            spent = spent_row["spent"]
            budget_amt = b["budget_amount"]
            pct = round((spent / budget_amt * 100) if budget_amt else 0, 1)

            if pct >= BUDGET_DANGER_PCT:
                alert = "danger"
            elif pct >= BUDGET_WARNING_PCT:
                alert = "warning"
            else:
                alert = "ok"

            results.append({
                "category": b["category"],
                "budget_amount": budget_amt,
                "spent": round(spent, 2),
                "remaining": round(budget_amt - spent, 2),
                "utilization_pct": pct,
                "alert": alert,
                "alert_emoji": "🔴" if alert == "danger" else ("🟡" if alert == "warning" else "🟢"),
            })
    return results


# ── Set / Update Budget ───────────────────────────────────────────────────────
def set_budget(category_id: int, month: int, year: int, amount: float) -> dict:
    """Upsert a budget for a category-month-year combination."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO budgets(category_id, month, year, amount)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(category_id, month, year) DO UPDATE SET amount=excluded.amount
        """, (category_id, month, year, amount))
    return {"status": "ok", "category_id": category_id, "month": month, "year": year, "amount": amount}
