from __future__ import annotations

import pytest

from dee.self_maintainer import HealthState, IntegrityState, MaintainerObservation, SelfMaintainer


def observation(**overrides):
    values = dict(component="gerchain", health=HealthState.HEALTHY, integrity=IntegrityState.VERIFIED, version="1.0", dependency_ok=True, lifecycle_ok=True)
    values.update(overrides)
    return MaintainerObservation(**values)


def test_healthy_component_requires_no_action():
    maintainer = SelfMaintainer({"gerchain": lambda: observation()})
    decision = maintainer.inspect_and_decide("gerchain")
    assert decision.action == "NONE"


def test_integrity_failure_isolated_fail_closed():
    maintainer = SelfMaintainer({"gerchain": lambda: observation(integrity=IntegrityState.MISMATCH)})
    decision = maintainer.inspect_and_decide("gerchain")
    assert decision.action == "ISOLATE"


def test_failed_health_requests_recovery():
    maintainer = SelfMaintainer({"gerchain": lambda: observation(health=HealthState.FAILED)})
    decision = maintainer.inspect_and_decide("gerchain")
    assert decision.action == "RECOVER"


def test_missing_component_is_isolated():
    maintainer = SelfMaintainer({})
    decision = maintainer.inspect_and_decide("unknown")
    assert decision.action == "ISOLATE"


def test_probe_must_return_observation():
    maintainer = SelfMaintainer({"bad": lambda: "bad"})
    with pytest.raises(TypeError, match="MaintainerObservation"):
        maintainer.inspect("bad")
