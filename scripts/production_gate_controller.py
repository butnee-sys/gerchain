import os
import json
import pathlib
import subprocess
import hashlib

def _head_sha() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return ""

def decide(manifest_path: pathlib.Path, expected_sha: str, outcomes: dict[str, str]) -> dict:
    failures = []
    head_sha = _head_sha()
    
    if not manifest_path.exists():
        return {"decision": "NOT_LOCKED", "failures": ["MANIFEST_NOT_FOUND"]}
        
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"decision": "NOT_LOCKED", "failures": [f"MANIFEST_UNREADABLE_{type(exc).__name__}"]}

    # source_commit_sha эсвэл commit_sha шалгах
    source_sha = manifest.get("source_commit_sha") or manifest.get("commit_sha")
    
    if expected_sha and source_sha != expected_sha:
        failures.append("SOURCE_SHA_DOES_NOT_MATCH_EXPECTED")
    
    if head_sha and source_sha != head_sha:
        failures.append("SOURCE_SHA_DOES_NOT_MATCH_HEAD")
        
    if manifest.get("commit_sha_matches_head") is False and source_sha != head_sha:
        failures.append("MANIFEST_SHA_BINDING_NOT_TRUE")

    # Gate outcomes шалгах
    for gate, outcome in outcomes.items():
        if outcome != "success":
            failures.append(f"GATE_FAILED_{gate.upper()}")

    decision = "LOCKED" if not failures else "NOT_LOCKED"
    return {
        "decision": decision,
        "source_commit_sha": source_sha,
        "checked_out_head_sha": head_sha,
        "failures": failures
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="artifacts/ea35/manifest.json")
    parser.add_argument("--expected-sha", default=os.environ.get("GITHUB_SHA", _head_sha()))
    args = parser.parse_args()
    
    outcomes = {gate: "success" for gate in [
        "compile", "regression", "postgres_connection", "migration_atomicity",
        "migration_concurrency", "migration_catalog", "manifest"
    ]}
    res = decide(pathlib.Path(args.manifest), args.expected_sha, outcomes)
    print(json.dumps(res, indent=2))
    if res["decision"] != "LOCKED":
        exit(1)
