from __future__ import annotations

"""Produce a single, checksum-addressed inventory of canonical and historical SQL migrations."""

import hashlib
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]

# The repository contains both postgres/migrations.py (historical checksum
# registry) and postgres/migrations/ (the active runner package). Python
# resolves "postgres.migrations" to the package, so load the registry file by
# explicit path rather than accidentally importing the package and failing.
_registry_path = ROOT / "postgres" / "migrations.py"
_registry_spec = importlib.util.spec_from_file_location(
    "gerchain_migration_registry_compat", _registry_path
)
if _registry_spec is None or _registry_spec.loader is None:
    raise ImportError(f"cannot load migration registry from {_registry_path}")
_registry = importlib.util.module_from_spec(_registry_spec)
_registry_spec.loader.exec_module(_registry)
FROZEN_CHECKSUMS = _registry.FROZEN_CHECKSUMS
LEGACY_CHECKSUMS = _registry.LEGACY_CHECKSUMS
_canonical_migration_files = _registry._canonical_migration_files
checksum = _registry.checksum
MIGRATION_DIR = ROOT / "postgres" / "migrations"
OUTPUT = Path(os.environ.get("MIGRATION_INVENTORY_REPORT", "migration-inventory-report.json"))


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return os.environ.get("GITHUB_SHA", "UNKNOWN")


