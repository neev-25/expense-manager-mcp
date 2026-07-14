"""
services/split_service.py — Friend management, general balances, and event splits.

Two systems:
  A. General Balance: ad-hoc "I paid for Rahul" entries with net tracking.
  B. Event-Based:    structured group expense splitting (equal/percentage/custom).
"""
from __future__ import annotations
import json
from datetime import datetime

from src.database.db import get_connection
from src.schemas.splitwise import FriendCreate, BalanceCreate, EventCreate, EventExpenseCreate


def _row_to_dict(row) -> dict:
    return dict(row)


# ── A. Friends ────────────────────────────────────────────────────────────────
def add_friend(data: FriendCreate) -> dict:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO friends(name, email, phone) VALUES (?, ?, ?)",
            (data.name, data.email, data.phone)
        )
        return {"status": "ok", "id": cur.lastrowid, "name": data.name}


def list_friends() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM friends ORDER BY name").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_friend(friend_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM friends WHERE id=?", (friend_id,)).fetchone()
    if not row:
        raise ValueError(f"Friend id={friend_id} not found.")
    return _row_to_dict(row)


# ── A. General Balances ───────────────────────────────────────────────────────
def record_balance(data: BalanceCreate) -> dict:
    """
    Record a money exchange.
    direction = "i_paid"    → friend owes me money
    direction = "they_paid" → I owe the friend money
    """
    if data.direction not in ("i_paid", "they_paid"):
        raise ValueError("direction must be 'i_paid' or 'they_paid'.")

    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO balances(friend_id, amount, direction, reason, expense_id)
               VALUES (?, ?, ?, ?, ?)""",
            (data.friend_id, data.amount, data.direction, data.reason, data.expense_id)
        )
    return {"status": "ok", "balance_id": cur.lastrowid}


def settle_balance(friend_id: int, amount: float | None = None) -> dict:
    """
    Mark balances as settled.
    If amount is given, settle exactly that amount; otherwise settle all pending.
    """
    with get_connection() as conn:
        if amount is None:
            conn.execute(
                "UPDATE balances SET status='settled' WHERE friend_id=? AND status='pending'",
                (friend_id,)
            )
        else:
            # Mark individual rows until amount is consumed
            rows = conn.execute(
                "SELECT * FROM balances WHERE friend_id=? AND status='pending' ORDER BY id",
                (friend_id,)
            ).fetchall()
            remaining = amount
            for r in rows:
                if remaining <= 0:
                    break
                if r["amount"] <= remaining:
                    conn.execute("UPDATE balances SET status='settled' WHERE id=?", (r["id"],))
                    remaining -= r["amount"]
    return {"status": "ok", "friend_id": friend_id}


def friend_balance_summary(friend_id: int) -> dict:
    """
    Net balance with a single friend.
    Positive net → friend owes ME money.
    Negative net → I owe the friend money.
    """
    with get_connection() as conn:
        friend = get_friend(friend_id)
        rows = conn.execute(
            "SELECT direction, SUM(amount) AS total FROM balances WHERE friend_id=? AND status='pending' GROUP BY direction",
            (friend_id,)
        ).fetchall()

    i_paid = 0.0
    they_paid = 0.0
    for r in rows:
        if r["direction"] == "i_paid":
            i_paid = r["total"]
        else:
            they_paid = r["total"]

    net = round(i_paid - they_paid, 2)
    return {
        "friend": friend["name"],
        "friend_id": friend_id,
        "they_owe_me": round(i_paid, 2),
        "i_owe_them": round(they_paid, 2),
        "net": net,
        "summary": (
            f"{friend['name']} owes you ₹{net}" if net > 0
            else (f"You owe {friend['name']} ₹{abs(net)}" if net < 0 else "Settled up!")
        )
    }


def overall_balance() -> dict:
    """Net balance across all friends (who owes you, who you owe)."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT f.id, f.name,
                   COALESCE(SUM(CASE WHEN b.direction='i_paid'    THEN b.amount ELSE 0 END), 0) AS they_owe_me,
                   COALESCE(SUM(CASE WHEN b.direction='they_paid' THEN b.amount ELSE 0 END), 0) AS i_owe_them
            FROM friends f
            LEFT JOIN balances b ON b.friend_id=f.id AND b.status='pending'
            GROUP BY f.id
            ORDER BY f.name
        """).fetchall()

    friends_data = []
    total_receivable = 0.0
    total_payable = 0.0

    for r in rows:
        net = round(r["they_owe_me"] - r["i_owe_them"], 2)
        friends_data.append({
            "friend_id": r["id"],
            "name": r["name"],
            "net": net,
            "label": "owes you" if net > 0 else ("you owe" if net < 0 else "settled"),
        })
        if net > 0:
            total_receivable += net
        else:
            total_payable += abs(net)

    return {
        "friends": friends_data,
        "total_receivable": round(total_receivable, 2),
        "total_payable": round(total_payable, 2),
    }


# ── B. Events ─────────────────────────────────────────────────────────────────
def create_event(data: EventCreate) -> dict:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO events(title, description, start_date, end_date) VALUES (?,?,?,?)",
            (data.title, data.description, data.start_date, data.end_date)
        )
        event_id = cur.lastrowid
        for fid in data.member_ids:
            conn.execute(
                "INSERT OR IGNORE INTO event_members(event_id, friend_id) VALUES (?,?)",
                (event_id, fid)
            )
    return {"status": "ok", "event_id": event_id, "title": data.title}


def add_event_member(event_id: int, friend_id: int) -> dict:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO event_members(event_id, friend_id) VALUES (?,?)",
            (event_id, friend_id)
        )
    return {"status": "ok"}


def add_event_expense(data: EventExpenseCreate) -> dict:
    """
    Add an expense to an event and compute per-member splits.

    Returns the computed split so the user can verify it immediately.
    """
    # Determine the set of members to split among
    with get_connection() as conn:
        member_rows = conn.execute(
            "SELECT friend_id FROM event_members WHERE event_id=?", (data.event_id,)
        ).fetchall()
    all_member_ids = [r["friend_id"] for r in member_rows]

    split_ids = data.included_member_ids if data.included_member_ids else all_member_ids

    # Compute the split_data dict: {friend_id_str: amount_owed}
    computed_split: dict[str, float] = {}

    if data.split_type == "equal":
        share = round(data.amount / len(split_ids), 2)
        for fid in split_ids:
            computed_split[str(fid)] = share

    elif data.split_type == "percentage":
        pct_total = sum(data.split_data.values())
        if abs(pct_total - 100) > 0.01:
            raise ValueError(f"Percentages must sum to 100, got {pct_total}")
        for fid_str, pct in data.split_data.items():
            computed_split[fid_str] = round(data.amount * pct / 100, 2)

    elif data.split_type == "custom":
        amt_total = sum(data.split_data.values())
        if abs(amt_total - data.amount) > 0.01:
            raise ValueError(f"Custom amounts must sum to {data.amount}, got {amt_total}")
        computed_split = {str(k): round(v, 2) for k, v in data.split_data.items()}

    else:
        raise ValueError(f"Unknown split_type: {data.split_type}")

    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO event_expenses
                (event_id, title, amount, paid_by_friend_id, split_type, split_data)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.event_id, data.title, data.amount,
            data.paid_by_friend_id, data.split_type,
            json.dumps(computed_split)
        ))

    return {
        "status": "ok",
        "event_expense_id": cur.lastrowid,
        "split": computed_split,
        "payer_id": data.paid_by_friend_id,
    }


def event_summary(event_id: int) -> dict:
    """
    Full event summary: members, expenses, per-member totals,
    and the minimum settlement transactions.
    """
    from src.services.settlement_service import compute_minimal_settlements

    with get_connection() as conn:
        event = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        if not event:
            raise ValueError(f"Event id={event_id} not found.")

        members_rows = conn.execute("""
            SELECT f.id, f.name FROM event_members em
            JOIN friends f ON f.id=em.friend_id
            WHERE em.event_id=?
        """, (event_id,)).fetchall()

        expenses_rows = conn.execute(
            "SELECT * FROM event_expenses WHERE event_id=?", (event_id,)
        ).fetchall()

    members = {r["id"]: r["name"] for r in members_rows}
    expenses = [_row_to_dict(r) for r in expenses_rows]

    # Build net balance map: net[friend_id] = amount they are owed (positive) or owe (negative)
    net: dict[int, float] = {fid: 0.0 for fid in members}
    total_spent = 0.0

    for exp in expenses:
        paid_by = exp["paid_by_friend_id"]
        amount = exp["amount"]
        total_spent += amount
        net[paid_by] = net.get(paid_by, 0.0) + amount
        split = json.loads(exp["split_data"])
        for fid_str, owed in split.items():
            fid = int(fid_str)
            net[fid] = net.get(fid, 0.0) - owed

    settlements = compute_minimal_settlements(net, members)

    return {
        "event": _row_to_dict(event),
        "members": [{"id": k, "name": v} for k, v in members.items()],
        "expenses": expenses,
        "total_spent": round(total_spent, 2),
        "per_member_net": {members[fid]: round(v, 2) for fid, v in net.items()},
        "settlements": settlements,
    }


def close_event(event_id: int) -> dict:
    with get_connection() as conn:
        conn.execute("UPDATE events SET status='closed' WHERE id=?", (event_id,))
    return {"status": "closed", "event_id": event_id}
