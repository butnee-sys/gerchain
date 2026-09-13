import base64
import hashlib

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from connectors import EXIMConnectorAdapter
from dee_security.audit import append_record, verify_chain
from dee_security.authorization import AuthorizationPolicy
from dee_security.e2e_governance import DEEE2EProof, require_dee_e2e_proof
from dee_security.failure_isolation import FailureIsolationRequest, authorize_failure_isolation
from dee_security.gateway_governance import GatewayAccessRequest, authorize_gateway_access
from dee_security.manifest import build_manifest
from dee_security.recovery import (
    RecoveryAuthority,
    RecoveryGovernance,
    RecoveryPolicy,
    RecoveryRequest,
    RecoveryRole,
    build_recovery_approval,
)
from dee_security.release_policy import ReleaseAuthorization
from dee_security.root_of_trust import RootOfTrust
from dee_security.signing import sign_release
from gateway import OpenMultiConnectorGateway
from money.engine import MoneyEngine
from money.ledger import MoneyLedger


TRINITY = {"trust": True, "transparency": True, "performance": True}


def _root():
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return key, RootOfTrust("OWNER-FULL-E2E", base64.b64encode(public).decode("ascii"))


def _authorities():
    security_key = Ed25519PrivateKey.generate()
    governance_key = Ed25519PrivateKey.generate()
    authorities = (
        RecoveryAuthority(
            "SEC-FULL",
            RecoveryRole.SECURITY,
            base64.b64encode(security_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )).decode("ascii"),
        ),
        RecoveryAuthority(
            "GOV-FULL",
            RecoveryRole.GOVERNANCE,
            base64.b64encode(governance_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )).decode("ascii"),
        ),
    )
    return security_key, governance_key, authorities


def test_full_dee_governed_flow_failure_recovery_and_release():
    owner_key, root = _root()
    gateway = OpenMultiConnectorGateway()
    connector = EXIMConnectorAdapter()
    gateway.register(
        connector,
        credential="full-e2e-secret",
        allowed_operations={"create_witness_chain", "create_escrow"},
    )

    authorize_gateway_access(
        root=root,
        request=GatewayAccessRequest(
            gateway_id="I2B-FULL-E2E", connector_id="EXIM",
            operation="create_witness_chain", request_id="REQ-FULL-WIT",
            actor_id=root.owner_id, nonce="nonce-full-wit",
        ),
        trinity_proof=TRINITY,
    )
    witness = gateway.dispatch(
        "EXIM", "create_witness_chain", credential="full-e2e-secret", nonce="nonce-full-wit",
        initial_state={"case_id": "FULL-E2E"}, manifest={"case_id": "FULL-E2E", "version": 1},
        witness_id="W-FULL-E2E",
    )

    authorize_gateway_access(
        root=root,
        request=GatewayAccessRequest(
            gateway_id="I2B-FULL-E2E", connector_id="EXIM",
            operation="create_escrow", request_id="REQ-FULL-ESC",
            actor_id=root.owner_id, nonce="nonce-full-esc",
        ),
        trinity_proof=TRINITY,
    )
    escrow = gateway.dispatch(
        "EXIM", "create_escrow", credential="full-e2e-secret", nonce="nonce-full-esc",
        escrow_id="ESC-FULL-E2E", amount=2_000_000, currency="MNT",
        settlement_provider="NEF", witness_chain=witness,
    )
    escrow.transition("FUNDED", "2026-09-14T01:00:01Z", {"case_id": "FULL-E2E"})
    escrow.transition("LOCKED", "2026-09-14T01:00:02Z", {"case_id": "FULL-E2E"})

    ledger = MoneyLedger("MNT")
    ledger.create_account("ESCROW_POOL", 2_000_000)
    ledger.create_account("BENEFICIARY", 0)
    money = MoneyEngine(ledger, escrow)

    original_transition = escrow.transition
    escrow.transition = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("forced recovery failure"))
    before = dict(ledger.balances)
    with pytest.raises(RuntimeError, match="forced recovery failure"):
        money.atomic_settlement(
            "TX-FULL-E2E", "RELEASED", "ESCROW_POOL", "BENEFICIARY", 2_000_000,
            "2026-09-14T01:00:03Z", {"case_id": "FULL-E2E"}, root=root,
            owner_id=root.owner_id, authorized=True, evidence_verified=True,
            trinity_proof=TRINITY,
        )
    escrow.transition = original_transition
    assert ledger.balances == before
    assert escrow.get_state()["state"] == "LOCKED"
    assert money.records == []

    authorize_failure_isolation(
        root=root,
        request=FailureIsolationRequest(
            component_id="ESCROW", incident_id="INC-FULL-E2E", actor_id=root.owner_id,
            operation="ISOLATE", target="NEF_GERCHAIN", recovery_mode="ISOLATE",
        ),
        trinity_proof=TRINITY,
    )
    security_key, governance_key, authorities = _authorities()
    recovery = RecoveryGovernance(RecoveryPolicy("DEE-RECOVERY-1.0", 2, authorities))
    recovery_request = RecoveryRequest(
        request_id="REC-FULL-E2E", incident_id="INC-FULL-E2E",
        reason="terminal settlement failure", target_owner_id=root.owner_id,
        replacement_key_id="OWNER-RECOVERY-KEY",
    )
    decision = recovery.authorize(
        recovery_request,
        (
            build_recovery_approval(security_key, "SEC-FULL", recovery_request),
            build_recovery_approval(governance_key, "GOV-FULL", recovery_request),
        ),
    )
    assert decision.approved
    assert len(decision.approver_ids) == 2

    policy = AuthorizationPolicy()
    protected_path = "dee_security/e2e_governance.py"
    manifest = build_manifest(
        version=1,
        commit_sha="FULL-E2E-COMMIT",
        protected_paths=[protected_path],
        artifact_hashes={protected_path: hashlib.sha256(b"full-e2e").hexdigest()},
    )
    release = sign_release(
        owner_key,
        owner_id=root.owner_id,
        release_id="REL-FULL-E2E",
        commit_sha=manifest["commit_sha"],
        manifest_hash=manifest["manifest_hash"],
    )
    ReleaseAuthorization().authorize(root=root, policy=policy, release=release, manifest=manifest)

    audit_one = append_record(
        sequence=1, event="FULL_E2E_RECOVERY", change_id="REC-FULL-E2E",
        owner_id=root.owner_id, decision="ALLOW", stage="RECOVERY",
        connector_id="EXIM", request_id="REC-FULL-E2E", operation="RECOVER",
        trinity=TRINITY,
    )
    audit_two = append_record(
        sequence=2, event="FULL_E2E_RELEASE", change_id="REL-FULL-E2E",
        owner_id=root.owner_id, decision="ALLOW", stage="RELEASE",
        connector_id="EXIM", request_id="REC-FULL-E2E", operation="RELEASE",
        previous_hash=audit_one.record_hash, trinity=TRINITY,
    )
    assert verify_chain([audit_one, audit_two])

    proof = DEEE2EProof(
        genesis_verified=True, owner_verified=True, governance_verified=True,
        identity_verified=True, contract_verified=True, evidence_verified=True,
        gateway_verified=True, connector_verified=True, exim_verified=True,
        core_verified=True, escrow_verified=True, witness_verified=True,
        settlement_verified=True, audit_verified=True, recovery_verified=True,
        release_verified=True,
    )
    require_dee_e2e_proof(root=root, owner_id=root.owner_id, proof=proof, trinity_proof=TRINITY)
