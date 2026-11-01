from __future__ import annotations

import os
import uuid

import psycopg
import pytest
from sqlalchemy.engine import make_url
from sqlalchemy import create_engine, text

from persistence.atomic_release import initialize_atomic_release_schema
from persistence.idempotency_store import IdempotencyBase
from persistence.durable_idempotency import IdempotencyBase as DurableIdempotencyBase
from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import TransactionWitness
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
from persistence.recovery_outbox import initialize_outbox_schema


@pytest.fixture(autouse=True)
def isolate_postgresql_core_state(request):
    """Keep PostgreSQL integration tests independent on the shared CI database.

    This is test-only isolation. Production state is never reset by this fixture.
    """
    # Dedicated-database tests bypass shared-table TRUNCATE to avoid lock coupling.
    if request.node.get_closest_marker("isolated_postgresql_database"):
        yield
        return

    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url or not url.startswith("postgresql"):
        yield
        return

    engine = create_engine(url, pool_pre_ping=True)
    # Legacy test fixtures remain available for legacy compatibility tests.
    initialize_atomic_release_schema(engine)
    IdempotencyBase.metadata.create_all(engine)
    initialize_outbox_schema(engine)
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


@pytest.fixture
def isolated_postgresql_database(monkeypatch):
    """Create a disposable PostgreSQL database for production runtime boot tests."""
    raw_url = os.getenv("GERCHAIN_DATABASE_URL") or os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not raw_url or not raw_url.startswith("postgresql"):
        pytest.skip("a PostgreSQL service URL is required")

    base_url = make_url(raw_url)
    database_name = f"gerchain_isolated_{uuid.uuid4().hex[:12]}"
    admin_dsn = base_url.set(database="postgres").render_as_string(hide_password=False)
    admin_dsn = admin_dsn.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute("CREATE DATABASE \"" + database_name + "\"")

    test_url = base_url.set(database=database_name).render_as_string(hide_password=False)
    monkeypatch.setenv("GERCHAIN_DATABASE_URL", test_url)
    monkeypatch.setenv("GERCHAIN_TEST_DATABASE_URL", test_url)
    monkeypatch.setenv("DATABASE_URL", test_url)
    try:
        yield test_url
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute("DROP DATABASE IF EXISTS \"" + database_name + "\" WITH (FORCE)")
