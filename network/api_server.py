from fastapi import FastAPI, HTTPException
from network.transaction_manager import TransactionManager
from network.nef_state_engine import NEFStateEngine

app = FastAPI(title="Gerchain NEF Node API", version="1.0.0")

# Серверийн санах ойд NEF болон TransactionManager-ийг эхлүүлэх
nef_engine = NEFStateEngine(static_pool=1000000.0, dynamic_limit=500000.0)
tx_manager = TransactionManager(state_engine=nef_engine)

@app.get("/")
def read_root():
    return {"project": "Gerchain", "module": "NEF Escrow", "status": "active"}

@app.post("/transaction/create")
def create_tx(tx_id: str, amount: float):
    success = tx_manager.create_transaction(tx_id, amount)
    if not success:
        raise HTTPException(status_code=400, detail="Transaction creation failed or limit exceeded.")
    return {"status": "SUCCESS", "tx_id": tx_id, "amount": amount, "tx_status": "PENDING"}

@app.get("/transaction/{tx_id}")
def get_tx_status(tx_id: str):
    status = tx_manager.get_transaction_status(tx_id)
    return {"tx_id": tx_id, "status": status}
