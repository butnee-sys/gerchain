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
from persistence.signed_change_authorization import canonical_payload_hash, canonical_release_payload
from services.gerchain_runtime import GerchainRuntime


def _signed_release(evidence):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    owner_id = "owner-1"
    root = RootOfTrust(owner_id, base64.b64encode(public_key).decode("ascii"))
    payload = canonical_release_payload(
        transaction_id="release-1", escrow_id="escrow-1",
        source="escrow-1", destination="bob", amount=40, currency="USD",
        decision_status="APPROVE", trust=True, transparency=True,
        performance=True, evidence_verified=True, evidence=evidence,
    )
    unsigned = SignedChange(
        owner_id=owner_id, change_id="change-release-1", version=1,
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


def test_production_runtime_release_uses_canonical_ledger(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for base in (AtomicLedgerBase, EscrowBase, WitnessBase, IdempotencyBase, OutboxBase):
        base.metadata.create_all(engine)
    sf = sessionmaker(bind=engine)
    now = datetime.now(timezone.utc)
    with sf.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="escrow-1", currency="USD", balance=40, version=1, updated_at=now),
            LedgerAccountModel(account_id="bob", currency="USD", balance=10, version=0, updated_at=now),
            CanonicalEscrow(
                id="escrow-1", sender_address="alice", receiver_address="bob",
                amount=40, state=EscrowState.LOCKED.value, condition_desc=None,
                refund_destination="alice", currency="USD", version=2,
                created_at=now, updated_at=now,
            ),
        ])
    evidence = {"evidence": "verified"}
    root, signed_change, owner_id = _signed_release(evidence)
    monkeypatch.setenv("GERCHAIN_AUTH_OWNER_ID", owner_id)
    monkeypatch.setenv(
        "GERCHAIN_AUTH_PUBLIC_KEY_B64", root.public_key_b64
    )
    runtime = GerchainRuntime(
        escrow_id="escrow-1", amount=40, currency="USD", witness_id="w-1"
    )
    runtime.configure_root_of_trust(root)
    runtime.configure_canonical_ledger(sf)
    result = runtime.release(
        transaction_id="release-1", destination="bob", timestamp="T2",
        evidence=evidence, root=root, signed_change=signed_change,
        owner_id=owner_id, authorized=True, evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        source="alice",
    )
    assert result["replayed"] is False
    with sf() as session:
        assert session.get(LedgerAccountModel, "escrow-1").balance == 0
        assert session.get(LedgerAccountModel, "bob").balance == 50
        assert session.get(CanonicalEscrow, "escrow-1").state == "RELEASED"
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1
    engine.dispose()
