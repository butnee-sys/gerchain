"""Real PostgreSQL integration contracts for SHUUD durable settlement.

These tests are intentionally skipped unless SHUUD_TEST_POSTGRES_URL is set.
They exercise real PostgreSQL transaction semantics rather than emulating them
with SQLite. WitnessChain and EscrowEngine remain outside this persistence
projection and therefore are not replaced by these tests.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shuud.persistence import (
    SHUUDLifecycleEvent,
    SHUUDReleaseAuthorizationRecord,
    SHUUDEscrowRecord,
    atomic_settlement,
    initialize_schema,
)
from shuud.publication_outbox import (
    SHUUDPublicationOutbox,
    publish_pending,
    queue_publication,
)

POSTGRES_URL = os.getenv("SHUUD_TEST_POSTGRES_URL", "").strip()
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="SHUUD_TEST_POSTGRES_URL is not configured",
)


def _engine():
    engine = create_engine(
        POSTGRES_URL,
        future=True,
        isolation_level="SERIALIZABLE",
        pool_pre_ping=True,
    )
    initialize_schema(engine)
    return engine


def _publication(prefix: str | None = None):
    suffix = prefix or uuid4().hex[:12]
    incident_id = f"PG-{suffix}"
    escrow_id = f"ESC-PG-{suffix}"
    authorization_hash = f"AUTH-PG-{suffix}"
    event_id = f"EV-PG-{suffix}"
    return (
        {
            "incident_id": incident_id,
            "event_id": event_id,
            "event_type": "SHUUD_RELEASED",
            "sequence": 1,
            "event_hash": f"EVENT-HASH-{suffix}",
            "payload_json": "{}",
            "evidence_json": "{}",
        },
        {
            "incident_id": incident_id,
            "escrow_id": escrow_id,
            "rule_version": "SHUUD-POLICY-1",
            "authorization_hash": authorization_hash,
            "damage_estimate_nef": "1500000",
            "authorization_json": "{}",
            "witness_event_id": event_id,
        },
        {
            "incident_id": incident_id,
            "escrow_id": escrow_id,
            "state": "RELEASED",
            "amount_nef": "1500000",
            "currency": "NEF",
            "transition_counter": 2,
        },
    )


def test_postgresql_uses_serializable_transactions_and_schema_bootstrap():
    engine = _engine()
    try:
        with engine.connect() as connection:
            isolation = connection.execute(text("SHOW transaction_isolation")).scalar_one()
            assert isolation == "serializable"
            assert connection.execute(
                text("SELECT to_regclass('public.shuud_schema_version')")
            ).scalar_one() == "shuud_schema_version"
            assert connection.execute(
                text("SELECT to_regclass('public.shuud_publication_outbox')")
            ).scalar_one() == "shuud_publication_outbox"
    finally:
        engine.dispose()


def test_postgresql_concurrent_schema_bootstrap_is_serialized():
    def bootstrap(url):
        engine = create_engine(url, future=True, pool_pre_ping=True)
        try:
            initialize_schema(engine)
            return None
        except Exception as exc:  # noqa: BLE001 - test reports exact failure
            return repr(exc)
        finally:
            engine.dispose()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(bootstrap, [POSTGRES_URL, POSTGRES_URL]))

    assert [result for result in results if result is not None] == []


def test_postgresql_duplicate_settlement_rolls_back_the_second_transaction():
    engine = _engine()
    first, authorization, escrow = _publication("DUP")
    second = dict(first, event_id=f"{first['event_id']}-CONFLICT", event_hash="EVENT-HASH-CONFLICT")
    try:
        atomic_settlement(
            engine,
            lifecycle_event=first,
            authorization=authorization,
            escrow=escrow,
        )

        with pytest.raises(IntegrityError):
            atomic_settlement(
                engine,
                lifecycle_event=second,
                authorization=authorization,
                escrow=escrow,
            )

        with Session(engine, expire_on_commit=False) as session:
            assert session.scalar(
                select(SHUUDReleaseAuthorizationRecord).where(
                    SHUUDReleaseAuthorizationRecord.incident_id == first["incident_id"]
                )
            ) is not None
            assert session.scalar(
                select(SHUUDEscrowRecord).where(
                    SHUUDEscrowRecord.incident_id == first["incident_id"]
                )
            ) is not None
            events = session.scalars(
                select(SHUUDLifecycleEvent).where(
                    SHUUDLifecycleEvent.incident_id == first["incident_id"]
                )
            ).all()
            assert len(events) == 1
            assert events[0].event_id == first["event_id"]
    finally:
        engine.dispose()


def test_postgresql_concurrent_outbox_workers_publish_exactly_once():
    engine = _engine()
    lifecycle_event, authorization, escrow = _publication("OUTBOX")
    key = f"PUB-PG-{uuid4().hex}"
    try:
        assert queue_publication(
            engine,
            publication_key=key,
            lifecycle_event=lifecycle_event,
            authorization=authorization,
            escrow=escrow,
        ) is True

        def worker():
            worker_engine = create_engine(
                POSTGRES_URL,
                future=True,
                isolation_level="SERIALIZABLE",
                pool_pre_ping=True,
            )
            try:
                return publish_pending(worker_engine, limit=1)
            finally:
                worker_engine.dispose()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))

        assert sum(results) == 1
        with Session(engine, expire_on_commit=False) as session:
            row = session.scalar(
                select(SHUUDPublicationOutbox).where(
                    SHUUDPublicationOutbox.publication_key == key
                )
            )
            assert row is not None
            assert row.status == "PUBLISHED"
            assert row.attempts >= 1
            assert session.scalar(
                select(SHUUDReleaseAuthorizationRecord).where(
                    SHUUDReleaseAuthorizationRecord.incident_id == lifecycle_event["incident_id"]
                )
            ) is not None
            assert session.scalar(
                select(SHUUDEscrowRecord).where(
                    SHUUDEscrowRecord.incident_id == lifecycle_event["incident_id"]
                )
            ) is not None
            assert len(
                session.scalars(
                    select(SHUUDLifecycleEvent).where(
                        SHUUDLifecycleEvent.incident_id == lifecycle_event["incident_id"]
                    )
                ).all()
            ) == 1
    finally:
        engine.dispose()
