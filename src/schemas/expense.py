"""
schemas/expense.py — Pydantic models for expense input/output validation.

Why Pydantic?
  MCP tools receive raw strings/ints from the AI client. Without validation,
  a bad value (e.g. amount = -50) silently corrupts the DB. Pydantic raises
  a clear error before anything touches the database.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import date


class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Short description, e.g. 'Domino's Pizza'")
    amount: float = Field(..., gt=0, description="Amount in the specified currency, must be > 0")
    expense_date: str = Field(..., description="Date in YYYY-MM-DD format")
    category_id: Optional[int] = Field(None, description="ID from the categories table")
    subcategory_id: Optional[int] = Field(None, description="ID from the subcategories table")
    description: str = Field("", description="Longer description or notes")
    merchant: str = Field("", description="Shop/restaurant/service name")
    payment_method: str = Field("Cash", description="UPI / Cash / Credit Card / etc.")
    currency: str = Field("INR", max_length=3, description="ISO 4217 code, e.g. INR, USD")
    location: str = Field("", description="City or place name")
    receipt_url: str = Field("", description="Link to receipt image")
    tags: str = Field("", description="Comma-separated tags, e.g. 'dinner,friends'")
    notes: str = Field("", description="Personal notes")

    @field_validator("expense_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("expense_date must be in YYYY-MM-DD format")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()


class ExpenseUpdate(BaseModel):
    """All fields are optional — only supplied fields get updated."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[float] = Field(None, gt=0)
    expense_date: Optional[str] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    payment_method: Optional[str] = None
    currency: Optional[str] = None
    location: Optional[str] = None
    receipt_url: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("expense_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValueError("expense_date must be in YYYY-MM-DD format")
        return v


class ExpenseFilters(BaseModel):
    """
    Filter parameters for list_expenses.
    Every field is optional — supply only what you want to filter by.
    """
    start_date: Optional[str] = None       # YYYY-MM-DD
    end_date: Optional[str] = None         # YYYY-MM-DD
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = Field(None, ge=2000)
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    merchant: Optional[str] = None        # partial match
    payment_method: Optional[str] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    tags: Optional[str] = None            # search within tags
    notes: Optional[str] = None           # search within notes
    location: Optional[str] = None        # partial match
    currency: Optional[str] = None
    friend_id: Optional[int] = None       # expenses linked via balance
    event_id: Optional[int] = None        # expenses in an event
    include_deleted: bool = False
