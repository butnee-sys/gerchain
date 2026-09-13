"""SHUUD Web + API application."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import router as shuud_v1_router
from .case_intake_api import router as shuud_case_intake_router
from .command_api import router as shuud_command_router
from .kpi_api import router as shuud_kpi_router
from .shuud_api import router as shuud_router


UI_DIR = Path(__file__).parent / "ui"


def create_app() -> FastAPI:
    app = FastAPI(
        title="SHUUD",
        version="0.5.0",
        description="2 минутын дотор замаа чөлөөл",
    )
    app.include_router(shuud_v1_router)
    app.include_router(shuud_kpi_router)
    app.include_router(shuud_command_router)
    app.include_router(shuud_case_intake_router)
    app.include_router(shuud_router)

    @app.get("/shuud", include_in_schema=False)
    def shuud_home() -> FileResponse:
        return FileResponse(UI_DIR / "index.html")

    @app.get("/shuud/app", include_in_schema=False)
    def shuud_app() -> FileResponse:
        return FileResponse(UI_DIR / "mobile.html")

    @app.get("/shuud/management", include_in_schema=False)
    def shuud_management() -> FileResponse:
        return FileResponse(UI_DIR / "kpi-panel.html")

    @app.get("/shuud/sandbox", include_in_schema=False)
    def shuud_sandbox() -> FileResponse:
        return FileResponse(UI_DIR / "sandbox.html")

    app.mount(
        "/",
        StaticFiles(directory=UI_DIR, html=True),
        name="shuud-web",
    )
    return app


app = create_app()
