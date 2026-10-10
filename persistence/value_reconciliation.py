from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from persistence.atomic_release import ReleaseAccount
from persistence.atomic_settlement import AccountBalance


@dataclass(frozen=True)
class ValueReconciliationReport:
    canonical_accounts: int
    release_accounts: int
    settlement_accounts: int
    account_mismatches: tuple[dict[str, Any], ...]
    movement_count: int
    matched: bool


def _snapshot_canonical(session: Session) -> dict[str, tuple[str, int]]:
    return {
        row.account_id: (row.currency, int(row.balance))
        for row in session.execute(select(LedgerAccountModel)).scalars()
    }


def _snapshot_release(session: Session) -> dict[str, int]:
    return {
        row.account_id: int(row.balance)
        for row in session.execute(select(ReleaseAccount)).scalars()
    }


def _snapshot_settlement(session: Session) -> dict[str, int]:
    return {
        row.account_id: int(row.balance)
        for row in session.execute(select(AccountBalance)).scalars()
    }


def reconcile_value_stores(session: Session) -> ValueReconciliationReport:
    """Compare legacy balance stores with Canonical Ledger without mutating either.

    Balance equality is only one condition. Currency/account-set equality is also
    required; movement evidence remains separately inspectable through the
    canonical ledger movement table.
    """
    canonical = _snapshot_canonical(session)
    release = _snapshot_release(session)
    settlement = _snapshot_settlement(session)
    mismatches: list[dict[str, Any]] = []

    all_accounts = set(canonical) | set(release) | set(settlement)
    for account_id in sorted(all_accounts):
        canonical_value = canonical.get(account_id)
        release_value = release.get(account_id)
        settlement_value = settlement.get(account_id)

        expected = canonical_value[1] if canonical_value is not None else None
        if release_value is not None and release_value != expected:
            mismatches.append({
                "account_id": account_id,
                "store": "release",
                "canonical": expected,
                "legacy": release_value,
            })
        if settlement_value is not None and settlement_value != expected:
            mismatches.append({
                "account_id": account_id,
                "store": "settlement",
                "canonical": expected,
                "legacy": settlement_value,
            })
        if canonical_value is None and (release_value is not None or settlement_value is not None):
            mismatches.append({
                "account_id": account_id,
                "store": "canonical",
                "canonical": None,
                "legacy_release": release_value,
                "legacy_settlement": settlement_value,
            })

    movement_count = len(session.execute(select(LedgerMovementModel.id)).all())
    return ValueReconciliationReport(
        canonical_accounts=len(canonical),
        release_accounts=len(release),
        settlement_accounts=len(settlement),
        account_mismatches=tuple(mismatches),
        movement_count=movement_count,
        matched=not mismatches,
    )


__all__ = ["ValueReconciliationReport", "reconcile_value_stores"]
