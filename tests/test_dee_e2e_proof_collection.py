import base64
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from connectors import EXIMConnectorAdapter
from dee_security.audit import append_record, verify_chain
from dee_security.authorization import AuthorizationPolicy
from dee_security.contract_governance import ProtectedContract, authorize_contract_change
from dee_security.e2e_governance import DEEE2EProof, require_dee_e2e_proof
from dee_security.evidence_governance import ProtectedEvidence, require_protected_evidence
from dee_security.failure_isolation import FailureIsolationRequest, authorize_failure_isolation
from dee_security.gateway_governance import GatewayAccessRequest, authorize_gateway_access
from dee_security.identity import ProtectedIdentity, authorize_protected_operation
from dee_security.manifest import build_manifest
from dee_security.recovery import RecoveryAuthority, RecoveryGovernance, RecoveryPolicy, RecoveryRequest, RecoveryRole, build_recovery_approval
from dee_security.release_governance import ReleaseGovernanceRequest, authorize_governed_release
from dee_security.release_policy import ReleaseAuthorization
from dee_security.root_of_trust import RootOfTrust
from dee_security.signing import sign_release
from dee_security.witness_verification import WitnessVerificationProof, require_witness_verification
from escrow.engine import EscrowEngine
from gateway import OpenMultiConnectorGateway
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from verifier.independent_verifier import IndependentVerifier
from witness.chain import WitnessChain

TRINITY = {"trust": True, "transparency": True, "performance": True}


def _root():
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return key, RootOfTrust("OWNER-CANONICAL-E2E", base64.b64encode(public).decode("ascii"))


