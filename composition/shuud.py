"""SHUUD composition root.

Concrete connector registration is intentionally kept here, outside the
application adapter. This is the bootstrap/composition boundary for the
SHUUD product and is the only place that wires a concrete connector into the
I2B gateway.
"""

import os

from application_adapters import SHUUDApplicationAdapter
from connectors import EXIMConnectorAdapter
from gateway import OpenMultiConnectorGateway


SHUUD_OPERATIONS = frozenset(
    {
        "export_status",
        "export_escrow_status",
        "export_settlement_status",
        "export_evidence_status",
        "export_audit_event",
        "create_witness_chain",
        "restore_witness_chain",
        "create_escrow",
        "restore_escrow",
        "verifier",
        "release_escrow",
        "release_escrow_authorized",
    }
)


def build_shuud_application_adapter(*, credential: str | None = None) -> SHUUDApplicationAdapter:
    """Build the governed SHUUD → Gateway → EXIM composition."""
    resolved = (credential if credential is not None else os.getenv("SHUUD_EXIM_CREDENTIAL", "")).strip()
    if not resolved:
        raise RuntimeError("SHUUD_EXIM_CREDENTIAL is required")

    gateway = OpenMultiConnectorGateway()
    gateway.register(
        EXIMConnectorAdapter(),
        credential=resolved,
        allowed_operations=SHUUD_OPERATIONS,
    )
    return SHUUDApplicationAdapter(gateway=gateway, credential=resolved)


__all__ = ["SHUUD_OPERATIONS", "build_shuud_application_adapter"]
