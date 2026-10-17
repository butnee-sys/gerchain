from pathlib import Path


CORE_ROOTS = (
    "architecture",
    "core",
    "dee_security",
    "escrow",
    "money",
    "persistence",
    "services",
)


def test_core_source_never_imports_shuud():
    root = Path(__file__).resolve().parents[1]
    offenders = []
    for folder in CORE_ROOTS:
        for path in (root / folder).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "import shuud" in text or "from shuud" in text:
                offenders.append(str(path.relative_to(root)))
    assert not offenders, f"CORE must not import SHUUD: {offenders}"


def test_shuud_workflows_are_path_isolated():
    root = Path(__file__).resolve().parents[1]
    for name in ("shuud-command-layer.yml", "shuud-sandbox-smoke.yml"):
        text = (root / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert 'paths:' in text
        assert '"shuud/**"' in text
        assert '"sandbox/**"' in text


def test_core_gate_does_not_execute_shuud_tests():
    root = Path(__file__).resolve().parents[1]
    text = (root / ".github" / "workflows" / "core-gates.yml").read_text(encoding="utf-8")
    assert "tests/test_shuud_" not in text
    assert "shuud/" not in text


def test_shuud_sandbox_declares_dee_security_dependency():
    root = Path(__file__).resolve().parents[1]
    dockerfile = (root / "sandbox" / "Dockerfile").read_text(encoding="utf-8")
    assert "cryptography>=46,<47" in dockerfile


def test_shuud_smoke_preserves_release_before_clearance_order():
    root = Path(__file__).resolve().parents[1]
    text = (root / ".github" / "workflows" / "shuud-sandbox-smoke.yml").read_text(encoding="utf-8")
    assert text.index('$API/release') < text.index('$API/metrics/clearance')
