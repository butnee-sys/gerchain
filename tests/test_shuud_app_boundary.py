from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "shuud"
FORBIDDEN_PREFIXES = (
    "core",
    "money",
    "escrow",
    "witness",
    "verifier",
    "services.gerchain_runtime",
    "services.authoritative_escrow",
)


def test_shuud_product_lives_under_independent_app_tree():
    assert APP.is_dir()
    assert not (ROOT / "services" / "shuud_service.py").exists()
    assert not (ROOT / "services" / "shuud_exim_flow.py").exists()
    assert not (ROOT / "services" / "shuud_governed_flow.py").exists()
    assert not (ROOT / "sandbox").exists()
    assert not (ROOT / "prototype").exists()


def test_shuud_has_no_direct_core_implementation_imports():
    violations = []
    for path in APP.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if name == "services" or any(name == prefix or name.startswith(prefix + ".") for prefix in FORBIDDEN_PREFIXES):
                    violations.append(f"{path.relative_to(ROOT)}: {name}")
    assert violations == []


def test_shuud_external_port_is_available():
    assert (ROOT / "nef_gerchain_port").is_dir()
