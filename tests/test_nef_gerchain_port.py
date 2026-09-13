from pathlib import Path

import pytest

from nef_gerchain_port.contract import (
    EXIM_PORT_VERSION,
    PORT_VERSION,
    AssetImportRequest,
    ContractImportRequest,
    EscrowRequest,
    EvidenceImportRequest,
    ExportedAsset,
    ExportedAudit,
    ExportedContract,
    ExportedEvidence,
    ExportedSettlement,
    ExportedStatus,
    PaymentRequest,
)
from nef_gerchain_port.export_api import ExternalPortExport
from nef_gerchain_port.import_api import ExternalPortImport


def test_exim_port_has_explicit_version():
    assert EXIM_PORT_VERSION == "1.0"
    assert PORT_VERSION == EXIM_PORT_VERSION


def test_external_port_can_create_witness_and_escrow():
    port = ExternalPortImport()
    witness = port.create_witness_chain(
        initial_state={"value": 0, "case_id": "CASE-001"},
        manifest={"purpose": "external-port-test"},
        witness_id="WITNESS-PORT-001",
    )
    escrow = port.create_escrow(EscrowRequest(escrow_id="ESCROW-PORT-001", amount=100), witness)
    assert escrow.get_state()["escrow_id"] == "ESCROW-PORT-001"
    assert escrow.get_state()["state"] == "CREATED"


def test_external_port_rejects_non_integer_money_amounts():
    port = ExternalPortImport()
    witness = port.create_witness_chain(initial_state={"value": 0}, manifest={}, witness_id="WITNESS-MONEY-001")
    with pytest.raises((TypeError, ValueError)):
        port.create_escrow(EscrowRequest(escrow_id="ESCROW-MONEY-001", amount=100.5), witness)


def test_external_port_rejects_non_positive_amounts():
    port = ExternalPortImport()
    witness = port.create_witness_chain(initial_state={"value": 0}, manifest={}, witness_id="WITNESS-MONEY-002")
    with pytest.raises(ValueError):
        port.create_escrow(EscrowRequest(escrow_id="ESCROW-MONEY-002", amount=0), witness)


def test_contract_money_boundary_rejects_bool_and_negative_values():
    with pytest.raises(TypeError):
        EscrowRequest(escrow_id="ESCROW-BOOL", amount=True)
    with pytest.raises(ValueError):
        PaymentRequest(escrow_id="ESCROW-NEG", amount=-1)
    with pytest.raises(ValueError):
        AssetImportRequest(asset_id="ASSET-001", asset_type="LIVESTOCK", value_nef=0)


def test_contract_boundary_rejects_unsupported_currency_and_provider():
    with pytest.raises(ValueError):
        EscrowRequest(escrow_id="ESCROW-USD", amount=100, currency="USD")
    with pytest.raises(ValueError):
        PaymentRequest(escrow_id="ESCROW-BANK", amount=100, settlement_provider="BANK")


def test_import_contract_dtos_require_identifiers():
    with pytest.raises(ValueError):
        EvidenceImportRequest(evidence_id="", case_id="CASE-001", evidence={})
    with pytest.raises(ValueError):
        EvidenceImportRequest(evidence_id="EVID-001", case_id="", evidence={})
    with pytest.raises(ValueError):
        ContractImportRequest(contract_id="", parties=("PARTY-A",))
    with pytest.raises(ValueError):
        ContractImportRequest(contract_id="CONTRACT-001", parties=())
    with pytest.raises(ValueError):
        ContractImportRequest(contract_id="CONTRACT-001", parties=("",))


def test_external_port_can_restore_witness_and_escrow():
    port = ExternalPortImport()
    witness = port.create_witness_chain(
        initial_state={"value": 0}, manifest={"purpose": "recovery-test"}, witness_id="WITNESS-PORT-RECOVER"
    )
    bundle = {
        "manifest": witness.manifest,
        "manifest_hash": witness.manifest_hash,
        "witness_id": witness.witness_id,
        "initial_state": witness.initial_state,
        "entries": [],
    }
    restored_witness = port.restore_witness_chain(bundle)
    escrow = port.restore_escrow(
        escrow_id="ESCROW-PORT-RECOVER", amount=100, currency="MNT",
        state={"escrow_id": "ESCROW-PORT-RECOVER", "state": "CREATED"},
        records=[], witness_chain=restored_witness,
    )
    assert restored_witness.witness_id == "WITNESS-PORT-RECOVER"
    assert escrow.get_state()["state"] == "CREATED"


def test_external_port_exports_import_contracts():
    exporter = ExternalPortExport()
    asset = exporter.asset(
        asset_id="ASSET-PORT-001", asset_type="LIVESTOCK", value_nef=100_000,
        metadata={"source": "EXIM"},
    )
    contract = exporter.contract(
        contract_id="CONTRACT-PORT-001", parties=("SELLER", "BUYER"),
        terms={"delivery": "FOB"}, metadata={"source": "EXIM"},
    )
    assert isinstance(asset, ExportedAsset)
    assert asset.port_version == PORT_VERSION
    assert asset.value_nef == 100_000
    assert isinstance(contract, ExportedContract)
    assert contract.parties == ("SELLER", "BUYER")
    assert contract.terms["delivery"] == "FOB"


