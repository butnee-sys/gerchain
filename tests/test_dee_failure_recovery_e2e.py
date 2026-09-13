import base64

import pytest
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
from witness.chain import WitnessChain


TRINITY = {"trust": True, "transparency": True, "performance": True}


def _root():
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes_raw()
    return key, RootOfTrust("OWNER-E2E", base64.b64encode(public).decode("ascii"))


def _locked_escrow():
    witness = WitnessChain(
        initial_state={"case_id": "FAIL-E2E"},
        manifest={"case_id": "FAIL-E2E", "version": 1},
        witness_id="W-FAIL-E2E",
    )
    escrow = EscrowEngine("ESC-FAIL-E2E", 2_000_000, "MNT", witness)
    escrow.transition("FUNDED", "2026-09-14T00:10:00Z", {"case_id": "FAIL-E2E"})
    escrow.transition("LOCKED", "2026-09-14T00:10:01Z", {"case_id": "FAIL-E2E"})
    return escrow


def test_atomic_settlement_rolls_back_money_escrow_and_witness_on_failure():
    key, root = _root()
    escrow = _locked_escrow()
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
            "TX-FAIL-E2E",
            "RELEASED",
            "ESCROW",
            "BENEFICIARY",
            2_000_000,
            "2026-09-14T00:10:02Z",
            {"case_id": "FAIL-E2E"},
            root=root,
            owner_id=root.owner_id,
            authorized=True,
            evidence_verified=True,
            trinity_proof=TRINITY,
        )

    escrow.transition = original_transition
    assert ledger.balances == before_balances
    assert escrow.get_state() == before_state
    assert escrow.witness_chain._checkpoint() == before_witness
    assert engine.records == []


def test_failed_execution_can_only_enter_recovery_through_multi_party_governance():
    _, root = _root()
    authorize_failure_isolation(
        root=root,
        request=FailureIsolationRequest(
            component_id="ESCROW",
            incident_id="INC-FAIL-E2E",
            actor_id=root.owner_id,
            operation="ISOLATE",
            target="NEF_GERCHAIN",
            recovery_mode="ISOLATE",
        ),
        trinity_proof=TRINITY,
    )

    security_key = Ed25519PrivateKey.generate()
    governance_key = Ed25519PrivateKey.generate()
    authorities = (
        RecoveryAuthority(
            "SEC-1",
            RecoveryRole.SECURITY,
            base64.b64encode(security_key.public_key().public_bytes_raw()).decode("ascii"),
        ),
        RecoveryAuthority(
            "GOV-1",
            RecoveryRole.GOVERNANCE,
            base64.b64encode(governance_key.public_key().public_bytes_raw()).decode("ascii"),
        ),
    )
    governance = RecoveryGovernance(RecoveryPolicy("DEE-RECOVERY-1.0", 2, authorities))
    request = RecoveryRequest(
        request_id="REC-FAIL-E2E",
        incident_id="INC-FAIL-E2E",
        reason="terminal settlement failure",
        target_owner_id=root.owner_id,
        replacement_key_id="OWNER-RECOVERY-KEY",
    )
    approvals = (
        build_recovery_approval(security_key, "SEC-1", request),
        build_recovery_approval(governance_key, "GOV-1", request),
    )
    decision = governance.authorize(request, approvals)
    assert decision.approved
    assert decision.threshold == 2
    assert governance.is_replayed(request.request_id)
