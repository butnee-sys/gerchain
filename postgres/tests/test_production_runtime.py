from __future__ import annotations

import os
import base64
import json
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.recovery_outbox import OutboxEvent
from persistence.atomic_value_transaction import TransactionWitness
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.signed_change_authorization import (
    SignedChangeAuthorization,
    canonical_release_payload,
    canonical_payload_hash,
)
from dee_security.root_of_trust import RootOfTrust, SignedChange
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory

DATABASE_URL = os.environ.get("GERCHAIN_POSTGRES_DSN")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="GERCHAIN_POSTGRES_DSN is not configured")


def test_production_runtime_canonical_value_flow_and_reconciliation():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    runtime_factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=DATABASE_URL,
            escrow_id="production-reperf-1",
            amount=40,
            currency="MNT",
            witness_id="production-witness-1",
        ),
        engine=engine,
    )
    runtime = runtime_factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory() as session:
        session.query(OutboxEvent).delete()
        session.query(TransactionWitness).delete()
        session.query(DurableIdempotencyRecord).delete()
        session.query(SignedChangeAuthorization).delete()
        session.query(CanonicalEscrow).delete()
        session.query(LedgerAccountModel).delete()
        session.commit()

        session.add_all([
            LedgerAccountModel(account_id="production-source", currency="MNT", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="production-beneficiary", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="production-reperf-1",
                sender_address="production-source",
                receiver_address="production-beneficiary",
                amount=40,
                state=EscrowState.CREATED.value,
                condition_desc="production re-performance",
                refund_destination="production-source",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="production-fund-1",
            escrow_id="production-reperf-1",
            source="production-source",
            amount=40,
            currency="MNT",
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="production-lock-1",
            escrow_id="production-reperf-1",
        )
        session.commit()

        release_payload = canonical_release_payload(
            transaction_id="production-release-1",
            escrow_id="production-reperf-1",
            source="production-reperf-1",
            destination="production-beneficiary",
            amount=40,
            currency="MNT",
            decision_status="APPROVE",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            evidence=None,
        )
        unsigned_change = SignedChange(
            owner_id="production-test-owner",
            change_id="production-release-approval-1",
            version=1,
            payload_hash=canonical_payload_hash(release_payload),
            signature="",
        )
        signing_bytes = json.dumps(
            unsigned_change.signing_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        signed_change = SignedChange(
            owner_id=unsigned_change.owner_id,
            change_id=unsigned_change.change_id,
            version=unsigned_change.version,
            payload_hash=unsigned_change.payload_hash,
            signature=base64.b64encode(private_key.sign(signing_bytes)).decode("ascii"),
        )
        root = RootOfTrust(
            owner_id="production-test-owner",
            public_key_b64=base64.b64encode(public_key).decode("ascii"),
        )
        release_escrow_in_transaction(
            session,
            transaction_id="production-release-1",
            escrow_id="production-reperf-1",
            beneficiary="production-beneficiary",
            amount=40,
            currency="MNT",
            decision_status="APPROVE",
            root=root,
            signed_change=signed_change,
            owner_id="production-test-owner",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "production-reperf-1")
        ).scalar_one()
        assert escrow.state == EscrowState.RELEASED.value

        source = session.get(LedgerAccountModel, "production-source")
        beneficiary = session.get(LedgerAccountModel, "production-beneficiary")
        assert source.balance == 60
        assert beneficiary.balance == 40

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()
