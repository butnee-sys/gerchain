from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from typing import Any

# A lock is permitted only when every required production gate has explicit
# successful evidence. Missing gates are failures, never implicit successes.
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
    """Return the checked-out commit, or the CI-provided SHA if git is unavailable."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        sha = res.stdout.strip()
        if sha:
            return sha
    except (OSError, subprocess.SubprocessError):
        pass
    return os.environ.get("GITHUB_SHA", "").strip()


def _failure_once(failures: list[str], value: str) -> None:
    if value not in failures:
        failures.append(value)


def _write_report(output: pathlib.Path, report: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def decide(
    manifest_path: pathlib.Path, expected_sha: str, outcomes: dict[str, str]
) -> dict[str, Any]:
    failures: list[str] = []
    head_sha = _head_sha()
    expected_sha = expected_sha.strip()

    if not expected_sha:
        _failure_once(failures, "EXPECTED_SHA_MISSING")
    if not head_sha:
        _failure_once(failures, "CHECKED_OUT_HEAD_SHA_MISSING")
    elif expected_sha and head_sha != expected_sha:
        _failure_once(failures, "CHECKED_OUT_HEAD_SHA_MISMATCH")

    if not manifest_path.is_file():
        return {
            "decision": "NOT_LOCKED",
            "source_commit_sha": None,
            "expected_sha": expected_sha or None,
            "checked_out_head_sha": head_sha or None,
            "failures": failures + ["MANIFEST_NOT_FOUND"],
        }

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {
            "decision": "NOT_LOCKED",
            "source_commit_sha": None,
            "expected_sha": expected_sha or None,
            "checked_out_head_sha": head_sha or None,
            "failures": failures + [f"MANIFEST_UNREADABLE_{type(exc).__name__}"],
        }

    if not isinstance(manifest, dict):
        _failure_once(failures, "MANIFEST_INVALID_SHAPE")
        manifest = {}

    source_sha = manifest.get("source_commit_sha") or manifest.get("commit_sha")
    if not isinstance(source_sha, str) or not source_sha.strip():
        _failure_once(failures, "MANIFEST_SOURCE_SHA_MISSING")
    else:
        source_sha = source_sha.strip()
        if expected_sha and source_sha != expected_sha:
            _failure_once(failures, "MANIFEST_SHA_MISMATCH")
        if head_sha and source_sha != head_sha:
            _failure_once(failures, "MANIFEST_HEAD_SHA_MISMATCH")

    manifest_head = manifest.get("checked_out_head_sha")
    if not isinstance(manifest_head, str) or not manifest_head.strip():
        _failure_once(failures, "MANIFEST_CHECKED_OUT_HEAD_SHA_MISSING")
    elif expected_sha and manifest_head.strip() != expected_sha:
        _failure_once(failures, "MANIFEST_CHECKED_OUT_HEAD_SHA_MISMATCH")

    if manifest.get("commit_sha_matches_head") is not True:
        _failure_once(failures, "MANIFEST_COMMIT_HEAD_MATCH_NOT_CONFIRMED")

    # Require migration history and schema evidence. An empty/missing inventory
    # cannot be treated as proof that a database is current.
    migrations = manifest.get("canonical_migrations")
    rows = manifest.get("schema_version_rows")
    count = manifest.get("canonical_migration_count")
    if not isinstance(migrations, list) or not migrations:
        _failure_once(failures, "MIGRATION_INVENTORY_MISSING")
        migrations = []
    if not isinstance(rows, list) or not rows:
        _failure_once(failures, "MIGRATION_HISTORY_MISSING")
        rows = []
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        _failure_once(failures, "MIGRATION_COUNT_INVALID")
    elif count != len(migrations) or count != len(rows):
        _failure_once(failures, "MIGRATION_COUNT_MISMATCH")

    migration_by_version: dict[int, dict[str, Any]] = {}
    for migration in migrations:
        if not isinstance(migration, dict):
            _failure_once(failures, "MIGRATION_INVENTORY_ROW_INVALID")
            continue
        version = migration.get("version")
        checksum = migration.get("runner_checksum")
        if not isinstance(version, int) or isinstance(version, bool):
            _failure_once(failures, "MIGRATION_VERSION_INVALID")
            continue
        if version in migration_by_version:
            _failure_once(failures, f"MIGRATION_DUPLICATE_VERSION_{version}")
        if not isinstance(checksum, str) or not checksum.strip():
            _failure_once(failures, f"MIGRATION_CHECKSUM_MISSING_VERSION_{version}")
        migration_by_version[version] = migration

    row_versions: set[int] = set()
    for row in rows:
        if not isinstance(row, dict):
            _failure_once(failures, "MIGRATION_HISTORY_ROW_INVALID")
            continue
        version = row.get("version")
        checksum = row.get("checksum")
        if not isinstance(version, int) or isinstance(version, bool):
            _failure_once(failures, "MIGRATION_HISTORY_VERSION_INVALID")
            continue
        if version in row_versions:
            _failure_once(failures, f"MIGRATION_HISTORY_DUPLICATE_VERSION_{version}")
        row_versions.add(version)
        migration = migration_by_version.get(version)
        if migration is None:
            _failure_once(failures, f"MIGRATION_HISTORY_VERSION_UNEXPECTED_{version}")
            continue
        runner_checksum = migration.get("runner_checksum")
        if not isinstance(checksum, str) or checksum != runner_checksum:
            _failure_once(failures, f"MIGRATION_CHECKSUM_MISMATCH_VERSION_{version}")

    if set(migration_by_version) != row_versions:
        _failure_once(failures, "MIGRATION_HISTORY_INVENTORY_VERSION_MISMATCH")

    if manifest.get("database_manifest_error") is not None:
        _failure_once(failures, "DATABASE_MANIFEST_ERROR")

    if not isinstance(outcomes, dict):
        outcomes = {}
        _failure_once(failures, "GATE_OUTCOMES_INVALID_SHAPE")

    for gate in REQUIRED_GATES:
        if gate not in outcomes:
            _failure_once(failures, f"GATE_{gate.upper()}_MISSING")
        elif outcomes[gate] != "success":
            _failure_once(failures, f"GATE_{gate.upper()}_{str(outcomes[gate]).upper()}")

    for gate in outcomes:
        if gate not in REQUIRED_GATES:
            _failure_once(failures, f"GATE_UNKNOWN_{str(gate).upper()}")

    return {
        "decision": "LOCKED" if not failures else "NOT_LOCKED",
        "source_commit_sha": source_sha if isinstance(source_sha, str) else None,
        "expected_sha": expected_sha or None,
        "checked_out_head_sha": head_sha or None,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed production gate controller")
    parser.add_argument("--manifest", default="artifacts/ea35/manifest.json")
    parser.add_argument("--expected-sha", default=_head_sha())
    parser.add_argument("--output", default="artifacts/ea35/production-gate-decision.json")
    parser.add_argument(
        "--outcomes-json",
        default="",
        help="JSON object containing explicit outcomes for every required gate",
    )
    args = parser.parse_args()
    output_path = pathlib.Path(args.output)

    if not args.outcomes_json:
        outcomes: dict[str, str] = {}
    else:
        try:
            outcomes = json.loads(args.outcomes_json)
        except json.JSONDecodeError as exc:
            # Overwrite any stale LOCKED report so malformed input cannot leave
            # a previous success artifact available to downstream consumers.
            report = {
                "decision": "NOT_LOCKED",
                "source_commit_sha": None,
                "expected_sha": args.expected_sha or None,
                "checked_out_head_sha": _head_sha() or None,
                "failures": ["OUTCOMES_JSON_INVALID"],
            }
            _write_report(output_path, report)
            print(f"Invalid --outcomes-json: {exc}", file=sys.stderr)
            print(json.dumps(report, indent=2))
            return 1
        if not isinstance(outcomes, dict):
            report = {
                "decision": "NOT_LOCKED",
                "source_commit_sha": None,
                "expected_sha": args.expected_sha or None,
                "checked_out_head_sha": _head_sha() or None,
                "failures": ["OUTCOMES_JSON_INVALID_SHAPE"],
            }
            _write_report(output_path, report)
            print("--outcomes-json must decode to a JSON object", file=sys.stderr)
            print(json.dumps(report, indent=2))
            return 1

    report = decide(pathlib.Path(args.manifest), args.expected_sha, outcomes)
    _write_report(output_path, report)
    print(json.dumps(report, indent=2))
    return 0 if report["decision"] == "LOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
