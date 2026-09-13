"""Inbound application API for the NEF–GerChain external boundary."""

from typing import Any, Dict

from .contract import (
    AssetImportRequest,
    EscrowRequest,
    EvidenceImportRequest,
)
from .gerchain_adapter import EscrowEngine, IndependentVerifier, WitnessChain
from .nef_adapter import NEFStateEngine


class ExternalPortImport:
    """Controlled inbound access for external applications."""

    def create_witness_chain(
        self,
        *,
        initial_state: Dict[str, Any],
        manifest: Dict[str, Any],
        witness_id: str,
        initial_money_state: Dict[str, Any] | None = None,
    ) -> WitnessChain:
        return WitnessChain(
            initial_state=initial_state,
            manifest=manifest,
            witness_id=witness_id,
            initial_money_state=initial_money_state,
        )

    def create_escrow(
        self,
        request: EscrowRequest,
        witness_chain: WitnessChain,
    ) -> EscrowEngine:
        if request.settlement_provider != "NEF":
            raise ValueError("Unsupported settlement provider")
        return EscrowEngine(
            escrow_id=request.escrow_id,
            amount=request.amount,
            currency=request.currency,
            witness_chain=witness_chain,
        )

    def verifier(self) -> IndependentVerifier:
        return IndependentVerifier()

    def nef_state_engine(
        self,
        *,
        static_pool: float = 0.0,
        dynamic_limit: float = 0.0,
    ) -> NEFStateEngine:
        return NEFStateEngine(
            static_pool=static_pool,
            dynamic_limit=dynamic_limit,
        )

    def validate_asset(self, request: AssetImportRequest) -> bool:
        return bool(request.asset_id and request.asset_type and request.value_nef >= 0)

    def validate_evidence(self, request: EvidenceImportRequest) -> bool:
        return bool(request.evidence_id and request.case_id)
