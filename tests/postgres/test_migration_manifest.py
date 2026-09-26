from pathlib import Path


def _migration_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "postgres" / "migrations"


def test_postgresql_migration_versions_are_unique_and_ordered():
    migrations = sorted(_migration_dir().glob("*.sql"))
    versions = [int(path.name.split("_", 1)[0]) for path in migrations]

    assert migrations, "PostgreSQL migration set must not be empty"
    assert len(versions) == len(set(versions)), (
        "PostgreSQL migration versions must be unique: "
        f"{versions}"
    )
    assert versions == sorted(versions)


def test_canonical_production_migration_chain_contains_required_stages():
    names = {path.name for path in _migration_dir().glob("*.sql")}

    required = {
        "001_concurrency.sql",
        "002_canonical_value_truth.sql",
        "003_canonical_value_authority.sql",
        "004_canonical_value_truth.sql",
        "005_canonical_production_reconciliation.sql",
        "006_canonical_movement_integrity.sql",
    }
    assert required <= names
