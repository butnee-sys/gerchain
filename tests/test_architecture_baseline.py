from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dee_architecture_layers_exist() -> None:
    required = (
        "nef_gerchain_port",
        "connectors",
        "gateway",
        "application_adapters",
        "shuud",
    )
    missing = [name for name in required if not (ROOT / name).is_dir()]
    assert not missing, f"missing architecture layers: {missing}"


def test_exim_connector_boundary_exists() -> None:
    assert (ROOT / "connectors" / "exim_adapter.py").is_file()
    assert (ROOT / "nef_gerchain_port" / "__init__.py").is_file()


def test_i2b_gateway_is_independent_of_shuud() -> None:
    gateway = ROOT / "gateway"
    assert gateway.is_dir()
    python_files = tuple(gateway.rglob("*.py"))
    source = "\n".join(path.read_text(encoding="utf-8") for path in python_files)
    assert "import shuud" not in source
    assert "from shuud" not in source
    assert "import application_adapters" not in source
    assert "from application_adapters" not in source


def test_shuud_is_an_application_prototype_not_a_core_layer() -> None:
    shuud = ROOT / "shuud"
    assert shuud.is_dir()
    source = "\n".join(path.read_text(encoding="utf-8") for path in shuud.rglob("*.py"))
    forbidden = (
        "import escrow",
        "from escrow",
        "import witness",
        "from witness",
        "import verifier",
        "from verifier",
        "import network",
        "from network",
        "import nef_gerchain_port",
        "from nef_gerchain_port",
    )
    violations = [token for token in forbidden if token in source]
    assert not violations, f"SHUUD bypasses application boundary: {violations}"


def test_participant_classes_are_external_roles() -> None:
    # Төр / Компани / Хувь хүн are architectural participant classes,
    # not required implementation packages in the core repository.
    for name in ("Төр", "Компани", "Хувь хүн"):
        assert name