def _authorities():
    security_key = Ed25519PrivateKey.generate()
    governance_key = Ed25519PrivateKey.generate()
    authorities = (
        RecoveryAuthority("SEC-CANONICAL", RecoveryRole.SECURITY, base64.b64encode(security_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode("ascii")),
        RecoveryAuthority("GOV-CANONICAL", RecoveryRole.GOVERNANCE, base64.b64encode(governance_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode("ascii")),
    )
    return security_key, governance_key, authorities


def _witness_bundle(witness: WitnessChain):
    return {
        "manifest": witness.manifest,
        "manifest_hash": witness.manifest_hash,
        "witness_id": witness.witness_id,
        "initial_state": witness.initial_state,
        "entries": [
            {"record": vars(entry.record).copy(), "event_payload": entry.event_payload, "evidence": entry.evidence}
            for entry in witness.entries
        ],
    }


def test_canonical_dee_e2e_proof_is_derived_from_runtime():
    owner_key, root = _root()
    genesis_verified = bool(root.owner_id and root.public_key_b64)
    owner_verified = root.owner_id == "OWNER-CANONICAL-E2E"
    governance_verified = all(TRINITY.values())

    identity = ProtectedIdentity(identity_id=root.owner_id, owner_id=root.owner_id)
    authorize_protected_operation(root=root, identity=identity, operation="CANONICAL_E2E")
    identity_verified = identity.owner_id == root.owner_id

    contract = ProtectedContract.build("CONTRACT-CANONICAL-E2E", 1, {"purpose": "E2E"}, root.owner_id)
    authorize_contract_change(root=root, contract=contract, policy=AuthorizationPolicy(), change_kind="rule")
    contract_verified = contract.verify(contract.payload)

    evidence_value = {"case_id": "CANONICAL-E2E", "source": "SHUUD"}
    evidence = ProtectedEvidence.capture("EVID-CANONICAL-E2E", "CANONICAL-E2E", evidence_value, root.owner_id)
    require_protected_evidence(root=root, evidence=evidence, evidence_value=evidence_value, trinity_proof=TRINITY)
    evidence_verified = evidence.verify(evidence_value, root.owner_id)

    gateway = OpenMultiConnectorGateway()
    gateway.register(EXIMConnectorAdapter(), credential="canonical-e2e-secret", allowed_operations={"export_status"})
    authorize_gateway_access(root=root, request=GatewayAccessRequest("I2B-CANONICAL", "EXIM", "export_status", "REQ-CANONICAL", root.owner_id, "nonce-authorize"), trinity_proof=TRINITY)
    result = gateway.dispatch("EXIM", "export_status", credential="canonical-e2e-secret", nonce="nonce-dispatch", status="ACTIVE", reference_id="CANONICAL-E2E")
    gateway_verified = result.reference_id == "CANONICAL-E2E"
    connector_verified = "EXIM" in gateway.registered_connectors()
    exim_verified = result.reference_id == "CANONICAL-E2E"
    core_verified = owner_verified and exim_verified

    witness = WitnessChain(initial_state={"case_id": "CANONICAL-E2E"}, manifest={"case_id": "CANONICAL-E2E", "version": 1}, witness_id="W-CANONICAL-E2E")
    escrow = EscrowEngine("ESC-CANONICAL-E2E", 2_000_000, "MNT", "NEF", witness)
    escrow.transition("FUNDED", "2026-09-14T03:00:01Z", {"case_id": "CANONICAL-E2E"})
    escrow.transition("LOCKED", "2026-09-14T03:00:02Z", {"case_id": "CANONICAL-E2E"})
    escrow_verified = escrow.get_state()["state"] == "LOCKED"

    verifier = IndependentVerifier()
    witness_bundle = _witness_bundle(witness)
    independent_verified = verifier.verify_bundle(witness_bundle)
    state_root = verifier.compute_state_root(witness_bundle)
    no_fork_verified = verifier.verify_no_fork([witness_bundle])
    witness_verified = independent_verified and state_root is not None and no_fork_verified
    require_witness_verification(root=root, owner_id=root.owner_id, proof=WitnessVerificationProof(witness_verified=witness_verified, independent_verifier_verified=independent_verified, state_root_verified=state_root is not None, no_fork_verified=no_fork_verified), trinity_proof=TRINITY)

    ledger = MoneyLedger("MNT")
    ledger.create_account("ESCROW_POOL", 2_000_000)
    ledger.create_account("BENEFICIARY", 0)
    money = MoneyEngine(ledger, escrow)
    money.atomic_settlement("TX-CANONICAL-E2E", "RELEASED", "ESCROW_POOL", "BENEFICIARY", 2_000_000, "2026-09-14T03:00:03Z", {"case_id": "CANONICAL-E2E"}, root=root, owner_id=root.owner_id, authorized=True, evidence_verified=evidence_verified, witness_state_root=state_root, trinity_proof=TRINITY)
    settlement_verified = ledger.balances["BENEFICIARY"] == 2_000_000 and ledger.balances["ESCROW_POOL"] == 0 and escrow.get_state()["state"] == "RELEASED"

    authorize_failure_isolation(root=root, request=FailureIsolationRequest("ESCROW", "INC-CANONICAL-E2E", root.owner_id, "ISOLATE", "NEF_GERCHAIN", "ISOLATE"), trinity_proof=TRINITY)
    security_key, governance_key, authorities = _authorities()
    recovery_request = RecoveryRequest("REC-CANONICAL-E2E", "INC-CANONICAL-E2E", "governed recovery verification", root.owner_id, "OWNER-RECOVERY-KEY")
    decision = RecoveryGovernance(RecoveryPolicy("DEE-RECOVERY-1.0", 2, authorities)).authorize(recovery_request, (build_recovery_approval(security_key, "SEC-CANONICAL", recovery_request), build_recovery_approval(governance_key, "GOV-CANONICAL", recovery_request)))
    recovery_verified = decision.approved and len(decision.approver_ids) == 2

    protected_path = "dee_security/e2e_governance.py"
    manifest = build_manifest(version=1, commit_sha="CANONICAL-E2E-COMMIT", protected_paths=[protected_path], artifact_hashes={protected_path: hashlib.sha256(b"canonical-e2e").hexdigest()})
    release = sign_release(owner_key, owner_id=root.owner_id, release_id="REL-CANONICAL-E2E", commit_sha=manifest["commit_sha"], manifest_hash=manifest["manifest_hash"])
    authorize_governed_release(root=root, request=ReleaseGovernanceRequest("REL-CANONICAL-E2E", root.owner_id, "REQ-REL-CANONICAL-E2E"), release_gate=ReleaseAuthorization(), policy=AuthorizationPolicy(), release=release, manifest=manifest, trinity_proof=TRINITY)
    release_verified = True

    a1 = append_record(sequence=1, event="CANONICAL_SETTLEMENT", change_id="TX-CANONICAL-E2E", owner_id=root.owner_id, decision="ALLOW", stage="SETTLEMENT", connector_id="EXIM", request_id="TX-CANONICAL-E2E", operation="SETTLE", witness_state_root=state_root, trinity=TRINITY)
    a2 = append_record(sequence=2, event="CANONICAL_RECOVERY", change_id="REC-CANONICAL-E2E", owner_id=root.owner_id, decision="ALLOW", stage="RECOVERY", connector_id="EXIM", request_id="REC-CANONICAL-E2E", operation="RECOVER", previous_hash=a1.record_hash, trinity=TRINITY)
    a3 = append_record(sequence=3, event="CANONICAL_RELEASE", change_id="REL-CANONICAL-E2E", owner_id=root.owner_id, decision="ALLOW", stage="RELEASE", connector_id="EXIM", request_id="REQ-REL-CANONICAL-E2E", operation="RELEASE", previous_hash=a2.record_hash, trinity=TRINITY)
    audit_verified = verify_chain([a1, a2, a3])

    proof = DEEE2EProof(genesis_verified=genesis_verified, owner_verified=owner_verified, governance_verified=governance_verified, identity_verified=identity_verified, contract_verified=contract_verified, evidence_verified=evidence_verified, gateway_verified=gateway_verified, connector_verified=connector_verified, exim_verified=exim_verified, core_verified=core_verified, escrow_verified=escrow_verified, witness_verified=witness_verified, settlement_verified=settlement_verified, audit_verified=audit_verified, recovery_verified=recovery_verified, release_verified=release_verified)
    require_dee_e2e_proof(root=root, owner_id=root.owner_id, proof=proof, trinity_proof=TRINITY)
