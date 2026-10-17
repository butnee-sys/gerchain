from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any


def build_w2_evidence(
    *,
    test_id: str,
    commit: str,
    schema: str,
    config: dict[str, Any],
    seed: int,
    input_state: dict[str, Any],
    initial_state: dict[str, Any],
    observed_state: dict[str, Any],
    final_state: dict[str, Any],
    oracle_version: str,
    result: str,
) -> dict[str, Any]:
    """Build a content-addressed W2 evidence record.

    The record deliberately takes the test result as an observation. It does not
    calculate the verdict from production output and therefore cannot replace the
    independent oracle or reproduction step.
    """
    run_id = os.getenv("GITHUB_RUN_ID", "LOCAL")
    evidence = {
        "EvidenceID": f"W2:{test_id}:{run_id}:{commit[:12]}",
        "GateID": "W2",
        "TestID": test_id,
        "RunID": run_id,
        "Commit": commit,
        "Schema": schema,
        "Config": config,
        "Seed": seed,
        "Input": input_state,
        "InitialState": initial_state,
        "ObservedState": observed_state,
        "FinalState": final_state,
        "OracleVersion": oracle_version,
        "Result": result,
        "Timestamp": datetime.now(timezone.utc).isoformat(),
    }
    canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    evidence["Hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return evidence


__all__ = ["build_w2_evidence"]
