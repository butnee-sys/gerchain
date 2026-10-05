from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import Engine

from persistence.atomic_ledger import AtomicLedgerBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.atomic_value_transaction import TransactionWitness
from persistence.postgres_canonical_schema import initialize_canonical_postgres_schema
from postgres.migrations import apply_migrations
from services.gerchain_runtime import GerchainRuntime


_REQUIRED_SCHEMA = {
    "escrows": {"id", "sender_address", "receiver_address", "amount", "state", "refund_destination", "currency", "version", "created_at", "updated_at"},
    "gerchain_ledger_accounts": {"account_id", "currency", "balance", "version", "updated_at"},
    "gerchain_ledger_movements": {"transaction_id", "source", "destination", "amount", "currency", "operation", "escrow_id", "integrity_hash", "created_at"},
    "gerchain_transaction_witnesses": {"transaction_id", "event_type", "escrow_id", "amount", "created_at"},
    "gerchain_outbox_events": {"event_id", "event_type", "aggregate_id", "payload_json", "state", "lease_until", "attempts", "created_at", "updated_at"},
    "gerchain_idempotency_records": {"key", "fingerprint", "result_json", "state", "created_at", "updated_at"},
}


def assert_canonical_production_schema(connection) -> None:
    """Fail closed unless every canonical production table/column exists."""
    from sqlalchemy import text

    for table, required_columns in _REQUIRED_SCHEMA.items():
        rows = connection.execute(
            text(
                "SELECT column_name "
                "FROM information_schema.columns "
                "WHERE table_schema = current_schema() AND table_name = :table"
            ),
            {"table": table},
        ).scalars().all()
        actual = set(rows)
        missing = required_columns - actual
        if missing:
            raise RuntimeError(
                f"canonical production schema incomplete for {table}: "
                f"missing {', '.join(sorted(missing))}"
            )


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
        """Apply the canonical PostgreSQL migration history before runtime boot."""
        migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
        with self.engine.connect() as connection:
            apply_migrations(connection, migration_dir)
            assert_canonical_production_schema(connection)

        # ORM metadata is retained as a defensive compatibility layer for
        # canonical persistence models not yet materialized by a historical
        # migration. It must not replace or bypass migration history.
        initialize_canonical_postgres_schema(self.engine)
        for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, TransactionWitness):
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
