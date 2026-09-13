"""Failure/invariant coverage for the DEE Escrow Trinity.

TRUST, TRANSPARENCY and PERFORMANCE are treated as fail-closed invariants:
invalid evidence, non-integer money, and unauthorized release must not cross
the EXIM Escrow Port boundary.
"""

import pytest

from dee_security.authorization import AuthorizationPolicy, RootOfTrust
from dee_security.manifest import build_manifest
from dee_security.release_policy import authorize_release
from dee_security.signing import sign_release
from nef_gerchain_port.contract import EscrowRequest
from nef_gerchain_port.import_api import ExternalPortImport



def _root_and_manifest():
    root = RootOfTrust.generate("trinity-invariant-owner")
    manifest = build_manifest(
        commit_sha="trinity-invariant",
        protected_paths=[
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
        ],
    )
    return root, manifest


def test_trust_rejects_non_integer_money_at_port_boundary():
    """Money semantics must fail closed before escrow creation."""
    with pytest.raises(TypeError):
        EscrowRequest(
            escrow_id="TRUST-FLOAT-001",
            amount=1250000.5,
            currency="MNT",
            settlement_provider="NEF",
        )


def test_performance_release_requires_verified_authorization():
    """A valid escrow cannot be released without DEE authorization."""
    port = ExternalPortImport()
    escrow = port.create_escrow(
        EscrowRequest(
            escrow_id="PERF-AUTH-001",
            amount=1250000,
            currency="MNT",
            settlement_provider="NEF",
        )
    )
    port.transition_escrow(escrow.escrow_id, "FUNDED")
    port.transition_escrow(escrow.escrow_id, "LOCKED")

    with pytest.raises(Exception):
        port.release_escrow_authorized(
            escrow.escrow_id,
            release_id="PERF-UNAUTHORIZED-001",
            authorization=None,
        )


def test_transparency_manifest_binding_rejects_tampering():
    """Changing protected paths invalidates the signed release context."""
    root, manifest = _root_and_manifest()
    policy = AuthorizationPolicy(owner=root.owner)
    signed = sign_release(
        root=root,
        manifest=manifest,
        change_id="TRN-TAMPER-001",
        reason="trinity invariant test",
    )

    tampered = build_manifest(
        commit_sha="trinity-invariant",
        protected_paths=["nef_gerchain_port/contract.py", "escrow/"],
    )

    with pytest.raises(Exception):
        authorize_release(
            root=root,
            policy=policy,
            manifest=tampered,
            signed_release=signed,
        )
