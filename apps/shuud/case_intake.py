"""SHUUD sandbox case intake policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .sandbox_config import SandboxConfig


@dataclass(frozen=True)
class SandboxCaseBinding:
    sandbox_id: str
    incident_id: str
    intake_date: date

    def to_dict(self) -> dict[str, str]:
        return {
            "sandbox_id": self.sandbox_id,
            "incident_id": self.incident_id,
            "intake_date": self.intake_date.isoformat(),
        }


def validate_case_intake(
    config: SandboxConfig,
    *,
    incident_id: str,
    intake_date: date,
) -> SandboxCaseBinding:
    if not incident_id.strip():
        raise ValueError("incident_id is required")
    if config.operational_status(intake_date) != "ACTIVE":
        raise ValueError("sandbox is not active for case intake")
    return SandboxCaseBinding(
        sandbox_id=config.sandbox_id,
        incident_id=incident_id,
        intake_date=intake_date,
    )


__all__ = ["SandboxCaseBinding", "validate_case_intake"]
