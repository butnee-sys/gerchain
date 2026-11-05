
def _signed_release(*, transaction_id, escrow_id, destination, amount, currency, evidence, monkeypatch, transparency=True):
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    public_key_b64 = base64.b64encode(public_key).decode("ascii")
    owner_id = "release-escrow-test-owner"
    monkeypatch.setenv("GERCHAIN_AUTH_OWNER_ID", owner_id)
    monkeypatch.setenv("GERCHAIN_AUTH_PUBLIC_KEY_B64", public_key_b64)
    root = RootOfTrust(owner_id=owner_id, public_key_b64=public_key_b64)
    payload = canonical_release_payload(
        transaction_id=transaction_id, escrow_id=escrow_id,
        source=escrow_id, destination=destination, amount=amount,
        currency=currency, decision_status="APPROVE", trust=True,
        transparency=transparency, performance=True, evidence_verified=True,
        evidence=evidence,
    )
    unsigned = SignedChange(
        owner_id=owner_id, change_id=f"CHANGE-{transaction_id}", version=1,
        payload_hash=canonical_payload_hash(payload), signature="",
    )
    signing_bytes = json.dumps(
        unsigned.signing_payload(), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    signed_change = SignedChange(
        owner_id=owner_id, change_id=unsigned.change_id, version=1,
        payload_hash=unsigned.payload_hash,
        signature=base64.b64encode(private_key.sign(signing_bytes)).decode("ascii"),
    )
    return root, signed_change, owner_id

from __future__ import annotations

from datetime import datetime, timezone
import os

import base64
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from dee_security.root_of_trust import RootOfTrust, SignedChange
from persistence.signed_change_authorization import (
    SignedChangeAuthorization, canonical_release_payload, canonical_payload_hash,
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.release_escrow import release_escrow_in_transaction


def _setup():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    WitnessBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    AuthorizationBase.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)


def _seed(factory):
    now = datetime.now(timezone.utc)
    with factory.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="E1", currency="MNT", balance=100, version=1, updated_at=now),
            LedgerAccountModel(account_id="BEN", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="E1", sender_address="SOURCE", receiver_address="BEN",
                amount=100, state=EscrowState.LOCKED.value, condition_desc="ok",
                refund_destination="SOURCE", currency="MNT", version=2,
                created_at=now, updated_at=now,
            ),
        ])


def _release(session, monkeypatch, tx="R1", transparency=True):
    evidence = {"proof": "release-test"}
    root, signed_change, owner_id = _signed_release(\n        transaction_id=tx, escrow_id="E1", destination="BEN", amount=100,\n        currency="MNT", evidence=evidence, monkeypatch=monkeypatch,\n        transparency=transparency,\n    )
    return release_escrow_in_transaction(
        session,
        transaction_id=tx,
        escrow_id="E1",
        beneficiary="BEN",
        amount=100,
        currency="MNT",
        decision_status="APPROVE",
        root=root,\n        signed_change=signed_change,\n        owner_id=owner_id,
        trust=True,
        transparency=transparency,
        performance=True,
        evidence_verified=True,
        payload={"evidence": evidence},
    )


def test_release_moves_value_and_transitions_atomically(monkeypatch):
    factory = _setup()
    _seed(factory)

    with factory.begin() as session:
        result = _release(session, monkeypatch)
        assert result["replayed"] is False

    with factory() as session:
        assert session.get(LedgerAccountModel, "E1").balance == 0
        assert session.get(LedgerAccountModel, "BEN").balance == 100
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.RELEASED.value
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1
        assert session.get(DurableIdempotencyRecord, 1).state == "COMPLETED"
        assert session.query(SignedChangeAuthorization).count() == 1


def test_release_rejects_missing_governance_before_value_movement(monkeypatch):
    factory = _setup()
    _seed(factory)

    evidence = {"proof": "release-test"}
    root, signed_change, owner_id = _signed_release(
        transaction_id="R1", escrow_id="E1", destination="BEN", amount=100,
        currency="MNT", evidence=evidence, monkeypatch=monkeypatch,
        transparency=False,
    )
    with factory.begin() as session:
        try:
            release_escrow_in_transaction(
                session, transaction_id="R1", escrow_id="E1",
                beneficiary="BEN", amount=100, currency="MNT",
                decision_status="APPROVE", root=root,
                signed_change=signed_change, owner_id=owner_id,
                trust=True, transparency=False, performance=True,
                evidence_verified=True, payload={"evidence": evidence},
            )
        except ValueError as exc:
            assert "complete trust evidence" in str(exc)
        else:
            raise AssertionError("expected governance rejection")

    with factory() as session:
        assert session.get(LedgerAccountModel, "E1").balance == 100
        assert session.get(LedgerAccountModel, "BEN").balance == 0
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.LOCKED.value
        assert session.query(LedgerMovementModel).count() == 0


def test_release_replay_does_not_move_value_twice(monkeypatch):
    factory = _setup()
    _seed(factory)

    with factory.begin() as session:
        _release(session, monkeypatch)

    with factory.begin() as session:
        result = _release(session)
        assert result["replayed"] is True

    with factory() as session:
        assert session.get(LedgerAccountModel, "E1").balance == 0
        assert session.get(LedgerAccountModel, "BEN").balance == 100
        assert session.query(LedgerMovementModel).count() == 1
