from datetime import date

import pytest

from shuud.sandbox_config import SandboxConfig, SandboxStatus


def test_day0_config_round_trips_and_builds_gate_thresholds():
    config = SandboxConfig(
        sandbox_id="UB-SHUUD-2026-Q4",
        name="Ulaanbaatar SHUUD 90-day sandbox",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 12, 29),
        status=SandboxStatus.PLANNED,
        target_seconds=120,
        minimum_cases=30,
        participants=("UB Road Operations", "Insurer A", "SHUUD Operator"),
    )

    restored = SandboxConfig.from_dict(config.to_dict())
    assert restored == config
    assert restored.thresholds.target_seconds == 120
    assert restored.thresholds.minimum_cases == 30
    assert restored.operational_status(date(2026, 9, 30)) == "PLANNED"
    assert restored.operational_status(date(2026, 10, 1)) == "ACTIVE"
    assert restored.operational_status(date(2026, 12, 30)) == "COMPLETED"


def test_suspended_status_does_not_auto_activate():
    config = SandboxConfig(
        sandbox_id="S-001",
        name="Test",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=SandboxStatus.SUSPENDED,
    )
    assert config.operational_status(date(2026, 6, 1)) == "SUSPENDED"


def test_day0_rejects_invalid_window_and_threshold_order():
    with pytest.raises(ValueError):
        SandboxConfig(
            sandbox_id="S-001",
            name="Test",
            start_date=date(2026, 10, 2),
            end_date=date(2026, 10, 1),
        )

    with pytest.raises(ValueError):
        SandboxConfig(
            sandbox_id="S-002",
            name="Test",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 2),
            conditional_clearance_rate=0.96,
            go_clearance_rate=0.95,
        )
