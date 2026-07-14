"""
schemas/splitwise.py — Models for friends, general balances, events, and splits.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ── Friends ───────────────────────────────────────────────────────────────────
class FriendCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field("", max_length=200)
    phone: str = Field("", max_length=20)


# ── General Balance (non-event) ───────────────────────────────────────────────
class BalanceCreate(BaseModel):
    """
    Record a money exchange between you and a friend.

    direction:
      "i_paid"    → I paid for the friend   → friend owes me
      "they_paid" → Friend paid for me       → I owe the friend
    """
    friend_id: int = Field(..., description="ID of the friend")
    amount: float = Field(..., gt=0, description="Amount exchanged, must be > 0")
    direction: str = Field(..., description="'i_paid' or 'they_paid'")
    reason: str = Field("", description="Brief reason, e.g. 'Dinner at Domino\\'s'")
    expense_id: Optional[int] = Field(None, description="Link to an existing expense if applicable")

    class Config:
        json_schema_extra = {
            "example": {
                "friend_id": 1,
                "amount": 500,
                "direction": "i_paid",
                "reason": "Flight ticket for Girnar trip"
            }
        }


# ── Events ────────────────────────────────────────────────────────────────────
class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Event name, e.g. 'Girnar Trip'")
    description: str = Field("", description="Optional notes about the event")
    start_date: str = Field("", description="YYYY-MM-DD")
    end_date: str = Field("", description="YYYY-MM-DD")
    member_ids: list[int] = Field(default_factory=list, description="Friend IDs to add as members")


class EventExpenseCreate(BaseModel):
    """
    Add one expense to an event.

    split_type options:
      "equal"      → split evenly among all members (or `included_member_ids` if provided)
      "percentage" → split_data = {"friend_id": percentage, ...}  (must sum to 100)
      "custom"     → split_data = {"friend_id": amount, ...}      (must sum to total amount)
    """
    event_id: int
    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    paid_by_friend_id: int = Field(..., description="Who physically paid the bill")
    split_type: str = Field(..., description="'equal', 'percentage', or 'custom'")
    split_data: dict = Field(default_factory=dict, description="Custom split amounts/percentages keyed by friend_id string")
    included_member_ids: list[int] = Field(default_factory=list, description="Subset of members to split among (equal split only)")
