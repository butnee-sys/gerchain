"""Fail-closed decision controller for the canonical production evidence gate.

Consumes exact workflow outcomes and the PostgreSQL evidence manifest, binds them
to the checked-out commit, and independently rechecks all canonical migration file
hashes and runner checksums. Missing or stale evidence => NOT_LOCKED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from postgres.migrations import _canonical_migration_files, checksum

REQUIRED_GATES = (
    "inventory_map",
    "error_duplicate_excess",
    "cross_store_reconciliation",
    "authority_boundary",
    "core_correctness",
    "adapter_boundaries",
    "eai_g3_governance",
    "transaction_correctness",
    "recovery",
    "auditability",
    "security_iam_mfa",
    "observability",
    "performance_stress",
    "disaster_recovery",
    "ci_release_governance",
    "independent_reperformance",
    "final_evidence_bundle",
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


def _verify_migrations(migrations: object, rows: object, failures: list[str]) -> None:
    if not isinstance(migrations, list) or len(migrations) != 17:
        failures.append("CANONICAL_MIGRATION_CHAIN_NOT_EXACTLY_17")
        return
    if not isinstance(rows, list) or [r.get("version") for r in rows if isinstance(r, dict)] != list(range(1, 18)):
        failures.append("DATABASE_SCHEMA_VERSION_ROWS_NOT_EXACTLY_1_TO_17")
        return

    try:
        actual_files = _canonical_migration_files(Path("postgres/migrations"))
    except Exception as exc:
        failures.append(f"CANONICAL_MIGRATION_FILES_UNREADABLE_{type(exc).__name__}")
        return

    if len(actual_files) != 17:
        failures.append("CHECKED_OUT_MIGRATION_CHAIN_NOT_EXACTLY_17")
        return

    rows_by_version = {row["version"]: row for row in rows}
    for expected_version, (item, path) in enumerate(zip(migrations, actual_files), start=1):
        if not isinstance(item, dict):
            failures.append(f"MIGRATION_RECORD_INVALID_VERSION_{expected_version}")
            continue
        if int(path.name.split("_", 1)[0]) != expected_version:
            failures.append(f"CHECKED_OUT_MIGRATION_ORDER_MISMATCH_VERSION_{expected_version}")
            continue
        relative_path = path.as_posix()
        if item.get("version") != expected_version or item.get("path") != relative_path:
            failures.append(f"MIGRATION_PATH_OR_VERSION_MISMATCH_VERSION_{expected_version}")
        actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        if item.get("sha256") != actual_sha256:
            failures.append(f"MIGRATION_FILE_SHA256_MISMATCH_VERSION_{expected_version}")
        actual_runner_checksum = checksum(path.read_text(encoding="utf-8"))
        if item.get("runner_checksum") != actual_runner_checksum:
            failures.append(f"MIGRATION_RUNNER_CHECKSUM_MISMATCH_VERSION_{expected_version}")
        row = rows_by_version[expected_version]
        if item.get("runner_checksum") != row.get("checksum"):
            failures.append(f"MIGRATION_CHECKSUM_MISMATCH_VERSION_{expected_version}")
        if item.get("database_checksum") != row.get("checksum"):
            failures.append(f"MIGRATION_DATABASE_CHECKSUM_FIELD_MISMATCH_VERSION_{expected_version}")
        if item.get("database_checksum_matches_runner") is not True:
            failures.append(f"MIGRATION_DATABASE_CHECKSUM_FLAG_NOT_TRUE_VERSION_{expected_version}")
        if row.get("applied_at") is None:
            failures.append(f"MIGRATION_APPLIED_AT_MISSING_VERSION_{expected_version}")


def decide(manifest_path: Path, expected_sha: str, outcomes: dict[str, str]) -> dict:
    failures: list[str] = []
    head_sha = _head_sha()
    if not expected_sha or expected_sha != head_sha:
        failures.append("EXPECTED_SHA_DOES_NOT_MATCH_CHECKED_OUT_HEAD")

    for gate in REQUIRED_GATES:
        outcome = outcomes.get(gate)
        if outcome != "success":
            failures.append(f"GATE_{gate.upper()}_{(outcome or 'MISSING').upper()}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        manifest = None
        failures.append(f"MANIFEST_UNREADABLE_{type(exc).__name__}")

    if manifest is not None:
        if manifest.get("commit_sha") != expected_sha:
            failures.append("MANIFEST_SHA_MISMATCH")
        if manifest.get("checked_out_head_sha") != head_sha:
            failures.append("MANIFEST_HEAD_MISMATCH")
        if manifest.get("commit_sha_matches_head") is not True:
            failures.append("MANIFEST_SHA_BINDING_NOT_TRUE")
        if manifest.get("canonical_migration_count") != 17:
            failures.append("MANIFEST_CANONICAL_MIGRATION_COUNT_INVALID")
        _verify_migrations(
            manifest.get("canonical_migrations"),
            manifest.get("schema_version_rows"),
            failures,
        )
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
