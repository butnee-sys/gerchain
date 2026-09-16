import pytest

from core.schema_authority import (
    SchemaAuthorityError,
    SchemaState,
    SchemaStatus,
    SchemaUpgrade,
    apply_upgrade,
)


def state(version=1):
    return SchemaState("GERCHAIN-CORE", version, f"hash-v{version}")


def upgrade(from_version=1, to_version=2, upgrade_id="U1"):
    return SchemaUpgrade(
        upgrade_id=upgrade_id,
        schema_id="GERCHAIN-CORE",
        from_version=from_version,
        to_version=to_version,
        migration_hash=f"migration-{upgrade_id}",
        authority="CORE-SCHEMA-AUTHORITY",
    )


def test_valid_successor_is_exactly_next_authoritative_state():
    result = apply_upgrade(state(), upgrade(), "hash-v2")
    assert result.schema_id == "GERCHAIN-CORE"
    assert result.current_version == 2
    assert result.state_hash == "hash-v2"
    assert result.status is SchemaStatus.ACTIVE


def test_stale_predecessor_is_rejected():
    with pytest.raises(SchemaAuthorityError, match="stale schema predecessor"):
        apply_upgrade(state(2), upgrade(from_version=1, to_version=3), "hash-v3")


def test_version_regression_is_rejected():
    with pytest.raises(SchemaAuthorityError, match="must increase"):
        apply_upgrade(state(2), upgrade(from_version=2, to_version=1), "hash-v1")


def test_identity_mismatch_is_rejected():
    bad = SchemaUpgrade("U1", "OTHER", 1, 2, "migration", "AUTH")
    with pytest.raises(SchemaAuthorityError, match="schema identity mismatch"):
        apply_upgrade(state(), bad, "hash-v2")
