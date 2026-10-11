from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.idempotency import IdempotencyEngine
from persistence.durable_idempotency import (
    DurableIdempotencyRecord,
    IdempotencyBase,
    begin_in_transaction,
    complete_in_transaction,
    get_existing_in_transaction,
)
from persistence.recovery_outbox import OutboxBase, OutboxEvent, PostgreSQLOutbox


def _file_database(path):
    engine = create_engine(f"sqlite:///{path}", future=True)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def test_restart_replays_completed_idempotency_without_creating_second_record(tmp_path):
    db_path = tmp_path / "restart-idempotency.db"
    payload = {
        "transaction_id": "restart-tx-1",
        "operation": "RELEASE",
        "escrow_id": "restart-escrow-1",
        "source": "restart-escrow-1",
        "destination": "beneficiary-1",
        "amount": 25,
        "currency": "USD",
    }
    result_json = json.dumps({"status": "RELEASED", "movement_count": 1}, sort_keys=True)

    engine1, factory1 = _file_database(db_path)
    with factory1() as session:
        assert begin_in_transaction(session, key="restart-tx-1", payload=payload) is None
        session.flush()
        complete_in_transaction(
            session, key="restart-tx-1", payload=payload, result_json=result_json
        )
        session.commit()
    engine1.dispose()

    # Simulate a process restart: dispose the first engine and build a fresh one.
    engine2, factory2 = _file_database(db_path)
    with factory2() as session:
        replay = get_existing_in_transaction(
            session, key="restart-tx-1", payload=payload
        )
        assert replay == result_json
        assert session.execute(
            select(DurableIdempotencyRecord).where(
                DurableIdempotencyRecord.key == "restart-tx-1"
            )
        ).scalars().all().__len__() == 1
    engine2.dispose()


def test_outbox_expired_lease_recovers_after_worker_restart(tmp_path):
    db_path = tmp_path / "restart-outbox.db"
    engine1, factory1 = _file_database(db_path)
    now = datetime.now(timezone.utc)
    with factory1() as session:
        session.add(
            OutboxEvent(
                event_id="gerchain_release:restart-tx-2",
                event_type="GERCHAIN_RELEASED",
                aggregate_id="restart-escrow-2",
                payload_json='{"transaction_id":"restart-tx-2"}',
                state="PROCESSING",
                lease_until=now - timedelta(minutes=5),
                attempts=1,
                created_at=now - timedelta(minutes=10),
                updated_at=now - timedelta(minutes=5),
            )
        )
        session.commit()
    engine1.dispose()

    # New worker/service instance sees the persisted expired lease.
    engine2, factory2 = _file_database(db_path)
    outbox = PostgreSQLOutbox(factory2, lease_seconds=60)
    assert outbox.recover_expired() == 1
    claimed = outbox.claim(limit=10)
    assert len(claimed) == 1
    assert claimed[0].event_id == "gerchain_release:restart-tx-2"
    assert claimed[0].attempts == 2

    with factory2() as session:
        event = session.execute(
            select(OutboxEvent).where(
                OutboxEvent.event_id == "gerchain_release:restart-tx-2"
            )
        ).scalar_one()
        assert event.state == "PROCESSING"
        assert event.attempts == 2
    engine2.dispose()
