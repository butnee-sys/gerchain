"""Inbound application API for the EXIM Escrow Port."""

from typing import Any, Dict

from .contract import AssetImportRequest, ContractImportRequest, EscrowRequest, EvidenceImportRequest
from .gerchain_adapter import EscrowEngine, EscrowRecord, IndependentVerifier, WitnessChain
from .nef_adapter import NEFStateEngine


def _require_integer_money(value: Any, *, field_name: str) -> int:
    """Enforce integer-only monetary values at the external port boundary."""
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
