from pathlib import Path


def test_postgresql_migration_versions_are_unique_and_ordered():
    migration_dir = Path(__file__).resolve().parents[2] / "postgres" / "schema"
    migrations = sorted(migration_dir.glob("*.sql"))
    versions = [int(path.name.split("_", 1)[0]) for path in migrations]

    assert migrations, "PostgreSQL migration set must not be empty"
    assert len(versions) == len(set(versions)), (
        "PostgreSQL migration versions must be unique: "
        f"{versions}"
    )
    assert versions == sorted(versions)


def test_canonical_production_migration_chain_contains_required_stages():
    migration_dir = Path(__file__).resolve().parents[2] / "postgres" / "schema"
    names = {path.name for path in migration_dir.glob("*.sql")}

    required = {
        "001_concurrency.sql",
        "002_canonical_persistence.sql",
        "003_ea25_durable_idempotency.sql",
        "004_ea26_value_flow_persistence.sql",
        "005_ea35_canonical_production.sql",
        "006_canonical_escrow_lifecycle_hardening.sql",
        "007_canonical_production_compat.sql",
    }
    assert required <= names
