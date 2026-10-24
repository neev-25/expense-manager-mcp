"""
server.py — The main FastMCP entry point.

Changes vs. original:
 - Uses streamable-http transport (not stdio) so it is reachable via a URL.
 - Reads X-User-Email header on every request → resolves/creates user → sets
   per-request ContextVar so all service queries are scoped to that user.
"""
import builtins
import functools
import sys

builtins.print = functools.partial(builtins.print, file=sys.stderr)
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.config import APP_NAME, APP_VERSION
from src.database.db import init_db
from src.database.migrations import run_migrations
from src.auth.user_context import resolve_user

# Create the shared MCP instance (streamable-http gives us an HTTP endpoint)
mcp = FastMCP(f"{APP_NAME} v{APP_VERSION}")


# ── Auth Middleware ────────────────────────────────────────────────────────────
class UserEmailMiddleware(BaseHTTPMiddleware):
    """
    Reads the X-User-Email header from every incoming HTTP request.
    Resolves (or creates) the matching user row and stores the user_id in
    a ContextVar so every tool call in that request is automatically scoped.
    """
    async def dispatch(self, request: Request, call_next):
        # Health-check / non-MCP paths don't need auth
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        email = request.headers.get("X-User-Email", "").strip()
        if not email:
            return JSONResponse(
                status_code=401,
                content={
                    "error": (
                        "Missing X-User-Email header. "
                        "In your Claude custom connector settings add a header: "
                        "X-User-Email: your@email.com"
                    )
                }
            )

        try:
            resolve_user(email)
        except Exception as exc:
            return JSONResponse(status_code=500, content={"error": str(exc)})

        return await call_next(request)


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
    # Get the underlying Starlette app from FastMCP and wrap it with our middleware
    app = mcp.http_app(path="/mcp")
    app.add_middleware(UserEmailMiddleware)

    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
