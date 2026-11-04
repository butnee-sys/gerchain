from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

ARCHITECTURE_GATES = [
    "inventory_map", "error_duplicate_excess", "cross_store_reconciliation",
    "authority_boundary", "core_correctness", "adapter_boundaries",
    "eai_g3_governance", "transaction_correctness", "recovery",
    "auditability", "security_iam_mfa", "observability",
    "performance_stress", "disaster_recovery", "ci_release_governance",
    "independent_reperformance", "final_evidence_bundle",
]

POSTGRES_GATES = [
    "compile", "regression", "postgres_connection", "migration_atomicity",
    "legacy_upgrade", "lifecycle", "migration_concurrency",
    "publication_integrity", "entrypoint", "production_boot",
    "migration_catalog", "deep_reconciliation", "manifest",
]

REQUIRED_GATES = ARCHITECTURE_GATES + POSTGRES_GATES



def resolve_artifact_evidence(artifact_root: pathlib.Path, evidence: object) -> pathlib.Path | None:
    """Resolve only an existing local evidence file confined to the artifact root.

    Remote URLs and URNs are deliberately rejected: a candidate-SHA substring
    is not proof that remote evidence content was fetched or authenticated.
    """
    if not isinstance(evidence, str) or not evidence.strip():
        return None
    relative = pathlib.Path(evidence)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    try:
        root = artifact_root.resolve(strict=True)
        candidate = (root / relative).resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if not candidate.is_relative_to(root) or not candidate.is_file():
        return None
    return candidate


def _head_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        return os.environ.get("GITHUB_SHA", "")


def _migration_failures(manifest: dict, repo_root: pathlib.Path) -> list[str]:
    """Verify the generated PostgreSQL migration evidence against checked-out files and DB rows."""
    failures: list[str] = []
    try:
        # When invoked as `python scripts/production_gate_controller.py`, Python
        # places scripts/ (not the repository root) at sys.path[0].
        root_string = str(repo_root.resolve())
        if root_string not in sys.path:
            sys.path.insert(0, root_string)
        from postgres.migrations import _canonical_migration_files
        canonical_paths = _canonical_migration_files(repo_root / "postgres" / "migrations")
    except Exception as exc:
        return [f"CANONICAL_MIGRATION_INVENTORY_UNREADABLE_{type(exc).__name__}"]

    expected_versions = list(range(1, len(canonical_paths) + 1))
    records = manifest.get("canonical_migrations")
    rows = manifest.get("schema_version_rows")
    count = manifest.get("canonical_migration_count")

    if not isinstance(records, list) or not records:
        return ["CANONICAL_MIGRATION_EVIDENCE_MISSING"]
    if count != len(canonical_paths) or len(records) != len(canonical_paths):
        failures.append("CANONICAL_MIGRATION_COUNT_MISMATCH")

    record_versions = [item.get("version") if isinstance(item, dict) else None for item in records]
    if record_versions != expected_versions:
        failures.append("CANONICAL_MIGRATION_VERSIONS_NOT_CONTIGUOUS")

    for version, expected_path in zip(expected_versions, canonical_paths):
        item = next((x for x in records if isinstance(x, dict) and x.get("version") == version), None)
        if item is None:
            failures.append(f"MIGRATION_EVIDENCE_MISSING_VERSION_{version}")
            continue

        relative_path = expected_path.relative_to(repo_root).as_posix()
        if item.get("path") != relative_path:
            failures.append(f"MIGRATION_PATH_MISMATCH_VERSION_{version}")
        raw = expected_path.read_bytes()
        source_text = expected_path.read_text(encoding="utf-8")
        disk_sha256 = hashlib.sha256(raw).hexdigest()
        runner_checksum = hashlib.sha256(source_text.encode("utf-8")).hexdigest()

        if item.get("sha256") != disk_sha256:
            failures.append(f"MIGRATION_FILE_SHA256_MISMATCH_VERSION_{version}")
        if item.get("runner_checksum") != runner_checksum:
            failures.append(f"MIGRATION_RUNNER_CHECKSUM_MISMATCH_VERSION_{version}")

    if not isinstance(rows, list) or not rows:
        failures.append("SCHEMA_VERSION_ROWS_MISSING")
        return failures

    row_versions = [row.get("version") if isinstance(row, dict) else None for row in rows]
    if row_versions != expected_versions:
        failures.append("SCHEMA_VERSION_ROWS_NOT_CONTIGUOUS")

    rows_by_version = {
        row.get("version"): row for row in rows if isinstance(row, dict)
    }
    records_by_version = {
        item.get("version"): item for item in records if isinstance(item, dict)
    }
    for version in expected_versions:
        row = rows_by_version.get(version)
        item = records_by_version.get(version)
        if row is None or item is None:
            continue
        if not row.get("applied_at"):
            failures.append(f"MIGRATION_APPLIED_AT_MISSING_VERSION_{version}")
        expected_checksum = item.get("runner_checksum")
        if row.get("checksum") != expected_checksum:
            failures.append(f"MIGRATION_DATABASE_CHECKSUM_MISMATCH_VERSION_{version}")
        if item.get("database_checksum") != row.get("checksum"):
            failures.append(f"MIGRATION_MANIFEST_DATABASE_CHECKSUM_MISMATCH_VERSION_{version}")
        if item.get("database_checksum_matches_runner") is not True:
            failures.append(f"MIGRATION_DATABASE_CHECKSUM_FLAG_NOT_TRUE_VERSION_{version}")

    if manifest.get("database_manifest_error"):
        failures.append("DATABASE_MIGRATION_MANIFEST_ERROR")
    return failures


