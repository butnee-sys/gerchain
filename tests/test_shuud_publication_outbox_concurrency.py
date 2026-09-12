"""SH-16.15 concurrent publication worker and lease safety tests."""

from datetime import datetime, timedelta, timezone
from threading import Barrier, Thread

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from shuud.persistence import SHUUDPersistenceBase, SHUUDReleaseAuthorizationRecord, SHUUDEscrowRecord, SHUUDLifecycleEvent
from shuud.publication_outbox import SHUUDPublicationOutbox, publish_pending, queue_publication
from tests.test_shuud_production_wiring import _publication


def _engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'concurrency.db'}", future=True)
    SHUUDPersistenceBase.metadata.create_all(engine)
    return engine


def test_two_workers_publish_one_queued_publication(tmp_path):
    engine = _engine(tmp_path)
    publication = _publication()
    assert queue_publication(engine, publication_key="PUB-CONCURRENT", **publication.__dict__)

    barrier = Barrier(2)
    results = []

    def worker():
        barrier.wait()
        results.append(publish_pending(engine))

    threads = [Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sum(results) == 1
    with Session(engine) as session:
        assert session.scalar(select(SHUUDPublicationOutbox).where(SHUUDPublicationOutbox.publication_key == "PUB-CONCURRENT")).status == "PUBLISHED"
        assert len(session.scalars(select(SHUUDReleaseAuthorizationRecord)).all()) == 1
        assert len(session.scalars(select(SHUUDEscrowRecord)).all()) == 1
        assert len(session.scalars(select(SHUUDLifecycleEvent)).all()) == 1


def test_stale_processing_claim_is_recovered(tmp_path):
    engine = _engine(tmp_path)
    publication = _publication()
    assert queue_publication(engine, publication_key="PUB-STALE", **publication.__dict__)

    with Session(engine) as session:
        row = session.scalar(select(SHUUDPublicationOutbox).where(SHUUDPublicationOutbox.publication_key == "PUB-STALE"))
        row.status = "PROCESSING"
        row.processing_at = datetime.now(timezone.utc) - timedelta(seconds=301)
        session.commit()

    assert publish_pending(engine, claim_timeout_seconds=300) == 1
    with Session(engine) as session:
        row = session.scalar(select(SHUUDPublicationOutbox).where(SHUUDPublicationOutbox.publication_key == "PUB-STALE"))
        assert row.status == "PUBLISHED"
        assert row.processing_at is None
        assert len(session.scalars(select(SHUUDReleaseAuthorizationRecord)).all()) == 1


def test_fresh_processing_claim_is_not_recovered(tmp_path):
    engine = _engine(tmp_path)
    publication = _publication()
    assert queue_publication(engine, publication_key="PUB-FRESH", **publication.__dict__)

    with Session(engine) as session:
        row = session.scalar(select(SHUUDPublicationOutbox).where(SHUUDPublicationOutbox.publication_key == "PUB-FRESH"))
        row.status = "PROCESSING"
        row.processing_at = datetime.now(timezone.utc)
        session.commit()

    assert publish_pending(engine, claim_timeout_seconds=300) == 0
    with Session(engine) as session:
        row = session.scalar(select(SHUUDPublicationOutbox).where(SHUUDPublicationOutbox.publication_key == "PUB-FRESH"))
        assert row.status == "PROCESSING"
