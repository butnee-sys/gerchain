from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from shuud.metrics import OperationalTiming, measure_clearance


def test_operational_timing_tracks_full_lifecycle_and_durations() -> None:
    start = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)
    timing = OperationalTiming({}).with_milestone("incident_created_at", start)
    timing = timing.with_milestone("evidence_locked_at", start + timedelta(seconds=20))
    timing = timing.with_milestone(
        "verification_completed_at", start + timedelta(seconds=35)
    )
    timing = timing.with_milestone("shiid_decided_at", start + timedelta(seconds=55))
    timing = timing.with_milestone(
        "clearance_confirmed_at", start + timedelta(seconds=110)
    )
    timing = timing.with_milestone(
        "settlement_released_at", start + timedelta(seconds=118)
    )

    assert timing.durations() == {
        "incident_to_evidence_seconds": 20.0,
        "evidence_to_verification_seconds": 15.0,
        "verification_to_shiid_seconds": 20.0,
        "shiid_to_clearance_seconds": 55.0,
        "clearance_to_settlement_seconds": 8.0,
        "incident_to_clearance_seconds": 110.0,
        "incident_to_settlement_seconds": 118.0,
    }
    assert timing.within_two_minutes() is True


def test_operational_timing_rejects_backward_milestones() -> None:
    start = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)
    timing = OperationalTiming({}).with_milestone("incident_created_at", start)

    with pytest.raises(ValueError, match="cannot move backward"):
        timing.with_milestone(
            "evidence_locked_at", start - timedelta(seconds=1)
        )


def test_operational_timing_requires_timezone_aware_timestamps() -> None:
    naive = datetime(2026, 9, 12, 12, 0)

    with pytest.raises(ValueError, match="timezone-aware"):
        OperationalTiming({}).with_milestone("incident_created_at", naive)


def test_operational_timing_round_trip_preserves_iso_timestamps() -> None:
    start = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)
    timing = OperationalTiming({}).with_milestone("incident_created_at", start)
    timing = timing.with_milestone(
        "clearance_confirmed_at", start + timedelta(seconds=90)
    )

    restored = OperationalTiming.from_dict(timing.as_dict())

    assert restored.timestamps == timing.timestamps
    assert restored.within_two_minutes() is True


def test_measure_clearance_keeps_existing_two_minute_contract() -> None:
    start = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)
    metric = measure_clearance("INC-1", start, start + timedelta(seconds=121))

    assert metric.elapsed_seconds == 121.0
    assert metric.within_two_minutes is False
