import os
import json
import pathlib
import subprocess
import argparse

def _head_sha() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return os.environ.get("GITHUB_SHA", "")

def decide(manifest_path: pathlib.Path, expected_sha: str, outcomes: dict[str, str], json_parse_error: bool = False) -> dict:
    failures = []
    head_sha = _head_sha()

    # 1. Malformed JSON failure (Fail-Closed)
    if json_parse_error:
        failures.append("MALFORMED_OUTCOMES_JSON")

    if not manifest_path.exists():
        return {"decision": "NOT_LOCKED", "failures": ["MANIFEST_NOT_FOUND"] + failures}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"decision": "NOT_LOCKED", "failures": [f"MANIFEST_UNREADABLE_{type(exc).__name__}"] + failures}

    source_sha = manifest.get("source_commit_sha") or manifest.get("commit_sha")

    # 2. Strict SHA check (Fail-Closed)
    if not expected_sha:
        failures.append("MISSING_EXPECTED_SHA")
    if not source_sha:
        failures.append("MISSING_SOURCE_COMMIT_SHA")
    if expected_sha and source_sha and source_sha != expected_sha:
        failures.append(f"SOURCE_SHA_MISMATCH_EXPECTED_{expected_sha}_GOT_{source_sha}")

    # 3. Mandatory gates strict verification (No default success)
    required_gates = [
        "inventory_map", "core_correctness", "transaction_correctness",
        "migration_atomicity", "migration_concurrency", "migration_catalog", "manifest"
    ]

    for gate in required_gates:
        outcome = outcomes.get(gate)
        if outcome != "success":
            failures.append(f"GATE_NOT_SUCCESS_{gate.upper()}")

    decision = "LOCKED" if not failures else "NOT_LOCKED"
    return {
        "decision": decision,
        "source_commit_sha": source_sha or "",
        "checked_out_head_sha": head_sha,
        "failures": failures
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Production Gate Controller (Strict Fail-Closed)")
    parser.add_argument("--manifest", default="artifacts/ea35/manifest.json")
    parser.add_argument("--expected-sha", default=_head_sha())
    parser.add_argument("--output", default="artifacts/ea35/production-gate-decision.json")
    parser.add_argument("--outcomes-json", default="{}")
    args = parser.parse_args()

    outcomes = {}
    json_parse_error = False

    if args.outcomes_json:
        try:
            parsed = json.loads(args.outcomes_json)
            if isinstance(parsed, dict):
                outcomes = parsed
            else:
                json_parse_error = True
        except Exception:
            json_parse_error = True

    res = decide(pathlib.Path(args.manifest), args.expected_sha, outcomes, json_parse_error)

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(res, indent=2), encoding="utf-8")

    print(json.dumps(res, indent=2))
    if res["decision"] != "LOCKED":
        exit(1)
