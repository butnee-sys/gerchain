"""
GerChain V77.0
Escrow transition record.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EscrowRecord:
    """Эскроу төлөвийн нэг өөрчлөгдөшгүй бүртгэл."""

    escrow_id: str
    sequence: int
    previous_state: str
    new_state: str
    amount: int
    currency: str
    transition_hash: str
    witness_event_hash: str
    witness_id: str