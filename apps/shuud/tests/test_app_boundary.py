from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "apps" / "shuud"
FORBIDDEN_PREFIXES = ("core", "money", "escrow", "witness", "verifier", "services.gerchain_runtime", "services.authoritative_escrow")


def test_shuud_is_the_only_product_namespace():
    assert APP.is_dir()
    root_names = {p.name for p in ROOT.iterdir()}
    assert "shuud" not in root_names
    assert "sandbox" not in root_names
    assert "prototype" not in root_names


def test_platform_tree_contains_no_shuud_named_elements():
    violations = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or APP in path.parents:
            continue
        if any(part.lower().startswith("shuud") for part in path.relative_to(ROOT).parts):
            violations.append(str(path.relative_to(ROOT)))
    assert violations == []


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
