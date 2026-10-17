"""Regression checks for the schema_version bootstrap contract.

The migration runner owns registry creation and duplicate-row repair. Historical
SQL migrations 001/002 retain guarded IF NOT EXISTS statements for checksum
compatibility; these must never become unguarded CREATE TABLE statements.
"""
from pathlib import Path

from postgres.migrations import _CANONICAL_FILES


ROOT = Path(__file__).resolve().parents[1] / "migrations"


def test_schema_version_bootstrap_is_guarded_in_historical_migrations():
    declarations = []
    for name in _CANONICAL_FILES:
        source = (ROOT / name).read_text(encoding="utf-8")
        for line_no, line in enumerate(source.splitlines(), start=1):
            if "CREATE TABLE" in line.upper() and "SCHEMA_VERSION" in line.upper():
                declarations.append((name, line_no, line.strip()))

    assert declarations, "expected historical schema_version declarations to be audited"
    assert all(
        "create table if not exists schema_version" in line.lower()
        for _, _, line in declarations
    ), declarations
    assert {name for name, _, _ in declarations} == {
        "001_canonical_production.sql",
        "002_canonical_production.sql",
    }


def test_migration_runner_owns_schema_version_duplicate_repair():
    source = (Path(__file__).resolve().parents[1] / "migrations" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "Conflicting schema_version checksums" in source
    assert "DELETE FROM schema_version AS duplicate" in source
    assert "CREATE UNIQUE INDEX schema_version_version_uq" in source
    assert "ON CONFLICT (version) DO NOTHING" in source
