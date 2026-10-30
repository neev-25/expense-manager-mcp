# 💰 Smart Expense — AI-Powered Expense Management MCP

Track expenses, split bills with friends, manage group trips, and get spending analytics — all through natural conversation with **Claude** or **ChatGPT**.

No app to open, no forms to fill. Just talk.

Built with **FastMCP + Python + Neon PostgreSQL**, and hosted on **Render**.

---

## ✨ What You Can Do

Just talk to Claude or ChatGPT naturally:

> "Add ₹450 expense at Domino's, Food category, paid via UPI, tags: dinner, friends."

> "How much did I spend on food this month?"

> "I paid ₹600 for Rahul for petrol."

> "Who owes me money?"

> "Create a Girnar Trip event with Rahul, Prince, and Jay."

> "Add ₹4000 hotel expense to Girnar Trip, split equally."

> "Who owes what in the Girnar trip?"

> "Set a ₹5000 budget for Food in July 2026."

> "Export July 2026 expenses to Excel."

The AI assistant understands your request, selects the appropriate MCP tool, and performs the operation.

---

## 🧩 Features

| Module | What it does |
|---|---|
| **Expenses** | Full CRUD, soft-delete/restore, tags, merchant, location, receipt URL |
| **Categories** | Dynamic categories and subcategories with emoji icons |
| **Filtering Engine** | 15+ dimensions — date, category, amount range, merchant, tags, payment method, event |
| **Analytics** | Monthly/yearly summaries, category breakdown with percentages, budget utilization and alerts |
| **Splitwise (General)** | Record "I paid for X" / "X paid for me" with net balance tracking per friend |
| **Splitwise (Events)** | Group trips with equal, percentage, and custom splits |
| **Settlement Engine** | Greedy two-pointer algorithm to minimize settle-up transactions |
| **Budgets** | Per-category monthly budgets with 🟢 🟡 🔴 alert levels |
| **Recurring Expenses** | Manage recurring entries for Netflix, rent, gym, etc. |
| **Reports** | Export expenses to CSV and Excel (`.xlsx`) |

---

## 🚀 Live Deployment

<details>
<summary>Deployment information</summary>

**Hosting:** Render

**MCP Server URL:**

```text
https://expense-manager-mcp.onrender.com/mcp
```

**Database:** Neon PostgreSQL

**Protocol:** MCP over Streamable HTTP

</details>

The MCP server is hosted on Render, so you don't need to clone the repository or install Python dependencies to connect your AI assistant.

Simply use the MCP URL above when configuring your connector.

---

## 🔌 Connect to Your AI Assistant

### 1. Connect with Claude

You can connect Smart Expense to Claude using a custom connector.

1. Open Claude.
2. Navigate to **Settings → Connectors**.
3. Select **Add custom connector**.
4. Enter the following details:

   **Name:**
   ```text
   Smart Expense
   ```

   **MCP Server URL:**
   ```text
   https://expense-manager-mcp.onrender.com/mcp
   ```

5. Save the connector.
6. Enable Smart Expense for your conversation.
7. Start chatting!

**Try this prompt:**

```text
Add a ₹200 coffee expense today, paid by cash.
```

Claude will connect to your deployed MCP server and use its available tools.

### Claude Desktop — Alternative Configuration

You can also configure the MCP server through Claude Desktop's configuration file.

Open `claude_desktop_config.json` and add:

```json
{
  "mcpServers": {
    "smart-expense-mcp": {
      "url": "https://expense-manager-mcp.onrender.com/mcp"
    }
  }
}
```

Save the configuration and restart Claude Desktop.

---

### 2. Connect with ChatGPT

ChatGPT supports custom remote MCP apps through Developer Mode on supported plans and workspaces.

Follow these steps:

**Step 1: Enable Developer Mode**

1. Open ChatGPT.
2. Navigate to **Settings → Apps & Connectors → Advanced Settings**.
3. Enable **Developer Mode**, if available.

**Step 2: Create a Custom App**

1. Open the Apps section.
2. Select **Create**.
3. Choose the option to create a custom app or connector.

**Step 3: Enter MCP Details**

Use the following configuration:

**App Name:**
```text
Smart Expense
```

**MCP Server URL:**
```text
https://expense-manager-mcp.onrender.com/mcp
```

4. Save and create the app.
5. ChatGPT will discover the tools exposed by the MCP server.

**Step 4: Start Using Smart Expense**

1. Open a new conversation.
2. Select the `+` button.
3. Open **More** and select **Smart Expense**.
4. Start interacting with your expense management server.

**Try this prompt:**

```text
Show my quick stats for this month.
```

ChatGPT will use the connected MCP tools to retrieve the relevant information.

> Note: Developer Mode and custom MCP app availability depend on your ChatGPT plan and workspace settings. The exact interface may vary.

---

## ⚠️ Important: Current Multi-User Limitation

**Please read this before using the application with real financial data.**

Currently, Smart Expense uses a shared database.

This means:

