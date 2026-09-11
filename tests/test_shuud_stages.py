from datetime import datetime, timedelta, timezone

import pytest

from shuud.stages import measure_stages


def test_stage_timing_measures_two_minute_clearance():
    start = datetime(2026, 9, 12, 0, 0, 0, tzinfo=timezone.utc)
    timestamps = {
        "incident_time": start,
        "evidence_locked_at": start + timedelta(seconds=20),
        "verification_complete_at": start + timedelta(seconds=35),
        "shiid_decided_at": start + timedelta(seconds=50),
        "release_authorized_at": start + timedelta(seconds=65),
        "escrow_released_at": start + timedelta(seconds=120),
    }

    metric = measure_stages("INC-001", timestamps)

    assert metric.clearance_seconds == 120
    assert metric.within_two_minutes is True
    assert metric.stage_seconds["evidence_locked_at"] == 20
    assert metric.stage_seconds["escrow_released_at"] == 55


def test_stage_timing_rejects_non_monotonic_timestamps():
    start = datetime(2026, 9, 12, 0, 0, 0, tzinfo=timezone.utc)
    timestamps = {
        "incident_time": start,
        "evidence_locked_at": start + timedelta(seconds=20),
        "verification_complete_at": start + timedelta(seconds=10),
        "shiid_decided_at": start + timedelta(seconds=50),
        "release_authorized_at": start + timedelta(seconds=65),
        "escrow_released_at": start + timedelta(seconds=120),
    }

    with pytest.raises(ValueError, match="monotonic"):
        measure_stages("INC-001", timestamps)


def test_stage_timing_requires_all_milestones():
    start = datetime(2026, 9, 12, 0, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="missing stage timestamps"):
        measure_stages("INC-001", {"incident_time": start})
