"""Explicit production construction for the GerChain durable runtime."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.atomic_value_transaction import TransactionWitness
from persistence.production_schema_guard import assert_canonical_production_schema
from postgres.migrations import apply_migrations
from services.gerchain_runtime import GerchainRuntime


@dataclass(frozen=True)
class ProductionRuntimeConfig:
    database_url: str
    escrow_id: str
    amount: int
    currency: str
    witness_id: str


class ProductionRuntimeFactory:
    """Construct the production runtime with Canonical Ledger authority."""

    def __init__(self, config: ProductionRuntimeConfig, *, engine: Engine | None = None) -> None:
        if not config.database_url:
            raise ValueError("database_url is required")
        if not config.database_url.startswith(
            ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")
        ):
            raise ValueError("ProductionRuntimeFactory requires PostgreSQL database URL")
        self.config = config
        self.engine = engine or create_engine(config.database_url, future=True)
        if self.engine.dialect.name != "postgresql":
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL engine")
        self.session_factory: Callable[[], Any] = sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

    def initialize(self) -> None:
        """Apply the canonical PostgreSQL schema before constructing the runtime.

        The SQL migration is authoritative for existing databases; ORM
        create_all alone cannot add columns or evolve constraints.
        Migration errors intentionally fail closed.
        """
        schema_path = (
            Path(__file__).resolve().parents[1]
            / "postgres"
            / "schema"
            / "001_concurrency.sql"
        )
        schema_sql = schema_path.read_text(encoding="utf-8")
        with self.engine.begin() as connection:
            connection.exec_driver_sql(schema_sql)

        for base in (
            AtomicLedgerBase,
            EscrowBase,
            OutboxBase,
            IdempotencyBase,
            TransactionWitness,
        ):
            base.metadata.create_all(self.engine)

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
