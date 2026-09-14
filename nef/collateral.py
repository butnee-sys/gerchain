from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CollateralStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    LIQUIDATED = "LIQUIDATED"


@dataclass(frozen=True)
class Collateral:
    collateral_id: str
    asset_id: str
    secured_party_id: str
    value: Decimal
    currency: str
    status: CollateralStatus = CollateralStatus.ACTIVE
    created_at: datetime = field(default_factory=utc_now)


class CollateralEngine:
    def create(
        self,
        collateral_id: str,
        asset_id: str,
        secured_party_id: str,
        value: Decimal,
        currency: str,
    ) -> Collateral:
        if not collateral_id:
            raise ValueError("collateral_id is required")
        if not asset_id:
            raise ValueError("asset_id is required")
        if not secured_party_id:
            raise ValueError("secured_party_id is required")
        if value < 0:
            raise ValueError("collateral value cannot be negative")
        if not currency:
            raise ValueError("currency is required")

        return Collateral(
            collateral_id=collateral_id,
            asset_id=asset_id,
            secured_party_id=secured_party_id,
            value=value,
            currency=currency,
        )

    def release(self, collateral: Collateral) -> Collateral:
        if collateral.status != CollateralStatus.ACTIVE:
            raise ValueError("only ACTIVE collateral can be released")

        return Collateral(
            collateral_id=collateral.collateral_id,
            asset_id=collateral.asset_id,
            secured_party_id=collateral.secured_party_id,
            value=collateral.value,
            currency=collateral.currency,
            status=CollateralStatus.RELEASED,
            created_at=collateral.created_at,
        )
