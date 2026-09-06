from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from gerchain.database import SessionLocal, engine, Base
from gerchain.models import RWAAsset, EscrowAccount, AuditTrail, MilestoneEvidence
import hashlib
import math

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gerchain + NEF RWA Dashboard", version="1.1.0")

@app.on_event("startup")
def startup_event():
    print("--- REGISTERED ROUTES ---")
    for route in app.routes:
        print(f"Path: {getattr(route, 'path', 'N/A')} | Methods: {getattr(route, 'methods', 'N/A')}")
    print("-------------------------")
    
    db = SessionLocal()
    try:
        if not db.query(RWAAsset).filter_by(asset_code="WB-MNG-2026-01").first():
            asset = RWAAsset(
                asset_code="WB-MNG-2026-01",
                asset_type="Windbreak Forest & Eco-Asset",
                location="Dundgovi Province",
                valuation_nef=150000.0,
                created_at=datetime.utcnow()
            )
            db.add(asset)
            
        if not db.query(EscrowAccount).filter_by(account_number="NEF-ESCROW-001").first():
            escrow1 = EscrowAccount(
                account_number="NEF-ESCROW-001",
                owner_name="National Escrow Fund Central",
                balance_nef=1000000.0,
                status="ACTIVE"
            )
            escrow2 = EscrowAccount(
                account_number="HERDER-ACC-05",
                owner_name="Dundgovi Herder Camp Association",
                balance_nef=50000.0,
                status="ACTIVE"
            )
            db.add_all([escrow1, escrow2])

        if db.query(AuditTrail).count() == 0:
            audit = AuditTrail(
                action="SYSTEM_FULL_INITIALIZED",
                details="Gerchain complete RWA, Escrow, and Milestone infrastructure initialized.",
                sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                timestamp=datetime.utcnow()
            )
            db.add(audit)
        db.commit()
    finally:
        db.close()

class AuditLogItem(BaseModel):
    id: int
    action: str
    details: Optional[str] = None
    sha256_hash: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    status: str
    count: int
    data: List[AuditLogItem]

class RWAAssetItem(BaseModel):
    id: int
    asset_code: str
    asset_type: str
    location: str
    valuation_nef: float
    created_at: datetime

    class Config:
        from_attributes = True

class RWAStatusResponse(BaseModel):
    status: str
    count: int
    rwa_assets: List[RWAAssetItem]

class RWAAssetCreate(BaseModel):
    asset_code: str
    asset_type: str
    location: str
    valuation_nef: float

class EscrowAccountItem(BaseModel):
    id: int
    account_number: str
    owner_name: Optional[str] = None
    balance_nef: float
    status: str

    class Config:
        from_attributes = True

class EscrowStatusResponse(BaseModel):
    status: str
    count: int
    escrow_accounts: List[EscrowAccountItem]

class EscrowCreateRequest(BaseModel):
    account_number: str
    owner_name: str
    initial_balance_nef: float

class EscrowTransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount_nef: float
    milestone_ref: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/audit/logs", response_model=AuditLogResponse)
def get_audit_logs(db: Session = Depends(get_db)):
    logs = db.query(AuditTrail).order_by(AuditTrail.timestamp.desc()).all()
    return {"status": "success", "count": len(logs), "data": logs}

@app.get("/api/v1/rwa/status", response_model=RWAStatusResponse)
def get_rwa_status(db: Session = Depends(get_db)):
    assets = db.query(RWAAsset).all()
    return {"status": "success", "count": len(assets), "rwa_assets": assets}

