"""
config.py — Central configuration for the Smart Expense MCP.
All paths, constants, and enums live here so nothing is hard-coded elsewhere.
"""
import os
from dotenv import load_dotenv

# Load variables from .env if present
load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
# __file__ is src/config.py → go one level up to project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NEON_DATABASE_URL = os.environ.get("NEON_DATABASE_URL", "")
REPORTS_DIR = os.environ.get("REPORTS_DIR", "/tmp/reports")
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

# "i_owe"   → I owe the friend
# "they_owe" → Friend owes me
BALANCE_DIRECTIONS = ["i_owe", "they_owe"]

# ── Budget Alert Thresholds ────────────────────────────────────────────────────
BUDGET_WARNING_PCT  = 80   # 🟡 Yellow warning
BUDGET_DANGER_PCT   = 100  # 🔴 Over budget

# ── Recurring Frequencies ─────────────────────────────────────────────────────
RECURRING_FREQUENCIES = ["daily", "weekly", "monthly", "yearly"]
