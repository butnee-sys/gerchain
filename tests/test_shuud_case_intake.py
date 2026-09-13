from datetime import date, timedelta

import pytest

from shuud.case_intake import SandboxCaseBinding, validate_case_intake
from shuud.sandbox_config import SandboxConfig, SandboxStatus


def _active_config() -> SandboxConfig:
    today = date.today()
    return SandboxConfig(
        sandbox_id="S-001",
        name="SHUUD test sandbox",
        start_date=today - timedelta(days=1),
        end_date=today + timedelta(days=89),
        status=SandboxStatus.ACTIVE,
    )


def test_case_intake_binds_active_sandbox_to_existing_incident():
    binding = validate_case_intake(
        _active_config(),
        incident_id="INC-001",
        intake_date=date.today(),
    )

    assert binding == SandboxCaseBinding(
        sandbox_id="S-001",
        incident_id="INC-001",
        intake_date=date.today(),
    )
    assert binding.to_dict()["sandbox_id"] == "S-001"


def test_case_intake_rejects_planned_sandbox():
    today = date.today()
    config = SandboxConfig(
        sandbox_id="S-002",
        name="SHUUD test sandbox",
        start_date=today + timedelta(days=1),
        end_date=today + timedelta(days=90),
        status=SandboxStatus.PLANNED,
    )

    with pytest.raises(ValueError, match="not active"):
        validate_case_intake(config, incident_id="INC-002", intake_date=today)


def test_case_intake_rejects_completed_window():
    today = date.today()
    config = SandboxConfig(
        sandbox_id="S-003",
        name="SHUUD test sandbox",
        start_date=today - timedelta(days=90),
        end_date=today - timedelta(days=1),
        status=SandboxStatus.ACTIVE,
    )

    with pytest.raises(ValueError, match="not active"):
        validate_case_intake(config, incident_id="INC-003", intake_date=today)
