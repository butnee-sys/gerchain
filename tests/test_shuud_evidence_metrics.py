from datetime import datetime, timedelta, timezone

import pytest

from shuud.evidence import create_evidence_envelope
from shuud.metrics import measure_clearance


def test_evidence_envelope_has_deterministic_commitment():
    kwargs = dict(
        incident_id="INC-001",
        evidence_refs=["PHOTO-001", "VIDEO-001"],
        gps_coordinates="47.9184,106.9177",
        captured_at="2026-09-12T00:00:00+00:00",
        vehicle_identity_refs=["VIN-A", "VIN-B"],
        consent_refs=["CONSENT-A", "CONSENT-B"],
        media_complete=True,
    )
    first = create_evidence_envelope(**kwargs)
    second = create_evidence_envelope(**kwargs)

    assert first.content_hash == second.content_hash
    assert first.incident_id == "INC-001"


def test_incomplete_media_is_rejected():
    with pytest.raises(ValueError):
        create_evidence_envelope(
            "INC-001",
            evidence_refs=["PHOTO-001"],
            gps_coordinates="47.9184,106.9177",
            captured_at="2026-09-12T00:00:00+00:00",
            vehicle_identity_refs=["VIN-A", "VIN-B"],
            consent_refs=["CONSENT-A", "CONSENT-B"],
            media_complete=False,
        )


def test_two_minute_metric():
    start = datetime(2026, 9, 12, tzinfo=timezone.utc)
    metric = measure_clearance(
        "INC-001",
        start,
        start + timedelta(seconds=120),
    )

    assert metric.elapsed_seconds == 120
    assert metric.within_two_minutes is True


def test_late_clearance_fails_kpi():
    start = datetime(2026, 9, 12, tzinfo=timezone.utc)
    metric = measure_clearance(
        "INC-001",
        start,
        start + timedelta(seconds=121),
    )

    assert metric.elapsed_seconds == 121
    assert metric.within_two_minutes is False
