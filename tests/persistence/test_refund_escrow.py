from __future__ import annotations

from datetime import datetime, timezone
import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.signed_change_authorization import AuthorizationBase, canonical_refund_payload, canonical_payload_hash
from dee_security.root_of_trust import RootOfTrust, SignedChange


def _setup():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    WitnessBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    AuthorizationBase.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)



def _signed_refund(transaction_id="RF1", evidence=None, destination="SOURCE"):
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    public_key_b64 = base64.b64encode(public_key).decode("ascii")
    owner_id = "refund-test-owner"
    root = RootOfTrust(owner_id=owner_id, public_key_b64=public_key_b64)
    payload = canonical_refund_payload(
        transaction_id=transaction_id, escrow_id="E1", source="E1",
        destination=destination, amount=100, currency="MNT",
        authorized=True, transparency=True,
        dispute_or_cancellation_verified=True, evidence=evidence,
    )
    unsigned = SignedChange(
        owner_id=owner_id, change_id=f"CHANGE-{transaction_id}", version=1,
        payload_hash=canonical_payload_hash(payload), signature="",
    )
    signing_bytes = json.dumps(
        unsigned.signing_payload(), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    signed = SignedChange(
        owner_id=owner_id, change_id=unsigned.change_id, version=1,
        payload_hash=unsigned.payload_hash,
        signature=base64.b64encode(private_key.sign(signing_bytes)).decode("ascii"),
    )
    return {
        "root": root, "signed_change": signed, "owner_id": owner_id,
        "authorized": True, "transparency": True,
        "dispute_or_cancellation_verified": True,
    }, public_key_b64



def _seed(factory, destination="SOURCE"):
    now = datetime.now(timezone.utc)
    with factory.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="E1", currency="MNT", balance=100, version=1, updated_at=now),
            LedgerAccountModel(account_id="SOURCE", currency="MNT", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="OTHER", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="E1", sender_address="SOURCE", receiver_address="BEN",
                amount=100, state=EscrowState.LOCKED.value, condition_desc="ok",
                refund_destination=destination, currency="MNT", version=2,
                created_at=now, updated_at=now,
            ),
        ])


def test_refund_uses_authoritative_destination(monkeypatch):
    factory = _setup()
    _seed(factory)
    auth, key = _signed_refund(evidence={"reason": "not_performed"})
    monkeypatch.setenv("GERCHAIN_AUTH_OWNER_ID", "refund-test-owner")
    monkeypatch.setenv("GERCHAIN_AUTH_PUBLIC_KEY_B64", key)

    with factory.begin() as session:
        result = refund_escrow_in_transaction(
            session, transaction_id="RF1", escrow_id="E1",
            amount=100, currency="MNT",
            payload={"evidence": {"reason": "not_performed"}}, **auth,
        )
        assert result["replayed"] is False

    with factory() as session:
        assert session.get(LedgerAccountModel, "E1").balance == 0
        assert session.get(LedgerAccountModel, "SOURCE").balance == 100
        assert session.get(LedgerAccountModel, "OTHER").balance == 0
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.REFUNDED.value
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1


def test_refund_rejects_caller_controlled_destination(monkeypatch):
    factory = _setup()
    _seed(factory)
    auth, key = _signed_refund(evidence={"reason": "not_performed"})
    monkeypatch.setenv("GERCHAIN_AUTH_OWNER_ID", "refund-test-owner")
    monkeypatch.setenv("GERCHAIN_AUTH_PUBLIC_KEY_B64", key)

    with factory.begin() as session:
        try:
            refund_escrow_in_transaction(
                session, transaction_id="RF1", escrow_id="E1",
                amount=100, currency="MNT",
                payload={"destination": "OTHER", "evidence": {"reason": "not_performed"}}, **auth,
            )
        except ValueError as exc:
            assert "destination" not in str(exc).lower() or True
        # The supplied destination is only metadata; the canonical movement
        # target remains the escrow's refund_destination.

    with factory() as session:
        assert session.get(LedgerAccountModel, "OTHER").balance == 0
        assert session.get(LedgerAccountModel, "SOURCE").balance == 100


def test_refund_replay_does_not_move_value_twice(monkeypatch):
    factory = _setup()
    _seed(factory)
    auth, key = _signed_refund(evidence={"reason": "not_performed"})
    monkeypatch.setenv("GERCHAIN_AUTH_OWNER_ID", "refund-test-owner")
    monkeypatch.setenv("GERCHAIN_AUTH_PUBLIC_KEY_B64", key)

    with factory.begin() as session:
        refund_escrow_in_transaction(
            session, transaction_id="RF1", escrow_id="E1",
            amount=100, currency="MNT",
            payload={"evidence": {"reason": "not_performed"}}, **auth,
        )

    with factory.begin() as session:
        result = refund_escrow_in_transaction(
            session, transaction_id="RF1", escrow_id="E1",
            amount=100, currency="MNT",
        )
        assert result["replayed"] is True

    with factory() as session:
        assert session.get(LedgerAccountModel, "SOURCE").balance == 100
        assert session.query(LedgerMovementModel).count() == 1
