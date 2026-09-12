import pytest
from sqlalchemy import create_engine, select

from shuud.persistence import (
    SHUUDEscrowRecord,
    SHUUDLifecycleEvent,
    SHUUDReleaseAuthorizationRecord,
    initialize_schema,
)
from shuud.persistence_adapter import SettlementPublication, SQLAlchemySettlementPersistence
from shuud.production import ProductionConfigurationError, create_production_persistence


def _publication():
    return SettlementPublication(
        lifecycle_event={"incident_id": "INC-WIRING", "event_id": "EV-RELEASE", "event_type": "ESCROW_RELEASED", "sequence": 6, "event_hash": "HASH-RELEASE", "payload_json": "{}", "evidence_json": "{}"},
        authorization={"incident_id": "INC-WIRING", "escrow_id": "ESC-WIRING", "rule_version": "SHIID-1", "authorization_hash": "AUTH-WIRING", "damage_estimate_nef": "1500000", "authorization_json": "{}", "witness_event_id": "EV-AUTH"},
        escrow={"incident_id": "INC-WIRING", "escrow_id": "ESC-WIRING", "state": "RELEASED", "amount_nef": "1500000", "currency": "NEF", "transition_counter": 3},
    )


def test_durable_adapter_wiring_uses_test_database(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'production.db'}", future=True)
    initialize_schema(engine)
    adapter = SQLAlchemySettlementPersistence(engine)
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
