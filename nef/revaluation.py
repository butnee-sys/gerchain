from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from .contracts import Asset
from .valuation import Valuation, ValuationBasis


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Revaluation:
    revaluation_id: str
    asset_id: str
    previous_valuation_id: str
    valuation: Valuation
    change: Decimal
    created_at: datetime = field(default_factory=utc_now)


class RevaluationEngine:
    def create(
        self,
        asset: Asset,
        revaluation_id: str,
        previous: Valuation,
        new_value: Decimal | int | float | str,
        basis: ValuationBasis,
        currency: str | None = None,
        valuer_id: str | None = None,
        evidence_ids: list[str] | None = None,
    ) -> Revaluation:
        amount = Decimal(str(new_value))

        if amount < 0:
            raise ValueError("revaluation cannot be negative")

        new_currency = currency or previous.currency

        valuation = Valuation(
            valuation_id=f"{revaluation_id}:VALUATION",
            asset_id=asset.asset_id,
            value=amount,
            currency=new_currency,
            basis=basis,
            valuer_id=valuer_id,
            evidence_ids=tuple(evidence_ids or []),
            version=previous.version + 1,
        )

        return Revaluation(
            revaluation_id=revaluation_id,
            asset_id=asset.asset_id,
            previous_valuation_id=previous.valuation_id,
            valuation=valuation,
            change=amount - previous.value,
        )
