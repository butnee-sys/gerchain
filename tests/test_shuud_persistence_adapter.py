from sqlalchemy import create_engine, select

from shuud.persistence import SHUUDEscrowRecord, SHUUDLifecycleEvent, SHUUDPersistenceBase, SHUUDReleaseAuthorizationRecord
from shuud.persistence_adapter import (
    MemorySettlementPersistence,
    SQLAlchemySettlementPersistence,
    SettlementPublication,
)


def _publication():
    return SettlementPublication(
        lifecycle_event={
            "incident_id": "INC-ADAPTER",
            "event_id": "EV-RELEASE",
            "event_type": "ESCROW_RELEASED",
            "sequence": 6,
            "event_hash": "HASH-RELEASE",
            "payload_json": "{}",
            "evidence_json": "{}",
        },
        authorization={
            "incident_id": "INC-ADAPTER",
            "escrow_id": "ESC-ADAPTER",
            "rule_version": "SHIID-1",
            "authorization_hash": "AUTH-ADAPTER",
            "damage_estimate_nef": "1500000",
            "authorization_json": "{}",
            "witness_event_id": "EV-AUTH",
        },
        escrow={
            "incident_id": "INC-ADAPTER",
            "escrow_id": "ESC-ADAPTER",
            "state": "RELEASED",
            "amount_nef": "1500000",
            "currency": "NEF",
            "transition_counter": 3,
        },
    )


def test_memory_adapter_is_explicitly_non_durable():
    adapter = MemorySettlementPersistence()
    publication = _publication()
    adapter.publish_settlement(publication)
    assert adapter.publications == [publication]


def test_sqlalchemy_adapter_uses_atomic_boundary(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'adapter.db'}", future=True)
    SHUUDPersistenceBase.metadata.create_all(engine)

    SQLAlchemySettlementPersistence(engine).publish_settlement(_publication())

    with engine.connect() as connection:
        assert len(connection.execute(select(SHUUDLifecycleEvent)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDReleaseAuthorizationRecord)).fetchall()) == 1
        assert len(connection.execute(select(SHUUDEscrowRecord)).fetchall()) == 1
