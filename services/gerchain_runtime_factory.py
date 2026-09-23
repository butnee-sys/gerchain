from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from postgres.migrations import apply_migrations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime import GerchainRuntime


@dataclass(frozen=True)
class ProductionRuntimeConfig:
    database_url: str
    escrow_id: str
    amount: int
    currency: str
    witness_id: str


class ProductionRuntimeFactory:
    """Create a GerChain runtime whose authoritative value path is PostgreSQL Canonical Ledger."""

    def __init__(self, config: ProductionRuntimeConfig, *, engine: Engine | None = None) -> None:
        if not config.database_url:
            raise ValueError("database_url is required")
        if not config.database_url.startswith(("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")):
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL database URL")
        self.config = config
        self.engine = engine or create_engine(config.database_url, future=True)
        if self.engine.dialect.name != "postgresql":
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL engine")
        self.session_factory: Callable[[], Any] = sessionmaker(bind=self.engine, expire_on_commit=False)

    def initialize(self) -> None:
        """Apply the repository's versioned PostgreSQL production schema."""
        migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
        with self.engine.connect() as conn:
            apply_migrations(conn, migration_dir)

    def create(self) -> GerchainRuntime:
        self.initialize()
        runtime = GerchainRuntime(
            escrow_id=self.config.escrow_id,
            amount=self.config.amount,
            currency=self.config.currency,
            witness_id=self.config.witness_id,
        )
        runtime.configure_canonical_ledger(self.session_factory)
        runtime.require_canonical_ledger_authority()
        return runtime


__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
