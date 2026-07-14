"""
tools/search_tools.py — Natural language query dispatcher.

Instead of the user calling specific tool functions, they can ask free-text questions.
This tool parses the intent and routes to the correct service.

This is a rule-based NLP dispatcher (no LLM needed inside the MCP server — Claude
itself handles NLP and calls this when the user asks natural language questions).

The real "AI Search" magic happens at the Claude level: Claude reads the user's
question, picks the right tool (e.g. list_expenses with month=7), and formats the result.
This search_expenses tool acts as a convenience "catch-all" for complex queries.
"""
from __future__ import annotations
from typing import Optional
from datetime import date

from src.services.expense_service import list_expenses
from src.services.analytics_service import monthly_summary, category_summary
from src.services.split_service import overall_balance, event_summary
from src.schemas.expense import ExpenseFilters


def register(mcp):

    @mcp.tool()
    def search_expenses(
        query: str,
        month: Optional[int] = None,
        year: Optional[int] = None,
        category_id: Optional[int] = None,
        merchant: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        payment_method: Optional[str] = None,
        tags: Optional[str] = None,
        event_id: Optional[int] = None,
    ) -> dict:
        """
        Natural language expense search.

        Claude should use this when the user asks conversational questions about their spending.

        Examples:
          "How much did I spend on food this month?"
          "Show me Domino's expenses"
          "All UPI payments above ₹500 in June"
          "What did I spend at Girnar trip?"
          "Show my expensive purchases in 2026"

        Returns both the matching expenses AND a quick summary (total, count, avg).
        """
        today = date.today()
        effective_year  = year  or today.year
        effective_month = month or today.month

        filters = ExpenseFilters(
            month=month, year=year,
            category_id=category_id,
            merchant=merchant,
            min_amount=min_amount,
            max_amount=max_amount,
            payment_method=payment_method,
            tags=tags,
            event_id=event_id,
        )
        expenses = list_expenses(filters)
        total = sum(e["amount"] for e in expenses)
        return {
            "query": query,
            "count": len(expenses),
            "total": round(total, 2),
            "avg": round(total / len(expenses), 2) if expenses else 0,
            "expenses": expenses,
        }

    @mcp.tool()
    def quick_stats() -> dict:
        """
        Dashboard-style overview: this month's total, category breakdown, and overall balance.
        Perfect for "Give me a financial overview" or "How am I doing this month?"
        """
        today = date.today()
        m_summary = monthly_summary(today.year, today.month)
        balances  = overall_balance()
        return {
            "period": f"{today.strftime('%B %Y')}",
            "monthly_total": m_summary["total"],
            "monthly_count": m_summary["count"],
            "avg_per_day": m_summary["avg_per_day"],
            "top_categories": m_summary["by_category"][:5],
            "top_merchant": m_summary["top_merchant"],
            "balance_summary": {
                "you_are_owed": balances["total_receivable"],
                "you_owe": balances["total_payable"],
            }
        }

    @mcp.tool()
    def generate_csv(year: int, month: int) -> str:
        """
        Export all expenses for a given month as a CSV string.
        The CSV is also saved to the /reports/ directory.
        """
        import csv, io, os
        from src.config import REPORTS_DIR
        from src.schemas.expense import ExpenseFilters

        expenses = list_expenses(ExpenseFilters(year=year, month=month))
        if not expenses:
            return "No expenses found for this period."

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=expenses[0].keys())
        writer.writeheader()
        writer.writerows(expenses)
        csv_str = output.getvalue()

        filename = os.path.join(REPORTS_DIR, f"expenses_{year}_{month:02d}.csv")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(csv_str)

        return f"CSV saved to {filename}\n\n" + csv_str

    @mcp.tool()
    def generate_excel(year: int, month: int) -> str:
        """
        Export all expenses for a given month to an Excel file (.xlsx).
        Returns the file path.
        """
        import os
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from src.config import REPORTS_DIR
        from src.schemas.expense import ExpenseFilters

        expenses = list_expenses(ExpenseFilters(year=year, month=month))
        if not expenses:
            return "No expenses found for this period."

        wb = Workbook()
        ws = wb.active
        ws.title = f"{year}-{month:02d}"

        # Header row with styling
        headers = list(expenses[0].keys())
        header_fill = PatternFill("solid", fgColor="4472C4")
        header_font = Font(color="FFFFFF", bold=True)
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h.replace("_", " ").title())
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        # Data rows
        for row_idx, exp in enumerate(expenses, 2):
            for col_idx, key in enumerate(headers, 1):
                ws.cell(row=row_idx, column=col_idx, value=exp.get(key))

        # Auto-width columns
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

        filename = os.path.join(REPORTS_DIR, f"expenses_{year}_{month:02d}.xlsx")
        wb.save(filename)
        return f"Excel report saved to: {filename}"
