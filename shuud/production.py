"""Production persistence bootstrap for SHUUD.

This module owns configuration and durable publication wiring only. It does
not become an authority for incident decisions, WitnessChain, or escrow state.
"""

from __future__ import annotations

import os

# Import the outbox model before schema initialization so its table is included
# in SHUUDPersistenceBase.metadata. The outbox is delivery infrastructure only.
from . import publication_outbox  # noqa: F401
from .persistence import create_persistence_engine, initialize_schema
from .persistence_adapter import SQLAlchemySettlementPersistence


class ProductionConfigurationError(RuntimeError):
    """Raised when production persistence configuration is unsafe or incomplete."""


def create_production_persistence(*, database_url: str | None = None):
    """Create and initialize the durable production settlement adapter.

    Production requires an explicit SQLAlchemy backend and database URL. The
    returned adapter only publishes already-authoritative domain facts.

    The production API remains fail-closed until the durable settlement path is
    explicitly enabled. An explicit SQLite URL may therefore be used by the
    isolated bootstrap/integration tests without becoming a production default.
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
