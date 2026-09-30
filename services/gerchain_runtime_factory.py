"""Explicit production construction for the GerChain durable runtime."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from postgres.migrations import apply_migrations
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

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
        """Apply the canonical PostgreSQL migration history atomically."""
        migration_dir = Path(__file__).resolve().parent.parent / "postgres" / "schema"
        with self.engine.connect() as conn:
            apply_migrations(conn, migration_dir)
            assert_canonical_production_schema(conn)

    def verify_schema(self) -> None:
        inspector = inspect(self.engine)
        required = {
            "escrows": {
                "id", "sender_address", "receiver_address", "amount", "state",
                "refund_destination", "currency", "version", "created_at", "updated_at",
            },
            "gerchain_ledger_accounts": {
                "account_id", "currency", "balance", "version", "updated_at",
            },
            "gerchain_ledger_movements": {
                "transaction_id", "source", "destination", "amount", "currency",
                "operation", "escrow_id", "integrity_hash", "created_at",
            },
            "gerchain_transaction_witnesses": {
                "transaction_id", "event_type", "escrow_id", "amount", "created_at",
            },
            "gerchain_idempotency_records": {
                "key", "fingerprint", "result_json", "state", "created_at", "updated_at",
            },
            "gerchain_outbox_events": {
                "event_id", "event_type", "aggregate_id", "payload_json", "state",
                "lease_until", "attempts", "created_at", "updated_at",
            },
        }
        missing = []
        for table, columns in required.items():
            if not inspector.has_table(table):
                missing.append(f"{table} (table)")
                continue
            actual = {column["name"] for column in inspector.get_columns(table)}
            for column in sorted(columns - actual):
                missing.append(f"{table}.{column}")
        if missing:
            raise RuntimeError(
                "canonical production schema incomplete; apply PostgreSQL migration before boot: "
                + ", ".join(missing)
            )

    def create(self) -> GerchainRuntime:
        self.initialize()
        self.verify_schema()
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
