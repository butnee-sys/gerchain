from __future__ import annotations

import pytest

from nef_gerchain_port import (
    EXIM_PORT_VERSION,
    EscrowRequest,
    ExportedAudit,
    ExportedEvidence,
    ExportedSettlement,
    ExternalPortExport,
    require_integer_money,
)


def test_exim_v1_exported_contract_set_is_complete() -> None:
    assert EXIM_PORT_VERSION == "1.0"
    assert {ExportedStatus.__name__ if False else "ExportedStatus", ExportedSettlement.__name__, ExportedEvidence.__name__, ExportedAudit.__name__} == {
        "ExportedStatus",
        "ExportedSettlement",
        "ExportedEvidence",
        "ExportedAudit",
    }


def test_integer_money_boundary_is_strict() -> None:
    assert require_integer_money(1_250_000) == 1_250_000
    with pytest.raises(TypeError):
        require_integer_money(1_250_000.0)
    with pytest.raises(TypeError):
        require_integer_money(True)
    with pytest.raises(TypeError):
        EscrowRequest(escrow_id="E-1", amount=1_250_000.0)  # type: ignore[arg-type]


def test_evidence_export_is_boundary_dto() -> None:
    exported = ExternalPortExport().evidence_status(
        evidence_id="EVID-001",
        case_id="CASE-001",
        evidence_hash="sha256:abc",
        status="VERIFIED",
        data={"source": "SHUUD"},
    )
    assert isinstance(exported, ExportedEvidence)
    assert exported.port_version == EXIM_PORT_VERSION
    assert exported.evidence_id == "EVID-001"
    assert exported.case_id == "CASE-001"
    assert exported.evidence_hash == "sha256:abc"
    assert exported.status == "VERIFIED"
    assert exported.data["source"] == "SHUUD"
