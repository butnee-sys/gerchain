from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_participant_classes_are_not_architecture_layers() -> None:
    # Төр / Компани / Хувь хүн are external participant classes.
    # They must not be required repository packages for the infrastructure.
    assert not (ROOT / "төр").exists()
    assert not (ROOT / "компани").exists()
    assert not (ROOT / "хувь_хүн").exists()


def test_shuud_is_replaceable_business_prototype() -> None:
    assert (ROOT / "shuud").is_dir()
    assert (ROOT / "application_adapters" / "shuud.py").is_file()


def test_gateway_is_not_named_after_shuud() -> None:
    assert (ROOT / "gateway").is_dir()
    gateway_sources = tuple((ROOT / "gateway").rglob("*.py"))
    source = "\n".join(path.read_text(encoding="utf-8") for path in gateway_sources)
    assert "SHUUD" not in source
    assert "SHIID" not in source
