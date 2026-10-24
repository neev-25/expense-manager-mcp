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

This server is hosted on **FastMCP Cloud**, so there's nothing to install — you just point your assistant at the server URL below.

> Replace `https://your-project.fastmcp.app/mcp` with your actual FastMCP Cloud deployment URL throughout this section.

### Connect with Claude (Desktop, Web, or Mobile)

1. Open **Settings → Connectors** in Claude (web/desktop) or ask Claude to open its connector settings.
2. Click **Add custom connector**.
3. Paste the server URL: `https://your-project.fastmcp.app/mcp`
4. Give it a name, e.g. `Smart Expense`.
5. Save, then enable it for your conversation.
6. Start chatting — e.g. *"Add a ₹200 coffee expense today, paid by cash."*

**Claude Desktop (local config) alternative** — add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "smart-expense-mcp": {
      "url": "https://expense-manager-mcp.fastmcp.app/mcp"
    }
  }
}
```

### Connect with ChatGPT

ChatGPT calls remote MCP servers through **Developer Mode** (currently available on Plus, Pro, Business, Enterprise, and Edu plans):

1. In ChatGPT, go to **Settings → Apps & Connectors → Advanced Settings**.
2. Toggle **Developer mode** ON.
3. Go back to **Apps**, click **Create**, and choose to add a custom app/connector.
4. Fill in:
   - **Name:** `Smart Expense`
   - **MCP server URL:** `https://expense-manager-mcp.fastmcp.app/mcp`
5. Click **Create**. ChatGPT will list the tools the server exposes.
6. In a new chat, click the **+** button → **More** → select **Smart Expense** to enable it for that conversation.
7. Start chatting — e.g. *"Show my quick stats for this month."*

> Note: the connector must be re-enabled per conversation — this is a ChatGPT behavior, not a limitation of this server.

---

## 🛠️ Local Development

If you want to run or modify the server yourself:

```bash
git clone https://github.com/<your-username>/expense-agent.git
cd expense-agent
uv sync
uv run python src/server.py
```

Then point Claude Desktop at your local instance:

```json
{
  "mcpServers": {
    "smart-expense-mcp": {
      "command": "uv",
      "args": ["run", "python", "src/server.py"],
      "cwd": "/path/to/expense-agent"
    }
  }
}
```

### Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `DB_DIR` | Directory where `expenses.db` is stored | project root (local) |
| `REPORTS_DIR` | Directory where generated CSV/Excel reports are saved | `<DB_DIR>/reports` |

> ⚠️ **On FastMCP Cloud**, the local filesystem is not guaranteed to persist across restarts/redeploys. For production use with real user data, back this server with a hosted database (e.g. Turso/libSQL or Postgres) rather than a local SQLite file. See [`docs/persistence.md`](docs/persistence.md) if you're migrating.

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
