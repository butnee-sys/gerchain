from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import Engine

from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
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
    """Create the production GerChain runtime with PostgreSQL as authority."""

    def __init__(
        self,
        config: ProductionRuntimeConfig,
        *,
        engine: Engine,
        session_factory: Callable[[], Any] | None = None,
    ) -> None:
        if engine is None or engine.dialect.name != "postgresql":
            raise ValueError("production runtime requires a PostgreSQL engine")
        if not config.database_url.startswith(
            ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")
        ):
            raise ValueError("ProductionRuntimeConfig requires a PostgreSQL database URL")
        if config.amount <= 0:
            raise ValueError("ProductionRuntimeConfig amount must be positive")
        self.config = config
        self.engine = engine
        if session_factory is None:
            from sqlalchemy.orm import sessionmaker
            session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        self.session_factory = session_factory

    def initialize(self) -> None:
        # Migration history is authoritative for PostgreSQL production schema.
        # ORM create_all is retained only as a compatibility backstop for
        # additive mapped objects; it is not the migration mechanism.
        migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
        with self.engine.connect() as connection:
            apply_migrations(connection, migration_dir)

        for base in (AtomicLedgerBase, EscrowBase, WitnessBase, IdempotencyBase, OutboxBase):
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
