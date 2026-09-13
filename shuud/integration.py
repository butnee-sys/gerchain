"""Compatibility shim for the SHUUD application.

The stable boundary is now ``nef_gerchain_port``.  Keep this module only as a
short-term compatibility surface while SHUUD callers are migrated.
"""

from nef_gerchain_port.gerchain_adapter import (
    EscrowEngine,
    EscrowRecord,
    IndependentVerifier,
    WitnessChain,
)

__all__ = [
    "EscrowEngine",
    "EscrowRecord",
    "IndependentVerifier",
    "WitnessChain",
]
