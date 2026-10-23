from pathlib import Path


def test_fundamental_gate_contains_no_downstream_app_execution():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "core-gates.yml").read_text(encoding="utf-8")

    # Exclusion globs may name downstream tests; that is not execution. Reject
    # actual downstream paths in the pytest argument list, while requiring the
    # full-suite invocation to explicitly ignore SHUUD tests.
    forbidden_path_fragments = ("shuud/", "sandbox/")
    offenders = [token for token in forbidden_path_fragments if token in workflow]
    assert not offenders, f"fundamental gate must exclude downstream app paths: {offenders}"

    pytest_path_lines = [
        line.strip()
        for line in workflow.splitlines()
        if line.strip().startswith(("tests/test_shuud_", "shuud/", "sandbox/"))
    ]
    assert not pytest_path_lines, f"downstream app paths must not be passed as executed pytest targets: {pytest_path_lines}"
    assert any(
        pattern in workflow
        for pattern in (
            "--ignore-glob='tests/test_shuud_*.py'",
            "--ignore-glob='tests/test_[s]huud_*.py'",
        )
    ), "full EAI suite must explicitly exclude downstream SHUUD tests from the fundamental gate"


def test_fundamental_gate_is_named_as_canonical_architecture_gate():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "core-gates.yml").read_text(encoding="utf-8")
    assert "Run canonical fundamental architecture gate" in workflow


def test_postgresql_concurrency_has_one_authoritative_gate():
    root = Path(__file__).resolve().parents[1]
    workflows = root / ".github" / "workflows"
    core_gate = (workflows / "core-gates.yml").read_text(encoding="utf-8")
    assert "tests/postgres/test_migration_concurrency.py" in core_gate
    assert not (workflows / "postgres-concurrency.yml").exists()
    assert not (workflows / "postgresql-concurrency.yml").exists()
