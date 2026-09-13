import base64

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security.recovery import (
    RecoveryApproval,
    RecoveryAuthority,
    RecoveryGovernance,
    RecoveryGovernanceError,
    RecoveryPolicy,
    RecoveryRequest,
    RecoveryRole,
    build_recovery_approval,
)


def _authority(authority_id: str, role: RecoveryRole):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes_raw()
    return private_key, RecoveryAuthority(
        authority_id=authority_id,
        role=role,
        public_key_b64=base64.b64encode(public_key).decode("ascii"),
    )


def _setup():
    k1, a1 = _authority("REC-SEC", RecoveryRole.SECURITY)
    k2, a2 = _authority("REC-GOV", RecoveryRole.GOVERNANCE)
    k3, a3 = _authority("REC-AUD", RecoveryRole.AUDITOR)
    policy = RecoveryPolicy("DEE-RECOVERY-1.0", 2, (a1, a2, a3))
    governance = RecoveryGovernance(policy)
    request = RecoveryRequest(
        request_id="REC-001",
        incident_id="INC-001",
        reason="owner key compromise",
        target_owner_id="OWNER-001",
        replacement_key_id="KEY-NEW-001",
    )
    return governance, request, (k1, k2, k3)


def test_threshold_recovery_succeeds_and_is_auditable():
    governance, request, keys = _setup()
    approvals = (
        build_recovery_approval(keys[0], "REC-SEC", request),
        build_recovery_approval(keys[1], "REC-GOV", request),
    )
    decision = governance.authorize(request, approvals)
    assert decision.approved is True
    assert decision.threshold == 2
    assert decision.approver_ids == ("REC-GOV", "REC-SEC")
    assert len(decision.request_hash) == 64
    assert len(decision.decision_hash) == 64
    assert governance.is_replayed("REC-001")


def test_insufficient_approvals_are_rejected():
    governance, request, keys = _setup()
    approval = build_recovery_approval(keys[0], "REC-SEC", request)
    with pytest.raises(RecoveryGovernanceError):
        governance.authorize(request, (approval,))


def test_duplicate_approver_is_rejected():
    governance, request, keys = _setup()
    approval = build_recovery_approval(keys[0], "REC-SEC", request)
    with pytest.raises(RecoveryGovernanceError, match="duplicate"):
        governance.authorize(request, (approval, approval))


def test_approvals_must_span_governance_roles():
    k1, a1 = _authority("REC-SEC-1", RecoveryRole.SECURITY)
    k2, a2 = _authority("REC-SEC-2", RecoveryRole.SECURITY)
    governance = RecoveryGovernance(RecoveryPolicy("DEE-RECOVERY-1.0", 2, (a1, a2)))
    request = RecoveryRequest("REC-002", "INC-002", "compromise", "OWNER-001", "KEY-NEW-002")
    approvals = (
        build_recovery_approval(k1, "REC-SEC-1", request),
        build_recovery_approval(k2, "REC-SEC-2", request),
    )
    with pytest.raises(RecoveryGovernanceError, match="distinct governance roles"):
        governance.authorize(request, approvals)


def test_unauthorized_authority_is_rejected():
    governance, request, keys = _setup()
    outsider_key, _ = _authority("OUTSIDER", RecoveryRole.SECURITY)
    approval = build_recovery_approval(outsider_key, "OUTSIDER", request)
    valid = build_recovery_approval(keys[1], "REC-GOV", request)
    with pytest.raises(RecoveryGovernanceError, match="unauthorized"):
        governance.authorize(request, (approval, valid))


def test_invalid_signature_is_rejected():
    governance, request, keys = _setup()
    valid = build_recovery_approval(keys[0], "REC-SEC", request)
    tampered = RecoveryApproval("REC-SEC", request.request_id, valid.signature[:-2] + "AA")
    other = build_recovery_approval(keys[1], "REC-GOV", request)
    with pytest.raises(RecoveryGovernanceError, match="invalid recovery signature"):
        governance.authorize(request, (tampered, other))


def test_request_binding_prevents_reason_or_target_tampering():
    governance, request, keys = _setup()
    approval = build_recovery_approval(keys[0], "REC-SEC", request)
    other = RecoveryRequest(
        request_id=request.request_id,
        incident_id=request.incident_id,
        reason="different reason",
        target_owner_id=request.target_owner_id,
        replacement_key_id=request.replacement_key_id,
    )
    second = build_recovery_approval(keys[1], "REC-GOV", other)
    with pytest.raises(RecoveryGovernanceError, match="invalid recovery signature"):
        governance.authorize(other, (approval, second))


def test_replay_is_rejected():
    governance, request, keys = _setup()
    approvals = (
        build_recovery_approval(keys[0], "REC-SEC", request),
        build_recovery_approval(keys[1], "REC-GOV", request),
    )
    governance.authorize(request, approvals)
    with pytest.raises(RecoveryGovernanceError, match="replay"):
        governance.authorize(request, approvals)


def test_policy_version_mismatch_fails_closed():
    governance, request, keys = _setup()
    mismatched = RecoveryRequest(
        request_id=request.request_id,
        incident_id=request.incident_id,
        reason=request.reason,
        target_owner_id=request.target_owner_id,
        replacement_key_id=request.replacement_key_id,
        policy_version="DEE-RECOVERY-2.0",
    )
    approvals = (
        build_recovery_approval(keys[0], "REC-SEC", mismatched),
        build_recovery_approval(keys[1], "REC-GOV", mismatched),
    )
    with pytest.raises(RecoveryGovernanceError, match="version mismatch"):
        governance.authorize(mismatched, approvals)


def test_private_keys_are_not_part_of_recovery_authority():
    _, authority = _authority("REC-SEC", RecoveryRole.SECURITY)
    assert not hasattr(authority, "private_key")
    assert not hasattr(authority, "secret_key")
