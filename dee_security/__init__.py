"""DEE Root of Trust, governance, protection, and key lifecycle primitives."""

from .root_of_trust import RootOfTrust, SignedChange, SecurityError
from .authorization import AuthorizationPolicy, authorize_change
from .identity import ProtectedIdentity, authorize_protected_operation
from .contract_governance import ContractGovernanceError, ProtectedContract, authorize_contract_change
from .evidence_governance import EvidenceGovernanceError, ProtectedEvidence, canonical_evidence, evidence_hash, require_protected_evidence
from .core_access import CoreAccessError, CoreAccessRequest, authorize_core_access
from .exim_port_security import EXIMPortRequest, EXIMPortSecurityError, authorize_exim_port_request
from .escrow_trinity import EscrowExecutionProof, EscrowTrinityError, require_escrow_trinity
from .witness_verification import WitnessVerificationError, WitnessVerificationProof, require_witness_verification, verify_witness_bundle
from .connector_governance import ConnectorAccessRequest, ConnectorGovernanceError, authorize_connector_access
from .gateway_governance import GatewayAccessRequest, GatewayGovernanceError, authorize_gateway_access
from .connector_isolation import ConnectorIsolationError, ConnectorIsolationRequest, authorize_connector_isolation
from .manifest import build_manifest, canonical_manifest
from .release_policy import ReleaseAuthorization, authorize_release
from .key_management import OwnerKeyRecord, generate_owner_keypair, key_id_from_public_key, load_private_key, public_key_b64
from .signing import SignedRelease, sign_change, sign_release, verify_release
from .rotation import KeyRegistry, KeyRotationRequest, build_rotation_request
from .persistent_registry import PersistentKeyRegistry
from .runtime_governance import RuntimeAction, RuntimeAuthorization, RuntimeGovernance, RuntimeGovernanceError, RuntimeIdentity, RuntimeRole
from .recovery import RecoveryApproval, RecoveryAuthority, RecoveryDecision, RecoveryGovernance, RecoveryGovernanceError, RecoveryPolicy, RecoveryRequest, RecoveryRole, build_recovery_approval
from .genesis import GenesisAnchor, GenesisError, build_genesis_anchor, verify_genesis_anchor
from .trinity import TrinityDecision, TrinityDimension, TrinityError, evaluate_trinity, require_trinity

__all__ = [
    "AuthorizationPolicy", "RootOfTrust", "SecurityError", "SignedChange", "authorize_change",
    "ProtectedIdentity", "authorize_protected_operation", "ContractGovernanceError", "ProtectedContract", "authorize_contract_change",
    "EvidenceGovernanceError", "ProtectedEvidence", "canonical_evidence", "evidence_hash", "require_protected_evidence",
    "CoreAccessError", "CoreAccessRequest", "authorize_core_access", "EXIMPortRequest", "EXIMPortSecurityError", "authorize_exim_port_request",
    "EscrowExecutionProof", "EscrowTrinityError", "require_escrow_trinity", "WitnessVerificationError", "WitnessVerificationProof",
    "require_witness_verification", "verify_witness_bundle", "ConnectorAccessRequest", "ConnectorGovernanceError", "authorize_connector_access",
    "GatewayAccessRequest", "GatewayGovernanceError", "authorize_gateway_access", "ConnectorIsolationError", "ConnectorIsolationRequest", "authorize_connector_isolation",
    "authorize_release", "build_manifest", "canonical_manifest", "ReleaseAuthorization",
    "OwnerKeyRecord", "generate_owner_keypair", "key_id_from_public_key", "load_private_key", "public_key_b64", "SignedRelease", "sign_change", "sign_release", "verify_release",
    "KeyRegistry", "KeyRotationRequest", "build_rotation_request", "PersistentKeyRegistry", "RuntimeAction", "RuntimeAuthorization", "RuntimeGovernance", "RuntimeGovernanceError", "RuntimeIdentity", "RuntimeRole",
    "RecoveryApproval", "RecoveryAuthority", "RecoveryDecision", "RecoveryGovernance", "RecoveryGovernanceError", "RecoveryPolicy", "RecoveryRequest", "RecoveryRole", "build_recovery_approval",
    "GenesisAnchor", "GenesisError", "build_genesis_anchor", "verify_genesis_anchor", "TrinityDecision", "TrinityDimension", "TrinityError", "evaluate_trinity", "require_trinity",
]
