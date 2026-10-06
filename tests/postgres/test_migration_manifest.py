from pathlib import Path


def _migration_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "postgres" / "schema"


def test_postgresql_migration_versions_are_resolvable():
    migrations = sorted(_migration_dir().glob("*.sql"))
    versions = [int(path.name.split("_", 1)[0]) for path in migrations]

    assert migrations, "PostgreSQL migration set must not be empty"
    assert versions == sorted(versions)

    duplicates = {v for v in versions if versions.count(v) > 1}
    assert duplicates == {2, 5, 6}


def test_canonical_migration_chain_contains_required_stages():
    names = {path.name for path in _migration_dir().glob("*.sql")}

    required = {
        "001_concurrency.sql",
        "002_canonical_production.sql",
        "003_canonical_integrity_constraints.sql",
        "004_ea26_value_flow_persistence.sql",
        "005_canonical_production.sql",
        "006_canonical_escrow_lifecycle_hardening.sql",
        "008_ea35_idempotency_compat.sql",
        "009_canonical_movement_integrity_hardening.sql",
        "010_ea35_settlement_binding_fix.sql",
    }
    assert required <= names
