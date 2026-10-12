from __future__ import annotations

import pytest

from services import production_entrypoint as entrypoint


class _FakeEngine:
    def __init__(self, url: str):
        self.url = url
        self.disposed = False

    def dispose(self):
        self.disposed = True


class _FakeRuntime:
    is_canonical_ledger_authoritative = True

    class _Escrow:
        escrow_id = "ESC-1"
        currency = "MNT"

    escrow_engine = _Escrow()


def test_build_production_runtime_uses_canonical_factory_and_validated_env(monkeypatch):
    captured = {}
    engine = _FakeEngine("postgresql://unit/test")

    monkeypatch.setenv("GERCHAIN_DATABASE_URL", "postgresql://unit/test")
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "ESC-1")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "25")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "MNT")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "W-1")
    monkeypatch.setattr(entrypoint, "create_engine", lambda *a, **k: engine)

    class FakeConfig:
        def __init__(self, **kwargs):
            captured["config"] = kwargs

    class FakeFactory:
        def __init__(self, config, *, engine=None):
            captured["factory_config"] = config
            captured["engine"] = engine

        def create(self):
            captured["created"] = True
            return _FakeRuntime()

    monkeypatch.setattr(entrypoint, "ProductionRuntimeConfig", FakeConfig)
    monkeypatch.setattr(entrypoint, "ProductionRuntimeFactory", FakeFactory)

    runtime, actual_engine = entrypoint.build_production_runtime()

    assert runtime.is_canonical_ledger_authoritative is True
    assert actual_engine is engine
    assert captured["config"] == {
        "database_url": "postgresql://unit/test",
        "escrow_id": "ESC-1",
        "amount": 25,
        "currency": "MNT",
        "witness_id": "W-1",
    }
    assert captured["factory_config"] is not None
    assert captured["engine"] is engine
    assert captured["created"] is True
    assert engine.disposed is False


@pytest.mark.parametrize(
    ("variable", "value", "message"),
    [
        ("GERCHAIN_DATABASE_URL", "sqlite:///not-production.db", "pointing to PostgreSQL"),
        ("GERCHAIN_ESCROW_AMOUNT", "not-an-int", "must be an integer"),
        ("GERCHAIN_ESCROW_AMOUNT", "0", "must be positive"),
    ],
)
def test_build_production_runtime_rejects_invalid_configuration(
    monkeypatch, variable, value, message
):
    monkeypatch.setenv("GERCHAIN_DATABASE_URL", "postgresql://unit/test")
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "ESC-1")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "25")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "MNT")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "W-1")
    monkeypatch.setenv(variable, value)

    with pytest.raises(RuntimeError, match=message):
        entrypoint.build_production_runtime()


def test_build_production_runtime_disposes_engine_if_factory_fails(monkeypatch):
    engine = _FakeEngine("postgresql://unit/test")
    monkeypatch.setenv("GERCHAIN_DATABASE_URL", "postgresql://unit/test")
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "ESC-1")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "25")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "MNT")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "W-1")
    monkeypatch.setattr(entrypoint, "create_engine", lambda *a, **k: engine)

    class FakeFactory:
        def __init__(self, *args, **kwargs):
            pass

        def create(self):
            raise RuntimeError("schema gate failed")

    monkeypatch.setattr(entrypoint, "ProductionRuntimeFactory", FakeFactory)

    with pytest.raises(RuntimeError, match="schema gate failed"):
        entrypoint.build_production_runtime()
    assert engine.disposed is True
