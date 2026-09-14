from __future__ import annotations

from .contracts import Asset, AssetState


class InvalidAssetStateTransition(ValueError):
    pass


class AssetStateEngine:
    ALLOWED_TRANSITIONS = {
        AssetState.REGISTERED: {
            AssetState.ACTIVE,
        },
        AssetState.ACTIVE: {
            AssetState.ENCUMBERED,
            AssetState.COLLATERALIZED,
            AssetState.TRANSFERRED,
            AssetState.RETIRED,
        },
        AssetState.ENCUMBERED: {
            AssetState.ACTIVE,
            AssetState.COLLATERALIZED,
            AssetState.RETIRED,
        },
        AssetState.COLLATERALIZED: {
            AssetState.ACTIVE,
            AssetState.ENCUMBERED,
            AssetState.RETIRED,
        },
        AssetState.TRANSFERRED: {
            AssetState.ACTIVE,
            AssetState.RETIRED,
        },
        AssetState.RETIRED: set(),
    }

    def transition(
        self,
        asset: Asset,
        target: AssetState,
    ) -> Asset:
        allowed = self.ALLOWED_TRANSITIONS.get(asset.state, set())

        if target not in allowed:
            raise InvalidAssetStateTransition(
                f"{asset.state.value} -> {target.value}"
            )

        asset.state = target
        asset.touch()

        return asset
