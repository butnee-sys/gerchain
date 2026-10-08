from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine


@pytest.fixture
def postgres_engine():
    dsn = os.environ.get("GERCHAIN_POSTGRES_DSN")
    if not dsn:
        pytest.skip("GERCHAIN_POSTGRES_DSN is not configured")
    engine = create_engine(dsn, pool_pre_ping=True)
    yield engine
    engine.dispose()
