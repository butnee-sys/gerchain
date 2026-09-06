"""
GerChain V78.0
Digital money movement record.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MoneyRecord:
    """Мөнгөний нэг шилжилтийн өөрчлөгдөшгүй бүртгэл."""

    transaction_id: str
    sequence: int
    source: str
    destination: str
    amount: int
    currency: str
    previous_source_balance: int
    new_source_balance: int
    previous_destination_balance: int
    new_destination_balance: int
    transfer_hash: str
    witness_event_hash: str
    witness_id: str