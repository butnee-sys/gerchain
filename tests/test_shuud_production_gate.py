import importlib

import pytest


def _load_api(monkeypatch, runtime_mode, backend):
    monkeypatch.setenv("SHUUD_RUNTIME_MODE", runtime_mode)
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", backend)
    import shuud.api as api
    return importlib.reload(api)


def test_production_memory_backend_fails_closed(monkeypatch):
    with pytest.raises(RuntimeError, match="durable persistence adapter"):
        _load_api(monkeypatch, "production", "memory")


def test_production_unknown_backend_fails_closed(monkeypatch):
    with pytest.raises(RuntimeError, match="unsupported SHUUD_PERSISTENCE_BACKEND"):
        _load_api(monkeypatch, "production", "unknown")


def test_production_sqlalchemy_backend_is_not_enabled_by_runtime_gate(monkeypatch):
    # A configured durable backend is necessary but not sufficient: the API
    # must remain closed until the production adapter is actually wired.
    with pytest.raises(RuntimeError, match="durable persistence adapter"):
        _load_api(monkeypatch, "production", "sqlalchemy")


def test_sandbox_memory_backend_remains_available(monkeypatch):
    api = _load_api(monkeypatch, "sandbox", "memory")
    assert api.SHUUD_RUNTIME_MODE == "sandbox"
    assert api.SHUUD_PERSISTENCE_BACKEND == "memory"
