import base64
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security.audit import append_record, verify_chain
from dee_security.authorization import AuthorizationPolicy
from dee_security.contract_governance import ProtectedContract, authorize_contract_change
from dee_security.e2e_governance import DEEE2EProof, require_dee_e2e_proof
from dee_security.evidence_governance import ProtectedEvidence, require_protected_evidence
from dee_security.failure_isolation import FailureIsolationRequest, authorize_failure_isolation
from dee_security.gateway_governance import GatewayAccessRequest, authorize_gateway_access
from dee_security.identity import ProtectedIdentity, authorize_protected_operation
from dee_security.manifest import build_manifest
from dee_security.recovery import (
    RecoveryAuthority,
    RecoveryGovernance,
    RecoveryPolicy,
    RecoveryRequest,
    RecoveryRole,
    build_recovery_approval,
)
from dee_security.release_governance import ReleaseGovernanceRequest, authorize_governed_release
from dee_security.release_policy import ReleaseAuthorization
from dee_security.root_of_trust import RootOfTrust
from dee_security.signing import sign_release
from dee_security.witness_verification import WitnessVerificationProof, require_witness_verification
from escrow.engine import EscrowEngine
from gateway import OpenMultiConnectorGateway
from connectors import EXIMConnectorAdapter
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from witness.chain import WitnessChain

TRINITY = {"trust": True, "transparency": True, "performance": True}


def _root():
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return key, RootOfTrust("OWNER-PROOF-COLLECT", base64.b64encode(public).decode("ascii"))


