"""SHUUD Web + API application."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import router as shuud_v1_router
from .case_intake_api import router as shuud_case_intake_router
from .command_api import router as shuud_command_router
from .kpi_api import router as shuud_kpi_router
from .shuud_api import router as shuud_router


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
    app.mount(
        "/",
        StaticFiles(directory=Path(__file__).parent / "ui", html=True),
        name="shuud-web",
    )
    return app


app = create_app()
