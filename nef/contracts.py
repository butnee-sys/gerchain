from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AssetState(str, Enum):
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    ENCUMBERED = "ENCUMBERED"
    COLLATERALIZED = "COLLATERALIZED"
    TRANSFERRED = "TRANSFERRED"
    RETIRED = "RETIRED"


class OwnershipType(str, Enum):
    OWNER = "OWNER"
    BENEFICIAL_OWNER = "BENEFICIAL_OWNER"
    CO_OWNER = "CO_OWNER"
    RIGHTS_HOLDER = "RIGHTS_HOLDER"


@dataclass(frozen=True)
class AssetIdentity:
    asset_id: str
    asset_type: str
    namespace: str = "NEF"


@dataclass
class OwnershipRight:
    subject_id: str
    right_type: OwnershipType
    percentage: float
    effective_from: datetime = field(default_factory=utc_now)


@dataclass
class DigitalAssetRecord:
    record_id: str
    version: int
    data: dict[str, Any]
    evidence_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Asset:
    asset_id: str
    asset_type: str
    identity: AssetIdentity
    state: AssetState = AssetState.REGISTERED
    ownership_rights: list[OwnershipRight] = field(default_factory=list)
    digital_record: DigitalAssetRecord | None = None
    version: int = 1
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.version += 1
        self.updated_at = utc_now()
