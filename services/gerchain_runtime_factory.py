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
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase
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


def assert_canonical_production_schema(connection) -> None:
    """Fail closed unless the full canonical runtime schema is present.

    A migration version alone is not sufficient: restored databases and manual
    schema edits can leave a version-13 marker alongside missing columns.
    """
    required_columns = {
        "schema_version": {
            "version", "checksum", "applied_at",
        },
        "escrows": {
            "id", "sender_address", "receiver_address", "amount", "state",
            "condition_desc", "refund_destination", "currency", "version",
            "created_at", "updated_at",
        },
        "gerchain_ledger_accounts": {
            "account_id", "currency", "balance", "version", "updated_at",
        },
        "gerchain_ledger_movements": {
            "id", "transaction_id", "source", "destination", "amount",
            "currency", "operation", "escrow_id", "integrity_hash", "created_at",
        },
        "gerchain_transaction_witnesses": {
            "id", "transaction_id", "event_type", "escrow_id", "amount", "created_at",
        },
        "gerchain_outbox_events": {
            "id", "event_id", "event_type", "aggregate_id", "payload_json",
            "state", "lease_until", "attempts", "created_at", "updated_at",
        },
        "gerchain_idempotency_records": {
            "id", "key", "fingerprint", "result_json", "state", "created_at", "updated_at",
        },
    }
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    missing_tables = set(required_columns) - tables
    if missing_tables:
        raise RuntimeError(
            f"canonical production schema incomplete; missing tables: {sorted(missing_tables)}"
        )

    missing_columns = {
        table: sorted(columns - {column["name"] for column in inspector.get_columns(table)})
        for table, columns in required_columns.items()
    }
    missing_columns = {table: columns for table, columns in missing_columns.items() if columns}
    if missing_columns:
        raise RuntimeError(
            f"canonical production schema incomplete; missing columns: {missing_columns}"
        )

    version = connection.execute(text("SELECT MAX(version) FROM schema_version")).scalar()
    if version is None or int(version) < 13:
        raise RuntimeError(
            f"canonical production schema history incomplete; latest={version}; required=13"
        )

    required_unique = {
        "gerchain_ledger_accounts": {"account_id"},
        "gerchain_ledger_movements": {"transaction_id"},
        "gerchain_transaction_witnesses": {"transaction_id"},
        "gerchain_outbox_events": {"event_id"},
        "gerchain_idempotency_records": {"key"},
    }
    for table, column in required_unique.items():
        constraints = inspector.get_unique_constraints(table)
        indexes = inspector.get_indexes(table)
        unique_sets = {
            tuple(item.get("column_names") or ())
            for item in constraints
        } | {
            tuple(item.get("column_names") or ())
            for item in indexes if item.get("unique")
        }
        if (column,) not in unique_sets:
            raise RuntimeError(
                f"canonical production schema incomplete; {table}.{column} must be unique"
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
        """Apply and validate the authoritative PostgreSQL schema."""
        initialize_canonical_postgres_schema(self.engine)

    def _validate_configured_escrow(self) -> None:
        """Fail closed unless the configured escrow already exists as canonical truth."""
        from sqlalchemy import select

        with self.session_factory() as session:
            escrow = session.execute(
                select(CanonicalEscrow).where(
                    CanonicalEscrow.id == self.config.escrow_id
                )
            ).scalar_one_or_none()
            if escrow is None:
                raise RuntimeError(
                    f"configured escrow {self.config.escrow_id!r} is absent from canonical PostgreSQL state"
                )
            if int(escrow.amount) != self.config.amount:
                raise RuntimeError("configured escrow amount does not match canonical PostgreSQL state")
            if escrow.currency != self.config.currency:
                raise RuntimeError("configured escrow currency does not match canonical PostgreSQL state")
            if not escrow.sender_address or not escrow.receiver_address or not escrow.refund_destination:
                raise RuntimeError("configured escrow is missing authoritative party/refund fields")

    def create(self) -> GerchainRuntime:
        self.initialize()
        with self.engine.connect() as connection:
            assert_canonical_production_schema(connection)
        self._validate_configured_escrow()
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
