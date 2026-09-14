from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class AssetVersion:
    asset_id: str
    version: int
    snapshot: dict[str, Any]
    created_at: datetime = field(default_factory=utc_now)


class AssetVersionEngine:
    def create(
        self,
        asset_id: str,
        version: int,
        snapshot: dict[str, Any],
    ) -> AssetVersion:
        if not asset_id:
            raise ValueError("asset_id is required")

        if version < 1:
            raise ValueError("version must be >= 1")

        return AssetVersion(
            asset_id=asset_id,
            version=version,
            snapshot=dict(snapshot),
        )
