from dee_security.release_governance import ReleaseGovernanceError, ReleaseGovernanceRequest, authorize_governed_release


def test_release_governance_requires_owner_and_trinity():
    class Root:
        owner_id = "OWNER"

    class Release:
        release_id = "REL-1"

    class Gate:
        def __init__(self):
            self.called = False
        def authorize(self, **kwargs):
            self.called = True

    gate = Gate()
    authorize_governed_release(root=Root(), request=ReleaseGovernanceRequest("REL-1", "OWNER", "REQ-1"), release_gate=gate, policy=object(), release=Release(), manifest={}, trinity_proof={"trust": True, "transparency": True, "performance": True})
    assert gate.called


def test_release_governance_denies_non_owner():
    class Root:
        owner_id = "OWNER"
    class Release:
        release_id = "REL-1"
    try:
        authorize_governed_release(root=Root(), request=ReleaseGovernanceRequest("REL-1", "APP", "REQ-1"), release_gate=object(), policy=object(), release=Release(), manifest={}, trinity_proof={"trust": True, "transparency": True, "performance": True})
    except ReleaseGovernanceError:
        return
    raise AssertionError("non-owner release authority must be denied")


def test_release_governance_fails_closed_without_trinity():
    class Root:
        owner_id = "OWNER"
    class Release:
        release_id = "REL-1"
    try:
        authorize_governed_release(root=Root(), request=ReleaseGovernanceRequest("REL-1", "OWNER", "REQ-1"), release_gate=object(), policy=object(), release=Release(), manifest={}, trinity_proof={"trust": True})
    except ReleaseGovernanceError:
        return
    raise AssertionError("release governance must fail closed without Trinity")


def test_release_governance_rejects_partial_execution_context():
    class Root:
        owner_id = "OWNER"
    class Release:
        release_id = "REL-1"
    request = ReleaseGovernanceRequest("REL-1", "OWNER", "REQ-1", witness_state_root="STATE", settlement_hash="SETTLEMENT")
    try:
        authorize_governed_release(root=Root(), request=request, release_gate=object(), policy=object(), release=Release(), manifest={}, trinity_proof={"trust": True, "transparency": True, "performance": True})
    except ReleaseGovernanceError:
        return
    raise AssertionError("partial execution context must fail closed")


def test_release_governance_rejects_execution_chain_mismatch():
    class Root:
        owner_id = "OWNER"
    class Release:
        release_id = "REL-1"
    request = ReleaseGovernanceRequest("REL-1", "OWNER", "REQ-1", witness_state_root="STATE", settlement_hash="SETTLEMENT", recovery_decision_hash="RECOVERY", execution_chain_hash="WRONG")
    try:
        authorize_governed_release(root=Root(), request=request, release_gate=object(), policy=object(), release=Release(), manifest={}, trinity_proof={"trust": True, "transparency": True, "performance": True})
    except ReleaseGovernanceError:
        return
    raise AssertionError("execution chain mismatch must fail closed")
