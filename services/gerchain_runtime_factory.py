from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

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
        """Apply the canonical PostgreSQL migration set under an advisory lock."""
        migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "schema"
        with self.engine.connect() as conn:
            apply_migrations(conn, migration_dir)

    def validate_production_schema(self) -> None:
        """Fail closed unless the canonical production schema is complete."""
        from sqlalchemy import inspect

        required = {
            "gerchain_ledger_accounts": {"account_id", "currency", "balance", "version", "updated_at"},
            "gerchain_ledger_movements": {"transaction_id", "source", "destination", "amount", "currency", "operation", "escrow_id", "integrity_hash", "created_at"},
            "escrows": {"id", "sender_address", "receiver_address", "amount", "state", "condition_desc", "refund_destination", "currency", "version", "created_at", "updated_at"},
            "gerchain_transaction_witnesses": {"transaction_id", "event_type", "escrow_id", "amount", "created_at"},
            "gerchain_outbox_events": {"event_id", "event_type", "aggregate_id", "payload_json", "state", "lease_until", "attempts", "created_at", "updated_at"},
            "gerchain_idempotency_records": {"key", "fingerprint", "result_json", "state", "created_at", "updated_at"},
        }
        inspector = inspect(self.engine)
        missing_tables = [name for name in required if not inspector.has_table(name)]
        if missing_tables:
            raise RuntimeError("canonical production schema missing tables: " + ", ".join(sorted(missing_tables)))
        missing_columns = []
        for table, columns in required.items():
            actual = {column["name"] for column in inspector.get_columns(table)}
            absent = sorted(columns - actual)
            if absent:
                missing_columns.append(table + ": " + ", ".join(absent))
        if missing_columns:
            raise RuntimeError("canonical production schema incomplete: " + "; ".join(missing_columns))

    def create(self) -> GerchainRuntime:
        self.initialize()
        self.validate_production_schema()
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
