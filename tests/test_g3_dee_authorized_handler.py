import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from architecture.contracts import ActorType, BoundaryRequest
from dee_security import AuthorizationPolicy, ReleaseAuthorization, RootOfTrust, build_manifest, sign_release
from services.g3_core_handler import G3CoreRuntimeHandler
from services.g3_dee_authorized_handler import G3DEEAuthorizedHandler
from services.gerchain_runtime import GerchainRuntime


ESCROW_ID = "DEE-E2E-ESCROW-001"
AMOUNT = 2_000_000


def build_runtime():
    runtime = GerchainRuntime(
        escrow_id=ESCROW_ID,
        amount=AMOUNT,
        currency="MNT",
        witness_id="DEE-E2E-WITNESS-001",
        initial_money_state={
            "currency": "MNT",
            "balances": {"INSURER": AMOUNT, ESCROW_ID: 0, "BENEFICIARY": 0},
        },
    )
    runtime.create_account("INSURER", AMOUNT)
    runtime.create_account(ESCROW_ID, 0)
    runtime.create_account("BENEFICIARY", 0)
    return runtime


def prepare_locked(runtime):
    runtime.fund("TX-DEE-FUND-001", "INSURER", "2026-09-14T08:00:00Z", {"type": "FUND"})
    runtime.lock("TX-DEE-LOCK-001", "2026-09-14T08:01:00Z", {"type": "LOCK"})


def build_signed_release():
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    root = RootOfTrust("DEE-OWNER-001", base64.b64encode(public).decode("ascii"))
    manifest = build_manifest(
        version=1,
        commit_sha="commit-dee-e2e-001",
        protected_paths=["core/release.py"],
        artifact_hashes={"core/release.py": "sha256-demo"},
        schema_version="1",
    )
    release = sign_release(
        private,
        owner_id="DEE-OWNER-001",
        release_id="REL-DEE-E2E-001",
        commit_sha="commit-dee-e2e-001",
        manifest_hash=manifest["manifest_hash"],
    )
    return root, manifest, release


def request(manifest, release):
    return BoundaryRequest(
        actor_type=ActorType.COMPANY,
        actor_id="INSURER-001",
        activity="release_conditional_value_flow",
        correlation_id="CORR-DEE-E2E-001",
        payload={
            "asset": {
                "asset_id": "NEF-SHUUD-ASSET-001",
                "valuation_id": "VAL-001",
                "verification_id": "VER-001",
                "validation_status": "VALID",
                "asset_version": 1,
                "value": AMOUNT,
            },
            "condition_policy": {"trust": "PASS", "transparency": "PASS", "performance": "PASS"},
            "escrow": {"amount": AMOUNT, "currency": "MNT"},
            "decision": {"status": "APPROVE", "rule_version": "G3-1.0"},
            "release": release,
            "manifest": manifest,
            "transaction_id": "TX-DEE-RELEASE-001",
            "destination": "BENEFICIARY",
            "timestamp": "2026-09-14T08:02:00Z",
        },
    )


def test_signed_dee_release_reaches_authoritative_core():
    runtime = build_runtime()
    prepare_locked(runtime)
    root, manifest, release = build_signed_release()
    handler = G3DEEAuthorizedHandler(
        G3CoreRuntimeHandler(runtime),
        root=root,
        policy=AuthorizationPolicy(),
        gate=ReleaseAuthorization(),
    )

    response = handler(request(manifest, release))

    assert response.accepted is True
    assert runtime.get_escrow_state()["state"] == "RELEASED"
    assert runtime.get_balance("BENEFICIARY") == AMOUNT
    assert runtime.verify() is True


def test_tampered_manifest_is_denied_before_core_release():
    runtime = build_runtime()
    prepare_locked(runtime)
    root, manifest, release = build_signed_release()
    manifest["commit_sha"] = "tampered"
    handler = G3DEEAuthorizedHandler(
        G3CoreRuntimeHandler(runtime),
        root=root,
        policy=AuthorizationPolicy(),
        gate=ReleaseAuthorization(),
    )

    try:
        handler(request(manifest, release))
    except Exception as exc:
        assert "authorization failed" in str(exc)
    else:
        raise AssertionError("tampered DEE manifest must be denied")

    assert runtime.get_escrow_state()["state"] == "LOCKED"
    assert runtime.get_balance("BENEFICIARY") == 0


def test_replayed_release_id_is_denied():
    runtime = build_runtime()
    prepare_locked(runtime)
    root, manifest, release = build_signed_release()
    gate = ReleaseAuthorization()
    handler = G3DEEAuthorizedHandler(
        G3CoreRuntimeHandler(runtime),
        root=root,
        policy=AuthorizationPolicy(),
        gate=gate,
    )

    handler(request(manifest, release))
    assert runtime.get_balance("BENEFICIARY") == AMOUNT

    try:
        handler(request(manifest, release))
    except Exception as exc:
        assert "replayed release_id" in str(exc)
    else:
        raise AssertionError("replayed release_id must be denied")
