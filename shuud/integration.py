"""SHUUD integration boundary for the NEF–GerChain ecosystem.

SHUUD is the application product.  GerChain remains the authoritative
infrastructure for escrow, witness, and independent verification.  All
SHUUD-side access to those core engines should pass through this module so the
product boundary stays explicit and testable.
"""

from escrow.engine import EscrowEngine
from escrow.record import EscrowRecord
from verifier.independent_verifier import IndependentVerifier
from witness.chain import WitnessChain

__all__ = [
    "EscrowEngine",
    "EscrowRecord",
    "IndependentVerifier",
    "WitnessChain",
]