- All connected users access the same Neon PostgreSQL database.
- User-level data isolation has not yet been implemented.
- Expenses and financial records are not independently separated for each user.
- Different users may be able to access or modify records belonging to others.

**Planned improvement:**

Implement proper multi-user authentication and database-level user isolation so that every user can access only their own expenses, friends, budgets, events, and financial records.

Until this improvement is implemented and verified, this deployment should be treated as a development/demo application.

**Do not use it for confidential or sensitive financial information.**

---

## 🛠️ Local Development

If you want to run or modify the server yourself:

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Neon PostgreSQL database
- Git

### Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/expense-agent.git

cd expense-agent
```

Install dependencies:

```bash
uv sync
```

Configure the database connection and other required environment variables according to the project's configuration.

Run the MCP server:

```bash
uv run python src/server.py
```

The server will start locally.

Use the local MCP endpoint configured by your FastMCP server when connecting your development assistant.

---

## ☁️ Deployment Architecture

Smart Expense uses the following architecture:

```text
        Claude / ChatGPT
               |
               |
          MCP Protocol
               |
               |
       Render Web Service
               |
               |
       FastMCP Server
               |
               |
      Application Services
               |
               |
       Neon PostgreSQL
               |
               |
       Persistent Database
```

### Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| FastMCP 3.4.4+ | MCP server and tool integration |
| Pydantic 2 | Data validation and schemas |
| Neon PostgreSQL | Hosted relational database |
| Render | Application hosting |
| openpyxl | Excel report generation |
| python-dateutil | Date handling |

---

## 📁 Project Structure

```text
expense-agent/
│
├── src/
│   ├── server.py                 # FastMCP entry point
│   ├── config.py                 # Constants and configuration
│   │
│   ├── database/
│   │   ├── db.py                 # Database connection manager
│   │   ├── models.py             # Database table definitions
│   │   └── migrations.py         # Database migrations and seeds
│   │
│   ├── schemas/
│   │   ├── expense.py            # Expense schemas
│   │   ├── category.py           # Category schemas
│   │   ├── splitwise.py          # Friends and event schemas
│   │   └── analytics.py          # Analytics response schemas
│   │
│   ├── services/
│   │   ├── expense_service.py    # Expense CRUD and filtering
│   │   ├── analytics_service.py  # Summaries and budgets
│   │   ├── split_service.py      # Friend balances and splits
│   │   └── settlement_service.py # Settlement algorithm
│   │
│   └── tools/
│       ├── expense_tools.py      # Expense MCP tools
│       ├── category_tools.py     # Category MCP tools
│       ├── analytics_tools.py    # Analytics and budgets
│       ├── splitwise_tools.py    # Friend and balance tools
│       ├── event_tools.py        # Event and group tools
│       └── search_tools.py       # Search, stats and reports
│
└── reports/                      # Generated reports (local)
```

---

## 📚 MCP Tools Reference

### Expense Tools

| Tool | Description |
|---|---|
| `create_expense` | Add an expense with full metadata |
| `get_expense` | Get an expense by ID |
| `update_expense` | Update expense information |
| `delete_expense` | Soft-delete an expense |
| `restore_expense` | Restore a deleted expense |
| `list_expenses` | Filter expenses using 15+ dimensions |

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

## 🧮 Settlement Algorithm

Smart Expense uses a **Greedy Two-Pointer Algorithm** to minimize the number of transactions required to settle group debts.

**Example:**

Suppose:

- A owes B ₹100.
- B owes C ₹100.

A naive settlement would be:

```text
A → B : ₹100
B → C : ₹100
```

But the optimized settlement is:

```text
A → C : ₹100
```

Instead of two transactions, only one transaction is required.

The algorithm works by separating people with positive and negative balances, sorting them, and repeatedly settling the smaller outstanding amount.

Ask your assistant:

```text
Explain the settlement algorithm with an example.
```

---

## 📦 Dependencies

Main dependencies:

```toml
fastmcp>=3.4.4
pydantic>=2.0
openpyxl
python-dateutil
```

Additional PostgreSQL driver and database dependencies are managed through the project's dependency configuration.

---

## 🔒 Data & Privacy

Smart Expense uses Neon PostgreSQL as its hosted database.

Important considerations:

- Database credentials should be stored in environment variables.
- Never commit `.env` files or database credentials to GitHub.
- Keep database connection strings private.
- Use appropriate database backups and access controls.
- Do not expose sensitive financial information through public deployments.
- Multi-user data isolation is not implemented yet.

The current deployment is intended for development and demonstration until proper user authentication and data isolation are implemented.

---

## 🚀 Future Improvements

- [ ] User authentication and authorization.
- [ ] Individual user-level database isolation.
- [ ] Secure multi-user expense management.
- [ ] Improved recurring expense automation.
- [ ] Advanced spending insights and AI recommendations.
- [ ] More detailed financial reports.
- [ ] Improved dashboard and visualization support.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

**Built with ❤️ using FastMCP, Python, and Neon PostgreSQL.**

