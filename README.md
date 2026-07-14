# 🧠 Smart Expense Management MCP

> An AI-powered MCP server for personal and group expense management — built with FastMCP + SQLite.

## Features

| Module | What it does |
|---|---|
| **Expenses** | Full CRUD, soft-delete/restore, tags, merchant, location, receipt URL |
| **Categories** | Dynamic categories & subcategories with emoji icons |
| **Filtering Engine** | 15+ dimensions: date, category, amount range, merchant, tags, payment method, event … |
| **Analytics** | Monthly/yearly summaries, category breakdown with %, budget utilization with alerts |
| **Splitwise (General)** | Record "I paid for X" / "X paid for me" — net balance tracking per friend |
| **Splitwise (Events)** | Group trips with equal/percentage/custom splits, auto-settlement computation |
| **Settlement Engine** | Greedy two-pointer algorithm — minimizes number of transactions |
| **Budgets** | Per-category monthly budgets with 🟢🟡🔴 alert levels |
| **Recurring Expenses** | Auto-create entries for Netflix, Rent, Gym, etc. |
| **Reports** | Export to CSV and Excel (.xlsx) |

---

## Project Structure

```
expense-agent/
├── src/
│   ├── server.py          ← FastMCP entry point
│   ├── config.py          ← All constants & paths
│   ├── database/
│   │   ├── db.py          ← Connection manager (context-manager)
│   │   ├── models.py      ← 11 table definitions
│   │   └── migrations.py  ← Default categories seed
│   ├── schemas/
│   │   ├── expense.py     ← ExpenseCreate, ExpenseUpdate, ExpenseFilters
│   │   ├── category.py    ← CategoryCreate, SubcategoryCreate
│   │   ├── splitwise.py   ← FriendCreate, BalanceCreate, EventExpenseCreate
│   │   └── analytics.py   ← Response shapes
│   ├── services/
│   │   ├── expense_service.py    ← CRUD + dynamic filter engine
│   │   ├── analytics_service.py  ← Summary, budget tracking
│   │   ├── split_service.py      ← Balances + event splits
│   │   └── settlement_service.py ← Minimal transactions algorithm
│   └── tools/
│       ├── expense_tools.py      ← MCP: create, get, update, delete, restore, list
│       ├── category_tools.py     ← MCP: categories & subcategories
│       ├── analytics_tools.py    ← MCP: summaries, budgets, recurring
│       ├── splitwise_tools.py    ← MCP: friends, balances, settle
│       ├── event_tools.py        ← MCP: events, splits, settlements
│       └── search_tools.py       ← MCP: search, quick_stats, CSV, Excel
└── reports/               ← Generated CSV / Excel files
```

---

## Running the Server

```powershell
cd d:\Neev\expense-agent
uv run python src/server.py
```

### Claude Desktop Config

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "smart-expense-mcp": {
      "command": "uv",
      "args": ["run", "python", "src/server.py"],
      "cwd": "d:\\Neev\\expense-agent"
    }
  }
}
```

---

## MCP Tools Reference

### Expense Tools (7)
| Tool | Description |
|---|---|
| `create_expense` | Add an expense with full metadata |
| `get_expense` | Get one expense by ID |
| `update_expense` | Update any fields of an expense |
| `delete_expense` | Soft-delete (recoverable) |
| `restore_expense` | Undo a delete |
| `list_expenses` | Filter by 15+ dimensions |

### Category Tools (6)
`create_category`, `update_category`, `delete_category`, `list_categories`, `create_subcategory`, `move_subcategory`

### Analytics Tools (6)
`expense_summary`, `monthly_summary`, `yearly_summary`, `payment_summary`, `budget_summary`, `set_budget`

### Recurring Tools (3)
`add_recurring`, `list_recurring`, `process_recurring`

### Splitwise Tools (6)
`add_friend`, `list_friends`, `record_balance`, `settle`, `friend_summary`, `overall_balance`

### Event Tools (5)
`create_event`, `add_event_member`, `add_event_expense`, `event_summary`, `close_event`

### Search & Report Tools (4)
`search_expenses`, `quick_stats`, `generate_csv`, `generate_excel`

---

## Example Conversations

```
You: "Add ₹450 expense at Domino's, Food category, paid via UPI, tags: dinner, friends"
→ create_expense(title="Domino's Pizza", amount=450, ...)

You: "How much did I spend on food this month?"
→ expense_summary(month=7, year=2026)

You: "I paid ₹600 for Rahul for petrol"
→ record_balance(friend_id=1, amount=600, direction="i_paid", reason="Petrol")

You: "Who owes me money?"
→ overall_balance()

You: "Create Girnar Trip event with Rahul, Prince, Jay"
→ create_event(title="Girnar Trip", member_ids=[1,2,3])

You: "Add ₹4000 hotel expense to Girnar Trip, paid by me, split equally"
→ add_event_expense(event_id=1, title="Hotel", amount=4000, paid_by_friend_id=0, split_type="equal")

You: "Who owes what in the Girnar trip?"
→ event_summary(event_id=1)  # computes minimum transactions automatically

You: "Set a ₹5000 budget for Food in July 2026"
→ set_budget(category_id=1, month=7, year=2026, amount=5000)

You: "Export July 2026 expenses to Excel"
→ generate_excel(year=2026, month=7)
```

---

## The Settlement Algorithm

The `event_summary` tool uses a **greedy two-pointer algorithm** to find the minimum number of transactions to settle all debts in a group.

```
A owes B ₹100,  B owes C ₹100
→ Instead of: A→B, B→C
→ Optimal:    A→C   (1 transaction instead of 2)
```

Call `explain_settlement_algorithm()` in Claude to get the full explanation.

---

## Dependencies

```toml
fastmcp>=3.4.4
pydantic>=2.0
openpyxl
python-dateutil
```
