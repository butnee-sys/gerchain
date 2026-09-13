"""Fail-closed authorization policy for protected DEE changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .root_of_trust import RootOfTrust, SecurityError, SignedChange


@dataclass(frozen=True)
class AuthorizationPolicy:
    """Policy applied after cryptographic signature verification."""

    protected_prefixes: tuple[str, ...] = (
        "nef_gerchain_port/contract.py",
        "nef_gerchain_port/import_api.py",
        "nef_gerchain_port/export_api.py",
        "nef_gerchain_port/gerchain_adapter.py",
        "nef_gerchain_port/nef_adapter.py",
        "core/",
        "escrow/",
        "witness/",
        "verifier/",
        "database/migrations/",
        "dee_security/",
    )
    allowed_change_kinds: frozenset[str] = frozenset(
        {"source", "config", "schema", "rule", "release"}
    )
    minimum_version: int = 1
    _seen_change_ids: set[str] = field(default_factory=set, compare=False, repr=False)

    def protects(self, path: str) -> bool:
        return any(path == prefix or path.startswith(prefix) for prefix in self.protected_prefixes)

    def check(
        self,
        *,
        root: RootOfTrust,
        change: SignedChange,
        paths: Iterable[str],
        change_kind: str,
    ) -> None:
        if change.version < self.minimum_version:
            raise SecurityError("change version is below the authorization floor")
        if change_kind not in self.allowed_change_kinds:
            raise SecurityError("change kind is not allowed")
        protected = tuple(paths)
        if not protected or not all(self.protects(path) for path in protected):
            raise SecurityError("authorization policy only accepts protected DEE paths")
        if change.change_id in self._seen_change_ids:
            raise SecurityError("replayed change_id")
        root.require_valid(change)
        self._seen_change_ids.add(change.change_id)


def authorize_change(
    root: RootOfTrust,
    policy: AuthorizationPolicy,
    change: SignedChange,
    *,
    paths: Iterable[str],
    change_kind: str,
) -> None:
    policy.check(
        root=root,
        change=change,
        paths=paths,
        change_kind=change_kind,
    )
