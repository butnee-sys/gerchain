"""Fail-closed decision controller for the canonical production evidence gate.

This controller does not run infrastructure tests itself. It consumes the exact
workflow step outcomes and the PostgreSQL evidence manifest produced by the
master workflow, binds them to the checked-out commit, and emits one decision.
Missing evidence, unknown outcomes, stale SHAs, or any failed gate => NOT_LOCKED.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_GATES = (
    "compile",
    "regression",
    "postgres_connection",
    "migration_atomicity",
    "legacy_upgrade",
    "lifecycle",
    "migration_concurrency",
    "publication_integrity",
    "entrypoint",
    "production_boot",
    "migration_catalog",
    "deep_reconciliation",
    "manifest",
)


def _head_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.STDOUT
    ).strip()


def decide(manifest_path: Path, expected_sha: str, outcomes: dict[str, str]) -> dict:
    failures: list[str] = []
    head_sha = _head_sha()
    if not expected_sha or expected_sha != head_sha:
        failures.append("EXPECTED_SHA_DOES_NOT_MATCH_CHECKED_OUT_HEAD")

    for gate in REQUIRED_GATES:
        outcome = outcomes.get(gate)
        if outcome != "success":
            failures.append(f"GATE_{gate.upper()}_{(outcome or 'MISSING').upper()}")

    manifest = None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"MANIFEST_UNREADABLE_{type(exc).__name__}")

    if manifest is not None:
        if manifest.get("commit_sha") != expected_sha:
            failures.append("MANIFEST_SHA_MISMATCH")
        if manifest.get("checked_out_head_sha") != head_sha:
            failures.append("MANIFEST_HEAD_MISMATCH")
        if manifest.get("commit_sha_matches_head") is not True:
            failures.append("MANIFEST_SHA_BINDING_NOT_TRUE")
        migrations = manifest.get("canonical_migrations")
        rows = manifest.get("schema_version_rows")
        if manifest.get("canonical_migration_count") != 17 or not isinstance(migrations, list) or len(migrations) != 17:
            failures.append("CANONICAL_MIGRATION_CHAIN_NOT_EXACTLY_17")
        if not isinstance(rows, list) or [r.get("version") for r in rows] != list(range(1, 18)):
            failures.append("DATABASE_SCHEMA_VERSION_ROWS_NOT_EXACTLY_1_TO_17")
        if isinstance(migrations, list) and isinstance(rows, list) and len(migrations) == len(rows) == 17:
            row_checksums = {r.get("version"): r.get("checksum") for r in rows}
            for item in migrations:
                version = item.get("version")
                if item.get("runner_checksum") != row_checksums.get(version):
                    failures.append(f"MIGRATION_CHECKSUM_MISMATCH_VERSION_{version}")
        if manifest.get("database_manifest_error"):
            failures.append("DATABASE_MANIFEST_ERROR_PRESENT")

    return {
        "decision": "LOCKED" if not failures else "NOT_LOCKED",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": os.environ.get("GITHUB_REPOSITORY", "local"),
        "expected_commit_sha": expected_sha,
        "checked_out_head_sha": head_sha,
        "commit_sha_matches_head": expected_sha == head_sha,
        "required_gates": list(REQUIRED_GATES),
        "gate_outcomes": outcomes,
        "manifest_path": str(manifest_path),
        "failures": failures,
        "meaning": (
            "All required technical gates and exact-SHA PostgreSQL evidence passed."
            if not failures else
            "At least one required gate or evidence condition is missing, failed, or mismatched."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="artifacts/ea35/manifest.json")
    parser.add_argument("--output", default="artifacts/ea35/production-gate-decision.json")
    parser.add_argument("--expected-sha", default=os.environ.get("GITHUB_SHA", ""))
    parser.add_argument(
        "--outcomes-json",
        default=os.environ.get("PRODUCTION_GATE_OUTCOMES_JSON", "{}"),
        help="JSON object mapping each required gate key to a GitHub Actions outcome",
    )
    args = parser.parse_args()
    try:
        outcomes = json.loads(args.outcomes_json)
        if not isinstance(outcomes, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in outcomes.items()):
            raise ValueError("outcomes must be a JSON object of string keys and values")
        report = decide(Path(args.manifest), args.expected_sha, outcomes)
    except Exception as exc:
        report = {
            "decision": "NOT_LOCKED",
            "expected_commit_sha": args.expected_sha,
            "failures": [f"CONTROLLER_ERROR_{type(exc).__name__}: {exc}"],
        }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("decision") == "LOCKED" else 1


if __name__ == "__main__":
    sys.exit(main())
