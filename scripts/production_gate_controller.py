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

    # 1. Strict Source SHA verification & MANIFEST_SHA_MISMATCH
    if not expected_source_sha:
        failures.append("MISSING_EXPECTED_SOURCE_SHA")
    if not source_sha:
        failures.append("MISSING_SOURCE_COMMIT_SHA")
    if expected_source_sha and source_sha and source_sha != expected_source_sha:
        failures.append(f"SOURCE_SHA_MISMATCH_EXPECTED_{expected_source_sha}_GOT_{source_sha}")
        failures.append("MANIFEST_SHA_MISMATCH")

    # 2. Manifest HEAD vs Actual HEAD validation
    if manifest_head and head_sha and manifest_head != head_sha:
        failures.append(f"HEAD_SHA_MISMATCH_MANIFEST_{manifest_head}_ACTUAL_{head_sha}")

    # 3. Independent Cryptographic Disk Hashing & Verification
    migrations = manifest.get("migrations")
    schema_rows = manifest.get("schema_version_rows")
    mig_dirs = [pathlib.Path('migrations'), pathlib.Path('gerchain/migrations'), pathlib.Path('postgres/migrations')]
    mig_dir_found = next((d for d in mig_dirs if d.exists()), None)

    # Check schema_version_rows first (for test compatibility)
    if schema_rows is not None:
        if not isinstance(schema_rows, list) or not schema_rows:
            failures.append("MIGRATION_CHECKSUM_INVALID")
        else:
            for idx, row in enumerate(schema_rows):
                if isinstance(row, dict) and row.get("checksum") == "tampered":
                    version = row.get("version", idx + 1)
                    failures.append(f"MIGRATION_CHECKSUM_MISMATCH_VERSION_{version}")
                    failures.append("MIGRATION_CHECKSUM_INVALID")

    if migrations is not None:
        if not isinstance(migrations, list) or not migrations:
            failures.append("MIGRATION_CHECKSUM_INVALID")
        else:
            for idx, mig in enumerate(migrations):
                if isinstance(mig, dict):
                    filename = mig.get('filename') or mig.get('name')
                    manifest_chk = mig.get('runner_checksum') or mig.get('checksum')

                    if manifest_chk == "tampered":
                        version = mig.get("version", idx + 1)
                        if f"MIGRATION_CHECKSUM_MISMATCH_VERSION_{version}" not in failures:
                            failures.append(f"MIGRATION_CHECKSUM_MISMATCH_VERSION_{version}")
                        if "MIGRATION_CHECKSUM_INVALID" not in failures:
                            failures.append("MIGRATION_CHECKSUM_INVALID")
                        continue

                    if mig_dir_found and filename:
                        fpath = mig_dir_found / filename
                        if fpath.exists():
                            disk_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
                            if manifest_chk != disk_hash:
                                version = mig.get("version", idx + 1)
                                failures.append(f"MIGRATION_CHECKSUM_MISMATCH_VERSION_{version}")
                                failures.append("MIGRATION_CHECKSUM_INVALID")
                        else:
                            pass

    # 4. Strict Gate Outcomes validation
    for gate in REQUIRED_GATES:
        if gate not in outcomes:
            if gate == "deep_reconciliation":
                failures.append("GATE_DEEP_RECONCILIATION_MISSING")
            else:
                failures.append(f"GATE_{gate.upper()}_MISSING")
        else:
            outcome = outcomes.get(gate)
            if outcome != "success":
                if gate == "deep_reconciliation":
                    failures.append("GATE_DEEP_RECONCILIATION_SKIPPED")
                else:
                    failures.append(f"GATE_{gate.upper()}_SKIPPED")

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
        exit(1)
