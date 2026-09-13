"""DEE Root of Trust, governance, protection, and key lifecycle primitives."""

from .root_of_trust import RootOfTrust, SignedChange, SecurityError
from .authorization import AuthorizationPolicy, authorize_change
from .identity import ProtectedIdentity, authorize_protected_operation
from .manifest import build_manifest, canonical_manifest
from .release_policy import ReleaseAuthorization, authorize_release
from .key_management import OwnerKeyRecord, generate_owner_keypair, key_id_from_public_key, load_private_key, public_key_b64
from .signing import SignedRelease, sign_change, sign_release, verify_release
from .rotation import KeyRegistry, KeyRotationRequest, build_rotation_request
from .persistent_registry import PersistentKeyRegistry
from .runtime_governance import (
    RuntimeAction, RuntimeAuthorization, RuntimeGovernance, RuntimeGovernanceError,
    RuntimeIdentity, RuntimeRole,
)
from .recovery import (
    RecoveryApproval, RecoveryAuthority, RecoveryDecision, RecoveryGovernance,
    RecoveryGovernanceError, RecoveryPolicy, RecoveryRequest, RecoveryRole,
    build_recovery_approval,
)
from .genesis import GenesisAnchor, GenesisError, build_genesis_anchor, verify_genesis_anchor
from .trinity import TrinityDecision, TrinityDimension, TrinityError, evaluate_trinity, require_trinity

__all__ = [
    "AuthorizationPolicy", "RootOfTrust", "SecurityError", "SignedChange",
    "authorize_change", "ProtectedIdentity", "authorize_protected_operation",
    "authorize_release", "build_manifest", "canonical_manifest", "ReleaseAuthorization",
    "OwnerKeyRecord", "generate_owner_keypair", "key_id_from_public_key", "load_private_key", "public_key_b64",
    "SignedRelease", "sign_change", "sign_release", "verify_release",
    "KeyRegistry", "KeyRotationRequest", "build_rotation_request", "PersistentKeyRegistry",
    "RuntimeAction", "RuntimeAuthorization", "RuntimeGovernance", "RuntimeGovernanceError",
    "RuntimeIdentity", "RuntimeRole", "RecoveryApproval", "RecoveryAuthority", "RecoveryDecision",
    "RecoveryGovernance", "RecoveryGovernanceError", "RecoveryPolicy", "RecoveryRequest", "RecoveryRole",
    "build_recovery_approval", "GenesisAnchor", "GenesisError", "build_genesis_anchor", "verify_genesis_anchor",
    "TrinityDecision", "TrinityDimension", "TrinityError", "evaluate_trinity", "require_trinity",
]
