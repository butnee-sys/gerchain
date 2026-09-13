import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security import (
    FailureIsolationRequest,
    RecoveryAuthority,
    RecoveryGovernance,
    RecoveryPolicy,
    RecoveryRequest,
    RecoveryRole,
    authorize_failure_isolation,
    build_recovery_approval,
)
from dee_security.root_of_trust import RootOfTrust
from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from verifier.independent_verifier import IndependentVerifier
from witness.chain import WitnessChain

TRINITY = {"trust": True, "transparency": True, "performance": True}


def _root():
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return key, RootOfTrust("OWNER-E2E", base64.b64encode(public).decode("ascii"))


def _witness_bundle(witness):
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


def _locked_escrow():
    witness = WitnessChain(initial_state={"case_id": "FAIL-E2E"}, manifest={"case_id": "FAIL-E2E", "version": 1}, witness_id="W-FAIL-E2E")
    escrow = EscrowEngine("ESC-FAIL-E2E", 2_000_000, "MNT", witness)
    escrow.transition("FUNDED", "2026-09-14T00:10:00Z", {"case_id": "FAIL-E2E"})
    escrow.transition("LOCKED", "2026-09-14T00:10:01Z", {"case_id": "FAIL-E2E"})
    return escrow


def test_atomic_settlement_rolls_back_money_escrow_and_witness_on_failure():
    _, root = _root()
    escrow = _locked_escrow()
    verifier = IndependentVerifier()
    bundle = _witness_bundle(escrow.witness_chain)
    assert verifier.verify_bundle(bundle)
    witness_state_root = verifier.compute_state_root(bundle)
    assert witness_state_root is not None
    assert verifier.verify_no_fork([bundle])

    ledger = MoneyLedger("MNT")
    ledger.create_account("ESCROW", 2_000_000)
    ledger.create_account("BENEFICIARY", 0)
    engine = MoneyEngine(ledger, escrow)

    original_transition = escrow.transition

    def fail_after_money_movement(*args, **kwargs):
        raise RuntimeError("simulated terminal escrow failure")

    escrow.transition = fail_after_money_movement
    before_balances = dict(ledger.balances)
    before_state = escrow.get_state()
    before_witness = escrow.witness_chain._checkpoint()

    with pytest.raises(RuntimeError, match="simulated terminal escrow failure"):
        engine.atomic_settlement(
            "TX-FAIL-E2E", "RELEASED", "ESCROW", "BENEFICIARY", 2_000_000, "2026-09-14T00:10:02Z", {"case_id": "FAIL-E2E"},
            root=root, owner_id=root.owner_id, authorized=True, evidence_verified=True, witness_state_root=witness_state_root, trinity_proof=TRINITY,
        )

    escrow.transition = original_transition
    assert ledger.balances == before_balances
    assert escrow.get_state() == before_state
    assert escrow.witness_chain._checkpoint() == before_witness
    assert engine.records == []


def test_failed_execution_can_only_enter_recovery_through_multi_party_governance():
    _, root = _root()
    authorize_failure_isolation(root=root, request=FailureIsolationRequest("ESCROW", "INC-FAIL-E2E", root.owner_id, "ISOLATE", "NEF_GERCHAIN", "ISOLATE"), trinity_proof=TRINITY)

    security_key = Ed25519PrivateKey.generate()
    governance_key = Ed25519PrivateKey.generate()
    authorities = (
        RecoveryAuthority("SEC-1", RecoveryRole.SECURITY, base64.b64encode(security_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode("ascii")),
        RecoveryAuthority("GOV-1", RecoveryRole.GOVERNANCE, base64.b64encode(governance_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode("ascii")),
    )
    governance = RecoveryGovernance(RecoveryPolicy("DEE-RECOVERY-1.0", 2, authorities))
    request = RecoveryRequest("REC-FAIL-E2E", "INC-FAIL-E2E", "terminal settlement failure", root.owner_id, "OWNER-RECOVERY-KEY")
    approvals = (build_recovery_approval(security_key, "SEC-1", request), build_recovery_approval(governance_key, "GOV-1", request))
    decision = governance.authorize(request, approvals)
    assert decision.approved
    assert decision.threshold == 2
    assert governance.is_replayed(request.request_id)
