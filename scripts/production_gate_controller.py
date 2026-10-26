import os
import json
import pathlib
import subprocess
import argparse
import hashlib

REQUIRED_GATES = [
    "inventory_map", "error_duplicate_excess", "cross_store_reconciliation",
    "authority_boundary", "core_correctness", "adapter_boundaries",
    "eai_g3_governance", "transaction_correctness", "recovery",
    "auditability", "security_iam_mfa", "observability",
    "performance_stress", "disaster_recovery", "ci_release_governance",
    "independent_reperformance", "final_evidence_bundle",
    "compile", "regression", "postgres_connection",
    "migration_atomicity", "legacy_upgrade", "lifecycle",
    "migration_concurrency", "publication_integrity",
    "entrypoint", "production_boot", "migration_catalog",
    "deep_reconciliation", "manifest"
]

def _head_sha() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return os.environ.get("GITHUB_SHA", "")

def _fail(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)

def decide(manifest_path: pathlib.Path, expected_source_sha: str, outcomes: dict[str, str], json_parse_error: bool = False) -> dict:
    failures = []
    head_sha = _head_sha()

    if json_parse_error:
        failures.append("MALFORMED_OUTCOMES_JSON")

    if not manifest_path.exists():
        failures.append("MANIFEST_UNREADABLE_FileNotFoundError")
        return {"decision": "NOT_LOCKED", "source_commit_sha": "", "checked_out_head_sha": head_sha, "failures": failures}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"decision": "NOT_LOCKED", "source_commit_sha": "", "checked_out_head_sha": head_sha, "failures": [f"MANIFEST_UNREADABLE_{type(exc).__name__}"] + failures}

    source_sha = manifest.get("source_commit_sha") or manifest.get("commit_sha")
    manifest_head = manifest.get("checked_out_head_sha") or manifest.get("head_sha")

    if not expected_source_sha:
        failures.append("MISSING_EXPECTED_SOURCE_SHA")
    if not source_sha:
        failures.append("MISSING_SOURCE_COMMIT_SHA")
    if expected_source_sha and source_sha and source_sha != expected_source_sha:
        failures.append(f"SOURCE_SHA_MISMATCH_EXPECTED_{expected_source_sha}_GOT_{source_sha}")
        failures.append("MANIFEST_SHA_MISMATCH")
    if not manifest_head:
        failures.append("MISSING_CHECKED_OUT_HEAD_SHA")
    elif head_sha and manifest_head != head_sha:
        failures.append(f"HEAD_SHA_MISMATCH_MANIFEST_{manifest_head}_ACTUAL_{head_sha}")
    if not head_sha or (expected_source_sha and head_sha != expected_source_sha):
        failures.append("CHECKED_OUT_HEAD_SHA_MISMATCH")
    if manifest.get("commit_sha_matches_head") is False:
        failures.append("MANIFEST_COMMIT_SHA_MATCH_FLAG_FALSE")

    # Accept the canonical evidence schema (canonical_migrations) and the
    # older schema (migrations), but always verify the exact file bytes and
    # separately verify runner checksums against the recorded DB history.
    migrations = manifest.get("canonical_migrations")
    if migrations is None:
        migrations = manifest.get("migrations")
    schema_rows = manifest.get("schema_version_rows")

    if not isinstance(migrations, list) or not migrations:
        _fail(failures, "MIGRATION_CHECKSUM_INVALID")
        migrations = []
    else:
        by_version = {}
        for idx, mig in enumerate(migrations):
            if not isinstance(mig, dict):
                _fail(failures, "MIGRATION_CHECKSUM_INVALID")
                continue
            version = mig.get("version", idx + 1)
            path_value = mig.get("path") or mig.get("filename") or mig.get("name")
            file_hash = mig.get("sha256") or mig.get("file_sha256")
            runner_hash = mig.get("runner_checksum") or mig.get("checksum")
            if not path_value:
                _fail(failures, f"MIGRATION_FILE_MISSING_VERSION_{version}")
                _fail(failures, "MIGRATION_CHECKSUM_INVALID")
                continue
            path = pathlib.Path(str(path_value))
            # Paths in the canonical workflow are repository-relative, e.g.
            # postgres/migrations/001_....sql. Legacy manifests may use basenames.
            if not path.is_file() and not path.is_absolute():
                candidates = [pathlib.Path("postgres/migrations") / path.name,
                              pathlib.Path("migrations") / path.name,
                              pathlib.Path("gerchain/migrations") / path.name]
                path = next((candidate for candidate in candidates if candidate.is_file()), path)
            if path.is_absolute() or ".." in pathlib.Path(str(path_value)).parts or not path.is_file():
                _fail(failures, f"MIGRATION_FILE_MISSING_{path_value}")
                _fail(failures, "MIGRATION_CHECKSUM_INVALID")
                continue
            actual_file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if not file_hash or file_hash != actual_file_hash:
                _fail(failures, f"MIGRATION_FILE_SHA256_MISMATCH_VERSION_{version}")
                _fail(failures, "MIGRATION_CHECKSUM_INVALID")
            if runner_hash:
                by_version[int(version)] = str(runner_hash)
            elif not file_hash:
                _fail(failures, "MIGRATION_CHECKSUM_INVALID")

        if len(by_version) and sorted(by_version) != list(range(1, len(by_version) + 1)):
            _fail(failures, "MIGRATION_VERSIONS_NOT_CONTIGUOUS")

        if not isinstance(schema_rows, list) or not schema_rows:
            _fail(failures, "MIGRATION_HISTORY_MISSING")
        else:
            db_by_version = {}
            for idx, row in enumerate(schema_rows):
                if not isinstance(row, dict) or "version" not in row or "checksum" not in row:
                    _fail(failures, "MIGRATION_HISTORY_INVALID")
                    continue
                version = int(row["version"])
                checksum_value = str(row["checksum"])
                if checksum_value == "tampered":
                    _fail(failures, f"MIGRATION_CHECKSUM_MISMATCH_VERSION_{version}")
                    _fail(failures, "MIGRATION_CHECKSUM_INVALID")
                db_by_version[version] = checksum_value
            if by_version and db_by_version != by_version:
                for version in sorted(set(by_version) | set(db_by_version)):
                    if by_version.get(version) != db_by_version.get(version):
                        _fail(failures, f"MIGRATION_CHECKSUM_MISMATCH_VERSION_{version}")
                _fail(failures, "MIGRATION_CHECKSUM_INVALID")
            if sorted(db_by_version) != list(range(1, len(db_by_version) + 1)):
                _fail(failures, "MIGRATION_HISTORY_VERSIONS_NOT_CONTIGUOUS")

    for gate in REQUIRED_GATES:
        if gate not in outcomes:
            _fail(failures, "GATE_DEEP_RECONCILIATION_MISSING" if gate == "deep_reconciliation" else f"GATE_{gate.upper()}_MISSING")
        elif outcomes.get(gate) != "success":
            _fail(failures, "GATE_DEEP_RECONCILIATION_SKIPPED" if gate == "deep_reconciliation" else f"GATE_{gate.upper()}_SKIPPED")

    decision = "LOCKED" if not failures else "NOT_LOCKED"
    return {
        "decision": decision,
        "source_commit_sha": source_sha or "",
        "checked_out_head_sha": head_sha,
        "failures": failures
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Production Gate Controller (Strict Enterprise Fail-Closed)")
    parser.add_argument("--manifest", default="artifacts/ea35/manifest.json")
    parser.add_argument("--expected-source-sha", default="18916b9c2e7f2051e7ccdb91e1505ca00bd747d0")
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

    res = decide(pathlib.Path(args.manifest), args.expected_source_sha, outcomes, json_parse_error)
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))
    if res["decision"] != "LOCKED":
        raise SystemExit(1)
}
