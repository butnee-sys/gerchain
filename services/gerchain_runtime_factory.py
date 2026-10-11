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



def assert_canonical_production_schema(connection) -> None:
    """Fail closed unless all canonical ORM tables/columns and 13 migrations exist."""
    from sqlalchemy import inspect, text

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

    # Validate critical database-enforced invariants, not just ORM column presence.
    # These checks prevent a structurally incomplete schema from passing boot.
    if "escrows" not in inspector.get_table_names():
        raise RuntimeError("canonical production schema missing escrows table")
    escrow_checks = [
        item for item in inspector.get_check_constraints("escrows")
        if "state" in (item.get("sqltext") or "").lower()
    ]
    if len(escrow_checks) != 1 or escrow_checks[0].get("name") != "escrows_state_check":
        raise RuntimeError(
            "canonical production schema requires exactly one escrows_state_check; "
            f"actual={escrow_checks!r}"
        )

    if "schema_version" not in inspector.get_table_names():
        raise RuntimeError("canonical production schema missing schema_version; required=13 migrations")
    version_constraints = inspector.get_pk_constraint("schema_version")
    version_indexes = inspector.get_indexes("schema_version")
    has_unique_version = (
        version_constraints.get("constrained_columns") == ["version"]
        or any(index.get("unique") and index.get("column_names") == ["version"] for index in version_indexes)
    )
    if not has_unique_version:
        raise RuntimeError("canonical production schema requires unique schema_version.version")
    versions = connection.execute(text("SELECT version FROM schema_version ORDER BY version")).scalars().all()
    if versions != list(range(1, 14)):
        raise RuntimeError(
            f"canonical production schema migration history incomplete; required=13, actual={versions}"
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
