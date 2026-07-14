"""
schemas/category.py — Pydantic models for category and subcategory operations.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name, e.g. 'Food'")
    icon: str = Field("💰", max_length=10, description="Emoji icon for display, e.g. '🍔'")


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = Field(None, max_length=10)


class SubcategoryCreate(BaseModel):
    category_id: int = Field(..., description="ID of the parent category")
    name: str = Field(..., min_length=1, max_length=100, description="Subcategory name, e.g. 'Restaurant'")


class SubcategoryMove(BaseModel):
    """Move a subcategory to a different parent category."""
    subcategory_id: int
    new_category_id: int
