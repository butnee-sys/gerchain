"""Canonical PostgreSQL production runtime construction and schema bootstrap."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import psycopg
from sqlalchemy import Engine, create_engine
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
    url = make_url(engine.url)
    driver_url = url.set(drivername="postgresql").render_as_string(hide_password=False)
    migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
    from postgres.migrations import apply_migrations

    with psycopg.connect(driver_url) as connection:
        apply_migrations(connection, migration_dir)
    for base in (AtomicLedgerBase, EscrowBase, WitnessBase, IdempotencyBase, OutboxBase):
        base.metadata.create_all(engine)
    with engine.connect() as connection:
        assert_canonical_production_schema(connection)



def _constraint_definition_drift(expected_fragments: dict[str, tuple[str, ...]], actual_definitions: dict[str, str]) -> dict[str, dict[str, object]]:
    """Return missing/weakened/misbound CHECK definitions by canonical name.

    This deliberately checks semantic anchor fragments rather than relying on
    PostgreSQL's pretty-printer formatting, which varies across server versions.
    """
    def compact(value: str) -> str:
        return "".join(ch for ch in value.lower().replace('"', "") if not ch.isspace())

    drift = {}
    for name, fragments in expected_fragments.items():
        definition = compact(actual_definitions.get(name, ""))
        missing = [fragment for fragment in fragments if compact(fragment) not in definition]
        if missing:
            drift[name] = {"missing_fragments": missing, "actual": definition or None}
    return drift


def _has_unique_key(inspector, table_name: str, columns: tuple[str, ...]) -> bool:
    """Return true only when PostgreSQL enforces uniqueness for this exact key."""
    for constraint in inspector.get_unique_constraints(table_name):
        if tuple(constraint.get("column_names") or ()) == columns:
            return True
    for index in inspector.get_indexes(table_name):
        if index.get("unique") and tuple(index.get("column_names") or ()) == columns:
            return True
    primary_key = inspector.get_pk_constraint(table_name)
    return tuple(primary_key.get("constrained_columns") or ()) == columns


def assert_canonical_production_schema(connection) -> None:
    """Fail closed unless all canonical ORM tables/columns and 16 migrations exist."""
    from sqlalchemy import inspect, text as sql_text

    inspector = inspect(connection)
    required_tables = {}
    for base in (AtomicLedgerBase, EscrowBase, WitnessBase, IdempotencyBase, OutboxBase):
        for table_name, table in base.metadata.tables.items():
            required_tables[table_name] = {column.name for column in table.columns}

    missing_tables = sorted(set(required_tables) - set(inspector.get_table_names()))
    if missing_tables:
        raise RuntimeError(f"canonical production schema missing tables: {missing_tables}")

    missing_columns = []
    for table_name, expected_columns in required_tables.items():
        actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing = sorted(expected_columns - actual_columns)
        if missing:
            missing_columns.append(f"{table_name}: {missing}")
    if missing_columns:
        raise RuntimeError(f"canonical production schema missing columns: {'; '.join(missing_columns)}")

    # Concurrent requests can race past application-level existence checks.
    # Require DB-enforced uniqueness for every value/evidence idempotency boundary.
    required_unique_keys = {
        "gerchain_ledger_movements": ("transaction_id",),
        "gerchain_transaction_witnesses": ("transaction_id",),
        "gerchain_outbox_events": ("event_id",),
        "gerchain_idempotency_records": ("key",),
    }
    missing_unique_keys = [
        f"{table_name}{columns}"
        for table_name, columns in required_unique_keys.items()
        if not _has_unique_key(inspector, table_name, columns)
    ]
    if missing_unique_keys:
        raise RuntimeError(
            "canonical production schema missing required unique keys: "
            + ", ".join(missing_unique_keys)
        )

    # Validate critical database-enforced invariants, not just ORM column presence.
    # These checks prevent a structurally incomplete schema from passing boot.
    if "escrows" not in inspector.get_table_names():
        raise RuntimeError("canonical production schema missing escrows table")
    escrow_checks = [
        item for item in inspector.get_check_constraints("escrows")
        if "state" in (item.get("sqltext") or "").lower()
    ]
    if len(escrow_checks) != 1 or escrow_checks[0].get("name") != "escrows_state_canonical_check":
        raise RuntimeError(
            "canonical production schema requires exactly one escrows_state_canonical_check; "
            f"actual={escrow_checks!r}"
        )

    # Production boot must verify database-enforced invariants, not merely that
    # tables and columns happen to exist. Keep this registry aligned with the
    # final canonical migration chain (001..016).
    required_checks = {
        "escrows": {
            "escrows_state_canonical_check",
            "escrows_amount_positive_check",
        },
        "gerchain_ledger_accounts": {
            "gerchain_ledger_balance_nonnegative",
            "gerchain_ledger_version_check",
        },
        "gerchain_ledger_movements": {
            "gerchain_movement_amount_check",
            "gerchain_movement_operation_check",
            "gerchain_movement_integrity_hash_check",
            "gerchain_movement_escrow_binding_check",
            "gerchain_movement_distinct_accounts",
        },
        "gerchain_transaction_witnesses": {
            "gerchain_witness_amount_check",
            "gerchain_witness_event_type_check",
        },
        "gerchain_outbox_events": {
            "gerchain_outbox_state_check",
        },
        "gerchain_idempotency_records": {
            "gerchain_idempotency_state_check",
            "gerchain_idempotency_fingerprint_check",
        },
    }
    missing_checks = []
    for table_name, expected_names in required_checks.items():
        actual_names = {
            item.get("name")
            for item in inspector.get_check_constraints(table_name)
            if item.get("name")
        }
        missing = sorted(expected_names - actual_names)
        if missing:
            missing_checks.append(f"{table_name}: {missing}")
    if missing_checks:
        raise RuntimeError(
            "canonical production schema missing required CHECK constraints: "
            + "; ".join(missing_checks)
        )

    # Verify the actual expression, not just the constraint name. Out-of-band DDL
    # can drop/recreate a constraint under its canonical name but attach it to the
    # wrong column or weaken the predicate while migration history stays intact.
    expected_check_fragments = {
        "escrows_state_canonical_check": ("state", "created", "funded", "locked", "released", "refunded", "cancelled"),
        "escrows_amount_positive_check": ("amount", ">", "0"),
        "gerchain_ledger_balance_nonnegative": ("balance", ">=0"),
        "gerchain_ledger_version_check": ("version", ">=0"),
        "gerchain_movement_amount_check": ("amount", ">", "0"),
        "gerchain_movement_operation_check": ("operation", "fund", "release", "refund", "cancel", "settlement"),
        "gerchain_movement_integrity_hash_check": ("integrity_hash", "length", "64"),
        "gerchain_movement_escrow_binding_check": ("escrow_id", "is not null"),
        "gerchain_movement_distinct_accounts": ("source", "destination", "<>"),
        "gerchain_witness_amount_check": ("amount", ">=", "0"),
        "gerchain_witness_event_type_check": ("event_type", "gerchain_funded", "gerchain_locked", "gerchain_released", "gerchain_refunded", "gerchain_cancelled", "gerchain_settled"),
        "gerchain_outbox_state_check": ("state", "pending", "processing", "completed", "failed"),
        "gerchain_idempotency_state_check": ("state", "processing", "completed"),
        "gerchain_idempotency_fingerprint_check": ("fingerprint", "64"),
    }

    actual_constraint_definitions = connection.execute(
        sql_text(
            """
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE contype = 'c'
              AND conname = ANY(:constraint_names)
            """
        ),
        {"constraint_names": sorted(expected_check_fragments)},
    ).all()
    actual_definitions = {name: definition for name, definition in actual_constraint_definitions}
    drifted_definitions = _constraint_definition_drift(expected_check_fragments, actual_definitions)
    if drifted_definitions:
        raise RuntimeError(
            "canonical production schema CHECK constraint definition drift: "
            f"{drifted_definitions}"
        )

    # PostgreSQL enforces NOT NULL separately from CHECK constraints; verify both.
    movement_columns = {
        column["name"]: column
        for column in inspector.get_columns("gerchain_ledger_movements")
    }
    integrity_column = movement_columns.get("integrity_hash")
    if integrity_column is None or integrity_column.get("nullable", True):
        raise RuntimeError(
            "canonical production schema requires gerchain_ledger_movements.integrity_hash NOT NULL"
        )

    # A named but NOT VALID constraint does not prove legacy rows satisfy the
    # invariant. Reject boot until every required constraint has been validated.
    required_constraint_names = sorted(
        name for names in required_checks.values() for name in names
    )
    validated_rows = connection.execute(
        sql_text(
            """
            SELECT conname, convalidated
            FROM pg_constraint
            WHERE conname = ANY(:constraint_names)
            """
        ),
        {"constraint_names": required_constraint_names},
    ).all()
    validated = {name: is_validated for name, is_validated in validated_rows}
    unvalidated = sorted(
        name for name in required_constraint_names if validated.get(name) is not True
    )
    if unvalidated:
        raise RuntimeError(
            "canonical production schema has missing or NOT VALID CHECK constraints: "
            f"{unvalidated}"
        )

    if "schema_version" not in inspector.get_table_names():
        raise RuntimeError("canonical production schema missing schema_version; required=16 migrations")
    version_constraints = inspector.get_pk_constraint("schema_version")
    version_indexes = inspector.get_indexes("schema_version")
    has_unique_version = (
        version_constraints.get("constrained_columns") == ["version"]
        or any(index.get("unique") and index.get("column_names") == ["version"] for index in version_indexes)
    )
    if not has_unique_version:
        raise RuntimeError("canonical production schema requires unique schema_version.version")
    versions = connection.execute(text("SELECT version FROM schema_version ORDER BY version")).scalars().all()
    if versions != list(range(1, 17)):
        raise RuntimeError(
            f"canonical production schema migration history incomplete; required=16, actual={versions}"
        )


class ProductionRuntimeFactory:
    """Create the production GerChain runtime with PostgreSQL as authority."""

    def __init__(
        self,
        config: ProductionRuntimeConfig,
        *,
        engine: Engine | None = None,
        session_factory: Callable[[], Any] | None = None,
    ) -> None:
        if not config.database_url.startswith(("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")):
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL database URL")
        if engine is None and session_factory is not None:
            bind = getattr(session_factory, "kw", {}).get("bind")
            if bind is None:
                bind = getattr(session_factory, "bind", None)
            if bind is not None and getattr(bind, "dialect", None) is not None:
                engine = bind
        self.engine = engine or create_engine(config.database_url, pool_pre_ping=True)
        if self.engine.dialect.name != "postgresql":
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL engine")
        self.config = config
        self._provided_session_factory = session_factory

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

    @property
    def session_factory(self) -> Callable[[], Any]:
        """Return the factory bound to the canonical production engine.

        Exposed for controlled operational workflows and integration tests;
        callers must still use the canonical transaction boundaries.
        """
        return self._session_factory()

    def _session_factory(self) -> Callable[[], Any]:
        if self._provided_session_factory is not None:
            bind = getattr(self._provided_session_factory, "kw", {}).get("bind")
            if bind is not None and bind is not self.engine:
                raise ValueError("provided session_factory must be bound to the production engine")
            return self._provided_session_factory
        from sqlalchemy.orm import sessionmaker
        return sessionmaker(bind=self.engine, expire_on_commit=False)


__all__ = [
    "ProductionRuntimeConfig",
    "ProductionRuntimeFactory",
    "initialize_canonical_postgres_schema",
]
