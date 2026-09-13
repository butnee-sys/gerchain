"""DEE evidence governance with deterministic hashing and fail-closed checks."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .root_of_trust import RootOfTrust, SecurityError
from .trinity import require_trinity


class EvidenceGovernanceError(SecurityError):
    """Raised when evidence cannot be trusted, traced, or used."""


def canonical_evidence(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def evidence_hash(value: Any) -> str:
    return sha256(canonical_evidence(value)).hexdigest()


@dataclass(frozen=True)
class ProtectedEvidence:
    evidence_id: str
    case_id: str
    digest: str
    owner_id: str

    @classmethod
    def capture(cls, *, evidence_id: str, case_id: str, evidence: Any, root: RootOfTrust) -> "ProtectedEvidence":
        if not evidence_id or not case_id:
            raise EvidenceGovernanceError("evidence_id and case_id are required")
        return cls(evidence_id, case_id, evidence_hash(evidence), root.owner_id)

    def verify(self, *, root: RootOfTrust, evidence: Any) -> bool:
        return (
            self.owner_id == root.owner_id
            and self.digest == evidence_hash(evidence)
        )


def require_protected_evidence(
    *,
    root: RootOfTrust,
    evidence: ProtectedEvidence,
    payload: Any,
    trinity_proof: Mapping[str, bool],
) -> None:
    """Require owner binding, immutable evidence identity, and all Trinity dimensions."""
    if evidence.owner_id != root.owner_id:
        raise EvidenceGovernanceError("evidence owner is not bound to DEE Root of Trust")
    if evidence.digest != evidence_hash(payload):
        raise EvidenceGovernanceError("evidence integrity verification failed")
    require_trinity(trinity_proof)


__all__ = [
    "EvidenceGovernanceError",
    "ProtectedEvidence",
    "canonical_evidence",
    "evidence_hash",
    "require_protected_evidence",
]
