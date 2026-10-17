"""Backward-compatible import path for the canonical production runtime factory.

The authoritative implementation lives in services.gerchain_runtime_factory.
This module intentionally defines no second production runtime or value authority.
"""

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory

__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
