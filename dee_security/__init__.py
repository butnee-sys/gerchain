"""DEE Root of Trust, owner authorization, and key lifecycle primitives."""

from .root_of_trust import RootOfTrust, SignedChange, SecurityError
from .authorization import AuthorizationPolicy, authorize_change
from .manifest import build_manifest, canonical_manifest
from .release_policy import ReleaseAuthorization, authorize_release
from .key_management import OwnerKeyRecord, generate_owner_keypair, key_id_from_public_key, load_private_key, public_key_b64
from .signing import SignedRelease, sign_change, sign_release, verify_release
from .rotation import KeyRegistry, KeyRotationRequest, build_rotation_request
from .persistent_registry import PersistentKeyRegistry

__all__ = [
    "AuthorizationPolicy", "RootOfTrust", "SecurityError", "SignedChange",
    "authorize_change", "authorize_release", "build_manifest", "canonical_manifest",
    "ReleaseAuthorization", "OwnerKeyRecord", "generate_owner_keypair", "key_id_from_public_key", "load_private_key", "public_key_b64",
    "SignedRelease", "sign_change", "sign_release", "verify_release",
    "KeyRegistry", "KeyRotationRequest", "build_rotation_request", "PersistentKeyRegistry",
]
