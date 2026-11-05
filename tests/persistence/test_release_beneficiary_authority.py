from datetime import datetime, timezone
import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import TransactionWitness
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.release_escrow import release_escrow_in_transaction
from persistence.signed_change_authorization import AuthorizationBase, SignedChangeAuthorization, canonical_release_payload, canonical_payload_hash
from dee_security.root_of_trust import RootOfTrust, SignedChange
from persistence.recovery_outbox import OutboxBase


def _factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    TransactionWitness.metadata.create_all(engine)
    AuthorizationBase.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)



def _signed_release_for_destination(destination):
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    public_key_b64 = base64.b64encode(public_key).decode("ascii")
    owner_id = "release-beneficiary-test-owner"
    payload = canonical_release_payload(
        transaction_id="tx-release-redirect", escrow_id="esc-release",
        source="esc-release", destination=destination, amount=10,
        currency="USD", decision_status="APPROVE", trust=True,
        transparency=True, performance=True, evidence_verified=True,
        evidence={"reason": "beneficiary authorization test"},
    )
    unsigned = SignedChange(
        owner_id=owner_id, change_id="CHANGE-RELEASE-REDIRECT", version=1,
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
    return RootOfTrust(owner_id, public_key_b64), signed, owner_id, public_key_b64


def test_release_cannot_redirect_authoritative_beneficiary(monkeypatch):
    engine, factory = _factory()
    with factory() as session:
        now = datetime.now(timezone.utc)
        session.add(CanonicalEscrow(
            id="esc-release",
            sender_address="SRC",
            receiver_address="BENEFICIARY",
            amount=10,
            state=EscrowState.LOCKED.value,
            condition_desc="test",
            refund_destination="SRC",
            currency="USD",
            version=1,
            created_at=now,
            updated_at=now,
        ))
        session.commit()

        root, signed_change, owner_id, public_key_b64 = _signed_release_for_destination("ATTACKER")
        monkeypatch.setenv("GERCHAIN_AUTH_OWNER_ID", owner_id)
        monkeypatch.setenv("GERCHAIN_AUTH_PUBLIC_KEY_B64", public_key_b64)
        with pytest.raises(ValueError, match="authoritative escrow beneficiary"):
            release_escrow_in_transaction(
                session,
                transaction_id="tx-release-redirect",
                escrow_id="esc-release",
                beneficiary="ATTACKER",
                amount=10,
                currency="USD",
                decision_status="APPROVE",
                root=root,
                signed_change=signed_change,
                owner_id=owner_id,
                trust=True,
                transparency=True,
                performance=True,
                evidence_verified=True,
                payload={"evidence": {"reason": "beneficiary authorization test"}},
            )

        session.rollback()
        assert session.get(CanonicalEscrow, "esc-release").state == EscrowState.LOCKED.value
        assert session.query(TransactionWitness).count() == 0
        assert session.query(SignedChangeAuthorization).count() == 0
    engine.dispose()
