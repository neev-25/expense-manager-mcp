"""
server.py — The main FastMCP entry point.

Uses streamable-http so Claude/ChatGPT can reach the server by URL.
Identifies the user from (in order):
  1. X-User-Email header
  2. ?email= query param
  3. DEFAULT_USER_EMAIL env var (needed for ChatGPT / Claude web, which
     have no custom-header field)
"""
import builtins
import functools
import sys
from urllib.parse import parse_qs

builtins.print = functools.partial(builtins.print, file=sys.stderr)
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP
from starlette.responses import JSONResponse

from src.config import APP_NAME, APP_VERSION, DEFAULT_USER_EMAIL
from src.database.db import init_db
from src.database.migrations import run_migrations
from src.auth.user_context import resolve_user

# Create the shared MCP instance (streamable-http gives us an HTTP endpoint)
mcp = FastMCP(f"{APP_NAME} v{APP_VERSION}")


# ── Auth Middleware ────────────────────────────────────────────────────────────
# Pure ASGI middleware (not BaseHTTPMiddleware) so the user ContextVar is
# visible to FastMCP tool handlers on the same request.
class UserEmailMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or ""
        if path in ("/health", "/"):
            await self.app(scope, receive, send)
            return

        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in scope.get("headers", [])
        }
        email = headers.get("x-user-email", "").strip()
        if not email:
            qs = parse_qs(scope.get("query_string", b"").decode("latin-1"))
            email = (qs.get("email") or [""])[0].strip()
        if not email:
            email = DEFAULT_USER_EMAIL

        if not email:
            response = JSONResponse(
                status_code=401,
                content={
                    "error": (
                        "No user email. Set DEFAULT_USER_EMAIL on the server, "
                        "or send header X-User-Email / query ?email="
                    )
                },
            )
            await response(scope, receive, send)
            return

        try:
            resolve_user(email)
        except Exception as exc:
            response = JSONResponse(status_code=500, content={"error": str(exc)})
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


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
    print(f"[{APP_NAME}] Starting up...", file=sys.stderr)
    init_db()
    run_migrations()
    print(f"[{APP_NAME}] All systems ready ✅", file=sys.stderr)


if __name__ == "__main__":
    startup()
    app = UserEmailMiddleware(mcp.http_app(path="/mcp"))

    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
