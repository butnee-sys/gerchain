from importlib import import_module
from pathlib import Path
import py_compile


ROOT = Path(__file__).resolve().parents[2]


def test_production_runtime_source_compiles():
    for relative in (
        "services/gerchain_runtime.py",
        "services/gerchain_runtime_factory.py",
        "production_entrypoint.py",
    ):
        py_compile.compile(str(ROOT / relative), doraise=True)


def test_production_runtime_and_factory_import_without_construction():
    runtime_module = import_module("services.gerchain_runtime")
    factory_module = import_module("services.gerchain_runtime_factory")
    entrypoint_module = import_module("production_entrypoint")

    assert callable(runtime_module.GerchainRuntime)
    assert callable(factory_module.ProductionRuntimeFactory)
    assert callable(entrypoint_module.main)


def test_production_factory_constructs_canonical_ledger_runtime_path():
    source = (ROOT / "services" / "gerchain_runtime_factory.py").read_text(
        encoding="utf-8"
    )
    assert "runtime.configure_canonical_ledger(self.session_factory)" in source
    assert "runtime.require_canonical_ledger_authority()" in source
    assert "runtime.configure_postgres_release(self.session_factory)" not in source
