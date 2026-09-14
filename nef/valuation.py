from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from .contracts import Asset


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ValuationBasis(str, Enum):
    MARKET = "MARKET"
    COST = "COST"
    INCOME = "INCOME"
    EXPERT = "EXPERT"
    OTHER = "OTHER"


@dataclass(frozen=True)
class Valuation:
    valuation_id: str
    asset_id: str
    value: Decimal
    currency: str
    basis: ValuationBasis
    effective_at: datetime = field(default_factory=utc_now)
    valuer_id: str | None = None
    evidence_ids: tuple[str, ...] = ()
    version: int = 1


class ValuationEngine:
    def create(
        self,
        asset: Asset,
        valuation_id: str,
        value: Decimal | int | float | str,
        currency: str = "MNT",
        basis: ValuationBasis = ValuationBasis.EXPERT,
        valuer_id: str | None = None,
        evidence_ids: list[str] | None = None,
    ) -> Valuation:
        amount = Decimal(str(value))

        if amount < 0:
            raise ValueError("valuation cannot be negative")

        if not currency:
            raise ValueError("currency is required")

        return Valuation(
            valuation_id=valuation_id,
            asset_id=asset.asset_id,
            value=amount,
            currency=currency,
            basis=basis,
            valuer_id=valuer_id,
            evidence_ids=tuple(evidence_ids or []),
        )
