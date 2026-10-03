from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from persistence.atomic_release import initialize_atomic_release_schema
from persistence.idempotency_store import IdempotencyBase
from persistence.durable_idempotency import IdempotencyBase as DurableIdempotencyBase
from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import TransactionWitness
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
from postgres.migrations import apply_migrations
from persistence.recovery_outbox import initialize_outbox_schema


@pytest.fixture(autouse=True)
def isolate_postgresql_core_state():
    """Keep PostgreSQL integration tests independent on the shared CI database.

    This is test-only isolation. Production state is never reset by this fixture.
    """
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url or not url.startswith("postgresql"):
        yield
        return

    engine = create_engine(url, pool_pre_ping=True)
    # Legacy test fixtures remain available for legacy compatibility tests.
    initialize_atomic_release_schema(engine)
    IdempotencyBase.metadata.create_all(engine)
    initialize_outbox_schema(engine)
    with engine.connect() as connection:
        apply_migrations(connection, Path("postgres/migrations"))
    # Ensure every canonical table exists before isolation truncation.
    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, DurableIdempotencyBase, TransactionWitness):
        base.metadata.create_all(engine)
    # Canonical durable idempotency is production-owned by the migration chain;
    # create_all is only a test-fixture safety net for mixed legacy/core suites.
    DurableIdempotencyBase.metadata.create_all(engine)
    # Ensure the canonical table is visible on the exact connection used by
    # the isolation boundary before issuing TRUNCATE statements.
    with engine.begin() as connection:
        DurableIdempotencyBase.metadata.create_all(connection)
    tables = (
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
        "gerchain_ledger_movements",
        "gerchain_ledger_accounts",
        "escrows",
        "gerchain_release_witnesses",
        "gerchain_release_operations",
        "gerchain_release_escrows",
        "gerchain_release_accounts",
    )
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE " + ", ".join(tables) + " RESTART IDENTITY CASCADE"))
    yield
    engine.dispose()


@pytest.fixture
def canonical_postgresql_engine():
    """Provide a real PostgreSQL engine when production re-performance is enabled."""
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url or not url.startswith("postgresql"):
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is not configured")
    engine = create_engine(url, pool_pre_ping=True)
    yield engine
    engine.dispose()
