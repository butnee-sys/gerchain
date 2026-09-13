from pathlib import Path

from nef_gerchain_port.contract import PORT_VERSION, EscrowRequest
from nef_gerchain_port.export_api import ExternalPortExport
from nef_gerchain_port.import_api import ExternalPortImport


def test_external_port_has_explicit_version():
    assert PORT_VERSION == "1.0"


def test_external_port_can_create_witness_and_escrow():
    port = ExternalPortImport()
    witness = port.create_witness_chain(
        initial_state={"value": 0, "case_id": "CASE-001"},
        manifest={"purpose": "external-port-test"},
        witness_id="WITNESS-PORT-001",
    )
    escrow = port.create_escrow(
        EscrowRequest(
            escrow_id="ESCROW-PORT-001",
            amount=100,
        ),
        witness,
    )

    assert escrow.get_state()["escrow_id"] == "ESCROW-PORT-001"
    assert escrow.get_state()["state"] == "CREATED"


def test_external_port_exports_only_port_status():
    port = ExternalPortImport()
    witness = port.create_witness_chain(
        initial_state={"value": 0},
        manifest={"purpose": "external-port-test"},
        witness_id="WITNESS-PORT-002",
    )
    exported = ExternalPortExport().witness_status(witness)

    assert exported.port_version == PORT_VERSION
    assert exported.reference_id == "WITNESS-PORT-002"
    assert exported.data["entry_count"] == 0


def test_core_modules_are_not_imported_by_shuud_integration():
    root = Path(__file__).resolve().parents[1]
    integration = (root / "shuud" / "integration.py").read_text(encoding="utf-8")

    forbidden = (
        "from escrow",
        "from witness",
        "from verifier",
        "from network.nef",
    )
    assert not any(token in integration for token in forbidden)
