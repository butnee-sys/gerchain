from datetime import datetime, timedelta, timezone

import pytest

from shuud.app.domain.incident import Incident, IncidentState, IncidentType
from shuud.app.services.two_minute import achieved


def test_valid_transition_chain():
    incident = Incident.create(IncidentType.MINOR_COLLISION, 47.918, 106.917)
    incident = incident.transition(IncidentState.VERIFIED)
    incident = incident.transition(IncidentState.DISPATCHED)
    incident = incident.transition(IncidentState.ON_SCENE)
    incident = incident.transition(IncidentState.CLEARING)
    incident = incident.transition(IncidentState.CLEARED)
    assert incident.state == IncidentState.CLEARED


def test_invalid_transition_is_rejected():
    incident = Incident.create(IncidentType.BREAKDOWN, 47.918, 106.917)
    with pytest.raises(ValueError):
        incident.transition(IncidentState.CLOSED)


def test_two_minute_target():
    reported = datetime.now(timezone.utc)
    assert achieved(reported, reported + timedelta(seconds=119))
    assert not achieved(reported, reported + timedelta(seconds=121))
