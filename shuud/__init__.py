"""SHUUD application layer for GerChain.

SHUUD must remain above the GerChain trust/audit core. It does not bypass
Witness, verification, deterministic state transitions, or escrow invariants.
"""

__all__ = ["incident", "verify", "shiid"]
