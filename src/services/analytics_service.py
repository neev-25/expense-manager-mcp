"""
services/analytics_service.py — Spending analytics and budget tracking.
All queries are now scoped to user_id for per-user data isolation.
"""
from __future__ import annotations
from datetime import datetime

from src.database.db import get_connection, get_current_user_id
from src.config import BUDGET_WARNING_PCT, BUDGET_DANGER_PCT


def _row_to_dict(row) -> dict:
    return dict(row)


# ── Monthly Summary ───────────────────────────────────────────────────────────
def monthly_summary(year: int, month: int, user_id: int | None = None) -> dict:
    uid = user_id if user_id is not None else get_current_user_id()
    m_str = f"{month:02d}"
    y_str = str(year)

    with get_connection() as conn:
        totals = conn.execute("""
            SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE is_deleted=0 AND user_id=%s
              AND SUBSTRING(CAST(expense_date AS text) FROM 1 FOR 4) = %s
              AND SUBSTRING(CAST(expense_date AS text) FROM 6 FOR 2) = %s
        """, (uid, y_str, m_str)).fetchone()

        import calendar
        days_in_month = calendar.monthrange(year, month)[1]

        by_cat = conn.execute("""
            SELECT COALESCE(c.name, 'Uncategorized') AS category,
                   SUM(e.amount) AS total,
                   COUNT(*) AS count
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE e.is_deleted=0 AND e.user_id=%s
              AND SUBSTRING(CAST(e.expense_date AS text) FROM 1 FOR 4) = %s
              AND SUBSTRING(CAST(e.expense_date AS text) FROM 6 FOR 2) = %s
            GROUP BY category
            ORDER BY total DESC
        """, (uid, y_str, m_str)).fetchall()

        by_pay = conn.execute("""
            SELECT payment_method, SUM(amount) AS total, COUNT(*) AS count
            FROM expenses
            WHERE is_deleted=0 AND user_id=%s
              AND SUBSTRING(CAST(expense_date AS text) FROM 1 FOR 4) = %s
              AND SUBSTRING(CAST(expense_date AS text) FROM 6 FOR 2) = %s
            GROUP BY payment_method
            ORDER BY total DESC
        """, (uid, y_str, m_str)).fetchall()

        top_merchant = conn.execute("""
            SELECT merchant, SUM(amount) AS total
            FROM expenses
            WHERE is_deleted=0 AND merchant != '' AND user_id=%s
              AND SUBSTRING(CAST(expense_date AS text) FROM 1 FOR 4) = %s
              AND SUBSTRING(CAST(expense_date AS text) FROM 6 FOR 2) = %s
            GROUP BY merchant
            ORDER BY total DESC
            LIMIT 1
        """, (uid, y_str, m_str)).fetchone()

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
def yearly_summary(year: int, user_id: int | None = None) -> dict:
    uid = user_id if user_id is not None else get_current_user_id()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT SUBSTRING(CAST(expense_date AS text) FROM 6 FOR 2) AS month,
                   SUM(amount) AS total,
                   COUNT(*) AS count
            FROM expenses
            WHERE is_deleted=0 AND user_id=%s
              AND SUBSTRING(CAST(expense_date AS text) FROM 1 FOR 4) = %s
            GROUP BY month
            ORDER BY month
        """, (uid, str(year))).fetchall()

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
def category_summary(year: int | None = None, month: int | None = None, user_id: int | None = None) -> list[dict]:
    uid = user_id if user_id is not None else get_current_user_id()
    conditions = ["e.is_deleted = 0", "e.user_id = %s"]
    params: list = [uid]

    if year:
        conditions.append("SUBSTRING(CAST(e.expense_date AS text) FROM 1 FOR 4) = %s")
        params.append(str(year))
    if month:
        conditions.append("SUBSTRING(CAST(e.expense_date AS text) FROM 6 FOR 2) = %s")
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
        GROUP BY category, icon
        ORDER BY total DESC
    """
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── Payment Method Summary ────────────────────────────────────────────────────
def payment_summary(year: int | None = None, month: int | None = None, user_id: int | None = None) -> list[dict]:
    uid = user_id if user_id is not None else get_current_user_id()
    conditions = ["is_deleted = 0", "user_id = %s"]
    params: list = [uid]
    if year:
        conditions.append("SUBSTRING(CAST(expense_date AS text) FROM 1 FOR 4) = %s")
        params.append(str(year))
    if month:
        conditions.append("SUBSTRING(CAST(expense_date AS text) FROM 6 FOR 2) = %s")
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
def budget_summary(year: int, month: int, user_id: int | None = None) -> list[dict]:
    uid = user_id if user_id is not None else get_current_user_id()
    m_str = f"{month:02d}"
    y_str = str(year)

    with get_connection() as conn:
        budgets = conn.execute("""
            SELECT b.id, b.amount AS budget_amount, c.name AS category, b.category_id
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            WHERE b.user_id=%s AND b.month=%s AND b.year=%s
        """, (uid, month, year)).fetchall()

        results = []
        for b in budgets:
            spent_row = conn.execute("""
                SELECT COALESCE(SUM(amount), 0) AS spent
                FROM expenses
                WHERE is_deleted=0 AND user_id=%s
                  AND category_id=%s
                  AND SUBSTRING(CAST(expense_date AS text) FROM 1 FOR 4) = %s
                  AND SUBSTRING(CAST(expense_date AS text) FROM 6 FOR 2) = %s
            """, (uid, b["category_id"], y_str, m_str)).fetchone()

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
def set_budget(category_id: int, month: int, year: int, amount: float, user_id: int | None = None) -> dict:
    uid = user_id if user_id is not None else get_current_user_id()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM budgets WHERE user_id=%s AND category_id=%s AND month=%s AND year=%s",
            (uid, category_id, month, year)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE budgets SET amount=%s WHERE id=%s",
                (amount, existing["id"])
            )
        else:
            conn.execute(
                "INSERT INTO budgets(user_id, category_id, month, year, amount) VALUES (%s,%s,%s,%s,%s)",
                (uid, category_id, month, year, amount)
            )
    return {"status": "ok", "category_id": category_id, "month": month, "year": year, "amount": amount}
