from network.failure import FailureDetector, FailureStatus
from network.failure_isolation import WitnessFailureIsolation


def test_available_witness_is_active():
    isolation = WitnessFailureIsolation()
    status = FailureStatus("node-A", True)

    assert isolation.determine_status(status) == "ACTIVE"
    assert isolation.is_active(status) is True
    assert isolation.is_isolated(status) is False


def test_failed_witness_is_isolated():
    isolation = WitnessFailureIsolation()
    status = FailureStatus("node-A", False, "timeout")

    assert isolation.determine_status(status) == "ISOLATED"
    assert isolation.is_isolated(status) is True
    assert isolation.is_active(status) is False


def test_available_witness_participates_in_consensus():
    isolation = WitnessFailureIsolation()
    status = FailureStatus("node-A", True)

    result = isolation.isolate(status)

    assert result["participates_in_consensus"] is True
    assert result["isolation_status"] == "ACTIVE"


def test_failed_witness_does_not_participate_in_consensus():
    isolation = WitnessFailureIsolation()
    status = FailureStatus("node-A", False, "network_timeout")

    result = isolation.isolate(status)

    assert result["participates_in_consensus"] is False
    assert result["isolation_status"] == "ISOLATED"


def test_failed_reason_is_preserved():
    isolation = WitnessFailureIsolation()
    status = FailureStatus("node-A", False, "connection_lost")

    result = isolation.isolate(status)

    assert result["reason"] == "connection_lost"
    assert result["failure_status"] == "FAILED"


def test_available_status_is_preserved():
    isolation = WitnessFailureIsolation()
    status = FailureStatus("node-A", True)

    result = isolation.isolate(status)

    assert result["node_id"] == "node-A"
    assert result["failure_status"] == "AVAILABLE"
    assert result["isolation_status"] == "ACTIVE"


def test_isolation_is_deterministic():
    isolation = WitnessFailureIsolation()
    status = FailureStatus("node-A", False, "timeout")

    first = isolation.isolate(status)
    second = isolation.isolate(status)

    assert first == second


def test_custom_failure_detector_is_accepted():
    detector = FailureDetector()
    isolation = WitnessFailureIsolation(detector)

    status = detector.detect("node-B", False, "offline")

    assert isolation.is_isolated(status) is True


def test_invalid_status_rejected():
    isolation = WitnessFailureIsolation()

    try:
        isolation.determine_status("invalid")
        assert False
    except TypeError:
        pass


def test_isolation_result_contains_version():
    isolation = WitnessFailureIsolation()
    status = FailureStatus("node-A", False, "timeout")

    result = isolation.isolate(status)

    assert result["version"] == "V85.1"
    assert result["node_id"] == "node-A"
    assert result["failure_status"] == "FAILED"
    assert result["isolation_status"] == "ISOLATED"