from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text

from persistence.atomic_release import initialize_atomic_release_schema
from persistence.idempotency_store import IdempotencyBase
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
    initialize_atomic_release_schema(engine)
    IdempotencyBase.metadata.create_all(engine)
    initialize_outbox_schema(engine)
    tables = (
        "gerchain_release_witnesses",
        "gerchain_outbox_events",
        "gerchain_release_operations",
        "gerchain_release_escrows",
        "gerchain_release_accounts",
        "gerchain_idempotency_records",
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
