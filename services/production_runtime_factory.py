"""Compatibility import for the canonical GerChain production runtime factory.

The authoritative implementation lives in services.gerchain_runtime_factory.
This module exists only to preserve existing import paths during the migration.
"""
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory

__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
