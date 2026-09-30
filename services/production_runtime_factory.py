"""Compatibility import for the canonical production runtime factory.

The authoritative implementation lives in gerchain_runtime_factory.
This module remains only to preserve existing import paths.
"""
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory

__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
