import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from architecture.contracts import ActorType, BoundaryRequest
from architecture.g3_core import G3ToCoreBoundaryAdapter
from dee_security.root_of_trust import RootOfTrust, SignedChange
from persistence.signed_change_authorization import canonical_payload_hash, canonical_release_payload
from services.g3_core_handler import G3CoreRuntimeHandler
from services.gerchain_runtime import GerchainRuntime

ESCROW_ID = "G3-E2E-ESCROW-001"
AMOUNT = 2_000_000
OWNER_ID = "g3-e2e-owner"


def build_runtime():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    root = RootOfTrust(OWNER_ID, base64.b64encode(public_key).decode("ascii"))
    runtime = GerchainRuntime(
        escrow_id=ESCROW_ID, amount=AMOUNT, currency="MNT",
        witness_id="G3-E2E-WITNESS-001",
        initial_money_state={
            "currency": "MNT",
            "balances": {"INSURER": AMOUNT, ESCROW_ID: 0, "BENEFICIARY": 0},
        },
    )
    runtime.configure_root_of_trust(root)
    runtime.create_account("INSURER", AMOUNT)
    runtime.create_account(ESCROW_ID, 0)
    runtime.create_account("BENEFICIARY", 0)
    return runtime, root, private_key


def _signed_change(private_key, evidence):
    payload = canonical_release_payload(
        transaction_id="TX-G3-E2E-RELEASE-001", escrow_id=ESCROW_ID,
        source=ESCROW_ID, destination="BENEFICIARY", amount=AMOUNT,
        currency="MNT", decision_status="APPROVE", trust=True,
        transparency=True, performance=True, evidence_verified=True,
        evidence=evidence,
    )
    unsigned = SignedChange(
        owner_id=OWNER_ID, change_id="CHANGE-TX-G3-E2E-RELEASE-001",
        version=1, payload_hash=canonical_payload_hash(payload), signature="",
    )
    signature = private_key.sign(json.dumps(
        unsigned.signing_payload(), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8"))
    return SignedChange(
        owner_id=OWNER_ID, change_id=unsigned.change_id, version=1,
        payload_hash=unsigned.payload_hash,
        signature=base64.b64encode(signature).decode("ascii"),
    )


def request(root, private_key, **overrides):
    evidence = {"type": "G3-E2E", "reference": "SHUUD-001"}
    payload = {
        "asset": {
            "asset_id": "NEF-SHUUD-ASSET-001",
            "valuation_id": "VAL-SHUUD-001",
            "verification_id": "VER-SHUUD-001",
            "validation_status": "VALID",
            "asset_version": 1,
        },
        "condition_policy": {"trust": "PASS", "transparency": "PASS", "performance": "PASS"},
        "escrow": {"amount": AMOUNT, "currency": "MNT"},
        "decision": {"status": "APPROVE", "rule_version": "G3-1.0"},
        "authorization": {"status": "AUTHORIZED", "authorization_id": "AUTH-G3-E2E-001"},
        "_dee_context": {
            "root": root, "owner_id": OWNER_ID,
            "signed_change": _signed_change(private_key, evidence),
        },
        "transaction_id": "TX-G3-E2E-RELEASE-001",
        "destination": "BENEFICIARY", "source": "INSURER",
        "timestamp": "2026-09-14T08:00:00Z", "evidence": evidence,
    }
    payload.update(overrides)
    return BoundaryRequest(
        actor_type=ActorType.COMPANY, actor_id="INSURER-001",
        activity="release_conditional_value_flow",
        correlation_id="CORR-G3-E2E-001", payload=payload,
    )


def prepare_locked(runtime):
    runtime.fund("TX-G3-E2E-FUND-001", "INSURER", "2026-09-14T07:59:00Z", {"type": "FUNDING", "reference": "G3-E2E"})
    runtime.lock("TX-G3-E2E-LOCK-001", "2026-09-14T07:59:30Z", {"type": "LOCK", "reference": "G3-E2E"})


def test_g3_boundary_reaches_existing_authoritative_core():
    runtime, root, private_key = build_runtime()
    prepare_locked(runtime)
    adapter = G3ToCoreBoundaryAdapter(G3CoreRuntimeHandler(runtime))
    response = adapter.handle(request(root, private_key))
    assert response.accepted is True
    assert runtime.get_escrow_state()["state"] == "RELEASED"
    assert runtime.get_balance("INSURER") == 0
    assert runtime.get_balance(ESCROW_ID) == 0
    assert runtime.get_balance("BENEFICIARY") == AMOUNT
    assert runtime.verify() is True


def test_g3_boundary_fails_closed_without_approved_authorization():
    runtime, root, private_key = build_runtime()
    prepare_locked(runtime)
    adapter = G3ToCoreBoundaryAdapter(G3CoreRuntimeHandler(runtime))
    denied = adapter.handle(request(
        root, private_key,
        decision={"status": "HUMAN_REVIEW", "rule_version": "G3-1.0"},
        authorization={"status": "PENDING"},
    ))
    assert denied.accepted is False
    assert "APPROVE" in (denied.reason or "")
    assert runtime.get_escrow_state()["state"] == "LOCKED"
    assert runtime.get_balance("INSURER") == 0
    assert runtime.get_balance(ESCROW_ID) == AMOUNT
    assert runtime.get_balance("BENEFICIARY") == 0
