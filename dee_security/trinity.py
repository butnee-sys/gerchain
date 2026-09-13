"""DEE Trinity protection policy.

TRUST, TRANSPARENCY and PERFORMANCE are the three cross-cutting protection
properties of the DEE governance environment.  They are not an application
feature and are not limited to escrow; escrow is one execution domain where
these properties are enforced.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class TrinityError(ValueError):
    """Raised when a Trinity protection requirement is not satisfied."""


class TrinityDimension(str, Enum):
    TRUST = "TRUST"
    TRANSPARENCY = "TRANSPARENCY"
    PERFORMANCE = "PERFORMANCE"


@dataclass(frozen=True)
class TrinityDecision:
    """Fail-closed decision for a protected DEE operation."""

    trust: bool
    transparency: bool
    performance: bool

    @property
    def allowed(self) -> bool:
        return self.trust and self.transparency and self.performance

    def require_allowed(self) -> None:
        if not self.allowed:
            failed = [
                dimension.value
                for dimension, passed in (
                    (TrinityDimension.TRUST, self.trust),
                    (TrinityDimension.TRANSPARENCY, self.transparency),
                    (TrinityDimension.PERFORMANCE, self.performance),
                )
                if not passed
            ]
            raise TrinityError(f"DEE Trinity denied: {', '.join(failed)}")


def evaluate_trinity(*, trust: bool, transparency: bool, performance: bool) -> TrinityDecision:
    """Evaluate the three DEE protection dimensions with fail-closed semantics."""
    return TrinityDecision(
        trust=bool(trust),
        transparency=bool(transparency),
        performance=bool(performance),
    )


def require_trinity(proof: Mapping[str, bool]) -> TrinityDecision:
    """Require explicit proof for all three dimensions.

    Missing dimensions are denied rather than inferred. This keeps the Trinity
    boundary independent from any particular application or escrow workflow.
    """
    decision = evaluate_trinity(
        trust=proof.get(TrinityDimension.TRUST.value, False),
        transparency=proof.get(TrinityDimension.TRANSPARENCY.value, False),
        performance=proof.get(TrinityDimension.PERFORMANCE.value, False),
    )
    decision.require_allowed()
    return decision
