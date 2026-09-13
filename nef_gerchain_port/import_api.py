"""Inbound application API for the EXIM Escrow Port."""

from typing import Any, Dict, Mapping

from dee_security import AuthorizationPolicy, ReleaseAuthorization, RootOfTrust
from dee_security.signing import SignedRelease

from .contract import AssetImportRequest, ContractImportRequest, EscrowRequest, EvidenceImportRequest
from .gerchain_adapter import EscrowEngine, EscrowRecord, IndependentVerifier, WitnessChain
from .nef_adapter import NEFStateEngine


def _require_integer_money(value: Any, *, field_name: str) -> int:
    """Enforce the DEE money boundary: amounts must be real integers, not floats/bools."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer amount")
    return value


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
        amount = _require_integer_money(request.amount, field_name="escrow amount")
        if amount <= 0:
            raise ValueError("escrow amount must be a positive integer")
        if request.settlement_provider != "NEF":
            raise ValueError("Unsupported settlement provider")
        return EscrowEngine(escrow_id=request.escrow_id, amount=amount,
                            currency=request.currency, witness_chain=witness_chain)

    def restore_escrow(self, *, escrow_id: str, amount: int, currency: str, state: Dict[str, Any],
                       records: list[Dict[str, Any]], witness_chain: WitnessChain) -> EscrowEngine:
        """Reconstruct an escrow through the external port boundary."""
        amount = _require_integer_money(amount, field_name="escrow amount")
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
        """Controlled SHUUD release transition through the EXIM Port.

        This compatibility path preserves the existing application contract.
        Security-sensitive production release must use ``release_escrow_authorized``.
        """
        if not authorization_hash:
            raise ValueError("authorization_hash is required")
        if not incident_id:
            raise ValueError("incident_id is required")
        if not rule_version:
            raise ValueError("rule_version is required")
        state = escrow.get_state()
        if state.get("state") != "LOCKED":
            raise ValueError(f"SHUUD release requires LOCKED escrow, got {state.get('state')}")
        release_evidence = evidence or {
            "incident_id": incident_id,
            "authorization_hash": authorization_hash,
            "rule_version": rule_version,
        }
        return escrow.transition("RELEASED", timestamp, release_evidence)

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
        """Perform LOCKED -> RELEASED only after DEE release authorization.

        The security gate verifies protected paths, manifest integrity, exact
        commit binding, owner identity, Ed25519 release signature, and replay
        protection before the authoritative escrow state transition occurs.
        """
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
        return escrow.transition("RELEASED", timestamp, release_evidence)

    def verifier(self) -> IndependentVerifier:
        return IndependentVerifier()

    def nef_state_engine(self, *, static_pool: float = 0.0, dynamic_limit: float = 0.0) -> NEFStateEngine:
        return NEFStateEngine(static_pool=static_pool, dynamic_limit=dynamic_limit)

    def validate_asset(self, request: AssetImportRequest) -> bool:
        return bool(request.asset_id and request.asset_type and request.value_nef >= 0)

    def validate_contract(self, request: ContractImportRequest) -> bool:
        return bool(request.contract_id and request.parties)

    def validate_evidence(self, request: EvidenceImportRequest) -> bool:
        return bool(request.evidence_id and request.case_id)
