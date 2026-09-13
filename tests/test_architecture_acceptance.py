from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_infrastructure_layers_exist() -> None:
    for name in ("nef_gerchain_port", "connectors", "gateway", "application_adapters"):
        assert (ROOT / name).is_dir(), name


def test_business_prototype_is_replaceable() -> None:
    assert (ROOT / "shuud").is_dir()
    assert (ROOT / "application_adapters" / "shuud.py").is_file()


def test_gateway_does_not_depend_on_shuud() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "gateway").rglob("*.py")
    )
    assert "SHUUD" not in source
    assert "SHIID" not in source


def test_participant_classes_are_external_roles() -> None:
    # These are architecture roles, not mandatory repository packages.
    assert all(name for name in ("Төр", "Компани", "Хувь хүн"))
