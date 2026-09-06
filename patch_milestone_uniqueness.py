from pathlib import Path

path = Path("gerchain/web_ui.py")
text = path.read_text(encoding="utf-8")

needle = '''    if not milestone_ref:
        raise HTTPException(
            status_code=400,
            detail="Milestone reference is required."
        )

'''

insert = '''    if not milestone_ref:
        raise HTTPException(
            status_code=400,
            detail="Milestone reference is required."
        )

    # Milestone uniqueness invariant:
    # one milestone may authorize only one escrow transfer.
    existing_transfers = (
        db.query(AuditTrail)
        .filter(
            AuditTrail.action == "ESCROW_MILESTONE_TRANSFER"
        )
        .all()
    )

    milestone_prefix = f"Milestone [{milestone_ref}]:"

    if any(
        audit.details
        and audit.details.startswith(milestone_prefix)
        for audit in existing_transfers
    ):
        raise HTTPException(
            status_code=409,
            detail="Milestone reference has already been used for an escrow transfer."
        )

'''

if text.count(needle) != 1:
    raise SystemExit(
        f"EXPECTED exactly 1 insertion point, found {text.count(needle)}"
    )

path.write_text(
    text.replace(needle, insert, 1),
    encoding="utf-8"
)

print("MILESTONE UNIQUENESS HARDENING APPLIED")
