"""
schemas/analytics.py — Response models for analytics and budget endpoints.
These exist mainly for documentation; the actual data comes from services.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class CategoryTotal(BaseModel):
    category: str
    total: float
    count: int
    percentage: float   # % of overall spending


class MonthlySummary(BaseModel):
    year: int
    month: int
    total: float
    count: int
    by_category: list[CategoryTotal]
    by_payment_method: dict
    top_merchant: Optional[str]
    avg_per_day: float


class BudgetStatus(BaseModel):
    category: str
    budget_amount: float
    spent: float
    remaining: float
    utilization_pct: float
    alert: str   # "ok" | "warning" | "danger"
