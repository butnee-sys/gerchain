from pathlib import Path

from postgres.migrations import _canonical_migration_files


def _migration_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "postgres" / "migrations"


def test_postgresql_migration_versions_resolve_to_exact_canonical_chain():
    selected = _canonical_migration_files(_migration_dir())
    versions = [int(path.name.split("_", 1)[0]) for path in selected]

    assert len(selected) == 14
    assert versions == list(range(1, 15))


def test_canonical_migration_chain_contains_required_stages():
    names = {path.name for path in _canonical_migration_files(_migration_dir())}

    required = {
        "001_canonical_production.sql",
        "002_canonical_production.sql",
        "003_canonical_compatibility.sql",
        "004_canonical_value_truth.sql",
        "005_canonical_production.sql",
        "006_canonical_movement_integrity.sql",
        "007_canonical_production_reconciliation.sql",
        "008_ea35_idempotency_compat.sql",
        "009_canonical_movement_integrity_hardening.sql",
        "010_canonical_evidence_constraints.sql",
        "011_ea35_canonical_schema_finalization.sql",
        "012_canonical_production.sql",
        "013_ea35_canonical_schema_hardening.sql",
        "014_canonical_escrow_state_constraint.sql",
    }
    assert names == required
