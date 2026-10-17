from __future__ import annotations

from tests.w2_evidence import build_w2_evidence


def test_w2_evidence_is_content_addressed_and_reproducible_shape(monkeypatch):
    monkeypatch.setenv("GITHUB_RUN_ID", "123456")
    kwargs = {
        "test_id": "C2-shared-liquidity",
        "commit": "934cb570db6740c65857b70aec7ae8a3d42fd610",
        "schema": "release-v1",
        "config": {"postgres": "16", "lease_seconds": 300},
        "seed": 20260916,
        "input_state": {"capacity": 2_000_000, "requests": [1_500_000, 1_500_000]},
        "initial_state": {"committed": 0},
        "observed_state": {"successful_requests": 1},
        "final_state": {"committed": 1_500_000, "over_allocated": False},
        "oracle_version": "w2-oracle-v1",
        "result": "PASS",
    }
    first = build_w2_evidence(**kwargs)
    second = build_w2_evidence(**kwargs)

    assert first["EvidenceID"] == second["EvidenceID"]
    assert first["Hash"] != ""
    assert len(first["Hash"]) == 64
    assert first["Commit"] == kwargs["commit"]
    assert first["RunID"] == "123456"
    assert first["GateID"] == "W2"
