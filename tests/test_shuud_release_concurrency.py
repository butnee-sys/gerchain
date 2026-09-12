"""Adversarial concurrency tests for SHUUD escrow release."""

from concurrent.futures import ThreadPoolExecutor

from escrow.engine import EscrowEngine
from shuud.release import ReleaseAuthorization, release_escrow
from witness.chain import WitnessChain


def _locked_escrow():
    chain = WitnessChain(
        initial_state={"value": 0},
        manifest={"domain": "SHUUD", "incident_id": "INC-CONCURRENCY"},
        witness_id="WITNESS-ROOT-001",
    )
    escrow = EscrowEngine(
        escrow_id="ESC-CONCURRENCY",
        amount=1_500_000,
        currency="NEF",
        witness_chain=chain,
    )
    escrow.transition("FUNDED", "2026-09-12T00:00:01+00:00", {"source": "test"})
    escrow.transition("LOCKED", "2026-09-12T00:00:02+00:00", {"source": "test"})
    authorization = ReleaseAuthorization(
        incident_id="INC-CONCURRENCY",
        escrow_id="ESC-CONCURRENCY",
        rule_version="SHUUD-POLICY-1",
        authorization_hash="AUTH-CONCURRENCY",
        damage_estimate_nef=1_500_000,
    )
    return escrow, authorization


def test_concurrent_release_allows_exactly_one_transition():
    escrow, authorization = _locked_escrow()

    def attempt():
        try:
            record = release_escrow(
                escrow,
                authorization,
                timestamp="2026-09-12T00:00:03+00:00",
            )
            return ("success", record.new_state)
        except ValueError as exc:
            return ("rejected", str(exc))

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: attempt(), range(8)))

    successes = [result for result in results if result[0] == "success"]
    rejected = [result for result in results if result[0] == "rejected"]

    assert len(successes) == 1
    assert successes[0][1] == "RELEASED"
    assert len(rejected) == 7
    assert all("requires LOCKED escrow" in result[1] for result in rejected)
    assert escrow.get_state()["state"] == "RELEASED"
