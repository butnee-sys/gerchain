"""Boundary tests for the SHUUD application and EXIM Escrow Port."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from nef_gerchain_port import (
    EXIM_PORT_VERSION,
    EscrowRequest,
    EvidenceImportRequest,
    ExternalPortImport,
    ExportedAudit,
    ExportedSettlement,
    ExportedStatus,
    PaymentRequest,
)


ROOT = Path(__file__).resolve().parents[1]
SHUUD_DIR = ROOT / "shuud"
FORBIDDEN_IMPORT_ROOTS = {
    "gerchain",
    "gerchain_core",
    "gerchain_runtime",
    "ledger",
    "money_engine",
    "escrow_engine",
    "witness_chain",
}


def _imports_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_shuud_has_no_direct_gerchain_core_imports() -> None:
    """SHUUD may integrate with infrastructure only through the EXIM Port."""
    violations: list[tuple[str, str]] = []
    for path in SHUUD_DIR.glob("*.py"):
        for module in _imports_in(path):
            root = module.split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                violations.append((path.name, module))

    assert not violations, f"SHUUD direct core imports found: {violations}"


def test_shuud_uses_exim_port_not_legacy_integration_module() -> None:
    """The migration shim must not become an application dependency again."""
    violations: list[str] = []
    for path in SHUUD_DIR.glob("*.py"):
        if path.name == "integration.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "shuud.integration" in text or "from .integration" in text:
            violations.append(path.name)

    assert not violations, f"Legacy SHUUD integration dependency found: {violations}"


def test_exim_port_is_the_published_shuud_boundary() -> None:
    """The published boundary exposes versioned contracts and controlled access."""
    assert EXIM_PORT_VERSION
    assert EscrowRequest.__module__.startswith("nef_gerchain_port")
    assert EvidenceImportRequest.__module__.startswith("nef_gerchain_port")
    assert PaymentRequest.__module__.startswith("nef_gerchain_port")
    assert ExternalPortImport.__module__.startswith("nef_gerchain_port")
    assert ExportedStatus.__module__.startswith("nef_gerchain_port")
    assert ExportedSettlement.__module__.startswith("nef_gerchain_port")
    assert ExportedAudit.__module__.startswith("nef_gerchain_port")


def test_exim_port_rejects_float_money_at_boundary() -> None:
    """Money entering the Port must be integer MNT units, never floating point."""
    port = ExternalPortImport()
    request = EscrowRequest(
        escrow_id="SHUUD-BOUNDARY-001",
        amount=1000.5,
        currency="MNT",
        settlement_provider="NEF",
    )
    with pytest.raises(TypeError, match="integer amount"):
        port.create_escrow(request, object())
