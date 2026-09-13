from __future__ import annotations

import base64
import hashlib
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security import AuthorizationPolicy, RootOfTrust, SecurityError, SignedChange, authorize_release
from dee_security.audit import append_record, verify_chain
from dee_security.manifest import build_manifest, canonical_manifest
from dee_security.signing import sign_release
from nef_gerchain_port import EscrowRequest, ExternalPortImport


def _sign(private_key: Ed25519PrivateKey, change: SignedChange) -> str:
    payload = json.dumps(
        change.signing_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return base64.b64encode(private_key.sign(payload)).decode("ascii")


def _change(private_key: Ed25519PrivateKey, version: int = 1) -> SignedChange:
    unsigned = SignedChange(
        owner_id="owner:primary",
        change_id="chg-001",
        version=version,
        payload_hash=hashlib.sha256(b"protected-state").hexdigest(),
        signature="",
    )
    return SignedChange(**{**unsigned.__dict__, "signature": _sign(private_key, unsigned)})


def _root(private_key: Ed25519PrivateKey) -> RootOfTrust:
    return RootOfTrust(
        "owner:primary",
        base64.b64encode(private_key.public_key().public_bytes_raw()).decode(),
    )


def _manifest():
    return build_manifest(
        version=1,
        commit_sha="abc123",
        protected_paths=["core/state.py", "dee_security/root_of_trust.py"],
        artifact_hashes={"core/state.py": "deadbeef"},
        schema_version="1",
    )


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


def test_root_of_trust_accepts_owner_signature():
    private = Ed25519PrivateKey.generate()
    assert _root(private).verify(_change(private)) is True


def test_root_of_trust_rejects_tampering_and_other_owner():
    private = Ed25519PrivateKey.generate()
    other = Ed25519PrivateKey.generate()
    root = _root(private)
    valid = _change(private)
    assert root.verify(SignedChange(**{**valid.__dict__, "payload_hash": "tampered"})) is False
    other_change = SignedChange(**{**_change(other).__dict__, "owner_id": "owner:other"})
    assert root.verify(other_change) is False


def test_policy_rejects_replay():
    private = Ed25519PrivateKey.generate()
    root = _root(private)
    policy = AuthorizationPolicy()
    change = _change(private)
    policy.check(root=root, change=change, paths=["core/state.py"], change_kind="rule")
    with pytest.raises(SecurityError, match="replayed"):
        policy.check(root=root, change=change, paths=["core/state.py"], change_kind="rule")


def test_policy_rejects_unprotected_paths():
    private = Ed25519PrivateKey.generate()
    with pytest.raises(SecurityError, match="protected DEE paths"):
        AuthorizationPolicy().check(
            root=_root(private), change=_change(private), paths=["shuud/app.py"], change_kind="source"
        )


def test_manifest_is_canonical_and_hashed():
    manifest = _manifest()
    assert manifest["manifest_hash"] == hashlib.sha256(
        canonical_manifest({k: v for k, v in manifest.items() if k != "manifest_hash"})
    ).hexdigest()


def test_release_gate_binds_owner_commit_and_manifest_signature():
    private = Ed25519PrivateKey.generate()
    manifest = _manifest()
    release = sign_release(
        private,
        owner_id="owner:primary",
        release_id="release-001",
        commit_sha=manifest["commit_sha"],
        manifest_hash=manifest["manifest_hash"],
    )
    authorize_release(root=_root(private), policy=AuthorizationPolicy(), release=release, manifest=manifest)

    tampered = {**manifest, "artifact_hashes": {"core/state.py": "tampered"}}
    with pytest.raises(SecurityError, match="manifest hash mismatch"):
        authorize_release(root=_root(private), policy=AuthorizationPolicy(), release=release, manifest=tampered)


def test_release_commit_mismatch_is_rejected():
    private = Ed25519PrivateKey.generate()
    manifest = _manifest()
    release = sign_release(private, owner_id="owner:primary", release_id="release-002", commit_sha="wrong", manifest_hash=manifest["manifest_hash"])
    with pytest.raises(SecurityError, match="commit"):
        authorize_release(root=_root(private), policy=AuthorizationPolicy(), release=release, manifest=manifest)


def test_release_replay_is_rejected():
    private = Ed25519PrivateKey.generate()
    manifest = _manifest()
    release = sign_release(private, owner_id="owner:primary", release_id="release-003", commit_sha="abc123", manifest_hash=manifest["manifest_hash"])
    policy = AuthorizationPolicy()
    from dee_security.release_policy import ReleaseAuthorization
    gate = ReleaseAuthorization()
    authorize_release(root=_root(private), policy=policy, release=release, manifest=manifest, gate=gate)
    with pytest.raises(SecurityError, match="replayed"):
        authorize_release(root=_root(private), policy=policy, release=release, manifest=manifest, gate=gate)


def test_authorized_port_release_requires_the_dee_release_gate():
    private = Ed25519PrivateKey.generate()
    root = _root(private)
    manifest = _manifest()
    release = sign_release(
        private,
        owner_id=root.owner_id,
        release_id="release-port-001",
        commit_sha=manifest["commit_sha"],
        manifest_hash=manifest["manifest_hash"],
    )
    port, escrow = _locked_escrow()

    port.release_escrow_authorized(
        escrow,
        incident_id="CASE-SEC-001",
        authorization_hash="AUTH-SEC-001",
        rule_version="SHUUD-1.0",
        timestamp="2026-09-13T16:00:02Z",
        root=root,
        policy=AuthorizationPolicy(),
        release=release,
        manifest=manifest,
    )

    assert escrow.get_state()["state"] == "RELEASED"
    assert escrow.witness_chain.entries[-1].evidence["release_id"] == "release-port-001"


def test_authorized_port_release_rejects_invalid_signature_before_transition():
    private = Ed25519PrivateKey.generate()
    root = _root(private)
    manifest = _manifest()
    valid = sign_release(
        private,
        owner_id=root.owner_id,
        release_id="release-port-002",
        commit_sha=manifest["commit_sha"],
        manifest_hash=manifest["manifest_hash"],
    )
    invalid = valid.__class__(**{**valid.__dict__, "signature": "invalid"})
    port, escrow = _locked_escrow()

    with pytest.raises(SecurityError, match="invalid release signature"):
        port.release_escrow_authorized(
            escrow,
            incident_id="CASE-SEC-001",
            authorization_hash="AUTH-SEC-002",
            rule_version="SHUUD-1.0",
            timestamp="2026-09-13T16:00:02Z",
            root=root,
            policy=AuthorizationPolicy(),
            release=invalid,
            manifest=manifest,
        )
    assert escrow.get_state()["state"] == "LOCKED"


def test_audit_chain_is_tamper_evident():
    first = append_record(sequence=1, event="DEE_CHANGE_AUTHORIZED", change_id="chg-001", owner_id="owner:primary", decision="ALLOW")
    second = append_record(sequence=2, event="DEE_RELEASE_AUTHORIZED", change_id="chg-001", owner_id="owner:primary", decision="ALLOW", previous_hash=first.record_hash)
    assert verify_chain([first, second]) is True
    tampered = second.__class__(**{**second.__dict__, "decision": "DENY"})
    assert verify_chain([first, tampered]) is False
