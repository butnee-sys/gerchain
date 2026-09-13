from __future__ import annotations

import base64
import hashlib
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security import AuthorizationPolicy, RootOfTrust, SecurityError, SignedChange
from dee_security.audit import append_record, verify_chain
from dee_security.manifest import build_manifest, canonical_manifest


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


def test_root_of_trust_accepts_owner_signature():
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    root = RootOfTrust("owner:primary", base64.b64encode(public).decode())
    assert root.verify(_change(private)) is True


def test_root_of_trust_rejects_tampering_and_other_owner():
    private = Ed25519PrivateKey.generate()
    other = Ed25519PrivateKey.generate()
    root = RootOfTrust(
        "owner:primary",
        base64.b64encode(private.public_key().public_bytes_raw()).decode(),
    )
    valid = _change(private)
    assert root.verify(SignedChange(**{**valid.__dict__, "payload_hash": "tampered"})) is False
    other_change = SignedChange(**{**_change(other).__dict__, "owner_id": "owner:other"})
    assert root.verify(other_change) is False


def test_policy_rejects_replay():
    private = Ed25519PrivateKey.generate()
    root = RootOfTrust(
        "owner:primary",
        base64.b64encode(private.public_key().public_bytes_raw()).decode(),
    )
    policy = AuthorizationPolicy()
    change = _change(private)
    policy.check(root=root, change=change, paths=["core/state.py"], change_kind="rule")
    with pytest.raises(SecurityError, match="replayed"):
        policy.check(root=root, change=change, paths=["core/state.py"], change_kind="rule")


def test_policy_rejects_unprotected_paths():
    private = Ed25519PrivateKey.generate()
    root = RootOfTrust(
        "owner:primary",
        base64.b64encode(private.public_key().public_bytes_raw()).decode(),
    )
    with pytest.raises(SecurityError, match="protected DEE paths"):
        AuthorizationPolicy().check(
            root=root,
            change=_change(private),
            paths=["shuud/app.py"],
            change_kind="source",
        )


def test_manifest_is_canonical_and_hashed():
    manifest = build_manifest(
        version=1,
        commit_sha="abc123",
        protected_paths=["core/state.py", "nef_gerchain_port/contract.py"],
        artifact_hashes={"core/state.py": "deadbeef"},
        schema_version="1",
    )
    assert manifest["protected_paths"] == ["core/state.py", "nef_gerchain_port/contract.py"]
    assert manifest["manifest_hash"] == hashlib.sha256(
        canonical_manifest({k: v for k, v in manifest.items() if k != "manifest_hash"})
    ).hexdigest()


def test_audit_chain_is_tamper_evident():
    first = append_record(
        sequence=1,
        event="DEE_CHANGE_AUTHORIZED",
        change_id="chg-001",
        owner_id="owner:primary",
        decision="ALLOW",
    )
    second = append_record(
        sequence=2,
        event="DEE_RELEASE_AUTHORIZED",
        change_id="chg-001",
        owner_id="owner:primary",
        decision="ALLOW",
        previous_hash=first.record_hash,
    )
    assert verify_chain([first, second]) is True
    tampered = second.__class__(**{**second.__dict__, "decision": "DENY"})
    assert verify_chain([first, tampered]) is False
