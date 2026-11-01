from pathlib import Path

from postgres.migrations import CANONICAL_MIGRATION_NAMES, _canonical_migration_files


def test_canonical_migration_registry_is_contiguous_through_version_18():
    migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"

    assert list(CANONICAL_MIGRATION_NAMES) == list(range(1, 19))
    selected = _canonical_migration_files(migration_dir)
    assert len(selected) == 18
    assert [path.name for path in selected] == [
        CANONICAL_MIGRATION_NAMES[version] for version in range(1, 19)
    ]
    assert selected[-1].name == "018_eai_signed_change_authorization.sql"
