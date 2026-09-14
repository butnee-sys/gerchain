from pathlib import Path


def test_gerchain_does_not_depend_on_shuud():
    root = Path(__file__).resolve().parents[1]
    platform_dirs = [
        root / "core",
        root / "money",
        root / "escrow",
        root / "witness",
        root / "verifier",
        root / "nef_gerchain_port",
        root / "services",
        root / "tests",
    ]
    forbidden = ("from shuud", "import shuud")
    offenders = []
    for directory in platform_dirs:
        if not directory.exists():
            continue
        for path in directory.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if any(token in text for token in forbidden):
                offenders.append(path.relative_to(root).as_posix())
    assert offenders == [], f"GerChain platform must not depend on SHUUD: {offenders}"


def test_shuud_does_not_import_core_engines_directly():
    root = Path(__file__).resolve().parents[1]
    shuud_dir = root / "apps" / "shuud"
    forbidden = (
        "from escrow",
        "import escrow",
        "from witness",
        "import witness",
        "from verifier",
        "import verifier",
        "from network",
        "import network",
    )
    offenders = []
    for path in shuud_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            offenders.append(path.relative_to(root).as_posix())
    assert offenders == [], f"SHUUD must use the NEF–GerChain external port: {offenders}"


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
    source = (root / "apps" / "shuud" / "server.py").read_text(encoding="utf-8")
    assert "from .app import app" in source
    assert "gerchain.web_ui" not in source


def test_shuud_app_is_separate_fastapi_product():
    from apps.shuud.app import app
    assert app.title == "SHUUD"
    assert app.description == "2 минутын дотор замаа чөлөөл"
