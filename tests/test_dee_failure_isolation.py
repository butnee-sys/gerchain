from dee_security.failure_isolation import FailureIsolationError, FailureIsolationRequest, authorize_failure_isolation
from dee_security.root_of_trust import RootOfTrust


def root():
    return RootOfTrust(owner_id="OWNER-001", owner_public_key="key", genesis_anchor="genesis", policy_version="1")


def request(actor="OWNER-001", mode="ISOLATE"):
    return FailureIsolationRequest("CONNECTOR-A", "INC-1", actor, "freeze", "NEF_GERCHAIN", mode)


def trinity():
    return {"trust": True, "transparency": True, "performance": True}


def test_core_can_be_isolated_under_owner_governance():
    authorize_failure_isolation(root=root(), request=request(), trinity_proof=trinity())


def test_non_owner_cannot_control_recovery_boundary():
    try:
        authorize_failure_isolation(root=root(), request=request("APP-1"), trinity_proof=trinity())
    except FailureIsolationError:
        return
    raise AssertionError("non-owner must not control recovery boundary")


def test_failure_isolation_fails_closed_without_trinity():
    try:
        authorize_failure_isolation(root=root(), request=request(), trinity_proof={"trust": True})
    except FailureIsolationError:
        return
    raise AssertionError("failure isolation must fail closed without Trinity")


def test_unknown_recovery_mode_is_denied():
    try:
        authorize_failure_isolation(root=root(), request=request(mode="FORCE"), trinity_proof=trinity())
    except FailureIsolationError:
        return
    raise AssertionError("unknown recovery mode must be denied")
