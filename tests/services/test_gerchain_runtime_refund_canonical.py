from datetime import datetime, timezone
import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dee_security.root_of_trust import RootOfTrust, SignedChange
from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.signed_change_authorization import AuthorizationBase, canonical_payload_hash, canonical_refund_payload
from services.gerchain_runtime import GerchainRuntime


def _signed_refund(evidence):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    owner_id = "refund-runtime-owner"
    root = RootOfTrust(owner_id, base64.b64encode(public_key).decode("ascii"))
    payload = canonical_refund_payload(
        transaction_id="RF1", escrow_id="E1", source="E1",
        destination="SRC", amount=40, currency="MNT",
        authorized=True, transparency=True,
        dispute_or_cancellation_verified=True, evidence=evidence,
    )
    unsigned = SignedChange(
        owner_id=owner_id, change_id="CHANGE-RF1", version=1,
        payload_hash=canonical_payload_hash(payload), signature="",
    )
    signature = private_key.sign(json.dumps(
        unsigned.signing_payload(), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8"))
    signed_change = SignedChange(
        owner_id=owner_id, change_id=unsigned.change_id, version=1,
        payload_hash=unsigned.payload_hash,
        signature=base64.b64encode(signature).decode("ascii"),
    )
    return root, signed_change, owner_id


def test_production_runtime_refund_uses_authoritative_refund_destination(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for base in (AtomicLedgerBase, EscrowBase, WitnessBase, IdempotencyBase, OutboxBase, AuthorizationBase):
        base.metadata.create_all(engine)
    sf = sessionmaker(bind=engine)
    now = datetime.now(timezone.utc)
    with sf.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="E1", currency="MNT", balance=40, version=1, updated_at=now),
            LedgerAccountModel(account_id="SRC", currency="MNT", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="ATTACKER", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="E1", sender_address="SRC", receiver_address="BEN",
                amount=40, state=EscrowState.LOCKED.value, condition_desc="ok",
                refund_destination="SRC", currency="MNT", version=2,
                created_at=now, updated_at=now,
            ),
        ])
    evidence = {"verified": True, "reason": "not_performed"}
    root, signed_change, owner_id = _signed_refund(evidence)
    monkeypatch.setenv("GERCHAIN_AUTH_OWNER_ID", owner_id)
    monkeypatch.setenv("GERCHAIN_AUTH_PUBLIC_KEY_B64", root.public_key_b64)
    runtime = GerchainRuntime(escrow_id="E1", amount=40, currency="MNT", witness_id="w")
    runtime.configure_root_of_trust(root)
    runtime.configure_canonical_ledger(sf)
    result = runtime.refund(
        transaction_id="RF1", destination="ATTACKER", timestamp="T3",
        evidence=evidence, root=root, signed_change=signed_change,
        owner_id=owner_id, authorized=True, transparency=True,
        dispute_or_cancellation_verified=True,
    )
    assert result["replayed"] is False
    with sf() as session:
        assert session.get(LedgerAccountModel, "E1").balance == 0
        assert session.get(LedgerAccountModel, "SRC").balance == 40
        assert session.get(LedgerAccountModel, "ATTACKER").balance == 0
        assert session.get(CanonicalEscrow, "E1").state == "REFUNDED"
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1
    engine.dispose()
