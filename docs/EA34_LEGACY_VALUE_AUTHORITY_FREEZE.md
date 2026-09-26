# EA-34.14 — Legacy Value Authority Freeze

Status: IMPLEMENTED / NOT LOCKED

## Frozen production authority

Canonical Ledger is the only production value authority:
- gerchain_ledger_accounts
- gerchain_ledger_movements
- PostgreSQLAtomicLedger transaction-aware boundary

## Legacy stores explicitly non-authoritative

The following must not be used for production value mutation:
- money.ledger.MoneyLedger
- persistence.atomic_release.ReleaseAccount
- persistence.atomic_settlement.AccountBalance
- persistence.atomic_release.ReleaseEscrow
- persistence.atomic_release.ReleaseWitness
- persistence.atomic_settlement.SettlementMovement
- SQLite database/db.py accounts.balance
- SQLite database/db.py escrows state/value
- gerchain/database.py SQLite fallback

## Runtime rule

Production runtime paths must fail closed rather than silently fall back to any legacy value authority.

## Current state

Runtime FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT and BALANCE READ have been cut toward canonical authorities. Legacy API/Web UI mutation endpoints have been disabled with HTTP 410. Docker production entrypoint now uses production_entrypoint.py.

## Remaining closure

This document does NOT claim that legacy tables are already physically read-only or removed. Physical freeze/removal requires migration evidence and independent re-performance.

Next:
EA-35 — Deep Cross-Store Value Truth Reconciliation.
