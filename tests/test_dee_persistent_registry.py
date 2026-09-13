import pytest

from dee_security.key_management import OwnerKeyRecord, generate_owner_keypair, key_id_from_public_key, public_key_b64
from dee_security.persistent_registry import PersistentKeyRegistry
from dee_security.root_of_trust import SecurityError
from dee_security.rotation import build_rotation_request


def _record(owner_id, public):
    return OwnerKeyRecord(owner_id, key_id_from_public_key(public), public_key_b64(public))


def test_rotation_persists_across_registry_restart(tmp_path):
    old_private, old_public = generate_owner_keypair()
    new_private, new_public = generate_owner_keypair()
    db = f"sqlite:///{tmp_path / 'dee.db'}"
    registry = PersistentKeyRegistry(db, _record("owner", old_public))
    request = build_rotation_request(old_private, owner_id="owner", rotation_id="r1", new_public_key=new_public)

    active = registry.apply_rotation(request, old_public)
    assert active.key_id == key_id_from_public_key(new_public)

    restarted = PersistentKeyRegistry(db)
    assert restarted.active("owner").key_id == key_id_from_public_key(new_public)
    with pytest.raises(SecurityError):
        restarted.apply_rotation(request, old_public)
    assert new_private.public_key() is not None


def test_consecutive_rotations_reject_old_key(tmp_path):
    old_private, old_public = generate_owner_keypair()
    new_private, new_public = generate_owner_keypair()
    third_private, third_public = generate_owner_keypair()
    db = f"sqlite:///{tmp_path / 'dee.db'}"
    registry = PersistentKeyRegistry(db, _record("owner", old_public))

    registry.apply_rotation(
        build_rotation_request(old_private, owner_id="owner", rotation_id="r1", new_public_key=new_public),
        old_public,
    )
    with pytest.raises(SecurityError):
        registry.apply_rotation(
            build_rotation_request(old_private, owner_id="owner", rotation_id="r2", new_public_key=third_public),
            old_public,
        )

    active = registry.apply_rotation(
        build_rotation_request(new_private, owner_id="owner", rotation_id="r2", new_public_key=third_public),
        new_public,
    )
    assert active.key_id == key_id_from_public_key(third_public)
    assert third_private.public_key() is not None
