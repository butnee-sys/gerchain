"""SHUUD Web + API application."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .shuud_api import router as shuud_router


def create_app() -> FastAPI:
    app = FastAPI(title="SHUUD", version="0.3.0", description="2 минутын дотор замаа чөлөөл")
    app.include_router(shuud_router)
    app.mount("/", StaticFiles(directory=Path(__file__).parent / "ui", html=True), name="shuud-web")
    return app

app = create_app()
