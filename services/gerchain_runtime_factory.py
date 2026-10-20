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


def _has_unique_key(inspector: Any, table: str, columns: tuple[str, ...]) -> bool:
    """Return true only for an exact unique constraint, unique index, or primary key."""
    wanted = list(columns)
    for constraint in inspector.get_unique_constraints(table):
        if constraint.get("column_names") == wanted:
            return True
    for index in inspector.get_indexes(table):
        if index.get("unique") and index.get("column_names") == wanted:
            return True
    primary_key = inspector.get_pk_constraint(table)
    return primary_key.get("constrained_columns") == wanted


def _constraint_definition_drift(
    expected: dict[str, tuple[str, ...]],
    actual: dict[str, str],
) -> dict[str, dict[str, Any]]:
    """Compare named PostgreSQL CHECK constraints against required semantic fragments.

    This deliberately performs conservative fragment checks, not full SQL equivalence.
    Missing or weakened definitions are reported as drift and must fail the startup gate.
    """
    import re

    def normalize(value: str) -> str:
        value = value.lower().replace('"', "").replace("'", "")
        value = re.sub(r"::[a-z_][a-z_0-9]*(?:\[\])?", "", value)
        value = re.sub(r"\s+", "", value)
        value = value.replace("(", "").replace(")", "")
        return value

    drift: dict[str, dict[str, Any]] = {}
    for name, fragments in expected.items():
        definition = actual.get(name)
        normalized = normalize(definition) if definition is not None else ""
        missing = [fragment for fragment in fragments if normalize(fragment) not in normalized]
        if definition is None or missing:
            drift[name] = {
                "actual": definition,
                "missing_fragments": missing if definition is not None else list(fragments),
            }
    return drift


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

    unique_requirements = {
        "gerchain_ledger_movements": ("transaction_id",),
        "gerchain_outbox_events": ("event_id",),
        "gerchain_transaction_witnesses": ("transaction_id",),
        "gerchain_idempotency_records": ("key",),
    }
    for table, columns in unique_requirements.items():
        if not _has_unique_key(inspector, table, columns):
            raise RuntimeError(
                f"{table} must enforce unique key on {', '.join(columns)}"
            )

    # The migration runner owns schema evolution. Startup independently verifies
    # the two safety-critical catalog invariants before exposing a production runtime.
    version_index = connection.exec_driver_sql(
        """
        SELECT EXISTS (
            SELECT 1
            FROM pg_index i
            JOIN pg_class t ON t.oid = i.indrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = i.indkey[0]
            WHERE n.nspname = current_schema()
              AND t.relname = 'schema_version'
              AND i.indisunique
              AND i.indpred IS NULL
              AND i.indnkeyatts = 1
              AND a.attname = 'version'
        )
        """
    ).scalar_one()
    if not version_index:
        raise RuntimeError("schema_version.version must have a unique index")

    state_constraints = connection.exec_driver_sql(
        """
        SELECT conname, pg_get_constraintdef(oid), convalidated
        FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND contype = 'c'
          AND position('state' in lower(pg_get_constraintdef(oid))) > 0
        """
    ).all()
    if len(state_constraints) != 1:
        raise RuntimeError(
            "escrows.state must have exactly one canonical state CHECK constraint"
        )
    name, definition, validated = state_constraints[0]
    required_states = ("CREATED", "FUNDED", "LOCKED", "RELEASED", "REFUNDED", "CANCELLED")
    normalized_definition = str(definition).upper()
    if (
        name != "escrows_state_canonical_check"
        or not validated
        or any(state not in normalized_definition for state in required_states)
    ):
        raise RuntimeError(
            "escrows.state canonical CHECK is missing, unvalidated, or incomplete"
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
        with self.engine.connect() as connection:
            assert_canonical_production_schema(connection)

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
