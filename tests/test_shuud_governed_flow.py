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
        return BoundaryResponse(
            accepted=self.accepted,
            activity=request.activity,
            correlation_id=request.correlation_id,
            data={self.name: "passed"},
            reason=None if self.accepted else f"{self.name} denied",
        )


def req():
    return BoundaryRequest(
        actor_type=ActorType.COMPANY,
        actor_id="insurer-1",
        activity="shuud-rapid-release",
        payload={"incident_id": "INC-1", "evidence_verified": True},
        credential="cred",
        correlation_id="corr-1",
    )


def test_shuud_governed_flow_crosses_adapters_in_order():
    exim = Stub("exim")
    g3 = Stub("g3")
    core = Stub("core")
    flow = SHUUDGovernedFlow(
        i2b_exim=type("I2BEXIM", (), {"handle": lambda self, request: exim.handle(request)})(),
        dee_to_g3=DEEToG3BoundaryAdapter(g3),
        g3_to_core=G3ToCoreBoundaryAdapter(core),
    )
    response = flow.handle(req())
    assert response.accepted
    assert len(exim.seen) == 1
    assert len(g3.seen) == 1
    assert len(core.seen) == 1
    assert g3.seen[0].payload["exim"] == "passed"
    assert core.seen[0].payload["g3"] == "passed"


def test_shuud_governed_flow_stops_before_core_when_g3_denies():
    exim = Stub("exim")
    g3 = Stub("g3", accepted=False)
    core = Stub("core")
    flow = SHUUDGovernedFlow(
        i2b_exim=type("I2BEXIM", (), {"handle": lambda self, request: exim.handle(request)})(),
        dee_to_g3=DEEToG3BoundaryAdapter(g3),
        g3_to_core=G3ToCoreBoundaryAdapter(core),
    )
    response = flow.handle(req())
    assert not response.accepted
    assert len(core.seen) == 0
