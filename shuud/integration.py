"""Deprecated SHUUD integration shim.

Legacy callers are routed through the SHUUD application adapter. This module
contains no direct EXIM Port, NEF, or GerChain imports and remains only as a
migration marker while callers move to ``application_adapters``.
"""

from application_adapters import SHUUDApplicationAdapter


# Compatibility names only; the application adapter is the controlled boundary.
ExternalPortImport = SHUUDApplicationAdapter
ExternalPortExport = SHUUDApplicationAdapter

__all__ = ["ExternalPortImport", "ExternalPortExport"]
