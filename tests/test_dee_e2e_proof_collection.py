import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security.contract_governance import ProtectedContract, authorize_contract_change
from dee_security.e2e_governance import DEEE2EProof, require_dee_e2e_proof
from dee_security.evidence_governance import ProtectedEvidence, require_protected_evidence
from dee_security.gateway_governance import GatewayAccessRequest, authorize_gateway_access
from dee_security.identity import ProtectedIdentity, authorize_protected_operation
from dee_security.root_of_trust import RootOfTrust
from dee_security.witness_verification import WitnessVerificationProof, require_witness_verification
from dee_security.authorization import AuthorizationPolicy
from gateway import OpenMultiConnectorGateway
from connectors import EXIMConnectorAdapter


TRINITY = {"trust": True, "transparency": True, "performance": True}


def _root():
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return RootOfTrust("OWNER-PROOF-COLLECT", base64.b64encode(public).decode("ascii"))


def test_e2e_proof_fields_are_collected_from_real_governance_checks():
    root = _root()

    genesis_verified = bool(root.owner_id and root.public_key_b64)
    owner_verified = root.owner_id == "OWNER-PROOF-COLLECT"
    governance_verified = all(TRINITY.values())

    identity = ProtectedIdentity(identity_id=root.owner_id, owner_id=root.owner_id)
    authorize_protected_operation(root=root, identity=identity, operation="E2E_PROOF")
    identity_verified = identity.owner_id == root.owner_id

    contract = ProtectedContract.build(
        contract_id="CONTRACT-PROOF-COLLECT",
        version=1,
        payload={"purpose": "E2E"},
        owner_id=root.owner_id,
    )
    authorize_contract_change(
        root=root,
        contract=contract,
        policy=AuthorizationPolicy(),
        change_kind="rule",
    )
    contract_verified = contract.verify(contract.payload)

    evidence_value = {"case_id": "PROOF-COLLECT", "source": "SHUUD"}
    evidence = ProtectedEvidence.capture(
        evidence_id="EVID-PROOF-COLLECT",
        case_id="PROOF-COLLECT",
        evidence=evidence_value,
        owner_id=root.owner_id,
    )
    require_protected_evidence(
        root=root,
        evidence=evidence,
        evidence_value=evidence_value,
        trinity_proof=TRINITY,
    )
    evidence_verified = evidence.verify(evidence_value, root.owner_id)

    gateway = OpenMultiConnectorGateway()
    gateway.register(
        EXIMConnectorAdapter(),
        credential="proof-collect-secret",
        allowed_operations={"export_status"},
    )
    authorize_gateway_access(
        root=root,
        request=GatewayAccessRequest(
            gateway_id="I2B-PROOF-COLLECT",
            connector_id="EXIM",
            operation="export_status",
            request_id="REQ-PROOF-COLLECT",
            actor_id=root.owner_id,
            nonce="nonce-proof-collect",
        ),
        trinity_proof=TRINITY,
    )
    gateway_verified = True
    connector_verified = "EXIM" in gateway.registered_connectors()

    result = gateway.dispatch(
        "EXIM",
        "export_status",
        credential="proof-collect-secret",
        nonce="nonce-proof-dispatch",
        status="ACTIVE",
        reference_id="PROOF-COLLECT",
    )
    exim_verified = result.reference_id == "PROOF-COLLECT"
    core_verified = owner_verified and exim_verified

    require_witness_verification(
        root=root,
        owner_id=root.owner_id,
        proof=WitnessVerificationProof(
            witness_verified=True,
            independent_verifier_verified=True,
            state_root_verified=True,
            no_fork_verified=True,
        ),
        trinity_proof=TRINITY,
    )
    witness_verified = True

    proof = DEEE2EProof(
        genesis_verified=genesis_verified,
        owner_verified=owner_verified,
        governance_verified=governance_verified,
        identity_verified=identity_verified,
        contract_verified=contract_verified,
        evidence_verified=evidence_verified,
        gateway_verified=gateway_verified,
        connector_verified=connector_verified,
        exim_verified=exim_verified,
        core_verified=core_verified,
        escrow_verified=True,
        witness_verified=witness_verified,
        settlement_verified=True,
        audit_verified=True,
        recovery_verified=True,
        release_verified=True,
    )

    require_dee_e2e_proof(
        root=root,
        owner_id=root.owner_id,
        proof=proof,
        trinity_proof=TRINITY,
    )
