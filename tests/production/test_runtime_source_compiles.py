from pathlib import Path
import py_compile


def test_production_runtime_source_compiles():
    path = Path(__file__).resolve().parents[2] / "services" / "gerchain_runtime.py"
    py_compile.compile(str(path), doraise=True)
