"""
tools/expense_tools.py — MCP tools for expense CRUD and filtering.

Each function decorated with @mcp.tool() becomes a callable tool in Claude Desktop.
We keep the tool signatures flat (primitive types only) and validate inside
using Pydantic schemas before calling the service layer.
"""
from __future__ import annotations
from typing import Optional

from src.services import expense_service as svc
from src.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseFilters


def register(mcp):
    """Register all expense tools on the given FastMCP instance."""

    @mcp.tool()
    def create_expense(
        title: str,
        amount: float,
        expense_date: str,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        description: str = "",
        merchant: str = "",
        payment_method: str = "Cash",
        currency: str = "INR",
        location: str = "",
        receipt_url: str = "",
        tags: str = "",
        notes: str = "",
    ) -> dict:
        """
        Add a new expense.

        Examples:
          - "₹450 at Domino's for dinner, paid via UPI, category Food"
          - "Flight ticket ₹3500 for Rahul, category Travel"
        """
        data = ExpenseCreate(
            title=title, amount=amount, expense_date=expense_date,
            category_id=category_id, subcategory_id=subcategory_id,
            description=description, merchant=merchant,
            payment_method=payment_method, currency=currency,
            location=location, receipt_url=receipt_url,
            tags=tags, notes=notes,
        )
        return svc.create_expense(data)

    @mcp.tool()
    def get_expense(expense_id: int) -> dict:
        """Get full details of a single expense by ID."""
        return svc.get_expense(expense_id)

    @mcp.tool()
    def update_expense(
        expense_id: int,
        title: Optional[str] = None,
        amount: Optional[float] = None,
        expense_date: Optional[str] = None,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        merchant: Optional[str] = None,
        payment_method: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> dict:
        """Update specific fields of an expense. Only supply what you want to change."""
        data = ExpenseUpdate(
            title=title, amount=amount, expense_date=expense_date,
            category_id=category_id, subcategory_id=subcategory_id,
            merchant=merchant, payment_method=payment_method,
            notes=notes, tags=tags,
        )
        return svc.update_expense(expense_id, data)

    @mcp.tool()
    def delete_expense(expense_id: int) -> dict:
        """
        Soft-delete an expense (can be restored later with restore_expense).
        The record stays in the database with is_deleted=1.
        """
        return svc.delete_expense(expense_id)

    @mcp.tool()
    def restore_expense(expense_id: int) -> dict:
        """Restore a previously deleted expense."""
        return svc.restore_expense(expense_id)

    @mcp.tool()
    def list_expenses(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        merchant: Optional[str] = None,
        payment_method: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        tags: Optional[str] = None,
        notes: Optional[str] = None,
        location: Optional[str] = None,
        currency: Optional[str] = None,
        event_id: Optional[int] = None,
        include_deleted: bool = False,
    ) -> list[dict]:
        """
        List expenses with powerful multi-dimensional filtering.

        Examples:
          - "All food expenses in July 2026"       → month=7, year=2026, category_id=<food_id>
          - "UPI expenses above ₹500 this month"   → payment_method='UPI', min_amount=500
          - "Expenses at Domino's"                 → merchant='Domino'
          - "Expenses for Girnar trip"             → event_id=<event_id>
        """
        filters = ExpenseFilters(
            start_date=start_date, end_date=end_date,
            month=month, year=year,
            category_id=category_id, subcategory_id=subcategory_id,
            merchant=merchant, payment_method=payment_method,
            min_amount=min_amount, max_amount=max_amount,
            tags=tags, notes=notes, location=location, currency=currency,
            event_id=event_id, include_deleted=include_deleted,
        )
        return svc.list_expenses(filters)
