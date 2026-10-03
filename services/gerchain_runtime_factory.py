"""Explicit production construction for the GerChain durable runtime."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

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
            ("postgresql://", "postgresql+psycopg://")
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
        """Apply the frozen PostgreSQL migration chain and verify its contract."""
        migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
        with self.engine.connect() as connection:
            apply_migrations(connection, migration_dir)
        with self.engine.connect() as connection:
            assert_canonical_production_schema(connection)

    def _verify_canonical_schema(self) -> None:
        """Fail closed unless the durable canonical runtime schema is present."""
        inspector = inspect(self.engine)
        required = {
            "gerchain_ledger_accounts": {"account_id", "currency", "balance", "version", "updated_at"},
            "gerchain_ledger_movements": {
                "transaction_id", "source", "destination", "amount", "currency",
                "operation", "escrow_id", "integrity_hash", "created_at",
            },
            "gerchain_transaction_witnesses": {
                "transaction_id", "event_type", "escrow_id", "amount", "created_at",
            },
            "gerchain_outbox_events": {
                "event_id", "event_type", "aggregate_id", "payload_json",
                "state", "lease_until", "attempts", "created_at", "updated_at",
            },
            "gerchain_idempotency_records": {
                "key", "fingerprint", "result_json", "state", "created_at", "updated_at",
            },
            "escrows": {
                "id", "sender_address", "receiver_address", "amount", "state",
                "condition_desc", "refund_destination", "currency", "version",
                "created_at", "updated_at",
            },
        }
        missing = {}
        for table, columns in required.items():
            if not inspector.has_table(table):
                missing[table] = sorted(columns)
                continue
            actual = {column["name"] for column in inspector.get_columns(table)}
            absent = sorted(columns - actual)
            if absent:
                missing[table] = absent
        if missing:
            raise RuntimeError(
                "canonical production schema is incomplete; refusing startup: "
                + repr(missing)
            )

    def create(self) -> GerchainRuntime:
        self.initialize()
        self._verify_canonical_schema()
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
