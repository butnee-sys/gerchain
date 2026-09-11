"""Integrated SHUUD server entrypoint.

This keeps the existing GerChain dashboard application intact while mounting
SHUUD routes on the same FastAPI application. It is an integration adapter,
not a replacement for GerChain's core engines.

Run with:
    python -m uvicorn shuud.server:app --host 0.0.0.0 --port 8000
"""

from gerchain.web_ui import app as gerchain_app

from .api import router as shuud_router

app = gerchain_app

# Mount SHUUD only once when this integration entrypoint is imported.
if not any(getattr(route, "path", None) == "/api/v1/shuud/incidents" for route in app.routes):
    app.include_router(shuud_router)

__all__ = ["app"]
