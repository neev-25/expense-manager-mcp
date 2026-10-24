"""
tools/event_tools.py — MCP tools for event-based group expense splitting.
All DB operations are now scoped to the current user_id.
"""
from __future__ import annotations
from typing import Optional

from src.services import split_service as svc
from src.schemas.splitwise import EventCreate, EventExpenseCreate
from src.database.db import get_connection, get_current_user_id


def register(mcp):

    @mcp.tool()
    def create_event(
        title: str,
        description: str = "",
        start_date: str = "",
        end_date: str = "",
        member_ids: Optional[list[int]] = None,
    ) -> dict:
        """
        Create a group event for expense splitting.
        member_ids: list of friend IDs to add as participants.

        Example: "Girnar Trip" with Rahul (id=1), Prince (id=2), Jay (id=3)
        """
        return svc.create_event(EventCreate(
            title=title, description=description,
            start_date=start_date, end_date=end_date,
            member_ids=member_ids or [],
        ))

    @mcp.tool()
    def add_event_member(event_id: int, friend_id: int) -> dict:
        """Add a friend to an existing event."""
        return svc.add_event_member(event_id, friend_id)

    @mcp.tool()
    def add_event_expense(
        event_id: int,
        title: str,
        amount: float,
        paid_by_friend_id: int,
        split_type: str = "equal",
        split_data: Optional[dict] = None,
        included_member_ids: Optional[list[int]] = None,
    ) -> dict:
        """
        Add an expense to a group event and compute per-member splits.

        split_type options:
          "equal"      → split evenly among all members (or included_member_ids)
          "percentage" → supply split_data={"friend_id": percent, ...} summing to 100
          "custom"     → supply split_data={"friend_id": amount, ...} summing to total

        Returns the computed split immediately so you can verify it.
        """
        return svc.add_event_expense(EventExpenseCreate(
            event_id=event_id, title=title, amount=amount,
            paid_by_friend_id=paid_by_friend_id,
            split_type=split_type,
            split_data=split_data or {},
            included_member_ids=included_member_ids or [],
        ))

    @mcp.tool()
    def event_summary(event_id: int) -> dict:
        """
        Complete event summary including:
        - All expenses
        - Per-member net balances
        - Minimum settlement transactions (who pays whom, how much)
        """
        return svc.event_summary(event_id)

    @mcp.tool()
    def list_events() -> list[dict]:
        """List all events (active and closed) for the current user."""
        uid = get_current_user_id()
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE user_id=%s ORDER BY created_at DESC", (uid,)
            ).fetchall()
        return [dict(r) for r in rows]

    @mcp.tool()
    def close_event(event_id: int) -> dict:
        """Mark an event as closed (all expenses settled)."""
        return svc.close_event(event_id)
