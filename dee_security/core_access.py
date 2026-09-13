"""DEE Core Access Protection.

NEF–GerChain core access is deny-by-default and must cross the protected
Core Adapter boundary. Applications and connectors do not receive core
authority merely by reaching the adapter layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .root_of_trust import RootOfTrust, SecurityError
from .trinity import require_trinity


class CoreAccessError(SecurityError):
    """Raised when a request attempts to bypass protected core access."""


@dataclass(frozen=True)
class CoreAccessRequest:
    actor_id: str
    operation: str
    entrypoint: str
    request_id: str

    def validate(self) -> None:
        if not self.actor_id or not self.operation or not self.request_id:
            raise CoreAccessError("actor_id, operation, and request_id are required")
        if self.entrypoint != "CORE_ADAPTER":
            raise CoreAccessError("NEF–GerChain core access requires CORE_ADAPTER")


def authorize_core_access(
    *,
    root: RootOfTrust,
    request: CoreAccessRequest,
    trinity_proof: Mapping[str, bool],
    authorized_actor_id: str,
) -> None:
    """Authorize a core operation without granting authority to adapters themselves."""
    request.validate()
    if request.actor_id != authorized_actor_id:
        raise CoreAccessError("actor is not authorized for protected core access")
    if request.actor_id != root.owner_id:
        raise CoreAccessError("core authority is not inherited by application or connector actors")
    require_trinity(trinity_proof)


__all__ = ["CoreAccessError", "CoreAccessRequest", "authorize_core_access"]
