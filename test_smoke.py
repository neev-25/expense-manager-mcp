"""Quick smoke test for the Smart Expense MCP (multi-user build)."""
import sys
sys.path.insert(0, ".")

# ── Fake auth context ──────────────────────────────────────────────────────────
# In production the middleware sets this from the X-User-Email header.
# In tests we set it directly after creating/resolving a user.
from src.database.db import init_db
from src.database.migrations import run_migrations
init_db()
run_migrations()

from src.auth.user_context import get_or_create_user, resolve_user
resolve_user("test@example.com")   # sets ContextVar for this thread

# ── Import service layer AFTER setting user context ────────────────────────────
from src.services.expense_service import create_expense, get_expense, list_expenses, delete_expense, restore_expense
from src.schemas.expense import ExpenseCreate, ExpenseFilters

exp = create_expense(ExpenseCreate(
    title="Domino's Pizza", amount=450, expense_date="2026-07-14",
    merchant="Domino's", payment_method="UPI", tags="dinner,friends"
))
print(f"✅ Created expense id={exp['id']}: {exp['title']} ₹{exp['amount']}")

fetched = get_expense(exp["id"])
assert fetched["title"] == "Domino's Pizza"
print("✅ get_expense OK")

results = list_expenses(ExpenseFilters(merchant="Domino", payment_method="UPI"))
assert len(results) >= 1
print(f"✅ list_expenses filter OK: {len(results)} result(s)")

delete_expense(exp["id"])
deleted = list_expenses(ExpenseFilters(include_deleted=False))
assert all(e["id"] != exp["id"] for e in deleted)
print("✅ soft-delete OK")

restore_expense(exp["id"])
restored = get_expense(exp["id"])
assert restored["is_deleted"] == 0
print("✅ restore OK")

# ── Analytics ─────────────────────────────────────────────────────────────────
from src.services.analytics_service import monthly_summary, set_budget, budget_summary
summary = monthly_summary(2026, 7)
print(f"✅ monthly_summary: total=₹{summary['total']}, count={summary['count']}")

from src.database.db import get_connection
from src.database.db import get_current_user_id
uid = get_current_user_id()
with get_connection() as c:
    cat_id = c.execute("SELECT id FROM categories WHERE name='Food' AND user_id=%s", (uid,)).fetchone()["id"]

set_budget(cat_id, 7, 2026, 5000)
bs = budget_summary(2026, 7)
print(f"✅ budget_summary: {bs}")

# ── Settlement algorithm ───────────────────────────────────────────────────────
from src.services.settlement_service import compute_minimal_settlements
net = {1: -100, 2: -50, 3: 150.0}
names = {1: "A", 2: "B", 3: "C"}
txns = compute_minimal_settlements(net, names)
print(f"✅ Settlement: {[t['display'] for t in txns]}")
assert len(txns) == 2

# ── Events (isolation test: second user shouldn't see first user's events) ────
from src.services.split_service import add_friend, create_event, add_event_expense, event_summary
from src.schemas.splitwise import FriendCreate, EventCreate, EventExpenseCreate

r = add_friend(FriendCreate(name="Rahul"))
p = add_friend(FriendCreate(name="Prince"))
j = add_friend(FriendCreate(name="Jay"))

event = create_event(EventCreate(
    title="Girnar Trip", member_ids=[r["id"], p["id"], j["id"]]
))
eid = event["event_id"]

add_event_expense(EventExpenseCreate(
    event_id=eid, title="Hotel", amount=3000,
    paid_by_friend_id=r["id"], split_type="equal"
))
add_event_expense(EventExpenseCreate(
    event_id=eid, title="Food", amount=600,
    paid_by_friend_id=p["id"], split_type="equal"
))

ev_summary = event_summary(eid)
print(f"✅ event_summary total=₹{ev_summary['total_spent']}")
print(f"   Settlements: {[s['display'] for s in ev_summary['settlements']]}")

# ── Isolation check: second user sees no data ─────────────────────────────────
resolve_user("other@example.com")
other_expenses = list_expenses(ExpenseFilters())
assert len(other_expenses) == 0, f"Expected 0 for other user, got {len(other_expenses)}"
print("✅ Isolation check: other user sees 0 expenses ✅")

print("\n🎉 All smoke tests passed!")