@app.post("/api/v1/rwa/register", response_model=dict)
def register_rwa_asset(asset_data: RWAAssetCreate, db: Session = Depends(get_db)):
    existing = db.query(RWAAsset).filter_by(asset_code=asset_data.asset_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Asset code already exists")
    
    new_asset = RWAAsset(
        asset_code=asset_data.asset_code,
        asset_type=asset_data.asset_type,
        location=asset_data.location,
        valuation_nef=asset_data.valuation_nef,
        created_at=datetime.utcnow()
    )
    db.add(new_asset)
    
    log_details = f"Registered new RWA: {asset_data.asset_code} at {asset_data.location}"
    sha_hash = hashlib.sha256(log_details.encode()).hexdigest()
    
    audit_log = AuditTrail(
        action="RWA_REGISTER",
        details=log_details,
        sha256_hash=sha_hash,
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "status": "success",
        "message": "RWA asset successfully registered and audited.",
        "asset_code": new_asset.asset_code,
        "sha256_hash": sha_hash
    }

@app.get("/api/v1/escrow/status", response_model=EscrowStatusResponse)
def get_escrow_status(db: Session = Depends(get_db)):
    accounts = db.query(EscrowAccount).all()
    return {"status": "success", "count": len(accounts), "escrow_accounts": accounts}

@app.post("/api/v1/escrow/create", response_model=dict)
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

@app.post("/api/v1/escrow/transfer", response_model=dict)
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

    # Milestone uniqueness invariant:
    # one milestone may authorize only one escrow transfer.
    #
    # This pre-check improves deterministic sequential behavior.
    # The database UNIQUE constraint on AuditTrail.milestone_ref
    # remains the authoritative concurrency protection.
    existing_transfer = (
        db.query(AuditTrail)
        .filter(
            AuditTrail.action == "ESCROW_MILESTONE_TRANSFER",
            AuditTrail.milestone_ref == milestone_ref
        )
        .first()
    )

    if existing_transfer:
        raise HTTPException(
            status_code=409,
            detail="Milestone reference has already been used for an escrow transfer."
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
        milestone_ref=milestone_ref,
        details=log_details,
        sha256_hash=sha_hash,
        timestamp=timestamp
    )

    try:
        sender.balance_nef = new_sender_balance
        receiver.balance_nef = new_receiver_balance
        db.add(audit_log)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Milestone reference has already been used for an escrow transfer."
        )

    except Exception as exc:
        db.rollback()
        print(
            "G-08.1 CONCURRENCY EXCEPTION:",
            type(exc).__name__,
            repr(exc)
        )
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

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_view(db: Session = Depends(get_db)):
    assets_count = db.query(RWAAsset).count()
    escrow_count = db.query(EscrowAccount).count()
    logs_count = db.query(AuditTrail).count()
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gerchain + NEF Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f4f7f6; color: #333; }}
            .card {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h1 {{ color: #1b4332; }}
            .metric {{ font-size: 24px; font-weight: bold; color: #2d6a4f; }}
        </style>
    </head>
    <body>
        <h1>Gerchain & NEF RWA Financial Dashboard</h1>
        <p>State-to-household financial flow and environmental asset tracking infrastructure.</p>
        <div class="card">
            <h3>Registered RWA Assets</h3>
            <div class="metric">{assets_count}</div>
        </div>
        <div class="card">
            <h3>Active Escrow Accounts</h3>
            <div class="metric">{escrow_count}</div>
        </div>
        <div class="card">
            <h3>Cryptographic Audit Logs</h3>
            <div class="metric">{logs_count}</div>
        </div>
        <p><a href="/docs">Open FastAPI Swagger Docs</a></p>
    </body>
    </html>
    """
    return html_content

from pydantic import BaseModel

class EvidenceSubmitRequest(BaseModel):
    milestone_ref: str
    asset_code: str
    herder_account: str
    gps_coordinates: str
    photo_url: str
    commission_act_ref: str

class EvidenceVerifyRequest(BaseModel):
    milestone_ref: str
    approved: bool
    amount_nef: float
    from_account: str = "NEF-ESCROW-001"
    verifier_notes: str

@app.post("/api/v1/evidence/submit")
def submit_evidence(data: EvidenceSubmitRequest, db: Session = Depends(get_db)):
    existing = db.query(MilestoneEvidence).filter_by(milestone_ref=data.milestone_ref).first()
    if existing:
        raise HTTPException(status_code=400, detail="Evidence for this milestone already submitted.")
    
    evidence = MilestoneEvidence(
        milestone_ref=data.milestone_ref,
        asset_code=data.asset_code,
        herder_account=data.herder_account,
        gps_coordinates=data.gps_coordinates,
        photo_url=data.photo_url,
        commission_act_ref=data.commission_act_ref,
        status="PENDING"
    )
    db.add(evidence)
    
    raw_data = f"{data.milestone_ref}:{data.herder_account}:{data.gps_coordinates}:{datetime.utcnow()}"
    sha_hash = hashlib.sha256(raw_data.encode()).hexdigest()
    
    audit = AuditTrail(
        action="EVIDENCE_SUBMITTED",
        details=f"Evidence submitted for milestone {data.milestone_ref} with act {data.commission_act_ref}",
        sha256_hash=sha_hash
    )
    db.add(audit)
    db.commit()
    
    return {"status": "success", "message": "Milestone evidence submitted successfully, pending verification.", "milestone_ref": data.milestone_ref}

@app.post("/api/v1/evidence/verify-and-release")
def verify_and_release(data: EvidenceVerifyRequest, db: Session = Depends(get_db)):
    evidence = (
        db.query(MilestoneEvidence)
        .filter_by(milestone_ref=data.milestone_ref)
        .first()
    )

    if not evidence:
        raise HTTPException(
            status_code=404,
            detail="Milestone evidence not found."
        )

    if evidence.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail=f"Milestone is already finalized with status: {evidence.status}"
        )

    if not data.approved:
        evidence.status = "REJECTED"

        audit_details = (
            f"Milestone {data.milestone_ref} rejected by verifier. "
            f"No funds released."
        )

        sha_hash = hashlib.sha256(
            audit_details.encode()
        ).hexdigest()

        audit = AuditTrail(
            action="EVIDENCE_REJECTED",
            details=audit_details,
            sha256_hash=sha_hash,
            timestamp=datetime.utcnow()
        )

        db.add(audit)
        db.commit()

        return {
            "status": "rejected",
            "message": "Milestone evidence rejected by commission.",
            "milestone_ref": data.milestone_ref,
            "sha256_hash": sha_hash
        }

    if not math.isfinite(data.amount_nef) or data.amount_nef <= 0:
        raise HTTPException(
            status_code=400,
            detail="Transfer amount must be a finite positive number."
        )

    from_account = data.from_account.strip()
    to_account = evidence.herder_account.strip()

    if not from_account or not to_account:
        raise HTTPException(
            status_code=400,
            detail="Sender and recipient escrow accounts are required."
        )

    if from_account == to_account:
        raise HTTPException(
            status_code=400,
            detail="Sender and recipient escrow accounts must be different."
        )

    from_acc = (
        db.query(EscrowAccount)
        .filter_by(account_number=from_account)
        .first()
    )

    to_acc = (
        db.query(EscrowAccount)
        .filter_by(account_number=to_account)
        .first()
    )

    if not from_acc:
        raise HTTPException(
            status_code=404,
            detail="Source escrow account not found."
        )

    if not to_acc:
        raise HTTPException(
            status_code=404,
            detail="Recipient escrow account not found."
        )

    if from_acc.status != "ACTIVE":
        raise HTTPException(
            status_code=409,
            detail="Source escrow account is not ACTIVE."
        )

    if to_acc.status != "ACTIVE":
        raise HTTPException(
            status_code=409,
            detail="Recipient escrow account is not ACTIVE."
        )

    if not from_acc.owner_name or not from_acc.owner_name.strip():
        raise HTTPException(
            status_code=409,
            detail="Source escrow account has no valid owner."
        )

    if not to_acc.owner_name or not to_acc.owner_name.strip():
        raise HTTPException(
            status_code=409,
            detail="Recipient escrow account has no valid owner."
        )

    if from_acc.balance_nef is None or from_acc.balance_nef < data.amount_nef:
        raise HTTPException(
            status_code=400,
            detail="Insufficient funds in source escrow account."
        )

    try:
        timestamp = datetime.utcnow()

        from_acc.balance_nef -= data.amount_nef
        to_acc.balance_nef += data.amount_nef
        evidence.status = "APPROVED"

        raw_data = (
            f"{from_account}->{to_account}:"
            f"{data.amount_nef}:"
            f"{data.milestone_ref}:"
            f"{timestamp.isoformat()}"
        )

        sha_hash = hashlib.sha256(
            raw_data.encode()
        ).hexdigest()

        audit = AuditTrail(
            action="EVIDENCE_VERIFIED_AND_RELEASED",
            details=(
                f"Milestone {data.milestone_ref} approved by commission. "
                f"Transferred {data.amount_nef} NEF to {to_account}"
            ),
            sha256_hash=sha_hash,
            timestamp=timestamp
        )

        db.add(audit)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Escrow release failed. Transaction rolled back."
        )

    return {
        "status": "success",
        "message": "Evidence verified and funds automatically released via escrow.",
        "milestone_ref": data.milestone_ref,
        "transferred_amount": data.amount_nef,
        "sha256_hash": sha_hash
    }
