"""Production persistence bootstrap for SHUUD.

This module owns configuration and durable publication wiring only. It does
not become an authority for incident decisions, WitnessChain, or escrow state.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

# Import the outbox model before schema initialization so its table is included
# in SHUUDPersistenceBase.metadata. The outbox is delivery infrastructure only.
from . import publication_outbox  # noqa: F401
from .persistence import create_persistence_engine, initialize_schema
from .persistence_adapter import SQLAlchemySettlementPersistence


class ProductionConfigurationError(RuntimeError):
    """Raised when production persistence configuration is unsafe or incomplete."""


def _require_production_database_url(url: str) -> None:
    """Reject local/file databases from the production settlement boundary."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in {"postgresql", "postgresql+psycopg", "postgresql+psycopg2"}:
        raise ProductionConfigurationError(
            "production persistence requires a PostgreSQL SQLAlchemy URL"
        )
    if not parsed.hostname:
        raise ProductionConfigurationError(
            "production PostgreSQL URL must include a database host"
        )


def create_production_persistence(*, database_url: str | None = None):
    """Create and initialize the durable production settlement adapter.

    Production requires an explicit PostgreSQL SQLAlchemy backend and database
    URL. The returned adapter only publishes already-authoritative domain facts.
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
    _require_production_database_url(url)

    engine = create_persistence_engine(url)
    initialize_schema(engine)
    return SQLAlchemySettlementPersistence(engine)


__all__ = ["ProductionConfigurationError", "create_production_persistence"]
