"""Compatibility import for the canonical production runtime factory.

The production runtime has one authoritative factory implementation.
"""
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory

__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
