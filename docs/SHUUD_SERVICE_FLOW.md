# SHUUD Service Flow

SHUUD is an application service. It does not own ledger, escrow, witness, asset truth, authorization, or settlement.

```text
SHUUD
  ↓
I2B Service Center
  ↓
I2B Connection Gateway
  ↓
EXIM Port
  ↓
G-3 policy / Trinity
  ↓
DEE authorization
  ↓
NEF asset truth + GerChain value flow
  ↓
Atomic Release
  ↓
Settlement / payout
```

## Rapid-release boundary

The SHUUD service accepts a verified minor-incident request and rejects it closed when evidence is not verified or compensation exceeds the configured ₮2,000,000 application limit.

The application limit is a SHUUD policy, not a replacement for G-3, DEE authorization, or GerChain release governance.

## Core rule

SHUUD may request release; only the governed core may authorize and execute authoritative value movement.
