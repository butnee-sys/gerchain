from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from postgres.migrations import apply_migrations

from postgres.migrations import apply_migrations
from persistence.production_schema_guard import assert_canonical_production_schema
from services.gerchain_runtime import GerchainRuntime


@dataclass(frozen=True)
class ProductionRuntimeConfig:
    database_url: str
    escrow_id: str
    amount: int
    currency: str
    witness_id: str


class ProductionRuntimeFactory:
    """Construct the production GerChain runtime with Canonical Ledger authority."""

    def __init__(
        self,
        config: ProductionRuntimeConfig,
        *,
        engine: Engine | None = None,
    ) -> None:
        if not config.database_url:
            raise ValueError("database_url is required")
        if not config.database_url.startswith(
            ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")
        ):
            raise ValueError(
                "ProductionRuntimeFactory requires PostgreSQL database URL"
            )

        self.config = config
        self.engine = engine or create_engine(config.database_url, future=True)
        if self.engine.dialect.name != "postgresql":
            raise ValueError(
                "ProductionRuntimeFactory requires a PostgreSQL engine"
            )
        self.session_factory: Callable[[], Any] = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    def initialize(self) -> None:
        """Apply the versioned PostgreSQL schema before constructing the runtime."""
        migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "schema"
        with self.engine.begin() as conn:
            apply_migrations(conn, migration_dir)
            assert_canonical_production_schema(conn)

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

    @classmethod
    def from_engine(
        cls,
        *,
        escrow_id: str,
        amount: int,
        currency: str,
        witness_id: str,
        engine: Engine,
        session_factory: Callable[[], Any] | None = None,
    ) -> GerchainRuntime:
        factory = cls(
            ProductionRuntimeConfig(
                database_url=str(engine.url),
                escrow_id=escrow_id,
                amount=amount,
                currency=currency,
                witness_id=witness_id,
            ),
            engine=engine,
        )
        if session_factory is not None:
            factory.session_factory = session_factory
        return factory.create()

    build = create


__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
