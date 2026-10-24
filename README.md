# 💰 Smart Expense — AI-Powered Expense Management MCP

Track expenses, split bills with friends, manage group trips, and get spending analytics — all through natural conversation with **Claude** or **ChatGPT**. No app to open, no forms to fill. Just talk.

Built with [FastMCP](https://gofastmcp.com) + SQLite, and hosted on **FastMCP Cloud**.

---

## ✨ What You Can Do

Just talk to Claude or ChatGPT naturally:

> "Add ₹450 expense at Domino's, Food category, paid via UPI, tags: dinner, friends"
> "How much did I spend on food this month?"
> "I paid ₹600 for Rahul for petrol"
> "Who owes me money?"
> "Create a Girnar Trip event with Rahul, Prince, and Jay"
> "Add ₹4000 hotel expense to Girnar Trip, split equally"
> "Who owes what in the Girnar trip?"
> "Set a ₹5000 budget for Food in July 2026"
> "Export July 2026 expenses to Excel"

The assistant figures out which tool to call and handles the rest.

---

## 🧩 Features

| Module | What it does |
|---|---|
| **Expenses** | Full CRUD, soft-delete/restore, tags, merchant, location, receipt URL |
| **Categories** | Dynamic categories & subcategories with emoji icons |
| **Filtering Engine** | 15+ dimensions — date, category, amount range, merchant, tags, payment method, event |
| **Analytics** | Monthly/yearly summaries, category breakdown with %, budget utilization with alerts |
| **Splitwise (General)** | Record "I paid for X" / "X paid for me" — net balance tracking per friend |
| **Splitwise (Events)** | Group trips with equal / percentage / custom splits, auto-settlement computation |
| **Settlement Engine** | Greedy two-pointer algorithm — minimizes the number of settle-up transactions |
| **Budgets** | Per-category monthly budgets with 🟢 🟡 🔴 alert levels |
| **Recurring Expenses** | Auto-create entries for Netflix, Rent, Gym, etc. |
| **Reports** | Export to CSV and Excel (`.xlsx`) |

---

## 🚀 Quick Start — Connect to Your Assistant

This server is hosted and exposes an HTTP endpoint. Each user is identified by their **email address** sent as a custom header — no signup, no password.

### Connect with Claude (Web, Desktop, or Mobile)

1. Open **Settings → Connectors** in Claude.
2. Click **Add custom connector**.
3. Paste the server URL: `https://your-deployed-url/mcp`
4. Add a custom header:
   - **Name:** `X-User-Email`
   - **Value:** `your@email.com`
5. Give it a name, e.g. `Smart Expense`, and save.
6. Enable it for your conversation and start chatting.

> 💡 **Your data is completely private.** Each unique email address gets its own isolated slice of the database. No other user can see or affect your expenses.

**Claude Desktop (`claude_desktop_config.json`) alternative:**

```json
{
  "mcpServers": {
    "smart-expense-mcp": {
      "url": "https://your-deployed-url/mcp",
      "headers": {
        "X-User-Email": "your@email.com"
      }
    }
  }
}
```

### Connect with ChatGPT

1. Go to **Settings → Apps & Connectors → Advanced Settings** and enable **Developer mode**.
2. Create a new connector with MCP server URL: `https://your-deployed-url/mcp`
3. Add header `X-User-Email: your@email.com`.
4. Enable it per conversation via the **+** button.

> Note: the connector must be re-enabled per conversation — this is a ChatGPT behavior.

---

## 🛠️ Local Development

```bash
git clone https://github.com/<your-username>/expense-agent.git
cd expense-agent
uv sync
uv run python src/server.py   # starts HTTP server on port 8000
```

For first-time Neon setup (run once):
```bash
uv run python migrate_add_user_id.py
# Optional: attribute any pre-existing rows to an email:
uv run python migrate_add_user_id.py --attribute=your@email.com
```

Then point Claude Desktop at your local instance:

```json
{
  "mcpServers": {
    "smart-expense-mcp": {
      "url": "http://localhost:8000/mcp",
      "headers": { "X-User-Email": "your@email.com" }
    }
  }
}
```

### Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `NEON_DATABASE_URL` | Postgres connection string | required |
| `REPORTS_DIR` | Directory for CSV/Excel reports | `/tmp/reports` |
| `PORT` | HTTP server port | `8000` |

---

## 📁 Project Structure

```
expense-agent/
├── src/
│   ├── server.py                 ← FastMCP entry point
│   ├── config.py                 ← All constants & paths
│   ├── database/
│   │   ├── db.py                 ← Connection manager (context-manager)
│   │   ├── models.py             ← 11 table definitions
│   │   └── migrations.py         ← Default categories seed
│   ├── schemas/
│   │   ├── expense.py            ← ExpenseCreate, ExpenseUpdate, ExpenseFilters
│   │   ├── category.py           ← CategoryCreate, SubcategoryCreate
│   │   ├── splitwise.py          ← FriendCreate, BalanceCreate, EventExpenseCreate
│   │   └── analytics.py          ← Response shapes
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
└── reports/                       ← Generated CSV / Excel files (local dev only)
```

---

## 📚 MCP Tools Reference

### Expense Tools
| Tool | Description |
|---|---|
| `create_expense` | Add an expense with full metadata |
| `get_expense` | Get one expense by ID |
| `update_expense` | Update any fields of an expense |
| `delete_expense` | Soft-delete (recoverable) |
| `restore_expense` | Undo a delete |
| `list_expenses` | Filter by 15+ dimensions |

### Category Tools
`create_category` · `update_category` · `delete_category` · `list_categories` · `create_subcategory` · `move_subcategory`

### Analytics Tools
`expense_summary` · `monthly_summary` · `yearly_summary` · `payment_summary` · `budget_summary` · `set_budget`

### Recurring Tools
`add_recurring` · `list_recurring` · `process_recurring`

### Splitwise Tools
`add_friend` · `list_friends` · `record_balance` · `settle` · `friend_summary` · `overall_balance`

### Event Tools
`create_event` · `add_event_member` · `add_event_expense` · `event_summary` · `close_event`

### Search & Report Tools
`search_expenses` · `quick_stats` · `generate_csv` · `generate_excel`

---

## 🧮 The Settlement Algorithm

`event_summary` uses a **greedy two-pointer algorithm** to minimize the number of transactions needed to settle all debts in a group:

```
A owes B ₹100,  B owes C ₹100
→ Naive:    A → B, B → C            (2 transactions)
→ Optimal:  A → C                    (1 transaction)
```

Ask your assistant to *"explain the settlement algorithm"* for the full walkthrough.

---

## 📦 Dependencies

```toml
fastmcp>=3.4.4
pydantic>=2.0
openpyxl
python-dateutil
```

---

## 🔒 Data & Privacy

This server stores your expense data in a database controlled by the deployment. Do not commit database files (`expenses.db`, `*.db-wal`, `*.db-shm`) to version control — see `.gitignore`. If you're hosting this for multiple users, review your storage backend's data isolation and backup guarantees before relying on it for real financial records.

## 📄 License

MIT — see [`LICENSE`](LICENSE) for details.
