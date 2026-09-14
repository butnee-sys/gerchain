import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from persistence.atomic_settlement import PostgreSQLAtomicSettlement, initialize_settlement_schema


@pytest.fixture()
def settlement():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_engine(url, pool_pre_ping=True)
    initialize_settlement_schema(engine)
    service = PostgreSQLAtomicSettlement(lambda: Session(engine))
    service.ensure_account("PG-SOURCE", 10_000_000)
    service.ensure_account("PG-DEST", 0)
    return service


def test_settlement_moves_value_once(settlement):
    first = settlement.settle("TX-ATOMIC-001", "PG-SOURCE", "PG-DEST", 2_000_000)
    replay = settlement.settle("TX-ATOMIC-001", "PG-SOURCE", "PG-DEST", 2_000_000)

    assert first.replay is False
    assert replay.replay is True
    assert settlement.get_balance("PG-SOURCE") == 8_000_000
    assert settlement.get_balance("PG-DEST") == 2_000_000


def test_transaction_id_cannot_change_destination(settlement):
    settlement.settle("TX-ATOMIC-002", "PG-SOURCE", "PG-DEST", 1_000_000)
    with pytest.raises(ValueError):
        settlement.settle("TX-ATOMIC-002", "PG-SOURCE", "OTHER", 1_000_000)
