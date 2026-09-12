"""SH-16.13 recoverable publication and reconciliation tests.

The outbox retries durable publication only. It never recreates WitnessChain
or EscrowEngine authority and never issues a second release decision.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from time import sleep

from sqlalchemy import create_engine, select

from shuud.persistence import (
    SHUUDEscrowRecord,
    SHUUDLifecycleEvent,
    SHUUDReleaseAuthorizationRecord,
    initialize_schema,
)
from shuud.publication_outbox import (
    SHUUDPublicationOutbox,
    publish_pending,
    queue_publication,
)
from tests.test_shuud_production_wiring import _publication


def _engine(tmp_path, name):
    engine = create_engine(f"sqlite:///{tmp_path / name}", future=True)
    initialize_schema(engine)
    return engine


def _queue(engine, key, publication):
    return queue_publication(
        engine,
        publication_key=key,
        lifecycle_event=publication.lifecycle_event,
        authorization=publication.authorization,
        escrow=publication.escrow,
    )


def test_outbox_queues_authoritative_facts_once(tmp_path):
    engine = _engine(tmp_path, "outbox.db")
    publication = _publication()
    assert _queue(engine, "AUTH-WIRING", publication) is True
    assert _queue(engine, "AUTH-WIRING", publication) is False
    with engine.connect() as connection:
        rows = connection.execute(select(SHUUDPublicationOutbox)).fetchall()
    assert len(rows) == 1
    assert rows[0].status == "PENDING"


def test_pending_publication_becomes_durable_and_published(tmp_path):
    engine = _engine(tmp_path, "publish.db")
    publication = _publication()
    _queue(engine, "AUTH-PUBLISH", publication)
    assert publish_pending(engine) == 1
    with engine.connect() as connection:
        outbox = connection.execute(select(SHUUDPublicationOutbox)).fetchall()
        assert outbox[0].status == "PUBLISHED"
        assert outbox[0].attempts == 1
        assert len(connection.execute(select(SHUUDLifecycleEvent)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDReleaseAuthorizationRecord)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDEscrowRecord)).fetchall()) == 1


def test_retry_after_settlement_commit_does_not_duplicate_records(tmp_path):
    engine = _engine(tmp_path, "retry.db")
    publication = _publication()
    _queue(engine, "AUTH-RETRY", publication)
    from shuud.persistence import atomic_settlement
    atomic_settlement(
        engine,
        lifecycle_event=publication.lifecycle_event,
        authorization=publication.authorization,
        escrow=publication.escrow,
    )
    assert publish_pending(engine) == 1
    with engine.connect() as connection:
        outbox = connection.execute(select(SHUUDPublicationOutbox)).fetchall()
        assert outbox[0].status == "PUBLISHED"
        assert len(connection.execute(select(SHUUDLifecycleEvent)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDReleaseAuthorizationRecord)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDEscrowRecord)).fetchall()) == 1


def test_conflicting_durable_settlement_fails_closed(tmp_path):
    engine = _engine(tmp_path, "conflict.db")
    publication = _publication()
    _queue(engine, "AUTH-CONFLICT", publication)
    from shuud.persistence import atomic_settlement
    conflicting = {
        "lifecycle_event": dict(publication.lifecycle_event),
        "authorization": dict(publication.authorization),
        "escrow": dict(publication.escrow),
    }
    conflicting["authorization"]["authorization_hash"] = "DIFFERENT-AUTH"
    atomic_settlement(engine, **conflicting)
    assert publish_pending(engine) == 0
    with engine.connect() as connection:
        outbox = connection.execute(select(SHUUDPublicationOutbox)).fetchall()
        assert outbox[0].status == "FAILED"
        assert "conflicting" in outbox[0].last_error


def test_failed_publication_remains_retryable_on_transient_error(tmp_path, monkeypatch):
    engine = _engine(tmp_path, "transient.db")
    publication = _publication()
    _queue(engine, "AUTH-TRANSIENT", publication)
    import shuud.publication_outbox as outbox_module
    original = outbox_module.atomic_settlement
    calls = {"count": 0}
    def fail_once(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("database temporarily unavailable")
        return original(*args, **kwargs)
    monkeypatch.setattr(outbox_module, "atomic_settlement", fail_once)
    assert publish_pending(engine) == 0
    with engine.connect() as connection:
        row = connection.execute(select(SHUUDPublicationOutbox)).fetchone()
        assert row.status == "PENDING"
        assert row.attempts == 1
        assert "temporarily unavailable" in row.last_error
    assert publish_pending(engine) == 1
    with engine.connect() as connection:
        row = connection.execute(select(SHUUDPublicationOutbox)).fetchone()
        assert row.status == "PUBLISHED"
        assert row.attempts == 2
        assert row.last_error is None


def test_concurrent_workers_claim_one_publication(tmp_path, monkeypatch):
    engine = _engine(tmp_path, "concurrent.db")
    publication = _publication()
    _queue(engine, "AUTH-CONCURRENT", publication)
    import shuud.publication_outbox as outbox_module
    original = outbox_module.atomic_settlement
    calls = {"count": 0}
    def slow_settlement(*args, **kwargs):
        calls["count"] += 1
        sleep(0.05)
        return original(*args, **kwargs)
    monkeypatch.setattr(outbox_module, "atomic_settlement", slow_settlement)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: publish_pending(engine), range(2)))
    assert sorted(results) == [0, 1]
    assert calls["count"] == 1
    with engine.connect() as connection:
        row = connection.execute(select(SHUUDPublicationOutbox)).fetchone()
        assert row.status == "PUBLISHED"
        assert row.attempts == 1
        assert len(connection.execute(select(SHUUDLifecycleEvent)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDReleaseAuthorizationRecord)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDEscrowRecord)).fetchall()) == 1


def test_stale_processing_claim_is_recovered_and_published(tmp_path):
    engine = _engine(tmp_path, "stale.db")
    publication = _publication()
    _queue(engine, "AUTH-STALE", publication)
    with engine.connect() as connection:
        row = connection.execute(select(SHUUDPublicationOutbox)).fetchone()
        row_id = row.id
    with engine.begin() as connection:
        connection.execute(
            SHUUDPublicationOutbox.__table__.update()
            .where(SHUUDPublicationOutbox.id == row_id)
            .values(
                status="PROCESSING",
                attempts=1,
                processing_at=datetime.now(timezone.utc) - timedelta(seconds=601),
                last_error="worker crashed",
            )
        )
    assert publish_pending(engine, claim_timeout_seconds=600) == 1
    with engine.connect() as connection:
        row = connection.execute(select(SHUUDPublicationOutbox)).fetchone()
        assert row.status == "PUBLISHED"
        assert row.attempts == 2
        assert row.processing_at is None
        assert row.last_error is None
        assert len(connection.execute(select(SHUUDLifecycleEvent)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDReleaseAuthorizationRecord)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDEscrowRecord)).fetchall()) == 1
