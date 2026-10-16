from __future__ import annotations

from types import SimpleNamespace

import pytest

import production_entrypoint as entrypoint


class FakeEngine:
    def __init__(self):
        self.disposed = False

    def dispose(self):
        self.disposed = True


class FakeRuntime:
    runtime_mode = "production-postgresql"
    is_canonical_ledger_authoritative = True


def set_required_env(monkeypatch, url="postgresql+psycopg://user:pass@localhost/db"):
    monkeypatch.setenv("GERCHAIN_DATABASE_URL", url)
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "escrow-1")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "100")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "MNT")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "witness-1")


def test_build_production_runtime_uses_configured_factory_and_canonical_authority(monkeypatch):
    set_required_env(monkeypatch)
    engine = FakeEngine()
    monkeypatch.setattr(entrypoint, "create_engine", lambda *args, **kwargs: engine)
    captured = {}

    class Factory:
        def __init__(self, config, *, engine, session_factory):
            captured["config"] = config
            captured["engine"] = engine
            captured["session_factory"] = session_factory

        def create(self):
            return FakeRuntime()

    monkeypatch.setattr(entrypoint, "ProductionRuntimeFactory", Factory)
    runtime, actual_engine = entrypoint.build_production_runtime()
    assert runtime.is_canonical_ledger_authoritative is True
    assert actual_engine is engine
    assert captured["engine"] is engine
    assert captured["config"].database_url == "postgresql+psycopg://user:pass@localhost/db"
    assert captured["config"].escrow_id == "escrow-1"
    assert captured["config"].amount == 100
    assert captured["config"].currency == "MNT"
    assert captured["config"].witness_id == "witness-1"
    assert captured["session_factory"] is not None


@pytest.mark.parametrize("url", ["", "sqlite:///unsafe.db", "postgres://bad/db"])
def test_build_production_runtime_rejects_non_postgresql_url(monkeypatch, url):
    set_required_env(monkeypatch, url)
    monkeypatch.setattr(
        entrypoint, "create_engine",
        lambda *args, **kwargs: pytest.fail("engine must not be created"),
    )
    with pytest.raises(RuntimeError, match="pointing to PostgreSQL"):
        entrypoint.build_production_runtime()


def test_build_production_runtime_requires_all_identity(monkeypatch):
    set_required_env(monkeypatch)
    monkeypatch.delenv("GERCHAIN_ESCROW_ID")
    with pytest.raises(RuntimeError, match="GERCHAIN_ESCROW_ID"):
        entrypoint.build_production_runtime()


@pytest.mark.parametrize("amount", ["0", "-1", "bad"])
def test_build_production_runtime_rejects_invalid_amount(monkeypatch, amount):
    set_required_env(monkeypatch)
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", amount)
    monkeypatch.setattr(
        entrypoint, "create_engine",
        lambda *args, **kwargs: pytest.fail("engine must not be created"),
    )
    with pytest.raises(RuntimeError):
        entrypoint.build_production_runtime()


def test_build_production_runtime_disposes_engine_if_factory_fails(monkeypatch):
    set_required_env(monkeypatch)
    engine = FakeEngine()
    monkeypatch.setattr(entrypoint, "create_engine", lambda *args, **kwargs: engine)

    class Factory:
        @staticmethod
        def create(**kwargs):
            raise RuntimeError("schema initialization failed")

    monkeypatch.setattr(entrypoint, "ProductionRuntimeFactory", Factory)
    with pytest.raises(RuntimeError, match="schema initialization failed"):
        entrypoint.build_production_runtime()
    assert engine.disposed is True


def test_build_production_runtime_fails_closed_without_canonical_authority(monkeypatch):
    set_required_env(monkeypatch)
    engine = FakeEngine()
    monkeypatch.setattr(entrypoint, "create_engine", lambda *args, **kwargs: engine)

    class Factory:
        @staticmethod
        def create(**kwargs):
            return SimpleNamespace(is_canonical_ledger_authoritative=False)

    monkeypatch.setattr(entrypoint, "ProductionRuntimeFactory", Factory)
    with pytest.raises(RuntimeError, match="authority was not established"):
        entrypoint.build_production_runtime()
    assert engine.disposed is True
