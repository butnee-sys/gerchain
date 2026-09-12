"""SH-15.14 tests for the SHUUD sandbox/production persistence boundary."""

import importlib

import pytest


MODULE = "shuud.api"


def _reload_with_env(monkeypatch, *, runtime_mode, persistence_backend):
    monkeypatch.setenv("SHUUD_RUNTIME_MODE", runtime_mode)
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", persistence_backend)
    module = importlib.import_module(MODULE)
    return importlib.reload(module)


def test_sandbox_defaults_to_in_memory_boundary(monkeypatch):
    monkeypatch.delenv("SHUUD_RUNTIME_MODE", raising=False)
    monkeypatch.delenv("SHUUD_PERSISTENCE_BACKEND", raising=False)
    module = importlib.import_module(MODULE)
    module = importlib.reload(module)

    assert module.SHUUD_RUNTIME_MODE == "sandbox"
    assert module.SHUUD_PERSISTENCE_BACKEND == "memory"


def test_production_rejects_in_memory_persistence(monkeypatch):
    with pytest.raises(RuntimeError, match="SHUUD production requires durable persistence"):
        _reload_with_env(
            monkeypatch,
            runtime_mode="production",
            persistence_backend="memory",
        )


def test_production_accepts_only_explicit_durable_backend(monkeypatch):
    module = _reload_with_env(
        monkeypatch,
        runtime_mode="production",
        persistence_backend="sqlalchemy",
    )

    assert module.SHUUD_RUNTIME_MODE == "production"
    assert module.SHUUD_PERSISTENCE_BACKEND == "sqlalchemy"


def test_unknown_runtime_mode_fails_closed(monkeypatch):
    with pytest.raises(RuntimeError, match="unsupported SHUUD_RUNTIME_MODE"):
        _reload_with_env(
            monkeypatch,
            runtime_mode="unknown",
            persistence_backend="memory",
        )
