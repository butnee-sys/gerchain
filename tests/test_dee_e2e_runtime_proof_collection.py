from dee_security.audit import append_record, verify_chain
from dee_security.authorization import AuthorizationPolicy
from dee_security.e2e_governance import DEEE2EProof, require_dee_e2e_proof
from dee_security.failure_isolation import FailureIsolationRequest, authorize_failure_isolation
from dee_security.manifest import build_manifest
from dee_security.recovery import RecoveryAuthority, RecoveryGovernance, RecoveryPolicy, RecoveryRequest, RecoveryRole, build_recovery_approval
from dee_security.release_governance import ReleaseGovernanceRequest, authorize_governed_release
from dee_security.release_policy import ReleaseAuthorization
from dee_security.root_of_trust import RootOfTrust
from dee_security.signing import sign_release
from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from witness.chain import WitnessChain
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import base64
import hashlib

TRINITY = {"trust": True, "transparency": True, "performance": True}

def _root():
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return key, RootOfTrust("OWNER-RUNTIME-E2E", base64.b64encode(public).decode("ascii"))

def test_runtime_stages_feed_dee_e2e_proof():
    owner_key, root = _root()
    witness = WitnessChain(initial_state={"case_id": "RUNTIME-E2E"}, manifest={"case_id": "RUNTIME-E2E", "version": 1}, witness_id="W-RUNTIME-E2E")
    escrow = EscrowEngine("ESC-RUNTIME-E2E", 2_000_000, "MNT", "NEF", witness)
    escrow.transition("FUNDED", "2026-09-14T01:00:01Z", {"case_id": "RUNTIME-E2E"})
    escrow.transition("LOCKED", "2026-09-14T01:00:02Z", {"case_id": "RUNTIME-E2E"})
    escrow_verified = escrow.get_state()["state"] == "LOCKED"
    witness_verified = bool(witness.checkpoint())

    ledger = MoneyLedger("MNT")
    ledger.create_account("ESCROW_POOL", 2_000_000)
    ledger.create_account("BENEFICIARY", 0)
    money = MoneyEngine(ledger, escrow)
    money.atomic_settlement("TX-RUNTIME-E2E", "RELEASED", "ESCROW_POOL", "BENEFICIARY", 2_000_000, "2026-09-14T01:00:03Z", {"case_id": "RUNTIME-E2E"}, root=root, owner_id=root.owner_id, authorized=True, evidence_verified=True, trinity_proof=TRINITY)
    settlement_verified = ledger.balances["BENEFICIARY"] == 2_000_000 and escrow.get_state()["state"] == "RELEASED"

    sk = Ed25519PrivateKey.generate(); gk = Ed25519PrivateKey.generate()
    authorities = (RecoveryAuthority("SEC-RUNTIME", RecoveryRole.SECURITY, base64.b64encode(sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode("ascii")), RecoveryAuthority("GOV-RUNTIME", RecoveryRole.GOVERNANCE, base64.b64encode(gk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode("ascii")))
    recovery_request = RecoveryRequest("REC-RUNTIME-E2E", "INC-RUNTIME-E2E", "governed recovery verification", root.owner_id, "OWNER-RECOVERY-KEY")
    decision = RecoveryGovernance(RecoveryPolicy("DEE-RECOVERY-1.0", 2, authorities)).authorize(recovery_request, (build_recovery_approval(sk, "SEC-RUNTIME", recovery_request), build_recovery_approval(gk, "GOV-RUNTIME", recovery_request)))
    recovery_verified = decision.approved and len(decision.approver_ids) == 2
    authorize_failure_isolation(root=root, request=FailureIsolationRequest("ESCROW", "INC-RUNTIME-E2E", root.owner_id, "ISOLATE", "NEF_GERCHAIN", "ISOLATE"), trinity_proof=TRINITY)

    path = "dee_security/e2e_governance.py"
    manifest = build_manifest(version=1, commit_sha="RUNTIME-E2E-COMMIT", protected_paths=[path], artifact_hashes={path: hashlib.sha256(b"runtime-e2e").hexdigest()})
    release = sign_release(owner_key, owner_id=root.owner_id, release_id="REL-RUNTIME-E2E", commit_sha=manifest["commit_sha"], manifest_hash=manifest["manifest_hash"])
    authorize_governed_release(root=root, request=ReleaseGovernanceRequest("REL-RUNTIME-E2E", root.owner_id, "REQ-REL-RUNTIME-E2E"), release_gate=ReleaseAuthorization(), policy=AuthorizationPolicy(), release=release, manifest=manifest, trinity_proof=TRINITY)
    release_verified = True

    a1 = append_record(sequence=1, event="RUNTIME_SETTLEMENT", change_id="TX-RUNTIME-E2E", owner_id=root.owner_id, decision="ALLOW", stage="SETTLEMENT", connector_id="EXIM", request_id="TX-RUNTIME-E2E", operation="SETTLE", trinity=TRINITY)
    a2 = append_record(sequence=2, event="RUNTIME_RECOVERY", change_id="REC-RUNTIME-E2E", owner_id=root.owner_id, decision="ALLOW", stage="RECOVERY", connector_id="EXIM", request_id="REC-RUNTIME-E2E", operation="RECOVER", previous_hash=a1.record_hash, trinity=TRINITY)
    a3 = append_record(sequence=3, event="RUNTIME_RELEASE", change_id="REL-RUNTIME-E2E", owner_id=root.owner_id, decision="ALLOW", stage="RELEASE", connector_id="EXIM", request_id="REQ-REL-RUNTIME-E2E", operation="RELEASE", previous_hash=a2.record_hash, trinity=TRINITY)
    audit_verified = verify_chain([a1, a2, a3])

    proof = DEEE2EProof(genesis_verified=bool(root.owner_id and root.public_key_b64), owner_verified=root.owner_id == "OWNER-RUNTIME-E2E", governance_verified=all(TRINITY.values()), identity_verified=True, contract_verified=True, evidence_verified=True, gateway_verified=True, connector_verified=True, exim_verified=True, core_verified=True, escrow_verified=escrow_verified, witness_verified=witness_verified, settlement_verified=settlement_verified, audit_verified=audit_verified, recovery_verified=recovery_verified, release_verified=release_verified)
    require_dee_e2e_proof(root=root, owner_id=root.owner_id, proof=proof, trinity_proof=TRINITY)
