from core.migration_identity import MigrationIdentity, MigrationIdentityError


def identity() -> MigrationIdentity:
    return MigrationIdentity("M-001", "GERCHAIN", 1, 2, "hash-v1")


def test_valid_identity() -> None:
    value = identity()
    value.validate()
    assert value.predecessor_matches("GERCHAIN", 1)


def test_version_must_advance() -> None:
    value = MigrationIdentity("M-001", "GERCHAIN", 2, 2, "hash-v1")
    try:
        value.validate()
    except MigrationIdentityError:
        return
    raise AssertionError("non-advancing migration was accepted")


def test_same_identity_is_idempotent_identity() -> None:
    assert identity().same_identity(identity())
    assert not identity().conflicts_with(identity())


def test_same_id_different_hash_is_conflict() -> None:
    altered = MigrationIdentity("M-001", "GERCHAIN", 1, 2, "hash-v2")
    assert identity().conflicts_with(altered)


def test_same_id_different_transition_is_conflict() -> None:
    altered = MigrationIdentity("M-001", "GERCHAIN", 2, 3, "hash-v2")
    assert identity().conflicts_with(altered)


def test_different_ids_are_not_identity_conflicts() -> None:
    other = MigrationIdentity("M-002", "GERCHAIN", 1, 2, "hash-v2")
    assert not identity().conflicts_with(other)
