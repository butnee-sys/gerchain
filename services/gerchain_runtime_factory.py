"""Canonical PostgreSQL production runtime construction and schema bootstrap."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import psycopg
from sqlalchemy import Engine
from sqlalchemy.engine import make_url

from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
from services.gerchain_runtime import GerchainRuntime


@dataclass(frozen=True)
class ProductionRuntimeConfig:
    database_url: str
    escrow_id: str
    amount: int
    currency: str
    witness_id: str


def initialize_canonical_postgres_schema(engine: Engine) -> None:
    """Apply the single canonical migration registry, then create ORM-owned tables.

    The migration registry is authoritative for versioned PostgreSQL DDL.
    SQLAlchemy metadata creation only ensures the canonical runtime models
    exist; it does not replace the versioned migration ledger.
    """
    if engine.dialect.name != "postgresql":
        raise ValueError("canonical production schema requires PostgreSQL")
    url = make_url(str(engine.url))
    driver_url = url.set(drivername="postgresql").render_as_string(hide_password=False)
    migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
    from postgres.migrations import apply_migrations

    with psycopg.connect(driver_url) as connection:
        apply_migrations(connection, migration_dir)
    for base in (AtomicLedgerBase, EscrowBase, WitnessBase, IdempotencyBase, OutboxBase):
        base.metadata.create_all(engine)


class ProductionRuntimeFactory:
    """Create the production GerChain runtime with PostgreSQL as authority."""

    def __init__(self, config: ProductionRuntimeConfig, *, engine: Engine) -> None:
        if not config.database_url.startswith(("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")):
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL database URL")
        if engine is None or engine.dialect.name != "postgresql":
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL engine")
        self.config = config
        self.engine = engine

    def initialize(self) -> None:
        initialize_canonical_postgres_schema(self.engine)

    def create(self) -> GerchainRuntime:
        self.initialize()
        runtime = GerchainRuntime(
            escrow_id=self.config.escrow_id,
            amount=self.config.amount,
            currency=self.config.currency,
            witness_id=self.config.witness_id,
        )
        runtime.configure_canonical_ledger(self._session_factory())
        runtime.require_canonical_ledger_authority()
        return runtime

    def _session_factory(self) -> Callable[[], Any]:
        from sqlalchemy.orm import sessionmaker
        return sessionmaker(bind=self.engine, expire_on_commit=False)


__all__ = [
    "ProductionRuntimeConfig",
    "ProductionRuntimeFactory",
    "initialize_canonical_postgres_schema",
]
