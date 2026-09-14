from __future__ import annotations

from .contracts import AssetIdentity


class AssetIdentityEngine:
    def create(
        self,
        asset_id: str,
        asset_type: str,
        namespace: str = "NEF",
    ) -> AssetIdentity:
        if not asset_id:
            raise ValueError("asset_id is required")

        if not asset_type:
            raise ValueError("asset_type is required")

        return AssetIdentity(
            asset_id=asset_id,
            asset_type=asset_type,
            namespace=namespace,
        )

    def matches(self, identity: AssetIdentity, asset_id: str) -> bool:
        return identity.asset_id == asset_id
