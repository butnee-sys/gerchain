"""Small SHUUD application adapter for the existing FastAPI service."""

from fastapi import FastAPI

from .shuud_api import router as shuud_router


def create_app() -> FastAPI:
    app = FastAPI(title="SHUUD", version="0.1.0")
    app.include_router(shuud_router)
    return app


app = create_app()
