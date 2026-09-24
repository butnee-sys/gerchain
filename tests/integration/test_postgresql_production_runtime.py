from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyEngine
from persistence.escrow_aggregate import CanonicalEscrow
from persistence.recovery_outbox import OutboxEvent
from persistence.transactional_outbox import deterministic_event_id
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def _hash(tx, operation, escrow_id, source, destination, amount, currency):
    material = json.dumps(
        {
            "transaction_id": tx,
            "operation": operation,
            "escrow_id": escrow_id,
            "source": source,
            "destination": destination,
            "amount": amount,
            "currency": currency,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode()).hexdigest()


def test_production_factory_boots_against_real_postgresql():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-escrow-1",
            amount=10,
            currency="USD",
            witness_id="pg-witness-1",
        ),
        engine=engine,
    ).create()
    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"


def test_postgresql_deep_value_truth_reconciliation():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    session_factory = __import__("sqlalchemy").orm.sessionmaker(bind=engine, expire_on_commit=False)
    ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-escrow-2",
            amount=10,
            currency="USD",
            witness_id="pg-witness-2",
        ),
        engine=engine,
    ).create()
    now = datetime.now(timezone.utc)
    tx = "pg-release-1"
    escrow_id = "pg-escrow-2"
    source = "pg-source"
    destination = "pg-beneficiary"
    amount = 10
    currency = "USD"

    with session_factory() as session:
        session.add_all(
            [
                LedgerAccountModel(account_id=source, currency=currency, balance=90, version=1, updated_at=now),
                LedgerAccountModel(account_id=destination, currency=currency, balance=10, version=1, updated_at=now),
                CanonicalEscrow(
                    id=escrow_id,
                    sender_address=source,
                    receiver_address=destination,
                    amount=amount,
                    state="RELEASED",
                    condition_desc="integration",
                    refund_destination=source,
                    currency=currency,
                    version=1,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        movement = LedgerMovementModel(
            transaction_id=tx,
            source=source,
            destination=destination,
            amount=amount,
            currency=currency,
            operation="RELEASE",
            escrow_id=escrow_id,
            integrity_hash=_hash(tx, "RELEASE", escrow_id, source, destination, amount, currency),
            created_at=now,
        )
        session.add(movement)
        session.add(
            TransactionWitness(
                transaction_id=tx,
                event_type="GERCHAIN_RELEASE",
                escrow_id=escrow_id,
                amount=amount,
                created_at=now,
            )
        )
        payload = {"escrow_id": escrow_id, "operation": "RELEASE"}
        session.add(
            DurableIdempotencyRecord(
                key=tx,
                fingerprint=IdempotencyEngine.fingerprint(payload),
                result_json=json.dumps({"status": "RELEASED"}),
                state="COMPLETED",
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            OutboxEvent(
                event_id=deterministic_event_id("GERCHAIN_RELEASE", tx),
                event_type="GERCHAIN_RELEASE",
                aggregate_id=escrow_id,
                payload_json=json.dumps(payload),
                state="PENDING",
                attempts=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

