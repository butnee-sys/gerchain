class MilestoneOracleEngine:
    def __init__(self, db_session):
        self.db = db_session

    def verify_and_release(self, milestone_id: int, oracle_proof: dict) -> bool:
        milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            raise ValueError("Milestone not found")

        if oracle_proof.get("verified_status") == "APPROVED" and oracle_proof.get("score", 0) >= 80:
            milestone.status = "RELEASED"
            escrow = milestone.escrow
            escrow.locked_amount -= milestone.allocated_amount
            escrow.balance += milestone.allocated_amount
            self.db.commit()
            return True

        return False
