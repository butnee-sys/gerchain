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


def test_shuud_server_is_standalone_entrypoint():
    root = Path(__file__).resolve().parents[1]
    source = (root / "shuud" / "server.py").read_text(encoding="utf-8")

    assert "from .app import app" in source
    assert "gerchain.web_ui" not in source


def test_shuud_app_is_separate_fastapi_product():
    from shuud.app import app

    assert app.title == "SHUUD"
    assert app.description == "2 минутын дотор замаа чөлөөл"
