import base64

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from connectors import EXIMConnectorAdapter
from dee_security.audit import append_record, verify_chain
from dee_security.gateway_governance import GatewayAccessRequest, authorize_gateway_access
from dee_security.root_of_trust import RootOfTrust
from gateway import OpenMultiConnectorGateway


def _root() -> RootOfTrust:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes_raw()
    return RootOfTrust("OWNER-E2E", base64.b64encode(public_key).decode("ascii"))


def test_dee_runtime_path_gateway_to_exim_to_escrow_and_audit():
    root = _root()
    trinity = {"trust": True, "transparency": True, "performance": True}
    gateway = OpenMultiConnectorGateway()
    connector = EXIMConnectorAdapter()
    gateway.register(connector, credential="e2e-secret", allowed_operations={"create_witness_chain", "create_escrow"})

    authorize_gateway_access(
        root=root,
        request=GatewayAccessRequest(
            gateway_id="I2B-E2E",
            connector_id="EXIM",
            operation="create_witness_chain",
            request_id="REQ-WIT-1",
            actor_id="OWNER-E2E",
            nonce="nonce-wit-1",
        ),
        trinity_proof=trinity,
    )
    witness = gateway.dispatch(
        "EXIM",
        "create_witness_chain",
        credential="e2e-secret",
        nonce="nonce-wit-1",
        initial_state={"case_id": "CASE-E2E"},
        manifest={"case_id": "CASE-E2E", "version": 1},
        witness_id="W-E2E",
    )

    authorize_gateway_access(
        root=root,
        request=GatewayAccessRequest(
            gateway_id="I2B-E2E",
            connector_id="EXIM",
            operation="create_escrow",
            request_id="REQ-ESC-1",
            actor_id="OWNER-E2E",
            nonce="nonce-esc-1",
        ),
        trinity_proof=trinity,
    )
    escrow = gateway.dispatch(
        "EXIM",
        "create_escrow",
        credential="e2e-secret",
        nonce="nonce-esc-1",
        escrow_id="ESC-E2E",
        amount=2_000_000,
        currency="MNT",
        settlement_provider="NEF",
        witness_chain=witness,
    )
    escrow.transition("FUNDED", "2026-09-14T00:00:00Z", {"case_id": "CASE-E2E"})
    escrow.transition("LOCKED", "2026-09-14T00:00:01Z", {"case_id": "CASE-E2E"})

    records = [
        append_record(
            sequence=1,
            event="GATEWAY_AUTHORIZED",
            change_id="REQ-WIT-1",
            owner_id=root.owner_id,
            decision="ALLOW",
            stage="GATEWAY",
            connector_id="EXIM",
            request_id="REQ-WIT-1",
            operation="create_witness_chain",
            trinity=trinity,
        ),
        append_record(
            sequence=2,
            event="ESCROW_CREATED_AND_LOCKED",
            change_id="REQ-ESC-1",
            owner_id=root.owner_id,
            decision="ALLOW",
            stage="ESCROW",
            connector_id="EXIM",
            request_id="REQ-ESC-1",
            operation="create_escrow",
            previous_hash="PLACEHOLDER",
            trinity=trinity,
        ),
    ]
    # Rebind the second record to the actual first record hash without weakening
    # the audit verifier's chained-hash invariant.
    records[1] = append_record(
        sequence=2,
        event="ESCROW_CREATED_AND_LOCKED",
        change_id="REQ-ESC-1",
        owner_id=root.owner_id,
        decision="ALLOW",
        stage="ESCROW",
        connector_id="EXIM",
        request_id="REQ-ESC-1",
        operation="create_escrow",
        previous_hash=records[0].record_hash,
        trinity=trinity,
    )
    assert escrow.get_state()["state"] == "LOCKED"
    assert verify_chain(records)
    assert witness.entries
    assert gateway.audit_events()
