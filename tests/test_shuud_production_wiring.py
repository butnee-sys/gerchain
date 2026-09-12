import importlib

import pytest
from sqlalchemy import create_engine, select

from shuud.persistence import (
    SHUUDEscrowRecord,
    SHUUDLifecycleEvent,
    SHUUDReleaseAuthorizationRecord,
    SHUUDPersistenceBase,
)
from shuud.persistence_adapter import SettlementPublication
from shuud.production import ProductionConfigurationError, create_production_persistence


def _publication():
    return SettlementPublication(
        lifecycle_event={
            "incident_id": "INC-WIRING",
            "event_id": "EV-RELEASE",
            "event_type": "ESCROW_RELEASED",
            "sequence": 6,
            "event_hash": "HASH-RELEASE",
            "payload_json": "{}",
            "evidence_json": "{}",
        },
        authorization={
            "incident_id": "INC-WIRING",
            "escrow_id": "ESC-WIRING",
            "rule_version": "SHIID-1",
            "authorization_hash": "AUTH-WIRING",
            "damage_estimate_nef": "1500000",
            "authorization_json": "{}",
            "witness_event_id": "EV-AUTH",
        },
        escrow={
            "incident_id": "INC-WIRING",
            "escrow_id": "ESC-WIRING",
            "state": "RELEASED",
            "amount_nef": "1500000",
            "currency": "NEF",
            "transition_counter": 3,
        },
    )


def test_production_wiring_publishes_all_settlement_records(monkeypatch, tmp_path):
    monkeypatch.setenv("SHUUD_RUNTIME_MODE", "production")
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", "sqlalchemy")
    db_url = f"sqlite:///{tmp_path / 'production.db'}"

    adapter = create_production_persistence(database_url=db_url)
    adapter.publish_settlement(_publication())

    with adapter.engine.connect() as connection:
        assert len(connection.execute(select(SHUUDLifecycleEvent)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDReleaseAuthorizationRecord)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDEscrowRecord)).fetchall()) == 1


def test_production_wiring_rejects_incomplete_configuration(monkeypatch):
    monkeypatch.setenv("SHUUD_RUNTIME_MODE", "production")
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", "sqlalchemy")
    monkeypatch.delenv("SHUUD_DATABASE_URL", raising=False)

    with pytest.raises(ProductionConfigurationError, match="SHUUD_DATABASE_URL"):
        create_production_persistence()


def test_production_wiring_does_not_modify_api_runtime_gate(monkeypatch):
    monkeypatch.setenv("SHUUD_RUNTIME_MODE", "production")
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", "sqlalchemy")

    with pytest.raises(RuntimeError, match="production runtime is disabled"):
        importlib.import_module("shuud.api")
