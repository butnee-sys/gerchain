"""Production persistence bootstrap for SHUUD.

This module owns configuration and durable publication wiring only. It does
not become an authority for incident decisions, WitnessChain, or escrow state.
"""

from __future__ import annotations

import os

from .persistence import create_persistence_engine, initialize_schema
from .persistence_adapter import SQLAlchemySettlementPersistence


class ProductionConfigurationError(RuntimeError):
    """Raised when production persistence configuration is unsafe or incomplete."""


def create_production_persistence(*, database_url: str | None = None):
    """Create and initialize the durable production settlement adapter.

    Production requires an explicit SQLAlchemy backend and database URL. The
    returned adapter only publishes already-authoritative domain facts.
    """
    runtime = os.getenv("SHUUD_RUNTIME_MODE", "sandbox").strip().lower()
    backend = os.getenv("SHUUD_PERSISTENCE_BACKEND", "memory").strip().lower()
    url = database_url or os.getenv("SHUUD_DATABASE_URL", "").strip()

    if runtime != "production":
        raise ProductionConfigurationError(
            "production persistence requires SHUUD_RUNTIME_MODE='production'"
        )
    if backend != "sqlalchemy":
        raise ProductionConfigurationError(
            "production persistence requires SHUUD_PERSISTENCE_BACKEND='sqlalchemy'"
        )
    if not url:
        raise ProductionConfigurationError(
            "SHUUD_DATABASE_URL is required for production persistence"
        )

    engine = create_persistence_engine(url)
    initialize_schema(engine)
    return SQLAlchemySettlementPersistence(engine)


__all__ = ["ProductionConfigurationError", "create_production_persistence"]
