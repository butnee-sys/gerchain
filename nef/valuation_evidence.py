from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ValuationEvidence:
    evidence_id: str
    valuation_id: str
    evidence_type: str
    source: str
    reference: str
    verified: bool = False
    created_at: datetime = field(default_factory=utc_now)


class ValuationEvidenceEngine:
    def create(
        self,
        evidence_id: str,
        valuation_id: str,
        evidence_type: str,
        source: str,
        reference: str,
    ) -> ValuationEvidence:
        if not evidence_id:
            raise ValueError("evidence_id is required")

        if not valuation_id:
            raise ValueError("valuation_id is required")

        if not evidence_type:
            raise ValueError("evidence_type is required")

        if not source:
            raise ValueError("source is required")

        if not reference:
            raise ValueError("reference is required")

        return ValuationEvidence(
            evidence_id=evidence_id,
            valuation_id=valuation_id,
            evidence_type=evidence_type,
            source=source,
            reference=reference,
        )

    def verify(
        self,
        evidence: ValuationEvidence,
    ) -> ValuationEvidence:
        return ValuationEvidence(
            evidence_id=evidence.evidence_id,
            valuation_id=evidence.valuation_id,
            evidence_type=evidence.evidence_type,
            source=evidence.source,
            reference=evidence.reference,
            verified=True,
            created_at=evidence.created_at,
        )
