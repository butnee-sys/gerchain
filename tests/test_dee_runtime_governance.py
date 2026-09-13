import pytest

from dee_security.runtime_governance import (
    RuntimeAction,
    RuntimeGovernance,
    RuntimeGovernanceError,
    RuntimeIdentity,
    RuntimeRole,
)


def test_owner_can_authorize_governance_actions():
    governance = RuntimeGovernance()
    owner = RuntimeIdentity("owner:primary", RuntimeRole.OWNER)

    for action in (
        RuntimeAction.ARCHITECTURE,
        RuntimeAction.SECURITY_POLICY,
        RuntimeAction.ADAPTER_APPROVAL,
        RuntimeAction.RELEASE_APPROVAL,
    ):
        authorization = governance.authorize(owner, action)
        assert authorization.identity_id == owner.identity_id
        assert authorization.role is RuntimeRole.OWNER


def test_operator_is_limited_to_runtime_operations():
    governance = RuntimeGovernance()
    operator = RuntimeIdentity("operator:01", RuntimeRole.OPERATOR)

    assert governance.is_allowed(operator, RuntimeAction.MONITORING)
    assert governance.is_allowed(operator, RuntimeAction.OPERATIONS)
    assert governance.is_allowed(operator, RuntimeAction.ROUTINE_ACTIONS)
    assert not governance.is_allowed(operator, RuntimeAction.RELEASE_APPROVAL)
    assert not governance.is_allowed(operator, RuntimeAction.SECURITY_POLICY)


def test_application_is_limited_to_contracted_api():
    governance = RuntimeGovernance()
    application = RuntimeIdentity("app:shuud", RuntimeRole.APPLICATION)

    assert governance.is_allowed(application, RuntimeAction.CONTRACT_API)
    assert not governance.is_allowed(application, RuntimeAction.OPERATIONS)
    assert not governance.is_allowed(application, RuntimeAction.RELEASE_APPROVAL)


def test_denies_unknown_role_and_action():
    governance = RuntimeGovernance()
    identity = RuntimeIdentity("unknown:01", "UNKNOWN")  # type: ignore[arg-type]

    with pytest.raises(RuntimeGovernanceError, match="unknown runtime role"):
        governance.authorize(identity, RuntimeAction.MONITORING)

    with pytest.raises(RuntimeGovernanceError, match="unknown runtime action"):
        governance.authorize(
            RuntimeIdentity("operator:01", RuntimeRole.OPERATOR),
            "delete_everything",  # type: ignore[arg-type]
        )


def test_empty_identity_fails_closed():
    governance = RuntimeGovernance()
    with pytest.raises(RuntimeGovernanceError, match="identity is required"):
        governance.authorize(
            RuntimeIdentity("", RuntimeRole.OWNER),
            RuntimeAction.ARCHITECTURE,
        )
