"""Deprecated SHUUD integration shim.

SHUUD code must use ``nef_gerchain_port`` directly. This module intentionally
contains no GerChain or NEF imports and remains only as a migration marker.
"""

from nef_gerchain_port import ExternalPortExport, ExternalPortImport


__all__ = ["ExternalPortImport", "ExternalPortExport"]
