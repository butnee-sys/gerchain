from cryptography.hazmat.primitives import serialization
import pytest

from dee_security.key_management import OwnerKeyRecord, generate_owner_keypair, key_id_from_public_key, public_key_b64
from dee_security.root_of_trust import RootOfTrust, SecurityError
from dee_security.rotation import KeyRegistry, build_rotation_request
from dee_security.signing import sign_change, sign_release, verify_release


def _root(owner, public):
    return RootOfTrust(owner, public_key_b64(public))


def test_generate_owner_keypair_and_stable_id():
    private, public = generate_owner_keypair()
    assert private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw) == public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    assert key_id_from_public_key(public) == key_id_from_public_key(public)


def test_sign_and_verify_change():
    private, public = generate_owner_keypair()
    change = sign_change(private, owner_id="owner", change_id="c1", version=1, payload_hash="abc")
    assert _root("owner", public).verify(change)


def test_private_key_is_not_serialized_by_key_record():
    private, public = generate_owner_keypair()
    record = OwnerKeyRecord("owner", key_id_from_public_key(public), public_key_b64(public))
    assert not hasattr(record, "private_key")
    assert private is not None


def test_rotation_requires_current_owner_and_revokes_old_key():
    old_private, old_public = generate_owner_keypair()
    new_private, new_public = generate_owner_keypair()
    registry = KeyRegistry(OwnerKeyRecord("owner", key_id_from_public_key(old_public), public_key_b64(old_public)))
    request = build_rotation_request(old_private, owner_id="owner", rotation_id="r1", new_public_key=new_public)
    new_record = registry.apply_rotation(request, old_public)
    assert new_record.status == "active"
    assert new_record.rotated_from == request.current_key_id
    assert registry.active.key_id == key_id_from_public_key(new_public)
    assert new_private.public_key() is not None


def test_rotation_rejects_replay_and_wrong_owner_key():
    old_private, old_public = generate_owner_keypair()
    attacker, attacker_public = generate_owner_keypair()
    _, new_public = generate_owner_keypair()
    registry = KeyRegistry(OwnerKeyRecord("owner", key_id_from_public_key(old_public), public_key_b64(old_public)))
    request = build_rotation_request(old_private, owner_id="owner", rotation_id="r1", new_public_key=new_public)
    with pytest.raises(SecurityError):
        registry.authorize_rotation(request, attacker_public)
    registry.apply_rotation(request, old_public)
    with pytest.raises(SecurityError):
        registry.authorize_rotation(request, old_public)
    assert attacker is not None


def test_new_key_authorizes_after_rotation():
    old_private, old_public = generate_owner_keypair()
    new_private, new_public = generate_owner_keypair()
    registry = KeyRegistry(OwnerKeyRecord("owner", key_id_from_public_key(old_public), public_key_b64(old_public)))
    registry.apply_rotation(build_rotation_request(old_private, owner_id="owner", rotation_id="r1", new_public_key=new_public), old_public)
    change = sign_change(new_private, owner_id="owner", change_id="c2", version=1, payload_hash="xyz")
    assert _root("owner", new_public).verify(change)


def test_release_signature_binds_commit_and_manifest():
    private, public = generate_owner_keypair()
    release = sign_release(private, owner_id="owner", release_id="rel-1", commit_sha="abc123", manifest_hash="mhash")
    root = _root("owner", public)
    assert verify_release(root, release)
    tampered = sign_release(private, owner_id="owner", release_id="rel-2", commit_sha="different", manifest_hash="mhash")
    assert verify_release(root, tampered)
    assert release.commit_sha != tampered.commit_sha


def test_release_tamper_is_rejected():
    private, public = generate_owner_keypair()
    release = sign_release(private, owner_id="owner", release_id="rel-1", commit_sha="abc123", manifest_hash="mhash")
    tampered = type(release)(release.owner_id, release.release_id, "tampered", release.manifest_hash, release.version, release.signature)
    assert not verify_release(_root("owner", public), tampered)
