"""
server.py — The main FastMCP entry point.

This file:
  1. Creates the shared FastMCP instance.
  2. Initialises the database (creates tables if not exists).
  3. Seeds default categories on first run.
  4. Registers all tool groups.
  5. Processes any overdue recurring expenses.
  6. Starts the MCP server (stdio transport for Claude Desktop).
"""
import builtins
import functools
import sys

builtins.print = functools.partial(builtins.print, file=sys.stderr)
import os

# Make sure `src` is importable when run from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP

from src.config import APP_NAME, APP_VERSION
from src.database.db import init_db
from src.database.migrations import run_migrations

# Create the shared MCP instance
mcp = FastMCP(f"{APP_NAME} v{APP_VERSION}")

# ── Register all tool groups ───────────────────────────────────────────────────
from src.tools import expense_tools
from src.tools import category_tools
from src.tools import analytics_tools
from src.tools import splitwise_tools
from src.tools import event_tools
from src.tools import search_tools

expense_tools.register(mcp)
category_tools.register(mcp)
analytics_tools.register(mcp)
splitwise_tools.register(mcp)
event_tools.register(mcp)
search_tools.register(mcp)

# ── Startup tasks ──────────────────────────────────────────────────────────────
def startup():
    print(f"[{APP_NAME}] Starting up...",file=sys.stderr)
    init_db()
    run_migrations()
    print(f"[{APP_NAME}] All systems ready ✅",file=sys.stderr)

if __name__ == "__main__":
    startup()
    mcp.run()