def main() -> int:
    files = sorted(
        (p for p in MIGRATION_DIR.glob("*.sql") if p.name[:3].isdigit()),
        key=lambda p: (int(p.name.split("_", 1)[0]), p.name),
    )
    canonical = _canonical_migration_files(MIGRATION_DIR)
    canonical_by_version = {
        int(path.name.split("_", 1)[0]): path for path in canonical
    }
    groups: dict[int, list[Path]] = defaultdict(list)
    for path in files:
        groups[int(path.name.split("_", 1)[0])].append(path)

    rows = []
    for path in files:
        version = int(path.name.split("_", 1)[0])
        sql = path.read_text(encoding="utf-8")
        rows.append({
            "version": version,
            "filename": path.name,
            "selected_for_fresh_database": canonical_by_version.get(version) == path,
            "duplicate_version_count": len(groups[version]),
            "duplicate_version_filenames": [p.name for p in groups[version]],
            "sha256": checksum(sql),
            "git_blob_sha": None,
        })

    expected_versions = list(range(1, len(canonical) + 1))
    actual_versions = [int(path.name.split("_", 1)[0]) for path in canonical]
    report = {
        "status": "PASS" if actual_versions == expected_versions else "FAIL",
        "commit_sha": git_sha(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "SHA-256 over exact UTF-8 migration file text",
        "migration_directory": "postgres/migrations",
        "canonical_order": [
            {
                "sequence": i + 1,
                "version": int(path.name.split("_", 1)[0]),
                "filename": path.name,
                "sha256": checksum(path.read_text(encoding="utf-8")),
            }
            for i, path in enumerate(canonical)
        ],
        "all_versioned_files": rows,
        "duplicate_versions": {
            str(version): [p.name for p in paths]
            for version, paths in sorted(groups.items())
            if len(paths) > 1
        },
        "accepted_historical_checksums": {
            "frozen": {str(k): sorted(v) for k, v in FROZEN_CHECKSUMS.items()},
            "legacy": {str(k): sorted(v) for k, v in LEGACY_CHECKSUMS.items()},
        },
        "applied_history": {
            "status": "NOT_REQUESTED",
            "note": "Set GERCHAIN_MIGRATION_AUDIT_DATABASE_URL to attach live schema_version history.",
        },
    }

    database_url = os.environ.get("GERCHAIN_MIGRATION_AUDIT_DATABASE_URL")
    require_history = os.environ.get("REQUIRE_MIGRATION_HISTORY", "").strip().lower() in {"1", "true", "yes"}
    if require_history and not database_url:
        report["applied_history"] = {
            "status": "REQUIRED_BUT_NOT_CONFIGURED",
            "error": "REQUIRE_MIGRATION_HISTORY is enabled but GERCHAIN_MIGRATION_AUDIT_DATABASE_URL is missing",
        }
        report["status"] = "FAIL"
    if database_url:
        try:
            import psycopg

            normalized = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
            with psycopg.connect(normalized) as connection:
                rows_db = connection.execute(
                    "SELECT version, checksum, applied_at FROM schema_version ORDER BY version"
                ).fetchall()
            applied_versions = [row[0] for row in rows_db]
            duplicates = sorted(
                version for version in set(applied_versions)
                if applied_versions.count(version) > 1
            )
            canonical_digests = {
                int(path.name.split("_", 1)[0]): checksum(path.read_text(encoding="utf-8"))
                for path in canonical
            }
            checksum_mismatches = []
            for version, digest, _applied_at in rows_db:
                accepted = {canonical_digests.get(version)}
                accepted.update(FROZEN_CHECKSUMS.get(version, set()))
                accepted.update(LEGACY_CHECKSUMS.get(version, set()))
                if digest not in accepted:
                    checksum_mismatches.append({
                        "version": version,
                        "applied_checksum": digest,
                        "accepted_checksums": sorted(item for item in accepted if item),
                    })
            report["applied_history"] = {
                "status": "CAPTURED",
                "rows": [
                    {"version": version, "checksum": digest, "applied_at": applied_at.isoformat()}
                    for version, digest, applied_at in rows_db
                ],
                "versions": applied_versions,
                "duplicate_versions": duplicates,
                "checksum_mismatches": checksum_mismatches,
            }
            if (
                applied_versions != actual_versions
                or duplicates
                or checksum_mismatches
            ):
                report["applied_history"]["status"] = "HISTORY_MISMATCH"
                report["status"] = "FAIL"
        except Exception as exc:
            report["applied_history"] = {
                "status": "ERROR",
                "error": f"{type(exc).__name__}: {exc}",
            }
            report["status"] = "FAIL"

    checked_out_head_sha = git_sha()
    requested_head_sha = os.environ.get("TARGET_SHA", checked_out_head_sha)
    report["checked_out_head_sha"] = checked_out_head_sha
    report["requested_head_sha"] = requested_head_sha
    report["sha_match"] = requested_head_sha == checked_out_head_sha
    if not report["sha_match"]:
        report["status"] = "FAIL"
    report["evidence_status"] = (
        "PASS_CANDIDATE"
        if report["status"] == "PASS"
        and report["sha_match"]
        and report["applied_history"].get("status") == "CAPTURED"
        else "INCOMPLETE_OR_FAILED"
    )

    # Persist valid UTF-8 JSON with a real newline, then parse the exact bytes
    # back and enforce the SHA/evidence contract before returning success.
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    persisted = json.loads(OUTPUT.read_text(encoding="utf-8"))
    if persisted != report:
        raise SystemExit("FAIL: persisted migration evidence JSON differs from in-memory report")
    if persisted["commit_sha"] != persisted["checked_out_head_sha"]:
        raise SystemExit("FAIL: migration evidence commit SHA does not match checked-out HEAD")
    if persisted["requested_head_sha"] != persisted["checked_out_head_sha"]:
        raise SystemExit("FAIL: requested candidate SHA does not match checked-out HEAD")
    if persisted["evidence_status"] != "PASS_CANDIDATE":
        print(json.dumps({
            "status": persisted["status"],
            "evidence_status": persisted["evidence_status"],
            "commit_sha": persisted["commit_sha"],
            "checked_out_head_sha": persisted["checked_out_head_sha"],
            "applied_history_status": persisted["applied_history"]["status"],
        }, indent=2))
        return 1

    print(json.dumps({
        "status": report["status"],
        "evidence_status": report["evidence_status"],
        "commit_sha": report["commit_sha"],
        "checked_out_head_sha": report["checked_out_head_sha"],
        "canonical_versions": actual_versions,
        "versioned_sql_files": len(rows),
        "duplicate_versions": report["duplicate_versions"],
        "report": str(OUTPUT),
        "applied_history_status": report["applied_history"]["status"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
