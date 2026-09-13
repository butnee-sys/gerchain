"""Versioned contracts for the EXIM Escrow Port.

The package name is retained for compatibility, but this boundary is the v1
implementation of the EXIM Escrow Port between the NEF–GerChain Digital
Escrow Ecosystem and Open Systems.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

EXIM_PORT_VERSION = "1.0"
PORT_VERSION = EXIM_PORT_VERSION


def require_integer_money(value: Any, *, field_name: str = "amount") -> int:
    """Accept only integer monetary units; reject bool and floating point."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer amount")
    return value


@dataclass(frozen=True)
class AssetImportRequest:
    asset_id: str
    asset_type: str
    value_nef: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceImportRequest:
    evidence_id: str
    case_id: str
    evidence: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContractImportRequest:
    contract_id: str
    parties: tuple[str, ...]
    terms: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Canonical EXIM name; the Import suffix remains as a compatibility alias.
ContractRequest = ContractImportRequest


@dataclass(frozen=True)
class EscrowRequest:
    escrow_id: str
    amount: int
    currency: str = "MNT"
    settlement_provider: str = "NEF"
    release_condition: str = "VERIFIED_PERFORMANCE"

    def __post_init__(self) -> None:
        require_integer_money(self.amount, field_name="escrow amount")


@dataclass(frozen=True)
class PaymentRequest:
    escrow_id: str
    amount: int
    currency: str = "MNT"
    settlement_provider: str = "NEF"
    evidence: Any = None

    def __post_init__(self) -> None:
        require_integer_money(self.amount, field_name="payment amount")


@dataclass(frozen=True)
class ExportedStatus:
    port_version: str
    status: str
    reference_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExportedSettlement:
    port_version: str
    escrow_id: str
    status: str
    amount: int
    currency: str
    settlement_provider: str
    reference_id: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_integer_money(self.amount, field_name="settlement amount")


@dataclass(frozen=True)
class ExportedEvidence:
    port_version: str
    evidence_id: str
    case_id: str
    evidence_hash: Optional[str] = None
    status: str = "VERIFIED"
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExportedAudit:
    port_version: str
    reference_id: str
    event_type: str
    timestamp: str
    evidence_hash: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
