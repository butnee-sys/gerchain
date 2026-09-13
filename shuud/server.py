"""Integrated SHUUD server entrypoint."""

from pathlib import Path

from fastapi.staticfiles import StaticFiles

from gerchain.web_ui import app as gerchain_app

from .api import router as shuud_router
from .case_api import router as shuud_case_router
from .case_intake_api import router as shuud_case_intake_router
from .kpi_api import router as shuud_kpi_router
from .command_api import router as shuud_command_router

app = gerchain_app

if not any(getattr(route, "path", None) == "/api/v1/shuud/incidents" for route in app.routes):
    app.include_router(shuud_router)

if not any(getattr(route, "path", None) == "/api/v1/shuud/incidents/{incident_id}" for route in app.routes):
    app.include_router(shuud_case_router)

if not any(getattr(route, "path", None) == "/api/v1/shuud/sandbox/kpi" for route in app.routes):
    app.include_router(shuud_kpi_router)

if not any(getattr(route, "path", None) == "/api/v1/shuud/sandbox/command" for route in app.routes):
    app.include_router(shuud_command_router)

if not any(
    getattr(route, "path", None) == "/api/v1/shuud/sandbox/config/{sandbox_id}/cases/{incident_id}"
    for route in app.routes
):
    app.include_router(shuud_case_intake_router)

prototype_dir = Path(__file__).resolve().parent.parent / "prototype"
if prototype_dir.is_dir():
    if not any(getattr(route, "path", None) == "/shuud-demo" for route in app.routes):
        app.mount("/shuud-demo", StaticFiles(directory=str(prototype_dir), html=True), name="shuud-demo")
    if not any(getattr(route, "path", None) == "/shuud-ops" for route in app.routes):
        app.mount("/shuud-ops", StaticFiles(directory=str(prototype_dir), html=True), name="shuud-ops")

__all__ = ["app"]
