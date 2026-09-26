from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.transactional_outbox import deterministic_event_id, enqueue_in_transaction


def test_outbox_replay_with_same_payload_is_idempotent():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    OutboxBase.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)

    with factory.begin() as session:
        event_id = deterministic_event_id("GERCHAIN_RELEASED", "T1")
        assert enqueue_in_transaction(
            session,
            event_id=event_id,
            event_type="GERCHAIN_RELEASED",
            aggregate_id="E1",
            payload={"transaction_id": "T1", "amount": 100},
        ) is True
        assert enqueue_in_transaction(
            session,
            event_id=event_id,
            event_type="GERCHAIN_RELEASED",
            aggregate_id="E1",
            payload={"amount": 100, "transaction_id": "T1"},
        ) is False

    with factory() as session:
        assert session.query(OutboxEvent).count() == 1


def test_outbox_replay_with_different_payload_is_conflict():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    OutboxBase.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)

    with factory.begin() as session:
        event_id = deterministic_event_id("GERCHAIN_RELEASED", "T1")
        enqueue_in_transaction(
            session,
            event_id=event_id,
            event_type="GERCHAIN_RELEASED",
            aggregate_id="E1",
            payload={"transaction_id": "T1", "amount": 100},
        )

    with factory() as session:
        try:
            enqueue_in_transaction(
                session,
                event_id=event_id,
                event_type="GERCHAIN_RELEASED",
                aggregate_id="E1",
                payload={"transaction_id": "T1", "amount": 101},
            )
        except ValueError as exc:
            assert "outbox event conflict" in str(exc)
        else:
            raise AssertionError("expected outbox event conflict")
