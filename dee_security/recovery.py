"""Fail-closed, multi-party emergency recovery governance for DEE."""
from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class RecoveryGovernanceError(PermissionError):
    """Raised when an emergency recovery request is not authorized."""


class RecoveryRole(str, Enum):
    SECURITY = "SECURITY"
    GOVERNANCE = "GOVERNANCE"
    AUDITOR = "AUDITOR"


@dataclass(frozen=True)
class RecoveryAuthority:
    authority_id: str
    role: RecoveryRole
    public_key_b64: str


@dataclass(frozen=True)
class RecoveryRequest:
    request_id: str
    incident_id: str
    reason: str
    target_owner_id: str
    replacement_key_id: str
    policy_version: str = "DEE-RECOVERY-1.0"

    def signing_payload(self) -> dict[str, str]:
        return {
            "incident_id": self.incident_id,
            "policy_version": self.policy_version,
            "reason": self.reason,
            "replacement_key_id": self.replacement_key_id,
            "request_id": self.request_id,
            "target_owner_id": self.target_owner_id,
        }


@dataclass(frozen=True)
class RecoveryApproval:
    authority_id: str
    request_id: str
    signature: str

    def signing_payload(self, request: RecoveryRequest) -> dict[str, str]:
        return {
            "authority_id": self.authority_id,
            "request": _canonical(request.signing_payload()).decode("utf-8"),
            "request_id": self.request_id,
        }


@dataclass(frozen=True)
class RecoveryDecision:
    request_id: str
    policy_version: str
    threshold: int
    approver_ids: tuple[str, ...]
    request_hash: str
    decision_hash: str
    approved: bool = True


@dataclass(frozen=True)
class RecoveryPolicy:
    version: str
    threshold: int
    authorities: tuple[RecoveryAuthority, ...]

    def __post_init__(self) -> None:
        if not self.version or self.threshold < 1:
            raise RecoveryGovernanceError("invalid recovery policy")
        if self.threshold > len(self.authorities):
            raise RecoveryGovernanceError("recovery threshold exceeds authority set")
        ids = [a.authority_id for a in self.authorities]
        if not all(ids) or len(ids) != len(set(ids)):
            raise RecoveryGovernanceError("recovery authority ids must be unique")


class RecoveryGovernance:
    """Verifies emergency recovery approvals and consumes request ids exactly once."""

    def __init__(self, policy: RecoveryPolicy) -> None:
        self.policy = policy
        self._consumed_request_ids: set[str] = set()

    def authorize(
        self,
        request: RecoveryRequest,
        approvals: tuple[RecoveryApproval, ...],
    ) -> RecoveryDecision:
        self._validate_request(request)
        if request.request_id in self._consumed_request_ids:
            raise RecoveryGovernanceError("recovery request replay detected")
        if request.policy_version != self.policy.version:
            raise RecoveryGovernanceError("recovery policy version mismatch")
        if not approvals:
            raise RecoveryGovernanceError("recovery requires multi-party approval")

        authorities: Mapping[str, RecoveryAuthority] = {
            authority.authority_id: authority for authority in self.policy.authorities
        }
        approver_ids = [approval.authority_id for approval in approvals]
        if len(approver_ids) != len(set(approver_ids)):
            raise RecoveryGovernanceError("duplicate recovery approver")
        if len(approvals) < self.policy.threshold:
            raise RecoveryGovernanceError("recovery approval threshold not met")

        for approval in approvals:
            authority = authorities.get(approval.authority_id)
            if authority is None:
                raise RecoveryGovernanceError("unauthorized recovery authority")
            if approval.request_id != request.request_id:
                raise RecoveryGovernanceError("approval/request mismatch")
            if not approval.signature:
                raise RecoveryGovernanceError("missing recovery signature")
            _verify(authority, approval, request)

        if len({authorities[a].role for a in approver_ids}) < 2:
            raise RecoveryGovernanceError("recovery approvals must span distinct governance roles")

        request_hash = _sha256(_canonical(request.signing_payload()))
        decision_payload = {
            "approver_ids": sorted(approver_ids),
            "policy_version": self.policy.version,
            "request_hash": request_hash,
            "request_id": request.request_id,
            "threshold": self.policy.threshold,
        }
        decision_hash = _sha256(_canonical(decision_payload))
        decision = RecoveryDecision(
            request_id=request.request_id,
            policy_version=self.policy.version,
            threshold=self.policy.threshold,
            approver_ids=tuple(sorted(approver_ids)),
            request_hash=request_hash,
            decision_hash=decision_hash,
        )
        self._consumed_request_ids.add(request.request_id)
        return decision

    def is_replayed(self, request_id: str) -> bool:
        return bool(request_id) and request_id in self._consumed_request_ids

    @staticmethod
    def _validate_request(request: RecoveryRequest) -> None:
        fields = (
            request.request_id,
            request.incident_id,
            request.reason,
            request.target_owner_id,
            request.replacement_key_id,
        )
        if not all(field.strip() for field in fields):
            raise RecoveryGovernanceError("recovery request fields are incomplete")


def _canonical(payload: Mapping[str, str]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_recovery_approval(
    private_key,
    authority_id: str,
    request: RecoveryRequest,
) -> RecoveryApproval:
    """Sign a recovery approval with an externally held Ed25519 private key."""
    if not authority_id:
        raise RecoveryGovernanceError("authority id is required")
    unsigned = RecoveryApproval(authority_id, request.request_id, "")
    signature = base64.b64encode(private_key.sign(_canonical(unsigned.signing_payload(request)))).decode("ascii")
    return RecoveryApproval(authority_id, request.request_id, signature)


def _verify(authority: RecoveryAuthority, approval: RecoveryApproval, request: RecoveryRequest) -> None:
    try:
        public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(authority.public_key_b64, validate=True))
        public_key.verify(
            base64.b64decode(approval.signature, validate=True),
            _canonical(approval.signing_payload(request)),
        )
    except Exception as exc:
        raise RecoveryGovernanceError("invalid recovery signature") from exc
