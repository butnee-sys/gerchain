from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VerificationStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class VerificationResult:
    verification_id: str
    asset_id: str
    status: VerificationStatus
    verifier_id: str
    evidence_ids: tuple[str, ...] = ()
    reason: str | None = None
    verified_at: datetime = field(default_factory=utc_now)


class VerificationEngine:
    def verify(
        self,
        verification_id: str,
        asset_id: str,
        verifier_id: str,
        evidence_ids: list[str],
    ) -> VerificationResult:
        if not verification_id:
            raise ValueError("verification_id is required")

        if not asset_id:
            raise ValueError("asset_id is required")

        if not verifier_id:
            raise ValueError("verifier_id is required")

        if not evidence_ids:
            return VerificationResult(
                verification_id=verification_id,
                asset_id=asset_id,
                status=VerificationStatus.UNKNOWN,
                verifier_id=verifier_id,
                reason="No evidence supplied",
            )

        return VerificationResult(
            verification_id=verification_id,
            asset_id=asset_id,
            status=VerificationStatus.VERIFIED,
            verifier_id=verifier_id,
            evidence_ids=tuple(evidence_ids),
        )

    def reject(
        self,
        verification_id: str,
        asset_id: str,
        verifier_id: str,
        reason: str,
    ) -> VerificationResult:
        if not reason:
            raise ValueError("reason is required")

        return VerificationResult(
            verification_id=verification_id,
            asset_id=asset_id,
            status=VerificationStatus.REJECTED,
            verifier_id=verifier_id,
            reason=reason,
        )
