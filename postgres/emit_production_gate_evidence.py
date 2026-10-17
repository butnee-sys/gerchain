from __future__ import annotations

import json
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from persistence.production_schema_guard import REQUIRED_COLUMNS, REQUIRED_TABLES, assert_canonical_production_schema
from postgres.migrations import FROZEN_CHECKSUMS, LEGACY_CHECKSUMS, checksum


PREFERRED_NAMES = {
    2: "002_canonical_production.sql",
    5: "005_canonical_production.sql",
    6: "006_canonical_production.sql",
    7: "007_canonical_production.sql",
    8: "008_ea35_idempotency_compat.sql",
    9: "009_canonical_movement_integrity_hardening.sql",
    10: "010_canonical_evidence_constraints.sql",
    11: "011_ea35_canonical_schema_finalization.sql",
    12: "012_canonical_production.sql",
    13: "013_ea35_canonical_schema_hardening.sql",
}


def selected_migrations(directory: Path) -> dict[int, Path]:
    grouped: dict[int, list[Path]] = {}
    for path in sorted(directory.glob("*.sql")):
        version = int(path.name.split("_", 1)[0])
        grouped.setdefault(version, []).append(path)
    selected: dict[int, Path] = {}
    for version, candidates in grouped.items():
        preferred = PREFERRED_NAMES.get(version)
        if preferred:
            match = next((p for p in candidates if p.name == preferred), None)
            if match is not None:
                selected[version] = match
            elif len(candidates) == 1:
                selected[version] = candidates[0]
            else:
                raise RuntimeError(f"Cannot select migration for version {version}")
        elif len(candidates) == 1:
            selected[version] = candidates[0]
        else:
            raise RuntimeError(f"Ambiguous migration version {version}")
    return selected


def junit_summary(path: Path) -> dict[str, int]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    return {
        key: sum(int(suite.attrib.get(key, "0")) for suite in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }


def main() -> None:
    expected_sha = os.environ["EXPECTED_COMMIT_SHA"]
    checked_out_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    if checked_out_sha != expected_sha:
        raise RuntimeError(
            f"commit SHA mismatch: expected={expected_sha}, checked_out_head={checked_out_sha}"
        )

    database_url = os.environ.get("GERCHAIN_POSTGRES_DSN") or os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        raise RuntimeError("GERCHAIN_POSTGRES_DSN or GERCHAIN_TEST_DATABASE_URL is required")

    root = Path(__file__).resolve().parents[1]
    migration_dir = root / "postgres" / "schema"
    migrations = selected_migrations(migration_dir)
    engine = create_engine(database_url, future=True, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            assert_canonical_production_schema(connection)
            rows = connection.execute(
                text("SELECT version, checksum FROM schema_version ORDER BY version")
            ).all()
            applied = {int(version): digest for version, digest in rows}
            if sorted(applied) != list(range(1, 7)):
                raise RuntimeError(f"unexpected migration history versions: {sorted(applied)}")

            migration_evidence = []
            for version in sorted(applied):
                if version not in migrations:
                    raise RuntimeError(f"schema_version {version} has no selected migration file")
                path = migrations[version]
                current_digest = checksum(path.read_text(encoding="utf-8"))
                accepted = {current_digest}
                accepted.update(FROZEN_CHECKSUMS.get(version, set()))
                accepted.update(LEGACY_CHECKSUMS.get(version, set()))
                matches = applied[version] in accepted
                migration_evidence.append({
                    "version": version,
                    "file": path.relative_to(root).as_posix(),
                    "source_checksum_sha256": current_digest,
                    "database_recorded_checksum": applied[version],
                    "checksum_matches_current_or_frozen_legacy": matches,
                })
                if not matches:
                    raise RuntimeError(
                        f"migration checksum mismatch at version {version}: "
                        f"database={applied[version]} source={current_digest}"
                    )

            inspector = inspect(connection)
            table_names = set(inspector.get_table_names(schema="public"))
            missing_tables = sorted(REQUIRED_TABLES - table_names)
            column_evidence = {}
            for table, required in REQUIRED_COLUMNS.items():
                present = {col["name"] for col in inspector.get_columns(table, schema="public")}
                missing = sorted(required - present)
                column_evidence[table] = {
                    "required_columns": sorted(required),
                    "missing_columns": missing,
                }
                if missing:
                    raise RuntimeError(f"schema columns missing from {table}: {missing}")
            if missing_tables:
                raise RuntimeError(f"schema tables missing: {missing_tables}")

        junit_path = Path(os.environ.get("JUNIT_XML_PATH", "artifacts/postgres-production-runtime.xml"))
        tests = junit_summary(junit_path)
        if tests["tests"] < 1 or tests["failures"] or tests["errors"]:
            raise RuntimeError(f"JUnit evidence is not clean: {tests}")

        evidence = {
            "commit_sha": expected_sha,
            "checked_out_head_sha": checked_out_sha,
            "commit_sha_equals_checked_out_head_sha": expected_sha == checked_out_sha,
            "schema": {
                "required_tables": sorted(REQUIRED_TABLES),
                "missing_tables": [],
                "required_columns": column_evidence,
                "migration_versions": sorted(applied),
            },
            "migrations": migration_evidence,
            "tests": tests,
            "overall_pass": True,
        }
        output = Path("artifacts/production-gate-evidence.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2, sort_keys=True))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
