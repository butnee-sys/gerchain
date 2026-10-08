from pathlib import Path


def test_fundamental_gate_contains_no_downstream_app_execution():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "core-gates.yml").read_text(encoding="utf-8")
    forbidden = ("shuud/", "sandbox/", "tests/test_shuud_")
    offenders = [token for token in forbidden if token in workflow]
    assert not offenders, f"fundamental gate must exclude downstream app paths: {offenders}"


def test_fundamental_gate_is_named_as_canonical_architecture_gate():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "core-gates.yml").read_text(encoding="utf-8")
    assert "Run canonical fundamental architecture gate" in workflow


def test_postgresql_concurrency_has_one_authoritative_gate():
    root = Path(__file__).resolve().parents[1]
    workflows = root / ".github" / "workflows"
    core_gate = (workflows / "core-gates.yml").read_text(encoding="utf-8")
    assert "postgres/tests/test_concurrency.py" in core_gate
    assert not (workflows / "postgres-concurrency.yml").exists()
    assert not (workflows / "postgresql-concurrency.yml").exists()
