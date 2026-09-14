import base64
from decimal import Decimal

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from architecture.contracts import ActorType, BoundaryRequest
from architecture.nef_gerchain import NEFToGerChainAdapter
from dee_security import AuthorizationPolicy, ReleaseAuthorization, RootOfTrust, build_manifest, sign_release
from nef import (
    Asset,
    AssetIdentityEngine,
    AssetRegistryEngine,
    AssetState,
    AssetStateEngine,
    AssetValidationEngine,
    AssetValidationStatus,
    AssetVersionEngine,
    DigitalAssetRecordEngine,
    EvidenceProvenanceEngine,
    OwnershipRight,
    OwnershipRightsEngine,
    OwnershipType,
    ValuationBasis,
    ValuationEngine,
    ValuationEvidenceEngine,
    VerificationEngine,
)
from nef.audit import NEFAuditEngine
from nef.collateral import CollateralEngine
from nef.encumbrance import EncumbranceEngine, EncumbranceType
from nef.lifecycle import AssetLifecycleEngine
from nef.recovery import NEFRecoveryEngine, RecoveryStatus
from services.g3_core_handler import G3CoreRuntimeHandler
from services.g3_dee_authorized_handler import G3DEEAuthorizedHandler
from services.gerchain_runtime import GerchainRuntime


ASSET_ID = "NEF-FULL-E2E-ASSET-001"
VALUE = 2_000_000
ESCROW_ID = "NEF-FULL-E2E-ESCROW-001"


def build_nef_asset():
    identity = AssetIdentityEngine().create(ASSET_ID, "SHUUD-CONDITIONAL-ASSET")
    asset = Asset(asset_id=ASSET_ID, asset_type="SHUUD-CONDITIONAL-ASSET", identity=identity)
    registry = AssetRegistryEngine()
    registry.register(asset)
    AssetStateEngine().transition(asset, AssetState.ACTIVE)
    OwnershipRightsEngine().assign(
        asset,
        OwnershipRight("INSURER-001", OwnershipType.OWNER, 100),
    )

    evidence = ValuationEvidenceEngine().create(
        "VAL-EVID-001", "VAL-001", "INSURANCE", "SHUUD", "INCIDENT-001"
    )
    evidence = ValuationEvidenceEngine().verify(evidence)
    valuation = ValuationEngine().create(
        asset,
        "VAL-001",
        VALUE,
        "MNT",
        ValuationBasis.EXPERT,
        "VALUER-001",
        [evidence.evidence_id],
    )

    DigitalAssetRecordEngine().create(
        asset,
        {"valuation_id": valuation.valuation_id, "value": VALUE, "currency": "MNT"},
        [evidence.evidence_id],
    )
    provenance = EvidenceProvenanceEngine().create(
        "PROV-001", ASSET_ID, "VALUATION", valuation.valuation_id, "VALUED", "VALUER-001"
    )
    verification = VerificationEngine().verify(
        "VER-001", ASSET_ID, "VERIFIER-001", [evidence.evidence_id, provenance.provenance_id]
    )
    validation = AssetValidationEngine().validate(asset, verification)
    assert validation.status is AssetValidationStatus.VALID

    version = AssetVersionEngine().create(
        ASSET_ID,
        asset.version,
        {"state": asset.state.value, "valuation_id": valuation.valuation_id},
    )
    encumbrance = EncumbranceEngine().create(
        "ENC-001", ASSET_ID, EncumbranceType.PLEDGE, "INSURER-001", "SHUUD-001"
    )
    collateral = CollateralEngine().create(
        "COL-001", ASSET_ID, "INSURER-001", Decimal(VALUE), "MNT"
    )
    lifecycle = AssetLifecycleEngine().transition(
        ASSET_ID, "ACTIVE", "ENCUMBERED", "SHUUD conditional value flow"
    )
    audit = NEFAuditEngine().record(
        "AUD-001", ASSET_ID, "PREPARE_VALUE_FLOW", "INSURER-001", "PASS",
        {"valuation_id": valuation.valuation_id, "verification_id": verification.verification_id},
    )
    recovery_engine = NEFRecoveryEngine()
    recovery = recovery_engine.request(
        "REC-001", ASSET_ID, version.version, "INSURER-001", "E2E recovery checkpoint", version.snapshot
    )
    recovery = recovery_engine.complete(recovery_engine.approve(recovery))
    assert recovery.status is RecoveryStatus.COMPLETED

    return {
        "asset": asset,
        "valuation": valuation,
        "verification": verification,
        "validation": validation,
        "version": version,
        "encumbrance": encumbrance,
        "collateral": collateral,
        "lifecycle": lifecycle,
        "audit": audit,
        "recovery": recovery,
    }


