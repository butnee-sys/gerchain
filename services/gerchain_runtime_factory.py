from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import WitnessBase, TransactionWitness
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
from services.gerchain_runtime import GerchainRuntime
from postgres.migrations import apply_migrations


@dataclass(frozen=True)
class ProductionRuntimeConfig:
    database_url: str
    escrow_id: str
    amount: int
    currency: str
    witness_id: str


def assert_canonical_production_schema(connection) -> None:
    required = {
        "schema_version",
        "escrows",
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
    }
    tables = set(inspect(connection).get_table_names())
    missing = required - tables
    if missing:
        raise RuntimeError(
            f"canonical production schema incomplete; missing tables: {sorted(missing)}"
        )
    version = connection.execute(text("SELECT MAX(version) FROM schema_version")).scalar()
    if version is None or int(version) < 12:
        raise RuntimeError(
            f"canonical production schema history incomplete; latest={version}; required=5"
        )


def initialize_canonical_postgres_schema(engine: Engine) -> None:
    migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
    with engine.connect() as connection:
        apply_migrations(connection, migration_dir)
    with engine.connect() as connection:
        assert_canonical_production_schema(connection)


class ProductionRuntimeFactory:
    """Create the production GerChain runtime with PostgreSQL as authority."""

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
                "ProductionRuntimeFactory requires a PostgreSQL database URL"
            )
        self.config = config
        self.engine = engine or create_engine(config.database_url, future=True)
        if self.engine.dialect.name != "postgresql":
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL engine")
        self.session_factory: Callable[[], Any] = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
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
    "apply_migrations",
    "assert_canonical_production_schema",
    "initialize_canonical_postgres_schema",
    "AtomicLedgerBase",
    "EscrowBase",
    "OutboxBase",
    "IdempotencyBase",
    "TransactionWitness",
]
