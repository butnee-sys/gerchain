from __future__ import annotations

import base64
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security.core_access import CoreAccessError, CoreAccessRequest, authorize_core_access
from dee_security.root_of_trust import RootOfTrust


def _root() -> RootOfTrust:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    return RootOfTrust("owner-1", base64.b64encode(public).decode())


def _request(entrypoint: str = "CORE_ADAPTER", actor_id: str = "owner-1") -> CoreAccessRequest:
    return CoreAccessRequest(
        actor_id=actor_id,
        operation="read-core-state",
        entrypoint=entrypoint,
        request_id="REQ-1",
    )


def test_core_access_requires_core_adapter() -> None:
    with pytest.raises(CoreAccessError):
        authorize_core_access(
            root=_root(),
            request=_request(entrypoint="EXIM_PORT"),
            trinity_proof={"trust": True, "transparency": True, "performance": True},
            authorized_actor_id="owner-1",
        )


def test_core_access_rejects_non_owner_actor() -> None:
    with pytest.raises(CoreAccessError):
        authorize_core_access(
            root=_root(),
            request=_request(actor_id="shuud-app"),
            trinity_proof={"trust": True, "transparency": True, "performance": True},
            authorized_actor_id="shuud-app",
        )


def test_core_access_requires_trinity() -> None:
    with pytest.raises(Exception):
        authorize_core_access(
            root=_root(),
            request=_request(),
            trinity_proof={"trust": True, "transparency": True},
            authorized_actor_id="owner-1",
        )


def test_owner_core_access_can_pass() -> None:
    authorize_core_access(
        root=_root(),
        request=_request(),
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        authorized_actor_id="owner-1",
    )
