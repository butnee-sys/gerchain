from sqlalchemy import create_engine, Column, String, Integer, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class EscrowStateModel(Base):
    __tablename__ = 'gerchain_escrow_states'
    
    escrow_id = Column(String(64), primary_key=True)
    state = Column(String(32), nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String(16), nullable=False)
    history_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ChainTipModel(Base):
    __tablename__ = 'gerchain_chain_tips'
    
    sequence_id = Column(Integer, primary_key=True, autoincrement=True)
    chain_tip_hash = Column(String(64), nullable=False, unique=True)
    manifest_hash = Column(String(64), nullable=False)
    state_root = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def get_database_engine(connection_string: str = "sqlite:///gerchain.db"):
    """Датабааз engine үүсгэх (PostgreSQL эсвэл SQLite)"""
    if connection_string.startswith("sqlite"):
        engine = create_engine(connection_string, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(connection_string, pool_pre_ping=True)
    return engine

def init_db(engine):
    """Хүснэгтүүдийг үүсгэх"""
    Base.metadata.create_all(engine)
