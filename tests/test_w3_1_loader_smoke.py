"""Loader smoke test for the independent W3.1 oracle."""

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).parent / "independent" / "w3_1_schema_fingerprint_oracle.py"
SPEC = importlib.util.spec_from_file_location("w31_oracle", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_oracle_loader_registers_module_before_dataclass_processing():
    assert MODULE.run_vector_suite()["baseline_reconcile"] == "MATCH"
