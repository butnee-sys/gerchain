"""DEE Root of Trust and Owner Authorization primitives.

The security boundary is intentionally independent from the application layer.
Private signing keys must never be stored in this repository.
"""

from .root_of_trust import RootOfTrust, SignedChange, SecurityError
from .authorization import AuthorizationPolicy, authorize_change
from .manifest import build_manifest, canonical_manifest
from .release_policy import authorize_release

__all__ = [
    "AuthorizationPolicy",
    "RootOfTrust",
    "SecurityError",
    "SignedChange",
    "authorize_change",
    "authorize_release",
    "build_manifest",
    "canonical_manifest",
]
