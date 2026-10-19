"""Explicit production construction for the GerChain durable runtime."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import psycopg
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from postgres.migrations import apply_migrations
from services.gerchain_runtime import GerchainRuntime


@dataclass(frozen=True)
class ProductionRuntimeConfig:
    database_url: str
    escrow_id: str
    amount: int
    currency: str
    witness_id: str


def initialize_canonical_postgres_schema(engine: Engine) -> None:
    """Apply the single canonical, checksummed migration chain to PostgreSQL."""
    if engine.dialect.name != "postgresql":
        raise ValueError("canonical production schema requires PostgreSQL")
    url = engine.url.render_as_string(hide_password=False)
    url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
    with psycopg.connect(url) as connection:
        apply_migrations(connection, migration_dir)


def assert_canonical_production_schema(connection: Any) -> None:
    """Fail closed unless the canonical durable tables and critical columns exist."""
    from sqlalchemy import inspect

    inspector = inspect(connection)
    required = {
        "gerchain_ledger_accounts": {"account_id", "currency", "balance", "version"},
        "gerchain_ledger_movements": {
            "transaction_id", "source", "destination", "amount", "currency",
            "operation", "escrow_id", "integrity_hash",
        },
        "escrows": {
            "id", "sender_address", "receiver_address", "amount", "state",
            "refund_destination", "currency", "version",
        },
        "gerchain_transaction_witnesses": {"transaction_id", "event_type"},
        "gerchain_outbox_events": {"event_id", "event_type", "aggregate_id", "state"},
        "gerchain_idempotency_records": {"key", "fingerprint", "state"},
    }
    tables = set(inspector.get_table_names())
    missing_tables = sorted(set(required) - tables)
    if missing_tables:
        raise RuntimeError(
            "canonical production schema missing tables: " + ", ".join(missing_tables)
        )
    errors = []
    for table, expected_columns in required.items():
        actual = {column["name"] for column in inspector.get_columns(table)}
        missing = sorted(expected_columns - actual)
        if missing:
            errors.append(f"{table}: {', '.join(missing)}")
    if errors:
        raise RuntimeError(
            "canonical production schema missing required columns: " + "; ".join(errors)
        )



class ProductionRuntimeFactory:
    """Create a runtime whose authoritative value boundary is Canonical Ledger."""

    def __init__(
        self,
        config: ProductionRuntimeConfig,
        *,
        engine: Engine | None = None,
        session_factory: Callable[[], Any] | None = None,
    ) -> None:
        if not config.database_url:
            raise ValueError("database_url is required")
        if not config.database_url.startswith(
            ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")
        ):
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL database URL")
        self.config = config
        self.engine = engine or create_engine(config.database_url, pool_pre_ping=True, future=True)
        if self.engine.dialect.name != "postgresql":
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL engine")
        self.session_factory = session_factory or sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

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
        runtime.configure_canonical_ledger(self.session_factory)
        runtime.require_canonical_ledger_authority()
        return runtime


__all__ = [
    "ProductionRuntimeConfig",
    "ProductionRuntimeFactory",
    "initialize_canonical_postgres_schema",
    "assert_canonical_production_schema",
]
