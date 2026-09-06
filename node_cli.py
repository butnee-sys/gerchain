import sys
from network.transaction_manager import TransactionManager
from network.nef_state_engine import NEFStateEngine

def main():
    print("=== Gerchain NEF Node CLI ===")
    nef = NEFStateEngine(static_pool=50000.0, dynamic_limit=25000.0)
    manager = TransactionManager(state_engine=nef)
    
    # Жишээ тест командын ажиллагаа
    tx_id = "cli_tx_001"
    amount = 500.0
    
    if manager.create_transaction(tx_id, amount):
        print(f"[{tx_id}] Created successfully with amount {amount}")
        if manager.lock_transaction(tx_id):
            print(f"[{tx_id}] Locked in Escrow")
            if manager.release_transaction(tx_id):
                print(f"[{tx_id}] Released successfully")
    
    print(f"Final Status: {manager.get_transaction_status(tx_id)}")

if __name__ == "__main__":
    main()
