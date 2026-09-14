from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LifecycleTransition:
    asset_id: str
    previous_state: str
    new_state: str
    reason: str


class AssetLifecycleEngine:
    def transition(
        self,
        asset_id: str,
        previous_state: str,
        new_state: str,
        reason: str,
    ) -> LifecycleTransition:
        if not asset_id:
            raise ValueError("asset_id is required")
        if not previous_state:
            raise ValueError("previous_state is required")
        if not new_state:
            raise ValueError("new_state is required")
        if not reason:
            raise ValueError("reason is required")
        if previous_state == new_state:
            raise ValueError("lifecycle transition must change state")

        return LifecycleTransition(
            asset_id=asset_id,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason,
        )
