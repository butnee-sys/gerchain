from __future__ import annotations

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security import RootOfTrust, sign_change
from persistence.signed_change_authorization import canonical_release_payload, canonical_payload_hash
from services.gerchain_runtime import GerchainRuntime

from tests.test_g3_dee_authorized_handler import AMOUNT, ESCROW_ID, prepare_locked


_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
_PUBLIC_KEY = _PRIVATE_KEY.public_key().public_bytes(
    serialization.Encoding.Raw,
    serialization.PublicFormat.Raw,
)
_ROOT = RootOfTrust(
    "IDEMPOTENCY-OWNER",
    base64.b64encode(_PUBLIC_KEY).decode("ascii"),
)


def build_runtime():
    runtime = GerchainRuntime(
        escrow_id=ESCROW_ID,
        amount=AMOUNT,
        currency="MNT",
        witness_id="IDEMPOTENCY-WITNESS-001",
        initial_money_state={
            "currency": "MNT",
            "balances": {"INSURER": AMOUNT, ESCROW_ID: 0, "BENEFICIARY": 0, "OTHER": 0},
        },
    )
    runtime.configure_root_of_trust(_ROOT)
    runtime.create_account("INSURER", AMOUNT)
    runtime.create_account(ESCROW_ID, 0)
    runtime.create_account("BENEFICIARY", 0)
    runtime.create_account("OTHER", 0)
    return runtime


def _signed_change(transaction_id, destination):
    evidence = {"type": "TEST"}
    payload = canonical_release_payload(
        transaction_id=transaction_id,
        escrow_id=ESCROW_ID,
        source=ESCROW_ID,
        destination=destination,
        amount=AMOUNT,
        currency="MNT",
        decision_status="APPROVE",
        trust=True,
        transparency=True,
        performance=True,
        evidence_verified=True,
        evidence=evidence,
    )
    return sign_change(
        _PRIVATE_KEY,
        owner_id=_ROOT.owner_id,
        change_id=f"CHANGE-{transaction_id}",
        version=1,
        payload_hash=canonical_payload_hash(payload),
    )


def test_authoritative_release_replay_does_not_move_value_twice():
    runtime = build_runtime()
    prepare_locked(runtime)
    signed_change = _signed_change("TX-IDEMP-001", "BENEFICIARY")
    proof = {"trust": True, "transparency": True, "performance": True}

    first = runtime.release(
        transaction_id="TX-IDEMP-001",
        destination="BENEFICIARY",
        timestamp="2026-09-14T08:02:00Z",
        evidence={"type": "TEST"},
        root=_ROOT,
        signed_change=signed_change,
        owner_id=_ROOT.owner_id,
        authorized=False,
        evidence_verified=True,
        trinity_proof=proof,
    )
    records_after_first_release = len(runtime.money_engine.records)
    replay = runtime.release(
        transaction_id="TX-IDEMP-001",
        destination="BENEFICIARY",
        timestamp="2026-09-14T08:02:00Z",
        evidence={"type": "TEST"},
        root=_ROOT,
        signed_change=signed_change,
        owner_id=_ROOT.owner_id,
        authorized=False,
        evidence_verified=True,
        trinity_proof=proof,
    )

    assert replay == first
    assert runtime.get_balance("BENEFICIARY") == AMOUNT
    assert runtime.get_balance(ESCROW_ID) == 0
    assert len(runtime.money_engine.records) == records_after_first_release


def test_authoritative_release_rejects_signed_change_for_another_beneficiary():
    runtime = build_runtime()
    prepare_locked(runtime)
    signed_change = _signed_change("TX-IDEMP-002", "BENEFICIARY")
    proof = {"trust": True, "transparency": True, "performance": True}

    runtime.release(
        transaction_id="TX-IDEMP-002",
        destination="BENEFICIARY",
        timestamp="2026-09-14T08:02:00Z",
        evidence={"type": "TEST"},
        root=_ROOT,
        signed_change=signed_change,
        owner_id=_ROOT.owner_id,
        authorized=False,
        evidence_verified=True,
        trinity_proof=proof,
    )

    records_after_first_release = len(runtime.money_engine.records)
    try:
        runtime.release(
            transaction_id="TX-IDEMP-002",
            destination="OTHER",
            timestamp="2026-09-14T08:03:00Z",
            evidence={"type": "TEST"},
            root=_ROOT,
            signed_change=signed_change,
            owner_id=_ROOT.owner_id,
            authorized=True,
            evidence_verified=True,
            trinity_proof=proof,
        )
    except Exception as exc:
        assert "payload does not match" in str(exc)
    else:
        raise AssertionError("a signature for another beneficiary must be denied")

    assert runtime.get_balance("BENEFICIARY") == AMOUNT
    assert runtime.get_balance("OTHER") == 0
    assert len(runtime.money_engine.records) == records_after_first_release
