from __future__ import annotations

import ast
from pathlib import Path


CORE_MODULES = {
    "escrow",
    "witness",
    "verifier",
    "network",
}
ADAPTER_MODULES = {
    "nef_gerchain_port.gerchain_adapter",
    "nef_gerchain_port.nef_adapter",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _python_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*.py") if ".git" not in path.parts]


def _imports(path: Path) -> list[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.module, node.lineno))
    return imports


def _is_forbidden_core_import(module: str) -> bool:
    root = module.split(".", 1)[0]
    return root in CORE_MODULES


def test_gerchain_does_not_depend_on_shuud():
    root = _repo_root()
    # GerChain core is represented by the repository root packages, while
    # SHUUD is a separate application package. Do not silently pass because
    # a non-existent nested `gerchain/` directory was scanned.
    excluded = {"shuud", "tests", ".git", "nef_gerchain_port"}
    offenders: list[str] = []
    scanned = 0
    for path in _python_files(root):
        if path.parts[len(root.parts)] in excluded:
            continue
        scanned += 1
        for module, lineno in _imports(path):
            if module == "shuud" or module.startswith("shuud."):
                offenders.append(f"{path.relative_to(root).as_posix()}:{lineno}")
    assert scanned > 0, "GerChain boundary scan must inspect real repository Python files"
    assert offenders == [], f"GerChain must not depend on SHUUD: {offenders}"


def test_shuud_imports_core_engines_only_through_port():
    root = _repo_root()
    shuud_dir = root / "shuud"
    assert shuud_dir.is_dir(), "SHUUD package must exist"
    offenders: list[str] = []
    for path in shuud_dir.rglob("*.py"):
        for module, lineno in _imports(path):
            if _is_forbidden_core_import(module):
                offenders.append(f"{path.relative_to(root).as_posix()}:{lineno}:{module}")
    assert offenders == [], f"SHUUD must use the NEF–GerChain external port: {offenders}"


def test_port_adapters_are_the_only_core_import_boundary():
    root = _repo_root()
    port_dir = root / "nef_gerchain_port"
    assert port_dir.is_dir(), "EXIM Escrow Port package must exist"
    offenders: list[str] = []
    for path in port_dir.rglob("*.py"):
        relative = path.relative_to(root).as_posix()
        allowed_adapter = path.name in {"gerchain_adapter.py", "nef_adapter.py"}
        for module, lineno in _imports(path):
            if _is_forbidden_core_import(module) and not allowed_adapter:
                offenders.append(f"{relative}:{lineno}:{module}")
    assert offenders == [], f"Only adapters may import core: {offenders}"


def test_shuud_has_no_direct_core_imports_even_via_nested_modules():
    root = _repo_root()
    shuud_dir = root / "shuud"
    offenders: list[str] = []
    for path in shuud_dir.rglob("*.py"):
        for module, lineno in _imports(path):
            if module.startswith(("core.", "escrow.", "witness.", "verifier.", "network.")):
                offenders.append(f"{path.relative_to(root).as_posix()}:{lineno}:{module}")
    assert offenders == [], f"SHUUD must not bypass the Port through nested core modules: {offenders}"


def test_shuud_server_is_standalone_entrypoint():
    root = _repo_root()
    source = (root / "shuud" / "server.py").read_text(encoding="utf-8")
    assert "from .app import app" in source
    assert "gerchain.web_ui" not in source


def test_shuud_app_is_separate_fastapi_product():
    from shuud.app import app

    assert app.title == "SHUUD"
    assert app.description == "2 минутын дотор замаа чөлөөл"