def test_exported_dtos_enforce_version_and_invariants():
    with pytest.raises(ValueError):
        ExportedStatus(port_version="9.0", status="OK")
    with pytest.raises(ValueError):
        ExportedAsset(port_version=PORT_VERSION, asset_id="ASSET", asset_type="LIVESTOCK", value_nef=0)
    with pytest.raises(ValueError):
        ExportedContract(port_version=PORT_VERSION, contract_id="CONTRACT", parties=())
    with pytest.raises(ValueError):
        ExportedEvidence(port_version=PORT_VERSION, evidence_id="EVID", case_id="CASE", evidence_hash="")
    with pytest.raises(ValueError):
        ExportedSettlement(
            port_version=PORT_VERSION, escrow_id="ESCROW", status="LOCKED", amount=100,
            currency="USD", settlement_provider="NEF",
        )
    with pytest.raises(ValueError):
        ExportedAudit(
            port_version=PORT_VERSION, reference_id="REF", event_type="EVENT", timestamp="",
        )


def test_exim_port_level_e2e_import_verify_release_export():
    port = ExternalPortImport()
    exporter = ExternalPortExport()

    asset = AssetImportRequest(
        asset_id="ASSET-E2E-001",
        asset_type="VEHICLE",
        value_nef=2_000_000,
        metadata={"source": "SHUUD"},
    )
    contract = ContractImportRequest(
        contract_id="CONTRACT-E2E-001",
        parties=("DRIVER", "INSURER"),
        terms={"release": "VERIFIED_PERFORMANCE"},
    )
    evidence = EvidenceImportRequest(
        evidence_id="EVID-E2E-001",
        case_id="CASE-E2E-001",
        evidence={"minor_incident": True, "verified": True},
    )

    assert port.validate_asset(asset) is True
    assert port.validate_contract(contract) is True
    assert port.validate_evidence(evidence) is True

    witness = port.create_witness_chain(
        initial_state={"case_id": evidence.case_id, "asset_id": asset.asset_id},
        manifest={"contract_id": contract.contract_id, "port_version": PORT_VERSION},
        witness_id="WITNESS-E2E-001",
    )
    escrow = port.create_escrow(
        EscrowRequest(
            escrow_id="ESCROW-E2E-001",
            amount=100_000,
            currency="MNT",
            settlement_provider="NEF",
        ),
        witness,
    )

    escrow.transition("FUNDED", "2026-09-13T15:00:00Z", {"evidence_id": evidence.evidence_id})
    escrow.transition("LOCKED", "2026-09-13T15:00:01Z", {"evidence_id": evidence.evidence_id})

    settlement_before_release = exporter.settlement_status(escrow)
    assert isinstance(settlement_before_release, ExportedSettlement)
    assert settlement_before_release.status == "LOCKED"
    assert settlement_before_release.amount == 100_000
    assert settlement_before_release.currency == "MNT"
    assert settlement_before_release.settlement_provider == "NEF"

    port.release_escrow(
        escrow,
        incident_id=evidence.case_id,
        authorization_hash="AUTH-E2E-001",
        rule_version="SHUUD-1.0",
        timestamp="2026-09-13T15:00:02Z",
        evidence={
            "evidence_id": evidence.evidence_id,
            "evidence_hash": "EVIDENCE-HASH-E2E-001",
            "verified_performance": True,
        },
    )

    final_status = exporter.escrow_status(escrow)
    exported_evidence = exporter.evidence(
        evidence_id=evidence.evidence_id,
        case_id=evidence.case_id,
        evidence_hash="EVIDENCE-HASH-E2E-001",
        metadata={"verified": True},
    )
    exported_audit = exporter.audit_event(
        reference_id=evidence.case_id,
        event_type="ESCROW_RELEASED",
        timestamp="2026-09-13T15:00:02Z",
        evidence_hash=exported_evidence.evidence_hash,
        data={"escrow_id": "ESCROW-E2E-001"},
    )

    assert final_status.status == "RELEASED"
    assert final_status.reference_id == "ESCROW-E2E-001"
    assert exported_evidence.port_version == PORT_VERSION
    assert exported_audit.event_type == "ESCROW_RELEASED"
    assert exported_audit.evidence_hash == "EVIDENCE-HASH-E2E-001"
    assert len(escrow.records) == 3


def test_external_port_exports_versioned_evidence():
    exported = ExternalPortExport().evidence(
        evidence_id="EVID-PORT-001",
        case_id="CASE-PORT-001",
        evidence_hash="abc123",
        metadata={"source": "SHUUD"},
    )
    assert exported.port_version == PORT_VERSION
    assert exported.evidence_id == "EVID-PORT-001"
    assert exported.case_id == "CASE-PORT-001"
    assert exported.evidence_hash == "abc123"
    assert exported.metadata["source"] == "SHUUD"


def test_external_port_exports_only_port_status():
    port = ExternalPortImport()
    witness = port.create_witness_chain(initial_state={"value": 0}, manifest={"purpose": "external-port-test"},
                                        witness_id="WITNESS-PORT-002")
    exported = ExternalPortExport().witness_status(witness)
    assert exported.port_version == PORT_VERSION
    assert exported.reference_id == "WITNESS-PORT-002"
    assert exported.data["entry_count"] == 0


def test_external_port_evidence_export_requires_identifiers():
    exporter = ExternalPortExport()
    with pytest.raises(ValueError):
        exporter.evidence(evidence_id="", case_id="CASE-001")
    with pytest.raises(ValueError):
        exporter.evidence(evidence_id="EVID-001", case_id="")


def test_core_modules_are_not_imported_by_shuud_integration():
    root = Path(__file__).resolve().parents[1]
    integration = (root / "shuud" / "integration.py").read_text(encoding="utf-8")
    forbidden = ("from escrow", "from witness", "from verifier", "from network.nef")
    assert not any(token in integration for token in forbidden)
