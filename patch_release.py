from pathlib import Path
import re

path = Path("gerchain/web_ui.py")
text = path.read_text(encoding="utf-8")

if "import math" not in text:
    text = text.replace(
        "import hashlib",
        "import hashlib\nimport math",
        1
    )

pattern = r'@app\.post\("/api/v1/evidence/verify-and-release"\)[\s\S]*?(?=\n@app\.|\Z)'

replacement = r'''@app.post("/api/v1/evidence/verify-and-release")
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
'''

new_text, count = re.subn(
    pattern,
    replacement,
    text,
    count=1
)

if count != 1:
    raise SystemExit(
        "ERROR: verify-and-release block was not found."
    )

path.write_text(new_text, encoding="utf-8")

print("VERIFY-AND-RELEASE HARDENING APPLIED")