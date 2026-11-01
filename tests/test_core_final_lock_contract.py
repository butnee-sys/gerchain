from pathlib import Path


def test_fundamental_gate_contains_no_downstream_app_execution():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "core-gates.yml").read_text(encoding="utf-8")

    # SHUUD and SANDBOX are separate product MVPs. Their tests are explicitly
    # enumerated into a scope artifact and excluded from EAI regression execution.
    forbidden_path_fragments = ("shuud/", "sandbox/")
    pytest_run_lines = [
        line.strip()
        for line in workflow.splitlines()
        if line.strip().startswith(("pytest ", "python -m pytest "))
    ]
    offenders = [
        token
        for token in forbidden_path_fragments
        if any(token in line for line in pytest_run_lines)
    ]
    assert not offenders, f"fundamental gate must not execute downstream app paths: {offenders}"

    assert "test_shuud_*.py" in workflow, "EAI gate must enumerate SHUUD tests for explicit scope exclusion"
    assert "test_sandbox_*.py" in workflow, "EAI gate must enumerate SANDBOX tests for explicit scope exclusion"
    assert "excluded_product_tests" in workflow
    assert "product-tests-out-of-eai-scope.txt" in workflow
    assert "scope-disposition.txt" in workflow
    assert "ignore_args+=(--ignore=\"$test_file\")" in workflow


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
