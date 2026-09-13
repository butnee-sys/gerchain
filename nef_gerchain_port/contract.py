"""Versioned data contracts crossing the NEF–GerChain external boundary."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

PORT_VERSION = "1.0"


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
class EscrowRequest:
    escrow_id: str
    amount: int
    currency: str = "MNT"
    settlement_provider: str = "NEF"


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
