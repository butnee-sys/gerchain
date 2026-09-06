from network.failure import FailureDetector, FailureStatus


def test_failure_status_available():
    status = FailureStatus("node-A", True)
    assert status.available is True
    assert status.failed is False


def test_failure_status_failed():
    status = FailureStatus("node-A", False, "timeout")
    assert status.available is False
    assert status.failed is True
    assert status.reason == "timeout"


def test_detector_detect_available():
    detector = FailureDetector()
    status = detector.detect("node-A", True)
    assert status.available is True
    assert detector.is_available(status) is True
    assert detector.is_failed(status) is False


def test_detector_detect_failed():
    detector = FailureDetector()
    status = detector.detect("node-A", False, "network_timeout")
    assert status.failed is True
    assert detector.is_failed(status) is True
    assert detector.is_available(status) is False


def test_classify_available():
    detector = FailureDetector()
    status = detector.detect("node-A", True)
    assert detector.classify(status) == "AVAILABLE"


def test_classify_failed():
    detector = FailureDetector()
    status = detector.detect("node-A", False, "connection_lost")
    assert detector.classify(status) == "FAILED"


def test_to_dict_available():
    detector = FailureDetector()
    status = detector.detect("node-A", True)

    result = detector.to_dict(status)

    assert result["version"] == "V85.0"
    assert result["node_id"] == "node-A"
    assert result["available"] is True
    assert result["failed"] is False
    assert result["classification"] == "AVAILABLE"


def test_to_dict_failed():
    detector = FailureDetector()
    status = detector.detect("node-A", False, "timeout")

    result = detector.to_dict(status)

    assert result["version"] == "V85.0"
    assert result["node_id"] == "node-A"
    assert result["available"] is False
    assert result["failed"] is True
    assert result["reason"] == "timeout"
    assert result["classification"] == "FAILED"


def test_failure_status_is_immutable():
    status = FailureStatus("node-A", False, "timeout")

    try:
        status.node_id = "node-B"
        assert False
    except Exception:
        pass


def test_invalid_status_type_rejected():
    detector = FailureDetector()

    try:
        detector.is_failed("invalid")
        assert False
    except TypeError:
        pass