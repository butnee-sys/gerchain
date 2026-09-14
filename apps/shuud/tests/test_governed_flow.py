from architecture.contracts import ActorType, BoundaryRequest, BoundaryResponse
from architecture.governed_flow_adapters import DEEToG3BoundaryAdapter, G3ToCoreBoundaryAdapter
from apps.shuud.integration.shuud_governed_flow import SHUUDGovernedFlow


class Stub:
    def __init__(self, name, accepted=True):
        self.name = name
        self.accepted = accepted
        self.seen = []

    def handle(self, request):
        self.seen.append(request)
        return BoundaryResponse(self.accepted, request.activity, request.correlation_id, {self.name: "passed"}, None if self.accepted else f"{self.name} denied")


def req():
    return BoundaryRequest(ActorType.COMPANY, "insurer-1", "shuud-rapid-release", {"incident_id": "INC-1", "evidence_verified": True}, "cred", "corr-1")


def test_shuud_governed_flow_crosses_adapters_in_order():
    exim, g3, core = Stub("exim"), Stub("g3"), Stub("core")
    flow = SHUUDGovernedFlow(i2b_exim=type("I2BEXIM", (), {"handle": lambda self, request: exim.handle(request)})(), dee_to_g3=DEEToG3BoundaryAdapter(g3), g3_to_core=G3ToCoreBoundaryAdapter(core))
    response = flow.handle(req())
    assert response.accepted
    assert len(exim.seen) == len(g3.seen) == len(core.seen) == 1
    assert g3.seen[0].payload["exim"] == "passed"
    assert core.seen[0].payload["g3"] == "passed"


def test_shuud_governed_flow_stops_before_core_when_g3_denies():
    exim, g3, core = Stub("exim"), Stub("g3", accepted=False), Stub("core")
    flow = SHUUDGovernedFlow(i2b_exim=type("I2BEXIM", (), {"handle": lambda self, request: exim.handle(request)})(), dee_to_g3=DEEToG3BoundaryAdapter(g3), g3_to_core=G3ToCoreBoundaryAdapter(core))
    response = flow.handle(req())
    assert not response.accepted
    assert len(core.seen) == 0