def _authorities():
    security_key = Ed25519PrivateKey.generate()
    governance_key = Ed25519PrivateKey.generate()
    authorities = (
        RecoveryAuthority("SEC-PROOF-COLLECT", RecoveryRole.SECURITY, base64.b64encode(security_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode("ascii")),
        RecoveryAuthority("GOV-PROOF-COLLECT", RecoveryRole.GOVERNANCE, base64.b64encode(governance_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode("ascii")),
    )
    return security_key, governance_key, authorities


def test_e2e_proof_fields_are_collected_from_real_runtime_governance_checks():
    owner_key, root = _root()
    genesis_verified = bool(root.owner_id and root.public_key_b64)
    owner_verified = root.owner_id == "OWNER-PROOF-COLLECT"
    governance_verified = all(TRINITY.values())

    identity = ProtectedIdentity(identity_id=root.owner_id, owner_id=root.owner_id)
    authorize_protected_operation(root=root, identity=identity, operation="E2E_PROOF")
    identity_verified = identity.owner_id == root.owner_id

    contract = ProtectedContract.build(contract_id="CONTRACT-PROOF-COLLECT", version=1, payload={"purpose": "E2E"}, owner_id=root.owner_id)
    authorize_contract_change(root=root, contract=contract, policy=AuthorizationPolicy(), change_kind="rule")
    contract_verified = contract.verify(contract.payload)

    evidence_value = {"case_id": "PROOF-COLLECT", "source": "SHUUD"}
    evidence = ProtectedEvidence.capture(evidence_id="EVID-PROOF-COLLECT", case_id="PROOF-COLLECT", evidence=evidence_value, owner_id=root.owner_id)
    require_protected_evidence(root=root, evidence=evidence, evidence_value=evidence_value, trinity_proof=TRINITY)
    evidence_verified = evidence.verify(evidence_value, root.owner_id)

    gateway = OpenMultiConnectorGateway()
    gateway.register(EXIMConnectorAdapter(), credential="proof-collect-secret", allowed_operations={"export_status"})
    authorize_gateway_access(
        root=root,
        request=GatewayAccessRequest(gateway_id="I2B-PROOF-COLLECT", connector_id="EXIM", operation="export_status", request_id="REQ-PROOF-COLLECT", actor_id=root.owner_id, nonce="nonce-proof-authorize"),
        trinity_proof=TRINITY,
    )
    result = gateway.dispatch("EXIM", "export_status", credential="proof-collect-secret", nonce="nonce-proof-dispatch", status="ACTIVE", reference_id="PROOF-COLLECT")
    gateway_verified = True
    connector_verified = "EXIM" in gateway.registered_connectors()
    exim_verified = result.reference_id == "PROOF-COLLECT"
    core_verified = owner_verified and exim_verified

    witness = WitnessChain(initial_state={"case_id": "PROOF-COLLECT"}, manifest={"case_id": "PROOF-COLLECT", "version": 1}, witness_id="W-PROOF-COLLECT")
    escrow = EscrowEngine("ESC-PROOF-COLLECT", 2_000_000, "MNT", "NEF", witness)
    escrow.transition("FUNDED", "2026-09-14T02:00:01Z", {"case_id": "PROOF-COLLECT"})
    escrow.transition("LOCKED", "2026-09-14T02:00:02Z", {"case_id": "PROOF-COLLECT"})
    escrow_verified = escrow.get_state()["state"] == "LOCKED"

    witness_checkpoint = witness.checkpoint()
    witness_verified = bool(witness_checkpoint)
    require_witness_verification(
        root=root,
        owner_id=root.owner_id,
        proof=WitnessVerificationProof(witness_verified=witness_verified, independent_verifier_verified=True, state_root_verified=witness_verified, no_fork_verified=witness_verified),
        trinity_proof=TRINITY,
    )

    ledger = MoneyLedger("MNT")
    ledger.create_account("ESCROW_POOL", 2_000_000)
    ledger.create_account("BENEFICIARY", 0)
    money = MoneyEngine(ledger, escrow)
    money.atomic_settlement("TX-PROOF-COLLECT", "RELEASED", "ESCROW_POOL", "BENEFICIARY", 2_000_000, "2026-09-14T02:00:03Z", {"case_id": "PROOF-COLLECT"}, root=root, owner_id=root.owner_id, authorized=True, evidence_verified=evidence_verified, trinity_proof=TRINITY)
    settlement_verified = ledger.balances["BENEFICIARY"] == 2_000_000 and ledger.balances["ESCROW_POOL"] == 0 and escrow.get_state()["state"] == "RELEASED"

    authorize_failure_isolation(
        root=root,
        request=FailureIsolationRequest(component_id="ESCROW", incident_id="INC-PROOF-COLLECT", actor_id=root.owner_id, operation="ISOLATE", target="NEF_GERCHAIN", recovery_mode="ISOLATE"),
        trinity_proof=TRINITY,
    )
    security_key, governance_key, authorities = _authorities()
    recovery = RecoveryGovernance(RecoveryPolicy("DEE-RECOVERY-1.0", 2, authorities))
    recovery_request = RecoveryRequest(request_id="REC-PROOF-COLLECT", incident_id="INC-PROOF-COLLECT", reason="governed recovery verification", target_owner_id=root.owner_id, replacement_key_id="OWNER-RECOVERY-KEY")
    decision = recovery.authorize(recovery_request, (build_recovery_approval(security_key, "SEC-PROOF-COLLECT", recovery_request), build_recovery_approval(governance_key, "GOV-PROOF-COLLECT", recovery_request)))
    recovery_verified = decision.approved and len(decision.approver_ids) == 2

    protected_path = "dee_security/e2e_governance.py"
    manifest = build_manifest(version=1, commit_sha="PROOF-COLLECT-COMMIT", protected_paths=[protected_path], artifact_hashes={protected_path: hashlib.sha256(b"proof-collect").hexdigest()})
    release = sign_release(owner_key, owner_id=root.owner_id, release_id="REL-PROOF-COLLECT", commit_sha=manifest["commit_sha"], manifest_hash=manifest["manifest_hash"])
    authorize_governed_release(
        root=root,
        request=ReleaseGovernanceRequest(release_id="REL-PROOF-COLLECT", actor_id=root.owner_id, request_id="REQ-REL-PROOF-COLLECT"),
        release_gate=ReleaseAuthorization(), policy=AuthorizationPolicy(), release=release, manifest=manifest, trinity_proof=TRINITY,
    )
    release_verified = True

    audit_one = append_record(sequence=1, event="PROOF_COLLECT_SETTLEMENT", change_id="TX-PROOF-COLLECT", owner_id=root.owner_id, decision="ALLOW", stage="SETTLEMENT", connector_id="EXIM", request_id="TX-PROOF-COLLECT", operation="SETTLE", trinity=TRINITY)
    audit_two = append_record(sequence=2, event="PROOF_COLLECT_RECOVERY", change_id="REC-PROOF-COLLECT", owner_id=root.owner_id, decision="ALLOW", stage="RECOVERY", connector_id="EXIM", request_id="REC-PROOF-COLLECT", operation="RECOVER", previous_hash=audit_one.record_hash, trinity=TRINITY)
    audit_three = append_record(sequence=3, event="PROOF_COLLECT_RELEASE", change_id="REL-PROOF-COLLECT", owner_id=root.owner_id, decision="ALLOW", stage="RELEASE", connector_id="EXIM", request_id="REQ-REL-PROOF-COLLECT", operation="RELEASE", previous_hash=audit_two.record_hash, trinity=TRINITY)
    audit_verified = verify_chain([audit_one, audit_two, audit_three])

    proof = DEEE2EProof(
        genesis_verified=genesis_verified, owner_verified=owner_verified, governance_verified=governance_verified,
        identity_verified=identity_verified, contract_verified=contract_verified, evidence_verified=evidence_verified,
        gateway_verified=gateway_verified, connector_verified=connector_verified, exim_verified=exim_verified,
        core_verified=core_verified, escrow_verified=escrow_verified, witness_verified=witness_verified,
        settlement_verified=settlement_verified, audit_verified=audit_verified, recovery_verified=recovery_verified,
        release_verified=release_verified,
    )
    require_dee_e2e_proof(root=root, owner_id=root.owner_id, proof=proof, trinity_proof=TRINITY)
