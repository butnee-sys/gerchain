from pathlib import Path


def test_canonical_dee_layers_exist_without_duplicate_adapter_packages():
    root = Path(__file__).resolve().parents[1]

    required = {
        "nef_gerchain_port": root / "nef_gerchain_port",
        "core_adapter_gerchain": root / "nef_gerchain_port" / "gerchain_adapter.py",
        "core_adapter_nef": root / "nef_gerchain_port" / "nef_adapter.py",
        "connector_adapter": root / "connectors" / "exim_adapter.py",
        "i2b_gateway": root / "gateway" / "open_multi_connector.py",
        "application_adapter": root / "application_adapters" / "shuud.py",
    }

    missing = [name for name, path in required.items() if not path.exists()]
    assert missing == [], f"Canonical DEE components missing: {missing}"

    # The existing implementation already provides these adapter boundaries.
    # Do not create duplicate parallel packages merely to mirror the diagram.
    assert not (root / "core_adapter").exists()
    assert not (root / "connector_adapter").exists()


def test_digital_economy_dee_nef_gerchain_relationship_is_mandatory():
    root = Path(__file__).resolve().parents[1]
    baseline = (root / "docs" / "DEE_ARCHITECTURE_BASELINE.md").read_text(
        encoding="utf-8"
    )
    connector_doc = (root / "docs" / "DEE_CONNECTOR_ARCHITECTURE.md").read_text(
        encoding="utf-8"
    )

    required_phrases = (
        "DIGITAL ECONOMY",
        "DEE",
        "NEF + GERCHAIN",
        "Digital Economy → DEE → NEF + GerChain",
    )
    for phrase in required_phrases:
        assert phrase in baseline, f"Missing mandatory architecture element: {phrase}"

    assert "NEF–GerChain" in connector_doc
    assert "Digital Economy" in baseline
    assert "Digital Escrow Ecosystem" in baseline


def test_external_participant_classes_are_not_core_implementation_packages():
    root = Path(__file__).resolve().parents[1]

    # Төр / Компани / Хувь хүн are external participant classes, not required
    # Python implementation packages inside the infrastructure boundary.
    participant_packages = (
        root / "tur",
        root / "tor",
        root / "company",
        root / "individual",
        root / "person",
    )
    assert all(not path.exists() for path in participant_packages)


def test_shuud_is_a_replaceable_application_prototype():
    root = Path(__file__).resolve().parents[1]
    application = root / "application_adapters" / "shuud.py"
    shuud_runtime = root / "shuud"

    assert application.is_file()
    assert shuud_runtime.is_dir()

    # SHUUD may depend on application/gateway boundaries, but must remain
    # replaceable and must not become a required infrastructure layer.
    text = application.read_text(encoding="utf-8")
    assert "OpenMultiConnectorGateway" in text
    assert "nef_gerchain_port" not in text


def test_architecture_baseline_documents_the_three_participant_classes():
    root = Path(__file__).resolve().parents[1]
    baseline = root / "docs" / "DEE_ARCHITECTURE_BASELINE.md"
    connector_doc = root / "docs" / "DEE_CONNECTOR_ARCHITECTURE.md"

    baseline_text = baseline.read_text(encoding="utf-8")
    connector_text = connector_doc.read_text(encoding="utf-8")

    for participant in ("ТӨР", "КОМПАНИ", "ХУВЬ ХҮН"):
        assert participant in baseline_text
        assert participant in connector_text

    assert "SHUUD / SHIID" in baseline_text
    assert "business application prototype" in baseline_text
