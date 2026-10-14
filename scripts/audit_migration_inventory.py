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

from postgres.migrations import (
    FROZEN_CHECKSUMS,
    LEGACY_CHECKSUMS,
    _canonical_migration_files,
    checksum,
)

ROOT = Path(__file__).resolve().parents[1]
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
    if database_url:
        try:
            import psycopg

            normalized = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
            with psycopg.connect(normalized) as connection:
                rows_db = connection.execute(
                    "SELECT version, checksum, applied_at FROM schema_version ORDER BY version"
                ).fetchall()
            report["applied_history"] = {
                "status": "CAPTURED",
                "rows": [
                    {"version": version, "checksum": digest, "applied_at": applied_at.isoformat()}
                    for version, digest, applied_at in rows_db
                ],
                "versions": [row[0] for row in rows_db],
                "duplicate_versions": [],
            }
            if report["applied_history"]["versions"] != actual_versions:
                report["applied_history"]["status"] = "VERSION_MISMATCH"
                report["status"] = "FAIL"
        except Exception as exc:
            report["applied_history"] = {
                "status": "ERROR",
                "error": f"{type(exc).__name__}: {exc}",
            }
            report["status"] = "FAIL"

    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "commit_sha": report["commit_sha"],
        "canonical_versions": actual_versions,
        "versioned_sql_files": len(rows),
        "duplicate_versions": report["duplicate_versions"],
        "report": str(OUTPUT),
        "applied_history_status": report["applied_history"]["status"],
    }, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
