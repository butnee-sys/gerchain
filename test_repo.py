from repository import GerchainRepository

if __name__ == "__main__":
    repo = GerchainRepository("sqlite:///gerchain.db")
    
    # 1. Эскроу төлөв хадгалах жишээ
    repo.save_escrow_state(
        escrow_id="escrow_nomad_001",
        state="LOCKED",
        amount=5000,
        currency="MNT",
        history=[{"action": "CREATED", "timestamp": "2026-06-07"}]
    )
    
    # 2. Хадгалсан төлөвөө уншиж шалгах
    data = repo.get_escrow_state("escrow_nomad_001")
    print("Retrieved Escrow Data:", data)
    
    # 3. Блокчэйн Tip хадгалах жишээ
    repo.save_chain_tip(
        chain_tip_hash="abc123hash",
        manifest_hash="manifest789",
        state_root="stateroot456"
    )
    print("Repository operations completed successfully!")
