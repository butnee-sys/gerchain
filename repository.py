from sqlalchemy.orm import sessionmaker
from database import get_database_engine, EscrowStateModel, ChainTipModel
import datetime

class GerchainRepository:
    def __init__(self, connection_string: str = "sqlite:///gerchain.db"):
        self.engine = get_database_engine(connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def save_escrow_state(self, escrow_id: str, state: str, amount: int, currency: str, history: list):
        """Эскроу төлөвийг хадгалах эсвэл шинэчлэх (Upsert)"""
        session = self.SessionLocal()
        try:
            existing = session.query(EscrowStateModel).filter_by(escrow_id=escrow_id).first()
            if existing:
                existing.state = state
                existing.amount = amount
                existing.currency = currency
                existing.history_json = history
                existing.updated_at = datetime.datetime.utcnow()
            else:
                new_escrow = EscrowStateModel(
                    escrow_id=escrow_id,
                    state=state,
                    amount=amount,
                    currency=currency,
                    history_json=history
                )
                session.add(new_escrow)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_escrow_state(self, escrow_id: str):
        """Эскроу төлөвийг ID-аар нь олж авах"""
        session = self.SessionLocal()
        try:
            record = session.query(EscrowStateModel).filter_by(escrow_id=escrow_id).first()
            if record:
                return {
                    "escrow_id": record.escrow_id,
                    "state": record.state,
                    "amount": record.amount,
                    "currency": record.currency,
                    "history": record.history_json,
                    "updated_at": record.updated_at.isoformat()
                }
            return None
        finally:
            session.close()

    def save_chain_tip(self, chain_tip_hash: str, manifest_hash: str, state_root: str):
        """Блокчэйн chain tip болон state root хадгалах"""
        session = self.SessionLocal()
        try:
            new_tip = ChainTipModel(
                chain_tip_hash=chain_tip_hash,
                manifest_hash=manifest_hash,
                state_root=state_root
            )
            session.add(new_tip)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
