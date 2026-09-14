# GerChain Capability Audit — GATE-02

**Status:** active audit; CORE is not frozen.
**Date:** 2026-09-14

This audit distinguishes a capability that is actually executable from a name,
contract, or adapter. A capability is marked **AUTHORITATIVE** only when the
current GerChain runtime owns the operation and there is executable test
coverage for its invariant. A boundary adapter is never counted as a second
operational engine.

## Current verified authoritative capabilities

| Capability | Current owner | Evidence | Status |
|---|---|---|---|
| Money ledger / balances | `MoneyLedger` | `services/gerchain_runtime.py`, runtime lifecycle tests | AUTHORITATIVE |
| Money movement | `MoneyEngine` | runtime lifecycle + atomic release tests | AUTHORITATIVE |
| Escrow lifecycle | `EscrowEngine` / `AuthoritativeEscrowService` | runtime lifecycle tests | AUTHORITATIVE |
| Witness chain | `WitnessChain` | witness-sequence + verification tests | AUTHORITATIVE |
| Independent verification | `V80IndependentVerifier` | runtime verification tests | AUTHORITATIVE |
| Idempotency | `IdempotencyEngine` / PostgreSQL idempotency store | idempotency + PostgreSQL tests | AUTHORITATIVE |
| Hold / reservation | `HoldEngine` | hold tests | AUTHORITATIVE |
| Limits | `LimitEngine` | limit tests | AUTHORITATIVE |
| Transaction lifecycle | `TransactionStateMachine` | lifecycle tests | AUTHORITATIVE |
| PostgreSQL release authority | `PostgreSQLReleaseAdapter` / `PostgreSQLAtomicRelease` | PostgreSQL runtime + concurrency tests | AUTHORITATIVE |

## Boundary-only capabilities

These are composition or translation mechanisms and must never become value,
ledger, escrow, witness, settlement, or asset-truth engines:

- DE → DEE adapter
- DEE → G-3 adapter
- G-3 → Core adapter
- Core → EXIM adapter
- EXIM → I2B adapter
- I2B Service Center / MultiConnector routing

## Explicit non-duplication rule

The following operational authorities remain singular inside Core:

1. one money ledger
2. one money movement engine
3. one escrow state-transition authority
4. one witness chain
5. one independent verifier
6. one authoritative PostgreSQL release path

Adapters may validate, translate, route, and fail closed. They may not create a
parallel implementation of any of the above.

## GATE-02 completion criteria

Before CORE can be frozen, the remaining conceptual capability list must be
reconciled against executable code and tests. Each item must be classified as
exactly one of:

- **AUTHORITATIVE** — executable owner exists and invariant is tested.
- **COMPOSITE** — capability is a composition of existing authorities; no new
  engine is allowed.
- **BOUNDARY** — adapter/port/gateway only.
- **POLICY** — decision/constraint only; does not move value or own asset truth.
- **STRUCTURAL** — schema/type/documentation only; not an engine.
- **MISSING** — required capability has no authoritative implementation.
- **DUPLICATE** — more than one implementation claims the same authority.

A **MISSING** or **DUPLICATE** item blocks CORE freeze.

## Current conclusion

The first code-level audit confirms that GerChain already has a coherent set of
value-flow authorities. The next risk is not adding another engine; it is proving
that every remaining conceptual capability maps to one of these authorities or
is explicitly classified as composite, boundary, policy, or structural.

Therefore this gate must continue with capability-by-capability reconciliation
rather than adding new operational engines.
