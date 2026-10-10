from types import SimpleNamespace

import pytest

import production_entrypoint as entrypoint


def test_build_production_runtime_rejects_non_postgresql_url(monkeypatch):
    monkeypatch.setenv("GERCHAIN_DATABASE_URL", "sqlite:///not-production.db")
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "escrow-1")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "10")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "MNT")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "witness-1")

    with pytest.raises(RuntimeError, match="PostgreSQL"):
        entrypoint.build_production_runtime()


def test_build_production_runtime_requires_all_runtime_identity(monkeypatch):
    monkeypatch.setenv("GERCHAIN_DATABASE_URL", "postgresql://user:pass@localhost/db")
    for key in (
        "GERCHAIN_ESCROW_ID",
        "GERCHAIN_ESCROW_AMOUNT",
        "GERCHAIN_CURRENCY",
        "GERCHAIN_WITNESS_ID",
    ):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(RuntimeError, match="GERCHAIN_ESCROW_ID"):
        entrypoint.build_production_runtime()


def test_build_production_runtime_uses_instance_factory_and_canonical_authority(monkeypatch):
    monkeypatch.setenv("GERCHAIN_DATABASE_URL", "postgresql://user:pass@localhost/db")
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "escrow-1")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "10")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "MNT")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "witness-1")

    engine = SimpleNamespace(dispose=lambda: None)
    runtime = SimpleNamespace(is_canonical_ledger_authoritative=True)
    captured = {}

    monkeypatch.setattr(entrypoint, "create_engine", lambda *args, **kwargs: engine)

    class FakeFactory:
        def __init__(self, config, *, engine):
            captured["config"] = config
            captured["engine"] = engine

        def create(self):
            captured["created"] = True
            return runtime

    monkeypatch.setattr(entrypoint, "ProductionRuntimeFactory", FakeFactory)

    actual_runtime, actual_engine = entrypoint.build_production_runtime()

    assert actual_runtime is runtime
    assert actual_engine is engine
    assert captured["engine"] is engine
    assert captured["config"].escrow_id == "escrow-1"
    assert captured["config"].amount == 10
    assert captured["config"].currency == "MNT"
    assert captured["config"].witness_id == "witness-1"
    assert captured["created"] is True


def test_build_production_runtime_disposes_engine_if_authority_is_not_established(monkeypatch):
    monkeypatch.setenv("GERCHAIN_DATABASE_URL", "postgresql://user:pass@localhost/db")
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "escrow-1")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "10")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "MNT")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "witness-1")

    disposed = []
    engine = SimpleNamespace(dispose=lambda: disposed.append(True))
    monkeypatch.setattr(entrypoint, "create_engine", lambda *args, **kwargs: engine)

    class FakeFactory:
        def __init__(self, config, *, engine):
            pass

        def create(self):
            return SimpleNamespace(is_canonical_ledger_authoritative=False)

    monkeypatch.setattr(entrypoint, "ProductionRuntimeFactory", FakeFactory)

    with pytest.raises(RuntimeError, match="authority was not established"):
        entrypoint.build_production_runtime()

    assert disposed == [True]
