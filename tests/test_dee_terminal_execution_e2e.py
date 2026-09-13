import base64
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from connectors import EXIMConnectorAdapter
from dee_security.audit import append_record, verify_chain
from dee_security.authorization import AuthorizationPolicy
from dee_security.gateway_governance import GatewayAccessRequest, authorize_gateway_access
from dee_security.manifest import build_manifest
from dee_security.release_policy import ReleaseAuthorization
from dee_security.root_of_trust import RootOfTrust
from dee_security.signing import sign_release
from gateway import OpenMultiConnectorGateway
from money.engine import MoneyEngine
from money.ledger import MoneyLedger


def _root_and_key():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    root = RootOfTrust("OWNER-TERMINAL-E2E", base64.b64encode(public_key).decode("ascii"))
    return root, private_key


def test_locked_escrow_to_governed_settlement_and_audit():
    root, _ = _root_and_key()
    trinity = {"trust": True, "transparency": True, "performance": True}

    gateway = OpenMultiConnectorGateway()
    connector = EXIMConnectorAdapter()
    gateway.register(
        connector,
        credential="terminal-e2e-secret",
        allowed_operations={"create_witness_chain", "create_escrow"},
    )

    authorize_gateway_access(
        root=root,
        request=GatewayAccessRequest(
            gateway_id="I2B-TERMINAL-E2E",
            connector_id="EXIM",
            operation="create_witness_chain",
            request_id="REQ-TERM-WIT",
            actor_id=root.owner_id,
            nonce="nonce-term-wit",
        ),
        trinity_proof=trinity,
    )
    witness = gateway.dispatch(
        "EXIM",
        "create_witness_chain",
        credential="terminal-e2e-secret",
        nonce="nonce-term-wit",
        initial_state={"case_id": "CASE-TERM"},
        manifest={"case_id": "CASE-TERM", "version": 1},
        witness_id="W-TERM",
    )

    authorize_gateway_access(
        root=root,
        request=GatewayAccessRequest(
            gateway_id="I2B-TERMINAL-E2E",
            connector_id="EXIM",
            operation="create_escrow",
            request_id="REQ-TERM-ESC",
            actor_id=root.owner_id,
            nonce="nonce-term-esc",
        ),
        trinity_proof=trinity,
    )
    escrow = gateway.dispatch(
        "EXIM",
        "create_escrow",
        credential="terminal-e2e-secret",
        nonce="nonce-term-esc",
        escrow_id="ESC-TERM",
        amount=2_000_000,
        currency="MNT",
        settlement_provider="NEF",
        witness_chain=witness,
    )
    escrow.transition("FUNDED", "2026-09-14T00:00:10Z", {"case_id": "CASE-TERM"})
    escrow.transition("LOCKED", "2026-09-14T00:00:11Z", {"case_id": "CASE-TERM"})

    ledger = MoneyLedger("MNT")
    ledger.create_account("ESCROW_POOL", 2_000_000)
    ledger.create_account("BENEFICIARY", 0)
    money = MoneyEngine(ledger, escrow)

    record = money.atomic_settlement(
        transaction_id="TX-TERM-1",
        target_state="RELEASED",
        source="ESCROW_POOL",
        destination="BENEFICIARY",
        amount=2_000_000,
        timestamp="2026-09-14T00:00:12Z",
        evidence={"case_id": "CASE-TERM", "decision": "RELEASE"},
        root=root,
        owner_id=root.owner_id,
        authorized=True,
        evidence_verified=True,
        trinity_proof=trinity,
    )

    assert escrow.get_state()["state"] == "RELEASED"
    assert ledger.get_balance("ESCROW_POOL") == 0
    assert ledger.get_balance("BENEFICIARY") == 2_000_000
    assert money.records[-1] == record
    assert witness.entries

    first = append_record(
        sequence=1,
        event="GATEWAY_AUTHORIZED",
        change_id="REQ-TERM-WIT",
        owner_id=root.owner_id,
        decision="ALLOW",
        stage="GATEWAY",
        connector_id="EXIM",
        request_id="REQ-TERM-WIT",
        operation="create_witness_chain",
        trinity=trinity,
    )
    second = append_record(
        sequence=2,
        event="ATOMIC_SETTLEMENT_RELEASED",
        change_id="TX-TERM-1",
        owner_id=root.owner_id,
        decision="ALLOW",
        stage="SETTLEMENT",
        connector_id="EXIM",
        request_id="REQ-TERM-ESC",
        operation="atomic_settlement",
        previous_hash=first.record_hash,
        trinity=trinity,
    )
    assert verify_chain([first, second])


def test_governed_release_signature_is_real_and_manifest_bound():
    root, private_key = _root_and_key()
    policy = AuthorizationPolicy()
    protected_paths = ["dee_security/e2e_governance.py"]
    manifest = build_manifest(
        version=1,
        commit_sha="E2E-COMMIT",
        protected_paths=protected_paths,
        artifact_hashes={"dee_security/e2e_governance.py": hashlib.sha256(b"e2e").hexdigest()},
    )
    release = sign_release(
        private_key,
        owner_id=root.owner_id,
        release_id="REL-TERMINAL-E2E",
        commit_sha=manifest["commit_sha"],
        manifest_hash=manifest["manifest_hash"],
    )
    gate = ReleaseAuthorization()
    gate.authorize(root=root, policy=policy, release=release, manifest=manifest)

    assert release.owner_id == root.owner_id
    assert release.manifest_hash == manifest["manifest_hash"]
