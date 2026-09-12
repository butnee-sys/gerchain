import pytest
from sqlalchemy import create_engine

from shuud.persistence import (
    SHUUDEscrowRecord,
    SHUUDLifecycleEvent,
    SHUUDPersistenceBase,
    SHUUDReleaseAuthorizationRecord,
    initialize_schema,
)
from shuud.persistence_adapter import SettlementPublication, SQLAlchemySettlementPersistence
from shuud.production import ProductionConfigurationError, create_production_persistence


def _publication():
    return SettlementPublication(
        lifecycle_event={
            "incident_id": "INC-PROD",
            "event_id": "EV-RELEASE",
            "event_type": "ESCROW_RELEASED",
            "sequence": 6,
            "event_hash": "HASH-RELEASE",
            "payload_json": "{}",
            "evidence_json": "{}",
        },
        authorization={
            "incident_id": "INC-PROD",
            "escrow_id": "ESC-PROD",
            "rule_version": "SHIID-1",
            "authorization_hash": "AUTH-PROD",
            "damage_estimate_nef": "1500000",
            "authorization_json": "{}",
            "witness_event_id": "EV-AUTH",
        },
        escrow={
            "incident_id": "INC-PROD",
            "escrow_id": "ESC-PROD",
            "state": "RELEASED",
            "amount_nef": "1500000",
            "currency": "NEF",
            "transition_counter": 3,
        },
    )


def test_production_requires_explicit_runtime(monkeypatch):
    monkeypatch.setenv("SHUUD_RUNTIME_MODE", "sandbox")
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", "sqlalchemy")
    monkeypatch.setenv("SHUUD_DATABASE_URL", "sqlite:///:memory:")
    with pytest.raises(ProductionConfigurationError, match="RUNTIME_MODE"):
        create_production_persistence()


def test_production_requires_sqlalchemy_backend(monkeypatch):
    monkeypatch.setenv("SHUUD_RUNTIME_MODE", "production")
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", "memory")
    monkeypatch.setenv("SHUUD_DATABASE_URL", "sqlite:///:memory:")
    with pytest.raises(ProductionConfigurationError, match="PERSISTENCE_BACKEND"):
        create_production_persistence()


def test_production_requires_database_url(monkeypatch):
    monkeypatch.setenv("SHUUD_RUNTIME_MODE", "production")
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", "sqlalchemy")
    monkeypatch.delenv("SHUUD_DATABASE_URL", raising=False)
    with pytest.raises(ProductionConfigurationError, match="DATABASE_URL"):
        create_production_persistence()


def test_production_bootstrap_creates_durable_adapter(tmp_path):
    # SQLite is used here only as an isolated test database. The production
    # bootstrap itself rejects SQLite URLs, so this test exercises the same
    # durable adapter/schema path without weakening that production boundary.
    engine = create_engine(f"sqlite:///{tmp_path / 'production.db'}", future=True)
    initialize_schema(engine)
    adapter = SQLAlchemySettlementPersistence(engine)
    adapter.publish_settlement(_publication())

    with adapter.engine.connect() as connection:
        assert len(connection.execute(SHUUDLifecycleEvent.__table__.select()).fetchall()) == 1
        assert len(connection.execute(SHUUDReleaseAuthorizationRecord.__table__.select()).fetchall()) == 1
        assert len(connection.execute(SHUUDEscrowRecord.__table__.select()).fetchall()) == 1
