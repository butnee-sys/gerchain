from pathlib import Path


def test_gerchain_runtime_source_compiles_without_import_side_effects():
    """Keep the exact production runtime source syntax-valid at the checked-out revision."""
    source_path = Path(__file__).resolve().parents[2] / "services" / "gerchain_runtime.py"
    source = source_path.read_text(encoding="utf-8")
    compile(source, str(source_path), "exec")
