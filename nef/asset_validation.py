from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import Asset
from .verification import VerificationResult, VerificationStatus


class AssetValidationStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    VALID = "VALID"
    INVALID = "INVALID"


@dataclass(frozen=True)
class AssetValidationResult:
    asset_id: str
    status: AssetValidationStatus
    checks: tuple[str, ...]
    reason: str | None = None


class AssetValidationEngine:
    def validate(
        self,
        asset: Asset,
        verification: VerificationResult,
    ) -> AssetValidationResult:
        checks: list[str] = []

        if not asset.asset_id:
            return AssetValidationResult(
                asset_id=asset.asset_id,
                status=AssetValidationStatus.INVALID,
                checks=(),
                reason="Asset ID is missing",
            )

        checks.append("ASSET_ID")

        if asset.identity.asset_id != asset.asset_id:
            return AssetValidationResult(
                asset_id=asset.asset_id,
                status=AssetValidationStatus.INVALID,
                checks=tuple(checks),
                reason="Identity mismatch",
            )

        checks.append("IDENTITY")

        if verification.status == VerificationStatus.UNKNOWN:
            return AssetValidationResult(
                asset_id=asset.asset_id,
                status=AssetValidationStatus.UNKNOWN,
                checks=tuple(checks),
                reason="Verification is unknown",
            )

        if verification.status == VerificationStatus.REJECTED:
            return AssetValidationResult(
                asset_id=asset.asset_id,
                status=AssetValidationStatus.INVALID,
                checks=tuple(checks),
                reason=verification.reason or "Verification rejected",
            )

        checks.append("VERIFICATION")

        return AssetValidationResult(
            asset_id=asset.asset_id,
            status=AssetValidationStatus.VALID,
            checks=tuple(checks),
        )
