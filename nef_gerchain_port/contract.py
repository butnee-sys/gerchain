"""Versioned contracts for the EXIM Escrow Port.

The package name is retained for compatibility, but this boundary is the v1
implementation of the EXIM Escrow Port between the NEF–GerChain Digital
Escrow Ecosystem and Open Systems.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

EXIM_PORT_VERSION = "1.0"
# Compatibility alias for existing callers.
PORT_VERSION = EXIM_PORT_VERSION


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


@dataclass(frozen=True)
class EscrowRequest:
    escrow_id: str
    amount: int
    currency: str = "MNT"
    settlement_provider: str = "NEF"
    release_condition: str = "VERIFIED_PERFORMANCE"


@dataclass(frozen=True)
class PaymentRequest:
    escrow_id: str
    amount: int
    currency: str = "MNT"
    settlement_provider: str = "NEF"
    evidence: Any = None


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


@dataclass(frozen=True)
class ExportedAudit:
    port_version: str
    reference_id: str
    event_type: str
    timestamp: str
    evidence_hash: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
