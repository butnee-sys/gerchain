from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from shuud.persistence import SHUUDPersistence


POSTGRES_DSN = os.getenv("GERCHAIN_POSTGRES_DSN")
pytestmark = pytest.mark.skipif(
    not POSTGRES_DSN,
    reason="GERCHAIN_POSTGRES_DSN is required for SHUUD release CAS race test",
)


def test_only_one_concurrent_release_snapshot_wins():
    store = SHUUDPersistence(POSTGRES_DSN)
    incident_id = f"INC-RACE-{uuid4().hex}"
    expected = {
        "state": "LOCKED",
        "version": 7,
    }
    first = {
        "state": "RELEASED",
        "version": 8,
        "winner": "A",
    }
    second = {
        "state": "RELEASED",
        "version": 8,
        "winner": "B",
    }

    try:
        store.save_snapshot(incident_id, expected)

        def attempt(snapshot: dict[str, object]) -> bool:
            contender = SHUUDPersistence(POSTGRES_DSN)
            return contender.save_snapshot_if_current(
                incident_id,
                expected,
                snapshot,
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(attempt, (first, second)))

        assert sorted(results) == [False, True]
        final = store.load_snapshot(incident_id)
        assert final in (first, second)
    finally:
        store.delete_snapshot(incident_id)
