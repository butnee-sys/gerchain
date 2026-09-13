"""Integrated SHUUD server entrypoint.

This keeps the existing GerChain dashboard application intact while mounting
SHUUD routes and the presentation prototype on the same FastAPI application.
The presentation mounts are integration adapters, not replacements for
GerChain's core engines.

Run with:
    python -m uvicorn shuud.server:app --host 0.0.0.0 --port 8000
"""

from pathlib import Path

from fastapi.staticfiles import StaticFiles

from gerchain.web_ui import app as gerchain_app

from .api import router as shuud_router
from .kpi_api import router as shuud_kpi_router

app = gerchain_app

# Mount SHUUD only once when this integration entrypoint is imported.
if not any(getattr(route, "path", None) == "/api/v1/shuud/incidents" for route in app.routes):
    app.include_router(shuud_router)

if not any(getattr(route, "path", None) == "/api/v1/shuud/sandbox/kpi" for route in app.routes):
    app.include_router(shuud_kpi_router)

# Serve the SHUUD presentation UIs from the same origin as the API so browser
# demos can use the real sandbox/API without CORS or a second server.
prototype_dir = Path(__file__).resolve().parent.parent / "prototype"
if prototype_dir.is_dir():
    if not any(getattr(route, "path", None) == "/shuud-demo" for route in app.routes):
        app.mount(
            "/shuud-demo",
            StaticFiles(directory=str(prototype_dir), html=True),
            name="shuud-demo",
        )
    if not any(getattr(route, "path", None) == "/shuud-ops" for route in app.routes):
        app.mount(
            "/shuud-ops",
            StaticFiles(directory=str(prototype_dir), html=True),
            name="shuud-ops",
        )

__all__ = ["app"]