def build_runtime():
    runtime = GerchainRuntime(
        escrow_id=ESCROW_ID,
        amount=VALUE,
        currency="MNT",
        witness_id="NEF-FULL-E2E-WITNESS-001",
        initial_money_state={
            "currency": "MNT",
            "balances": {"INSURER-001": VALUE, ESCROW_ID: 0, "BENEFICIARY": 0},
        },
    )
    runtime.create_account("INSURER-001", VALUE)
    runtime.create_account(ESCROW_ID, 0)
    runtime.create_account("BENEFICIARY", 0)
    runtime.fund("TX-FULL-E2E-FUND", "INSURER-001", "2026-09-14T09:00:00Z", {"type": "FUND"})
    runtime.lock("TX-FULL-E2E-LOCK", "2026-09-14T09:01:00Z", {"type": "LOCK"})
    return runtime


def build_signed_release():
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    root = RootOfTrust("DEE-FULL-E2E-OWNER", base64.b64encode(public).decode("ascii"))
    manifest = build_manifest(
        version=1,
        commit_sha="commit-nef-full-e2e-001",
        protected_paths=["core/release.py"],
        artifact_hashes={"core/release.py": "sha256-nef-full-e2e"},
        schema_version="1",
    )
    release = sign_release(
        private,
        owner_id=root.owner_id,
        release_id="REL-NEF-FULL-E2E-001",
        commit_sha=manifest["commit_sha"],
        manifest_hash=manifest["manifest_hash"],
    )
    return root, manifest, release


def test_nef_17_engine_truth_reaches_authoritative_gerchain_release():
    nef = build_nef_asset()
    runtime = build_runtime()
    root, manifest, release = build_signed_release()

    core = G3CoreRuntimeHandler(runtime)
    dee = G3DEEAuthorizedHandler(
        core,
        root=root,
        policy=AuthorizationPolicy(),
        gate=ReleaseAuthorization(),
    )
    boundary = NEFToGerChainAdapter(dee)

    payload = {
        "asset": {
            "asset_id": nef["asset"].asset_id,
            "valuation_id": nef["valuation"].valuation_id,
            "verification_id": nef["verification"].verification_id,
            "validation_status": nef["validation"].status.value,
            "asset_version": nef["version"].version,
            "value": int(nef["valuation"].value),
            "currency": nef["valuation"].currency,
        },
        "condition_policy": {"trust": "PASS", "transparency": "PASS", "performance": "PASS"},
        "escrow": {"amount": VALUE, "currency": "MNT"},
        "decision": {"status": "APPROVE", "rule_version": "SHUUD-0.2"},
        "release": release,
        "manifest": manifest,
        "transaction_id": "TX-FULL-E2E-RELEASE",
        "destination": "BENEFICIARY",
        "timestamp": "2026-09-14T09:02:00Z",
        "evidence": {
            "asset_id": ASSET_ID,
            "valuation_id": nef["valuation"].valuation_id,
            "verification_id": nef["verification"].verification_id,
            "encumbrance_id": nef["encumbrance"].encumbrance_id,
            "collateral_id": nef["collateral"].collateral_id,
        },
    }

    response = boundary.handle(
        BoundaryRequest(
            actor_type=ActorType.COMPANY,
            actor_id="INSURER-001",
            activity="release_conditional_value_flow",
            correlation_id="CORR-NEF-FULL-E2E-001",
            payload=payload,
        )
    )

    assert response.accepted is True
    assert runtime.get_escrow_state()["state"] == "RELEASED"
    assert runtime.get_balance("INSURER-001") == 0
    assert runtime.get_balance(ESCROW_ID) == 0
    assert runtime.get_balance("BENEFICIARY") == VALUE
    assert runtime.verify() is True


def test_nef_unknown_validation_stops_before_value_flow():
    nef = build_nef_asset()
    runtime = build_runtime()
    root, manifest, release = build_signed_release()
    boundary = NEFToGerChainAdapter(
        G3DEEAuthorizedHandler(
            G3CoreRuntimeHandler(runtime),
            root=root,
            policy=AuthorizationPolicy(),
            gate=ReleaseAuthorization(),
        )
    )

    payload = {
        "asset": {
            "asset_id": ASSET_ID,
            "valuation_id": nef["valuation"].valuation_id,
            "verification_id": nef["verification"].verification_id,
            "validation_status": "UNKNOWN",
            "asset_version": nef["version"].version,
            "value": VALUE,
            "currency": "MNT",
        },
        "condition_policy": {"trust": "PASS", "transparency": "PASS", "performance": "PASS"},
        "escrow": {"amount": VALUE, "currency": "MNT"},
        "decision": {"status": "APPROVE"},
        "release": release,
        "manifest": manifest,
        "transaction_id": "TX-FULL-E2E-DENIED",
        "destination": "BENEFICIARY",
        "timestamp": "2026-09-14T09:03:00Z",
    }

    try:
        boundary.handle(
            BoundaryRequest(
                actor_type=ActorType.COMPANY,
                actor_id="INSURER-001",
                activity="release_conditional_value_flow",
                payload=payload,
            )
        )
    except Exception:
        pass
    else:
        raise AssertionError("UNKNOWN NEF validation must fail closed")

    assert runtime.get_escrow_state()["state"] == "LOCKED"
    assert runtime.get_balance("BENEFICIARY") == 0
