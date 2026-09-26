from __future__ import annotations

import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.idempotency import IdempotencyConflictError
from persistence.durable_idempotency import (
    DurableIdempotencyRecord,
    IdempotencyBase,
    begin_in_transaction,
    complete_in_transaction,
)


def test_durable_idempotency_same_request_replays():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    IdempotencyBase.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)
    payload = {"transaction_id": "T1", "amount": 100}

    with factory.begin() as session:
        assert begin_in_transaction(session, key="K1", payload=payload) is None
        complete_in_transaction(
            session, key="K1", payload=payload,
            result_json=json.dumps({"status": "COMPLETED"}, sort_keys=True),
        )

    with factory() as session:
        result = begin_in_transaction(session, key="K1", payload=payload)
        assert json.loads(result)["status"] == "COMPLETED"


def test_durable_idempotency_different_request_conflicts():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    IdempotencyBase.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)

    with factory.begin() as session:
        begin_in_transaction(
            session, key="K1",
            payload={"transaction_id": "T1", "amount": 100},
        )

    with factory() as session:
        try:
            begin_in_transaction(
                session, key="K1",
                payload={"transaction_id": "T1", "amount": 101},
            )
        except IdempotencyConflictError:
            pass
        else:
            raise AssertionError("expected idempotency conflict")


def test_durable_idempotency_completion_is_atomic_with_outer_transaction():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    IdempotencyBase.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)

    try:
        with factory.begin() as session:
            begin_in_transaction(
                session, key="K1",
                payload={"transaction_id": "T1", "amount": 100},
            )
            complete_in_transaction(
                session, key="K1",
                payload={"transaction_id": "T1", "amount": 100},
                result_json='{"status":"COMPLETED"}',
            )
            raise RuntimeError("force rollback")
    except RuntimeError:
        pass

    with factory() as session:
        assert session.query(DurableIdempotencyRecord).count() == 0
