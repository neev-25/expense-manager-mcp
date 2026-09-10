"""
tools/splitwise_tools.py — MCP tools for friends, general balances, and settlements.
"""
from __future__ import annotations
from typing import Optional

from src.services import split_service as svc
from src.schemas.splitwise import FriendCreate, BalanceCreate
from src.services.settlement_service import explain_algorithm


def register(mcp):

    @mcp.tool()
    def add_friend(name: str, email: str = "", phone: str = "") -> dict:
        """Add a friend to track balances with."""
        return svc.add_friend(FriendCreate(name=name, email=email, phone=phone))

    @mcp.tool()
    def list_friends() -> list[dict]:
        """List all friends."""
        return svc.list_friends()

    @mcp.tool()
    def record_balance(
        friend_id: int,
        amount: float,
        direction: str,
        reason: str = "",
        expense_id: Optional[int] = None,
    ) -> dict:
        """
        direction:
          "i_owe"    → I owe them
          "they_owe" → They owe me
        """
        return svc.record_balance(BalanceCreate(
            friend_id=friend_id, amount=amount,
            direction=direction, reason=reason, expense_id=expense_id
        ))

    @mcp.tool()
    def settle(friend_id: int, amount: Optional[float] = None) -> dict:
        """
        Mark balances with a friend as settled.
        If amount is given, settle exactly that much; otherwise settle everything.
        """
        return svc.settle_balance(friend_id, amount)

    @mcp.tool()
    def friend_summary(friend_id: int) -> dict:
        """
        Net balance summary with a specific friend.
        Returns: who owes whom, and by how much.
        """
        return svc.friend_balance_summary(friend_id)

    @mcp.tool()
    def overall_balance() -> dict:
        """
        Net balance summary across ALL friends.
        Shows total receivable (others owe you) and total payable (you owe others).
        """
        return svc.overall_balance()

    @mcp.tool()
    def explain_settlement_algorithm() -> str:
        """
        Explains how the minimal debt settlement algorithm works.
        Great for learning and interview preparation!
        """
        return explain_algorithm()
