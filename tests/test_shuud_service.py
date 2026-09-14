from architecture.contracts import ActorType, BoundaryRequest
from apps.shuud.service import SHUUDService


def request(**payload):
    return BoundaryRequest(ActorType.PERSON, "driver-1", "shuud-rapid-release", payload, correlation_id="SHUUD-C1")


def test_shuud_accepts_verified_compensation_within_limit():
    response = SHUUDService().handle(request(
        incident_id="INC-1", vehicle_id="VH-1", compensation=1_000_000, evidence_verified=True
    ))
    assert response.accepted is True
    assert response.data["status"] == "RELEASE_READY"
    assert response.data["compensation"] == 1_000_000


def test_shuud_fails_closed_when_evidence_is_not_verified():
    response = SHUUDService().handle(request(
        incident_id="INC-2", vehicle_id="VH-2", compensation=1_000_000, evidence_verified=False
    ))
    assert response.accepted is False


def test_shuud_rejects_over_limit():
    response = SHUUDService().handle(request(
        incident_id="INC-3", vehicle_id="VH-3", compensation=2_000_001, evidence_verified=True
    ))
    assert response.accepted is False
