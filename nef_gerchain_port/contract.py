"""Versioned contracts for the EXIM Escrow Port.

The package name is retained for compatibility, but this boundary is the v1
implementation of the EXIM Escrow Port between the NEF–GerChain Digital
Escrow Ecosystem and Open Systems.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

EXIM_PORT_VERSION = "1.0"
PORT_VERSION = EXIM_PORT_VERSION
DEFAULT_CURRENCY = "MNT"
DEFAULT_SETTLEMENT_PROVIDER = "NEF"
DEFAULT_RELEASE_CONDITION = "VERIFIED_PERFORMANCE"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_port_version(value: str) -> str:
    value = _require_text(value, "port_version")
    if value != EXIM_PORT_VERSION:
        raise ValueError(f"unsupported port_version: {value}")
    return value


def _require_integer_money(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer amount")
    if value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _require_currency(value: str) -> str:
    value = _require_text(value, "currency").upper()
    if value != DEFAULT_CURRENCY:
        raise ValueError(f"unsupported currency: {value}")
    return value


def _require_provider(value: str) -> str:
    value = _require_text(value, "settlement_provider").upper()
    if value != DEFAULT_SETTLEMENT_PROVIDER:
        raise ValueError(f"unsupported settlement provider: {value}")
    return value


@dataclass(frozen=True)
class AssetImportRequest:
    asset_id: str
    asset_type: str
    value_nef: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.asset_id, "asset_id")
        _require_text(self.asset_type, "asset_type")
        _require_integer_money(self.value_nef, "value_nef")


@dataclass(frozen=True)
class EvidenceImportRequest:
    evidence_id: str
    case_id: str
    evidence: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.case_id, "case_id")


@dataclass(frozen=True)
class ContractImportRequest:
    contract_id: str
    parties: tuple[str, ...]
    terms: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.contract_id, "contract_id")
        if not self.parties or any(not isinstance(party, str) or not party.strip() for party in self.parties):
            raise ValueError("parties must contain at least one non-empty string")


@dataclass(frozen=True)
class EscrowRequest:
    escrow_id: str
    amount: int
    currency: str = DEFAULT_CURRENCY
    settlement_provider: str = DEFAULT_SETTLEMENT_PROVIDER
    release_condition: str = DEFAULT_RELEASE_CONDITION

    def __post_init__(self) -> None:
        _require_text(self.escrow_id, "escrow_id")
        _require_integer_money(self.amount, "amount")
        _require_currency(self.currency)
        _require_provider(self.settlement_provider)
        _require_text(self.release_condition, "release_condition")


@dataclass(frozen=True)
class PaymentRequest:
    escrow_id: str
    amount: int
    currency: str = DEFAULT_CURRENCY
    settlement_provider: str = DEFAULT_SETTLEMENT_PROVIDER
    evidence: Any = None

    def __post_init__(self) -> None:
        _require_text(self.escrow_id, "escrow_id")
        _require_integer_money(self.amount, "amount")
        _require_currency(self.currency)
        _require_provider(self.settlement_provider)


@dataclass(frozen=True)
class ExportedStatus:
    port_version: str
    status: str
    reference_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_port_version(self.port_version)
        _require_text(self.status, "status")
        if self.reference_id is not None:
            _require_text(self.reference_id, "reference_id")


@dataclass(frozen=True)
class ExportedAsset:
    port_version: str
    asset_id: str
    asset_type: str
    value_nef: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_port_version(self.port_version)
        _require_text(self.asset_id, "asset_id")
        _require_text(self.asset_type, "asset_type")
        _require_integer_money(self.value_nef, "value_nef")


@dataclass(frozen=True)
class ExportedContract:
    port_version: str
    contract_id: str
    parties: tuple[str, ...]
    terms: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_port_version(self.port_version)
        _require_text(self.contract_id, "contract_id")
        if not self.parties or any(not isinstance(party, str) or not party.strip() for party in self.parties):
            raise ValueError("parties must contain at least one non-empty string")


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
        _require_port_version(self.port_version)
        _require_text(self.escrow_id, "escrow_id")
        _require_text(self.status, "status")
        _require_integer_money(self.amount, "amount")
        _require_currency(self.currency)
        _require_provider(self.settlement_provider)
        if self.reference_id is not None:
            _require_text(self.reference_id, "reference_id")


@dataclass(frozen=True)
class ExportedEvidence:
    port_version: str
    evidence_id: str
    case_id: str
    evidence_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_port_version(self.port_version)
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.case_id, "case_id")
        if self.evidence_hash is not None:
            _require_text(self.evidence_hash, "evidence_hash")


@dataclass(frozen=True)
class ExportedAudit:
    port_version: str
    reference_id: str
    event_type: str
    timestamp: str
    evidence_hash: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_port_version(self.port_version)
        _require_text(self.reference_id, "reference_id")
        _require_text(self.event_type, "event_type")
        _require_text(self.timestamp, "timestamp")
        if self.evidence_hash is not None:
            _require_text(self.evidence_hash, "evidence_hash")
