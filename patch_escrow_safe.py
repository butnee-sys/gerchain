from pathlib import Path
import re

path = Path.home() / "gerchain" / "gerchain" / "web_ui.py"
text = path.read_text(encoding="utf-8")

create_pattern = re.compile(
    r'(@app\.post\("/api/v1/escrow/create", response_model=dict\)\n)'
    r'def create_escrow_account\(.*?(?=\n@app\.post\("/api/v1/escrow/transfer")',
    re.S,
)

create_replacement = r'''@app.post("/api/v1/escrow/create", response_model=dict)
def create_escrow_account(
    escrow_data: EscrowCreateRequest,
    db: Session = Depends(get_db)
):
    account_number = escrow_data.account_number.strip()
    owner_name = escrow_data.owner_name.strip()
    initial_balance = escrow_data.initial_balance_nef

    if not account_number:
        raise HTTPException(
            status_code=400,
            detail="Escrow account number is required."
        )

    if not owner_name:
        raise HTTPException(
            status_code=400,
            detail="Escrow account owner is required."
        )

    if not math.isfinite(initial_balance) or initial_balance < 0:
        raise HTTPException(
            status_code=400,
            detail="Initial balance must be a finite non-negative number."
        )

    existing = (
        db.query(EscrowAccount)
        .filter_by(account_number=account_number)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Escrow account number already exists."
        )

    timestamp = datetime.utcnow()

    new_escrow = EscrowAccount(
        account_number=account_number,
        owner_name=owner_name,
        balance_nef=initial_balance,
        status="ACTIVE"
    )

    log_details = (
        f"Created Escrow Account: {account_number} "
        f"for {owner_name} with initial balance {initial_balance} NEF"
    )

    raw_data = (
        f"ESCROW_CREATE:"
        f"{account_number}:"
        f"{owner_name}:"
        f"{initial_balance}:"
        f"{timestamp.isoformat()}"
    )

    sha_hash = hashlib.sha256(raw_data.encode()).hexdigest()

    audit_log = AuditTrail(
        action="ESCROW_CREATE",
        details=log_details,
        sha256_hash=sha_hash,
        timestamp=timestamp
    )

    try:
        db.add(new_escrow)
        db.add(audit_log)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Escrow account creation failed. Transaction rolled back."
        )

    return {
        "status": "success",
        "message": "Escrow account successfully created and audited.",
        "account_number": account_number,
        "sha256_hash": sha_hash
    }
'''

transfer_pattern = re.compile(
    r'(@app\.post\("/api/v1/escrow/transfer", response_model=dict\)\n)'
    r'def transfer_escrow_funds\(.*?(?=\n@app\.get\("/dashboard")',
    re.S,
)

transfer_replacement = r'''@app.post("/api/v1/escrow/transfer", response_model=dict)
def transfer_escrow_funds(
    transfer_data: EscrowTransferRequest,
    db: Session = Depends(get_db)
):
    from_account = transfer_data.from_account.strip()
    to_account = transfer_data.to_account.strip()
    milestone_ref = transfer_data.milestone_ref.strip()
    amount = transfer_data.amount_nef

    if not from_account or not to_account:
        raise HTTPException(
            status_code=400,
            detail="Sender and receiver escrow accounts are required."
        )

    if not milestone_ref:
        raise HTTPException(
            status_code=400,
            detail="Milestone reference is required."
        )

    if from_account == to_account:
        raise HTTPException(
            status_code=400,
            detail="Sender and receiver escrow accounts must be different."
        )

    if not math.isfinite(amount) or amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Transfer amount must be a finite positive number."
        )

    sender = (
        db.query(EscrowAccount)
        .filter_by(account_number=from_account)
        .first()
    )

    receiver = (
        db.query(EscrowAccount)
        .filter_by(account_number=to_account)
        .first()
    )

    if not sender:
        raise HTTPException(
            status_code=404,
            detail="Source escrow account not found."
        )

    if not receiver:
        raise HTTPException(
            status_code=404,
            detail="Recipient escrow account not found."
        )

    if sender.status != "ACTIVE":
        raise HTTPException(
            status_code=409,
            detail="Source escrow account is not ACTIVE."
        )

    if receiver.status != "ACTIVE":
        raise HTTPException(
            status_code=409,
            detail="Recipient escrow account is not ACTIVE."
        )

    if not sender.owner_name or not sender.owner_name.strip():
        raise HTTPException(
            status_code=409,
            detail="Source escrow account has no valid owner."
        )

    if not receiver.owner_name or not receiver.owner_name.strip():
        raise HTTPException(
            status_code=409,
            detail="Recipient escrow account has no valid owner."
        )

    if sender.balance_nef is None or not math.isfinite(sender.balance_nef):
        raise HTTPException(
            status_code=409,
            detail="Source escrow account has an invalid balance."
        )

    if receiver.balance_nef is None or not math.isfinite(receiver.balance_nef):
        raise HTTPException(
            status_code=409,
            detail="Recipient escrow account has an invalid balance."
        )

    if sender.balance_nef < amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient funds in source escrow account."
        )

    new_sender_balance = sender.balance_nef - amount
    new_receiver_balance = receiver.balance_nef + amount

    if not math.isfinite(new_sender_balance):
        raise HTTPException(
            status_code=409,
            detail="Resulting sender balance is invalid."
        )

    if not math.isfinite(new_receiver_balance):
        raise HTTPException(
            status_code=409,
            detail="Resulting receiver balance is invalid."
        )

    timestamp = datetime.utcnow()

    log_details = (
        f"Milestone [{milestone_ref}]: "
        f"Transferred {amount} NEF from "
        f"{sender.account_number} to {receiver.account_number}"
    )

    raw_data = (
        f"ESCROW_MILESTONE_TRANSFER:"
        f"{sender.account_number}->"
        f"{receiver.account_number}:"
        f"{amount}:"
        f"{milestone_ref}:"
        f"{timestamp.isoformat()}"
    )

    sha_hash = hashlib.sha256(raw_data.encode()).hexdigest()

    audit_log = AuditTrail(
        action="ESCROW_MILESTONE_TRANSFER",
        details=log_details,
        sha256_hash=sha_hash,
        timestamp=timestamp
    )

    try:
        sender.balance_nef = new_sender_balance
        receiver.balance_nef = new_receiver_balance
        db.add(audit_log)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Escrow transfer failed. Transaction rolled back."
        )

    return {
        "status": "success",
        "message": "Milestone-verified escrow transfer executed successfully.",
        "milestone_ref": milestone_ref,
        "transferred_amount": amount,
        "sha256_hash": sha_hash
    }
'''

create_match = create_pattern.search(text)
transfer_match = transfer_pattern.search(text)

if not create_match:
    raise SystemExit("ERROR: create_escrow_account block not found")

if not transfer_match:
    raise SystemExit("ERROR: transfer_escrow_funds block not found")

text = create_pattern.sub(create_replacement, text, count=1)
text = transfer_pattern.sub(transfer_replacement, text, count=1)

path.write_text(text, encoding="utf-8")

print("SAFE ESCROW HARDENING APPLIED")
