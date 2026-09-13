from dee_security.release_governance import ReleaseGovernanceError, ReleaseGovernanceRequest, authorize_governed_release


class Root:
    owner_id = "OWNER"


class Release:
    release_id = "REL-1"


TRINITY = {"trust": True, "transparency": True, "performance": True}


class Gate:
    def __init__(self):
        self.called = False

    def authorize(self, **kwargs):
        self.called = True


def _request(**kwargs):
    return ReleaseGovernanceRequest("REL-1", "OWNER", "REQ-1", **kwargs)


def test_release_governance_requires_owner_and_trinity():
    gate = Gate()
    authorize_governed_release(root=Root(), request=_request(), release_gate=gate, policy=object(), release=Release(), manifest={}, trinity_proof=TRINITY)
    assert gate.called


def test_release_governance_denies_non_owner():
    request = ReleaseGovernanceRequest("REL-1", "APP", "REQ-1")
    try:
        authorize_governed_release(root=Root(), request=request, release_gate=object(), policy=object(), release=Release(), manifest={}, trinity_proof=TRINITY)
    except ReleaseGovernanceError:
        return
    raise AssertionError("non-owner release authority must be denied")


def test_release_governance_fails_closed_without_trinity():
    try:
        authorize_governed_release(root=Root(), request=_request(), release_gate=object(), policy=object(), release=Release(), manifest={}, trinity_proof={"trust": True})
    except ReleaseGovernanceError:
        return
    raise AssertionError("release governance must fail closed without Trinity")


def test_release_governance_rejects_partial_execution_context():
    request = _request(witness_state_root="STATE", settlement_hash="SETTLEMENT")
    try:
        authorize_governed_release(root=Root(), request=request, release_gate=object(), policy=object(), release=Release(), manifest={}, trinity_proof=TRINITY)
    except ReleaseGovernanceError:
        return
    raise AssertionError("partial execution context must fail closed")


def test_release_governance_rejects_execution_chain_mismatch():
    request = _request(witness_state_root="STATE", settlement_hash="SETTLEMENT", recovery_decision_hash="RECOVERY", execution_chain_hash="WRONG")
    try:
        authorize_governed_release(root=Root(), request=request, release_gate=object(), policy=object(), release=Release(), manifest={}, trinity_proof=TRINITY)
    except ReleaseGovernanceError:
        return
    raise AssertionError("execution chain mismatch must fail closed")


def test_release_governance_accepts_correct_execution_chain_binding():
    request = _request(witness_state_root="STATE", settlement_hash="SETTLEMENT", recovery_decision_hash="RECOVERY")
    request = ReleaseGovernanceRequest(**{**vars(request), "execution_chain_hash": request.computed_execution_chain_hash()})
    gate = Gate()
    authorize_governed_release(root=Root(), request=request, release_gate=gate, policy=object(), release=Release(), manifest={}, trinity_proof=TRINITY)
    assert gate.called


def test_release_governance_detects_changed_witness_after_chain_hash():
    request = _request(witness_state_root="STATE", settlement_hash="SETTLEMENT", recovery_decision_hash="RECOVERY")
    chain_hash = request.computed_execution_chain_hash()
    tampered = ReleaseGovernanceRequest(**{**vars(request), "witness_state_root": "TAMPERED", "execution_chain_hash": chain_hash})
    try:
        authorize_governed_release(root=Root(), request=tampered, release_gate=object(), policy=object(), release=Release(), manifest={}, trinity_proof=TRINITY)
    except ReleaseGovernanceError:
        return
    raise AssertionError("witness context tampering must fail closed")


def test_release_governance_detects_changed_recovery_after_chain_hash():
    request = _request(witness_state_root="STATE", settlement_hash="SETTLEMENT", recovery_decision_hash="RECOVERY")
    chain_hash = request.computed_execution_chain_hash()
    tampered = ReleaseGovernanceRequest(**{**vars(request), "recovery_decision_hash": "TAMPERED", "execution_chain_hash": chain_hash})
    try:
        authorize_governed_release(root=Root(), request=tampered, release_gate=object(), policy=object(), release=Release(), manifest={}, trinity_proof=TRINITY)
    except ReleaseGovernanceError:
        return
    raise AssertionError("recovery context tampering must fail closed")
