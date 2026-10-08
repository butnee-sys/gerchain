"""Legacy SQLite repository compatibility models.

These helpers are test/legacy persistence only; production value authority remains
Canonical PostgreSQL Ledger infrastructure.
"""
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import JSON
from datetime import datetime, timezone

Base = declarative_base()

class EscrowStateModel(Base):
    __tablename__ = "escrow_states"
    id = Column(Integer, primary_key=True)
    escrow_id = Column(String, unique=True, nullable=False)
    state = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)
    history_json = Column(JSON, nullable=False, default=list)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class ChainTipModel(Base):
    __tablename__ = "chain_tips"
    id = Column(Integer, primary_key=True)
    chain_tip_hash = Column(String, nullable=False)
    manifest_hash = Column(String, nullable=False)
    state_root = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

def get_database_engine(connection_string: str = "sqlite:///gerchain.db"):
    return create_engine(connection_string, future=True)

__all__ = ["Base", "EscrowStateModel", "ChainTipModel", "get_database_engine"]
