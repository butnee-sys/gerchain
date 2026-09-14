from __future__ import annotations

from .contracts import Asset, OwnershipRight


class OwnershipRightsEngine:
    def assign(self, asset: Asset, right: OwnershipRight) -> Asset:
        if not right.subject_id:
            raise ValueError("subject_id is required")

        if not 0 < right.percentage <= 100:
            raise ValueError("percentage must be > 0 and <= 100")

        duplicate = any(
            existing.subject_id == right.subject_id
            and existing.right_type == right.right_type
            for existing in asset.ownership_rights
        )

        if duplicate:
            raise ValueError("duplicate ownership right")

        total = self.total_ownership(asset) + right.percentage

        if total > 100:
            raise ValueError("ownership percentage exceeds 100")

        asset.ownership_rights.append(right)
        asset.touch()

        return asset

    def total_ownership(self, asset: Asset) -> float:
        return sum(
            right.percentage
            for right in asset.ownership_rights
        )
