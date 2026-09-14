from pathlib import Path

import pytest

from nef_gerchain_port.contract import EXIM_PORT_VERSION, PORT_VERSION, EscrowRequest
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


def test_external_port_exports_only_port_status():
    port = ExternalPortImport()
    witness = port.create_witness_chain(initial_state={"value": 0}, manifest={"purpose": "external-port-test"},
                                        witness_id="WITNESS-PORT-002")
    exported = ExternalPortExport().witness_status(witness)
    assert exported.port_version == PORT_VERSION
    assert exported.reference_id == "WITNESS-PORT-002"
    assert exported.data["entry_count"] == 0


def test_core_modules_are_not_imported_by_shuud_integration():
    root = Path(__file__).resolve().parents[1]
    integration_files = (
        root / "apps" / "shuud" / "integration" / "shuud_exim_flow.py",
        root / "apps" / "shuud" / "integration" / "shuud_governed_flow.py",
    )
    forbidden = ("from escrow", "from witness", "from verifier", "from network.nef")
    for integration in integration_files:
        assert integration.is_file()
        content = integration.read_text(encoding="utf-8")
        assert not any(token in content for token in forbidden)
