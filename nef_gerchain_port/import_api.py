"""Inbound application API for the EXIM Escrow Port."""

from typing import Any, Dict, Mapping

from dee_security import AuthorizationPolicy, ReleaseAuthorization, RootOfTrust
from dee_security.signing import SignedRelease

from .contract import (
    AssetImportRequest,
    ContractImportRequest,
    EscrowRequest,
    EvidenceImportRequest,
    PaymentRequest,
    require_integer_money,
)
from .gerchain_adapter import EscrowEngine, EscrowRecord, IndependentVerifier, WitnessChain
from .nef_adapter import NEFStateEngine


class ExternalPortImport:
    """Controlled inbound access for Open Systems."""

    def create_witness_chain(self, *, initial_state: Dict[str, Any], manifest: Dict[str, Any], witness_id: str,
                             initial_money_state: Dict[str, Any] | None = None) -> WitnessChain:
        return WitnessChain(initial_state=initial_state, manifest=manifest, witness_id=witness_id,
                            initial_money_state=initial_money_state)

    def restore_witness_chain(self, bundle: Dict[str, Any]) -> WitnessChain:
        """Reconstruct an authoritative witness chain from a persisted bundle."""
        if not isinstance(bundle, dict):
            raise ValueError("witness bundle must be a dictionary")
        return WitnessChain.from_dict(bundle)

    def create_escrow(self, request: EscrowRequest, witness_chain: WitnessChain) -> EscrowEngine:
        amount = require_integer_money(request.amount, field_name="escrow amount")
        if amount <= 0:
            raise ValueError("escrow amount must be a positive integer")
        if request.settlement_provider != "NEF":
            raise ValueError("Unsupported settlement provider")
        return EscrowEngine(escrow_id=request.escrow_id, amount=amount,
                            currency=request.currency, witness_chain=witness_chain)

    def restore_escrow(self, *, escrow_id: str, amount: int, currency: str, state: Dict[str, Any],
                       records: list[Dict[str, Any]], witness_chain: WitnessChain) -> EscrowEngine:
        """Reconstruct an escrow through the external port boundary."""
        amount = require_integer_money(amount, field_name="escrow amount")
        if amount <= 0:
            raise ValueError("escrow amount must be a positive integer")
        escrow = EscrowEngine(escrow_id=escrow_id, amount=amount, currency=currency,
                              witness_chain=witness_chain)
        escrow.state = state
        escrow.records = [EscrowRecord(**record) for record in records]
        return escrow

    def release_escrow(
        self,
        escrow: EscrowEngine,
        *,
        authorization_hash: str,
        incident_id: str,
        rule_version: str,
        timestamp: str,
        evidence: Any | None = None,
    ) -> Any:
        """Legacy release entrypoint; terminal execution is denied without DEE governance."""
        raise PermissionError(
            "Direct escrow release is disabled; use release_escrow_authorized through DEE governance."
        )

    def release_escrow_authorized(
        self,
        escrow: EscrowEngine,
        *,
        incident_id: str,
        authorization_hash: str,
        rule_version: str,
        timestamp: str,
        root: RootOfTrust,
        policy: AuthorizationPolicy,
        release: SignedRelease,
        manifest: Mapping[str, Any],
        gate: ReleaseAuthorization | None = None,
        evidence: Any | None = None,
    ) -> Any:
        """Perform LOCKED -> RELEASED only after DEE release authorization and Trinity proof."""
        if not authorization_hash:
            raise ValueError("authorization_hash is required")
        if not incident_id:
            raise ValueError("incident_id is required")
        if not rule_version:
            raise ValueError("rule_version is required")
        state = escrow.get_state()
        if state.get("state") != "LOCKED":
            raise ValueError(f"SHUUD release requires LOCKED escrow, got {state.get('state')}")

        from dee_security import authorize_release

        authorize_release(
            root=root,
            policy=policy,
            release=release,
            manifest=manifest,
            gate=gate,
        )
        release_evidence = evidence or {
            "incident_id": incident_id,
            "authorization_hash": authorization_hash,
            "rule_version": rule_version,
            "release_id": release.release_id,
            "manifest_hash": release.manifest_hash,
            "commit_sha": release.commit_sha,
        }
        return escrow.transition(
            "RELEASED",
            timestamp,
            release_evidence,
            root=root,
            owner_id=root.owner_id,
            authorized=True,
            evidence_verified=bool(release_evidence),
            trinity_proof={
                "trust": True,
                "transparency": bool(release_evidence),
                "performance": True,
            },
        )

    def create_payment(self, request: PaymentRequest) -> PaymentRequest:
        """Validate and return a canonical payment request at the Port boundary."""
        require_integer_money(request.amount, field_name="payment amount")
        if request.amount <= 0:
            raise ValueError("payment amount must be a positive integer")
        return request

    def verifier(self) -> IndependentVerifier:
        return IndependentVerifier()

    def nef_state_engine(self, *, static_pool: int = 0, dynamic_limit: int = 0) -> NEFStateEngine:
        """Create a NEF state adapter using integer monetary units only."""
        static_pool = require_integer_money(static_pool, field_name="static pool")
        dynamic_limit = require_integer_money(dynamic_limit, field_name="dynamic limit")
        if static_pool < 0 or dynamic_limit < 0:
            raise ValueError("NEF pools and limits cannot be negative")
        return NEFStateEngine(static_pool=static_pool, dynamic_limit=dynamic_limit)

    def validate_asset(self, request: AssetImportRequest) -> bool:
        require_integer_money(request.value_nef, field_name="asset value")
        return bool(request.asset_id and request.asset_type and request.value_nef >= 0)

    def validate_contract(self, request: ContractImportRequest) -> bool:
        return bool(request.contract_id and request.parties)

    def validate_evidence(self, request: EvidenceImportRequest) -> bool:
        return bool(request.evidence_id and request.case_id)
