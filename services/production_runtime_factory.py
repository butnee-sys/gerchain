"""Compatibility export for the canonical GerChain production runtime factory.

The production runtime has one authoritative construction path:
services.gerchain_runtime_factory. This module is retained only for
backward-compatible imports and must not define a second factory.
"""

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)

__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
