from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
from services.gerchain_runtime_factory import assert_canonical_production_schema


def _create_canonical_test_schema(engine) -> None:
    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, WitnessBase):
        base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE schema_version ("
            "version BIGINT PRIMARY KEY, checksum TEXT NOT NULL, "
            "applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        ))
        connection.execute(text(
            "INSERT INTO schema_version(version, checksum) VALUES (13, 'test')"
        ))


def test_canonical_schema_assertion_accepts_complete_schema() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    _create_canonical_test_schema(engine)
    with engine.connect() as connection:
        assert_canonical_production_schema(connection)
    engine.dispose()


def test_canonical_schema_assertion_rejects_version_marker_with_missing_columns() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE escrows (id TEXT PRIMARY KEY, state TEXT NOT NULL)"
        ))
    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, WitnessBase):
        base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE schema_version ("
            "version BIGINT PRIMARY KEY, checksum TEXT NOT NULL, "
            "applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        ))
        connection.execute(text(
            "INSERT INTO schema_version(version, checksum) VALUES (13, 'test')"
        ))
    with engine.connect() as connection:
        with pytest.raises(RuntimeError, match="missing columns"):
            assert_canonical_production_schema(connection)
    engine.dispose()


def test_canonical_schema_assertion_rejects_incomplete_migration_history() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    _create_canonical_test_schema(engine)
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM schema_version"))
        connection.execute(text(
            "INSERT INTO schema_version(version, checksum) VALUES (12, 'test')"
        ))
    with engine.connect() as connection:
        with pytest.raises(RuntimeError, match="required=13"):
            assert_canonical_production_schema(connection)
    engine.dispose()
