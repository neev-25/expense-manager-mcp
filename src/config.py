"""
config.py — Central configuration for the Smart Expense MCP.
All paths, constants, and enums live here so nothing is hard-coded elsewhere.
"""
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
# __file__ is src/config.py → go one level up to project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH     = os.path.join(ROOT_DIR, "expenses.db")
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# ── App Identity ───────────────────────────────────────────────────────────────
APP_NAME         = "SmartExpenseMCP"
APP_VERSION      = "1.0.0"
DEFAULT_CURRENCY = "INR"         # ISO 4217 code
CURRENCY_SYMBOL  = "₹"
TIMEZONE         = "Asia/Kolkata"

# ── Payment Methods (allowed values) ──────────────────────────────────────────
PAYMENT_METHODS = [
    "UPI",
    "Cash",
    "Credit Card",
    "Debit Card",
    "Net Banking",
    "Wallet",
    "Other",
]

# ── Split Types for Events ─────────────────────────────────────────────────────
SPLIT_TYPES = ["equal", "percentage", "custom"]

# ── Balance Directions ─────────────────────────────────────────────────────────
# "i_paid"   → I paid for the friend  (friend owes me)
# "they_paid" → Friend paid for me    (I owe the friend)
BALANCE_DIRECTIONS = ["i_paid", "they_paid"]

# ── Budget Alert Thresholds ────────────────────────────────────────────────────
BUDGET_WARNING_PCT  = 80   # 🟡 Yellow warning
BUDGET_DANGER_PCT   = 100  # 🔴 Over budget

# ── Recurring Frequencies ─────────────────────────────────────────────────────
RECURRING_FREQUENCIES = ["daily", "weekly", "monthly", "yearly"]