def decide(
    manifest_path: pathlib.Path,
    expected_source_sha: str,
    outcomes: dict[str, str],
    json_parse_error: bool = False,
) -> dict:
    failures: list[str] = []
    head_sha = _head_sha()
    repo_root = pathlib.Path.cwd()

    if json_parse_error:
        failures.append("MALFORMED_OUTCOMES_JSON")

    if not manifest_path.exists():
        failures.append("MANIFEST_UNREADABLE_FileNotFoundError")
        return {
            "decision": "NOT_LOCKED",
            "source_commit_sha": "",
            "checked_out_head_sha": head_sha,
            "failures": failures,
        }

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "decision": "NOT_LOCKED",
            "source_commit_sha": "",
            "checked_out_head_sha": head_sha,
            "failures": [f"MANIFEST_UNREADABLE_{type(exc).__name__}"] + failures,
        }

    source_sha = manifest.get("commit_sha") or manifest.get("source_commit_sha")
    manifest_head = manifest.get("checked_out_head_sha") or manifest.get("head_sha")

    if not expected_source_sha:
        failures.append("MISSING_EXPECTED_SOURCE_SHA")
    if not source_sha:
        failures.append("MISSING_SOURCE_COMMIT_SHA")
    if expected_source_sha and source_sha and source_sha != expected_source_sha:
        failures.append(f"SOURCE_SHA_MISMATCH_EXPECTED_{expected_source_sha}_GOT_{source_sha}")
        failures.append("MANIFEST_SHA_MISMATCH")
    if not head_sha or head_sha != expected_source_sha:
        failures.append("CHECKED_OUT_HEAD_SHA_MISMATCH")
    if manifest_head != head_sha:
        failures.append("MANIFEST_HEAD_SHA_MISMATCH")
    if manifest.get("commit_sha_matches_head") is not True:
        failures.append("MANIFEST_COMMIT_SHA_MATCH_FLAG_NOT_TRUE")

    failures.extend(_migration_failures(manifest, repo_root))

    for gate in REQUIRED_GATES:
        if gate not in outcomes:
            failures.append(f"GATE_{gate.upper()}_MISSING")
        elif outcomes.get(gate) != "success":
            failures.append(f"GATE_{gate.upper()}_NOT_SUCCESS")

    decision = "LOCKED" if not failures else "NOT_LOCKED"
    return {
        "decision": decision,
        "source_commit_sha": source_sha or "",
        "checked_out_head_sha": head_sha,
        "required_gate_count": len(REQUIRED_GATES),
        "passed_gate_count": sum(outcomes.get(gate) == "success" for gate in REQUIRED_GATES),
        "failures": failures,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Production Gate Controller (strict enterprise fail-closed)"
    )
    parser.add_argument("--manifest", default="artifacts/ea35-current/manifest.json")
    parser.add_argument(
        "--expected-sha",
        "--expected-source-sha",
        dest="expected_source_sha",
        default=os.environ.get("GITHUB_SHA", ""),
    )
    parser.add_argument("--output", default="artifacts/ea35-current/production-gate-decision.json")
    parser.add_argument("--outcomes-json", default="{}")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    outcomes: dict[str, str] = {}
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

    result = decide(
        pathlib.Path(args.manifest),
        args.expected_source_sha,
        outcomes,
        json_parse_error,
    )
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["decision"] != "LOCKED":
        raise SystemExit(1)
