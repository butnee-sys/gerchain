"""Failure/invariant coverage for the DEE Escrow Trinity.

TRUST, TRANSPARENCY and PERFORMANCE are treated as fail-closed invariants:
invalid evidence, non-integer money, and unauthorized release must not cross
the EXIM Escrow Port boundary.
"""

import base64

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security.authorization import AuthorizationPolicy, RootOfTrust
from dee_security.manifest import build_manifest
from dee_security.release_policy import authorize_release
from dee_security.signing import sign_release
from nef_gerchain_port.contract import EscrowRequest
from nef_gerchain_port.import_api import ExternalPortImport


def _root_and_manifest():
    private = Ed25519PrivateKey.generate()
    root = RootOfTrust(
        "trinity-invariant-owner",
        base64.b64encode(private.public_key().public_bytes_raw()).decode(),
    )
    manifest = build_manifest(
        version=1,
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
        artifact_hashes={"nef_gerchain_port/contract.py": "protected"},
        schema_version="1",
    )
    return private, root, manifest


def _locked_escrow():
    port = ExternalPortImport()
    witness = port.create_witness_chain(
        initial_state={"case_id": "PERF-AUTH-001"},
        manifest={"purpose": "trinity-invariant-test"},
        witness_id="WITNESS-TRINITY-001",
    )
    escrow = port.create_escrow(
        EscrowRequest(
            escrow_id="PERF-AUTH-001",
            amount=1250000,
            currency="MNT",
            settlement_provider="NEF",
        ),
        witness,
    )
    escrow.transition("FUNDED", "2026-09-13T16:00:00Z", {"case_id": "PERF-AUTH-001"})
    escrow.transition("LOCKED", "2026-09-13T16:00:01Z", {"case_id": "PERF-AUTH-001"})
    return port, escrow


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
    """A valid escrow cannot be released without a valid DEE release object."""
    port, escrow = _locked_escrow()

    with pytest.raises(Exception):
        port.release_escrow_authorized(
            escrow,
            incident_id="PERF-AUTH-001",
            authorization_hash="AUTH-PERF-001",
            rule_version="SHUUD-1.0",
            timestamp="2026-09-13T16:00:02Z",
            root=None,
            policy=AuthorizationPolicy(),
            release=None,
            manifest={},
        )

    assert escrow.get_state()["state"] == "LOCKED"


def test_transparency_manifest_binding_rejects_tampering():
    """Changing protected manifest content invalidates the signed release context."""
    private, root, manifest = _root_and_manifest()
    policy = AuthorizationPolicy()
    signed = sign_release(
        private,
        owner_id=root.owner_id,
        release_id="TRN-TAMPER-001",
        commit_sha=manifest["commit_sha"],
        manifest_hash=manifest["manifest_hash"],
    )

    tampered = dict(manifest)
    tampered["artifact_hashes"] = {"nef_gerchain_port/contract.py": "tampered"}

    with pytest.raises(Exception):
        authorize_release(
            root=root,
            policy=policy,
            manifest=tampered,
            release=signed,
        )
