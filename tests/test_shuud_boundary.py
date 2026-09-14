from pathlib import Path


def test_gerchain_does_not_depend_on_shuud():
    root = Path(__file__).resolve().parents[1]
    gerchain_dir = root / "gerchain"
    forbidden = ("from shuud", "import shuud")
    offenders = []
    for path in gerchain_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            offenders.append(path.relative_to(root).as_posix())
    assert offenders == [], f"GerChain must not depend on SHUUD: {offenders}"


def test_shuud_does_not_import_core_or_exim_port_directly():
    root = Path(__file__).resolve().parents[1]
    shuud_dir = root / "shuud"
    forbidden = (
        "from escrow", "import escrow", "from witness", "import witness",
        "from verifier", "import verifier", "from network", "import network",
        "from nef_gerchain_port", "import nef_gerchain_port",
    )
    offenders = []
    for path in shuud_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            offenders.append(path.relative_to(root).as_posix())
    assert offenders == [], f"SHUUD must use the application adapter boundary: {offenders}"


def test_composition_root_is_the_only_concrete_connector_wiring_boundary():
    root = Path(__file__).resolve().parents[1]
    composition = (root / "composition" / "shuud.py").read_text(encoding="utf-8")
    adapter = (root / "application_adapters" / "shuud.py").read_text(encoding="utf-8")
    connector = (root / "connectors" / "exim_adapter.py").read_text(encoding="utf-8")
    gateway = (root / "gateway" / "open_multi_connector.py").read_text(encoding="utf-8")
    assert "EXIMConnectorAdapter" in composition
    assert "EXIMConnectorAdapter" not in adapter
    assert "from connectors" not in adapter
    assert "from composition" not in adapter
    assert "from nef_gerchain_port" in connector
    assert "nef_gerchain_port" not in gateway


def test_port_adapters_are_the_only_core_import_boundary():
    root = Path(__file__).resolve().parents[1]
    port_dir = root / "nef_gerchain_port"
    for path in port_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if path.name in {"gerchain_adapter.py", "nef_adapter.py"}:
            continue
        forbidden = ("from escrow", "import escrow", "from witness", "import witness", "from verifier", "import verifier", "from network", "import network")
        assert not any(token in text for token in forbidden), f"Only adapters may import core: {path.relative_to(root)}"


def test_shuud_server_is_standalone_entrypoint():
    root = Path(__file__).resolve().parents[1]
    source = (root / "shuud" / "server.py").read_text(encoding="utf-8")
    assert "from .app import app" in source
    assert "gerchain.web_ui" not in source


def test_shuud_app_is_separate_fastapi_product():
    from shuud.app import app
    assert app.title == "SHUUD"
    assert app.description == "2 минутын дотор замаа чөлөөл"
