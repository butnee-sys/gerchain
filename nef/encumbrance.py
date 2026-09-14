from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EncumbranceType(str, Enum):
    PLEDGE = "PLEDGE"
    LIEN = "LIEN"
    MORTGAGE = "MORTGAGE"
    RESTRICTION = "RESTRICTION"
    OTHER = "OTHER"


class EncumbranceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Encumbrance:
    encumbrance_id: str
    asset_id: str
    encumbrance_type: EncumbranceType
    holder_id: str
    reference: str
    status: EncumbranceStatus = EncumbranceStatus.ACTIVE
    created_at: datetime = field(default_factory=utc_now)
    released_at: datetime | None = None


class EncumbranceEngine:
    def create(
        self,
        encumbrance_id: str,
        asset_id: str,
        encumbrance_type: EncumbranceType,
        holder_id: str,
        reference: str,
    ) -> Encumbrance:
        required = {
            "encumbrance_id": encumbrance_id,
            "asset_id": asset_id,
            "holder_id": holder_id,
            "reference": reference,
        }

        for name, value in required.items():
            if not value:
                raise ValueError(f"{name} is required")

        return Encumbrance(
            encumbrance_id=encumbrance_id,
            asset_id=asset_id,
            encumbrance_type=encumbrance_type,
            holder_id=holder_id,
            reference=reference,
        )

    def release(self, encumbrance: Encumbrance) -> Encumbrance:
        if encumbrance.status != EncumbranceStatus.ACTIVE:
            raise ValueError("only ACTIVE encumbrance can be released")

        return Encumbrance(
            encumbrance_id=encumbrance.encumbrance_id,
            asset_id=encumbrance.asset_id,
            encumbrance_type=encumbrance.encumbrance_type,
            holder_id=encumbrance.holder_id,
            reference=encumbrance.reference,
            status=EncumbranceStatus.RELEASED,
            created_at=encumbrance.created_at,
            released_at=utc_now(),
        )
