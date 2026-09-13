"""SHUUD Web + API application."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import router as shuud_v1_router
from .shuud_api import router as shuud_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="SHUUD",
        version="0.4.0",
        description="2 минутын дотор замаа чөлөөл",
    )
    # Authoritative SHUUD application lifecycle.
    app.include_router(shuud_v1_router)
    # Keep the earlier compact API temporarily for backward compatibility.
    app.include_router(shuud_router)
    app.mount(
        "/",
        StaticFiles(directory=Path(__file__).parent / "ui", html=True),
        name="shuud-web",
    )
    return app


app = create_app()
