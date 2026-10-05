"""Compatibility import for the canonical production runtime factory.

The authoritative implementation lives in :mod:`services.gerchain_runtime_factory`.
This module remains as a stable import path for existing tests and callers.
"""

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory

__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
