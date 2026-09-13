from __future__ import annotations

import base64
import hashlib
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security import AuthorizationPolicy, RootOfTrust, SecurityError, SignedChange
from dee_security.manifest import build_manifest
from dee_security.signing import export_public_key_b64, sign_release
from nef_gerchain_port import EscrowRequest, ExternalPortImport


def _sign_change(private: Ed25519PrivateKey, change: SignedChange) -> str:
    payload = json.dumps(
        change.signing_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return base64.b64encode(private.sign(payload)).decode("ascii")


def _authorized_release_fixture():
    private = Ed25519PrivateKey.generate()
    owner_id = "owner:primary"
    commit_sha = "abc123def456"
    root = RootOfTrust(owner_id, export_public_key_b64(private))
    manifest = build_manifest(
        version=1,
        commit_sha=commit_sha,
        protected_paths=["nef_gerchain_port/import_api.py", "dee_security/release_policy.py"],
        artifact_hashes={"nef_gerchain_port/import_api.py": hashlib.sha256(b"artifact").hexdigest()},
        schema_version="1",
    )
    unsigned_change = SignedChange(
        owner_id=owner_id,
        change_id="change-release-001",
        version=1,
        payload_hash=manifest["manifest_hash"],
        signature="",
    )
    change = SignedChange(**{**unsigned_change.__dict__, "signature": _sign_change(private, unsigned_change)})
    signed_release = sign_release(
        private,
        release_id="release-001",
        owner_id=owner_id,
        manifest_hash=manifest["manifest_hash"],
        commit_sha=commit_sha,
    )
    return private, root, manifest, change, signed_release, commit_sha


def _locked_escrow():
    port = ExternalPortImport()
    witness = port.create_witness_chain(
        initial_state={"case_id": "CASE-SEC-001"},
        manifest={"purpose": "security-release-test"},
        witness_id="WITNESS-SEC-001",
    )
    escrow = port.create_escrow(
        EscrowRequest(
            escrow_id="ESCROW-SEC-001",
            amount=100_000,
            currency="MNT",
            settlement_provider="NEF",
        ),
        witness,
    )
    escrow.transition("FUNDED", "2026-09-13T16:00:00Z", {"case_id": "CASE-SEC-001"})
    escrow.transition("LOCKED", "2026-09-13T16:00:01Z", {"case_id": "CASE-SEC-001"})
    return port, escrow


def test_hardened_release_requires_owner_signature_and_exact_commit():
    _, root, manifest, change, signed_release, commit_sha = _authorized_release_fixture()
    port, escrow = _locked_escrow()

    result = port.release_escrow_authorized(
        escrow,
        incident_id="CASE-SEC-001",
        authorization_hash="AUTH-SEC-001",
        rule_version="SHUUD-1.0",
        timestamp="2026-09-13T16:00:02Z",
        root=root,
        policy=AuthorizationPolicy(),
        change=change,
        manifest=manifest,
        signed_release=signed_release,
        expected_commit_sha=commit_sha,
    )

    assert result.state == "RELEASED"
    assert escrow.records[-1].evidence["release_id"] == "release-001"


def test_hardened_release_rejects_tampered_signature():
    _, root, manifest, change, signed_release, commit_sha = _authorized_release_fixture()
    port, escrow = _locked_escrow()
    tampered = signed_release.__class__(**{**signed_release.__dict__, "commit_sha": "tampered"})

    with pytest.raises(SecurityError, match="signed release commit SHA mismatch"):
        port.release_escrow_authorized(
            escrow,
            incident_id="CASE-SEC-001",
            authorization_hash="AUTH-SEC-001",
            rule_version="SHUUD-1.0",
            timestamp="2026-09-13T16:00:02Z",
            root=root,
            policy=AuthorizationPolicy(),
            change=change,
            manifest=manifest,
            signed_release=tampered,
            expected_commit_sha=commit_sha,
        )
    assert escrow.get_state()["state"] == "LOCKED"


def test_hardened_release_rejects_release_replay():
    _, root, manifest, change, signed_release, commit_sha = _authorized_release_fixture()
    port = ExternalPortImport()
    policy = AuthorizationPolicy()

    for suffix in ("001", "002"):
        escrow = _locked_escrow()[1]
        release = signed_release if suffix == "001" else sign_release(
            Ed25519PrivateKey.generate(),
            release_id="release-002",
            owner_id=root.owner_id,
            manifest_hash=manifest["manifest_hash"],
            commit_sha=commit_sha,
        )
        if suffix == "002":
            release = sign_release(
                _authorized_release_fixture()[0],
                release_id="release-002",
                owner_id=root.owner_id,
                manifest_hash=manifest["manifest_hash"],
                commit_sha=commit_sha,
            )
        port.release_escrow_authorized(
            escrow,
            incident_id="CASE-SEC-001",
            authorization_hash=f"AUTH-SEC-{suffix}",
            rule_version="SHUUD-1.0",
            timestamp="2026-09-13T16:00:02Z",
            root=root,
            policy=policy,
            change=change,
            manifest=manifest,
            signed_release=release,
            expected_commit_sha=commit_sha,
        )

    replay_escrow = _locked_escrow()[1]
    with pytest.raises(SecurityError, match="replayed release_id"):
        port.release_escrow_authorized(
            replay_escrow,
            incident_id="CASE-SEC-001",
            authorization_hash="AUTH-SEC-REPLAY",
            rule_version="SHUUD-1.0",
            timestamp="2026-09-13T16:00:03Z",
            root=root,
            policy=policy,
            change=change,
            manifest=manifest,
            signed_release=signed_release,
            expected_commit_sha=commit_sha,
        )
