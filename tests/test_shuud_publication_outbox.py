"""SH-16.10 recoverable publication tests.

The outbox retries durable publication only. It never recreates WitnessChain
or EscrowEngine authority and never issues a second release decision.
"""

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


def test_outbox_queues_authoritative_facts_once(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'outbox.db'}", future=True)
    initialize_schema(engine)
    publication = _publication()

    assert queue_publication(
        engine,
        publication_key="AUTH-WIRING",
        lifecycle_event=publication.lifecycle_event,
        authorization=publication.authorization,
        escrow=publication.escrow,
    ) is True
    assert queue_publication(
        engine,
        publication_key="AUTH-WIRING",
        lifecycle_event=publication.lifecycle_event,
        authorization=publication.authorization,
        escrow=publication.escrow,
    ) is False

    with engine.connect() as connection:
        rows = connection.execute(select(SHUUDPublicationOutbox)).fetchall()
    assert len(rows) == 1
    assert rows[0].status == "PENDING"


def test_pending_publication_becomes_durable_and_published(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'publish.db'}", future=True)
    initialize_schema(engine)
    publication = _publication()
    queue_publication(
        engine,
        publication_key="AUTH-PUBLISH",
        lifecycle_event=publication.lifecycle_event,
        authorization=publication.authorization,
        escrow=publication.escrow,
    )

    assert publish_pending(engine) == 1

    with engine.connect() as connection:
        outbox = connection.execute(select(SHUUDPublicationOutbox)).fetchall()
        assert outbox[0].status == "PUBLISHED"
        assert outbox[0].attempts == 1
        assert len(connection.execute(select(SHUUDLifecycleEvent)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDReleaseAuthorizationRecord)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDEscrowRecord)).fetchall()) == 1


def test_retry_after_settlement_commit_does_not_duplicate_records(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'retry.db'}", future=True)
    initialize_schema(engine)
    publication = _publication()
    queue_publication(
        engine,
        publication_key="AUTH-RETRY",
        lifecycle_event=publication.lifecycle_event,
        authorization=publication.authorization,
        escrow=publication.escrow,
    )

    # Simulate a worker crash after the settlement transaction committed but
    # before the outbox acknowledgement was written.
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
