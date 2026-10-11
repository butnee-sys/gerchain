from __future__ import annotations

import pytest

import production_entrypoint as entrypoint


class _FakeEngine:
    def __init__(self):
        self.disposed = False

    def dispose(self):
        self.disposed = True


class _FakeRuntime:
    is_canonical_ledger_authoritative = True


def _set_required_env(monkeypatch):
    monkeypatch.setenv("GERCHAIN_DATABASE_URL", "postgresql+psycopg://user:pass@localhost/db")
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "escrow-1")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "100")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "MNT")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "witness-1")


def test_entrypoint_builds_instance_factory_and_requires_canonical_authority(monkeypatch):
    _set_required_env(monkeypatch)
    engine = _FakeEngine()
    monkeypatch.setattr(entrypoint, "create_engine", lambda *args, **kwargs: engine)

    seen = {}

    class Factory:
        def __init__(self, config, *, engine):
            seen["config"] = config
            seen["engine"] = engine

        def create(self):
            return _FakeRuntime()

    monkeypatch.setattr(entrypoint, "ProductionRuntimeFactory", Factory)
    runtime, returned_engine = entrypoint.build_production_runtime()

    assert runtime.is_canonical_ledger_authoritative is True
    assert returned_engine is engine
    assert seen["engine"] is engine
    assert seen["config"].database_url == "postgresql+psycopg://user:pass@localhost/db"
    assert seen["config"].escrow_id == "escrow-1"
    assert seen["config"].amount == 100
    assert seen["config"].currency == "MNT"
    assert seen["config"].witness_id == "witness-1"


@pytest.mark.parametrize("database_url", ["", "sqlite:///unsafe.db", "postgres://not-an-accepted-prefix"])
def test_entrypoint_rejects_non_postgresql_url_before_engine_creation(monkeypatch, database_url):
    monkeypatch.setenv("GERCHAIN_DATABASE_URL", database_url)
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "escrow-1")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "100")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "MNT")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "witness-1")
    monkeypatch.setattr(
        entrypoint,
        "create_engine",
        lambda *args, **kwargs: pytest.fail("engine must not be created for invalid URL"),
    )

    with pytest.raises(RuntimeError, match="pointing to PostgreSQL"):
        entrypoint.build_production_runtime()


@pytest.mark.parametrize("amount", ["0", "-1"])
def test_entrypoint_rejects_nonpositive_amount(monkeypatch, amount):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", amount)
    monkeypatch.setattr(
        entrypoint,
        "create_engine",
        lambda *args, **kwargs: pytest.fail("engine must not be created for invalid amount"),
    )

    with pytest.raises(RuntimeError, match="must be positive"):
        entrypoint.build_production_runtime()


def test_entrypoint_disposes_engine_when_factory_fails(monkeypatch):
    _set_required_env(monkeypatch)
    engine = _FakeEngine()
    monkeypatch.setattr(entrypoint, "create_engine", lambda *args, **kwargs: engine)

    class Factory:
        def __init__(self, config, *, engine):
            pass

        def create(self):
            raise RuntimeError("schema migration failed")

    monkeypatch.setattr(entrypoint, "ProductionRuntimeFactory", Factory)

    with pytest.raises(RuntimeError, match="schema migration failed"):
        entrypoint.build_production_runtime()
    assert engine.disposed is True


def test_entrypoint_fails_closed_if_factory_does_not_establish_canonical_authority(monkeypatch):
    _set_required_env(monkeypatch)
    engine = _FakeEngine()
    monkeypatch.setattr(entrypoint, "create_engine", lambda *args, **kwargs: engine)

    class Factory:
        def __init__(self, config, *, engine):
            pass

        def create(self):
            return type("Runtime", (), {"is_canonical_ledger_authoritative": False})()

    monkeypatch.setattr(entrypoint, "ProductionRuntimeFactory", Factory)

    with pytest.raises(RuntimeError, match="authority was not established"):
        entrypoint.build_production_runtime()
    assert engine.disposed is True
