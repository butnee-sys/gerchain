# CORE Capability Reconciliation — Pre-SHUUD Gate

**Status:** FROZEN CANDIDATE — reconciliation contract
**Purpose:** verify that the frozen DEE / G-3 / NEF / GerChain / EXIM / I2B architecture has no unowned or multiply-owned core authority before SHUUD real E2E work.

## Rule

This is a reconciliation gate, not an engine-building gate.

Every capability explicitly enumerated by the canonical architecture must have exactly one of these classifications:

- `AUTHORITATIVE` — one operational owner;
- `COMPOSITE` — composed only from existing authoritative owners;
- `BOUNDARY` — adapter, port, gateway, or translation only;
- `POLICY` — rule, constraint, governance, or decision authority;
- `STRUCTURAL` — schema, DTO, type, hash, or documentation only;
- `MISSING` — required behavior has no owner;
- `DUPLICATE` — more than one component claims the same authority.

`MISSING = 0` and `DUPLICATE = 0` are mandatory for CORE freeze.

## Authoritative architecture inventory

The following inventory is derived from `docs/DEE_ARCHITECTURE_FREEZE.md` and is the only pre-SHUUD architectural source of truth.

| Domain | Capability set | Classification / ownership rule |
|---|---|---|
| DEE | governance, policy, protection, trust framework, identity, access control, authorization policy, security, compliance, risk control, audit policy, data governance, recovery policy, interoperability | `POLICY` / `STRUCTURAL` / ecosystem authority; must not duplicate operational money, ledger, escrow, or settlement engines |
| G-3 | condition policy | `POLICY` |
| G-3 | escrow policy | `POLICY` |
| G-3 | governance policy | `POLICY` |
| G-3 | escrow trinity: trust + transparency + performance | `COMPOSITE` / policy benchmark; not a second operational escrow engine |
| NEF | asset registry | `AUTHORITATIVE` — NEF asset truth |
| NEF | asset identity | `AUTHORITATIVE` — NEF asset truth |
| NEF | ownership and rights | `AUTHORITATIVE` — NEF asset truth |
| NEF | valuation | `AUTHORITATIVE` — NEF asset truth |
| NEF | asset state | `AUTHORITATIVE` — NEF asset truth |
| NEF | asset evidence | `AUTHORITATIVE` — NEF asset truth |
| NEF | asset lifecycle | `AUTHORITATIVE` — NEF asset truth |
| NEF | collateral / encumbrance | `AUTHORITATIVE` — NEF asset truth |
| NEF | verification / validation linkage | `COMPOSITE` / NEF asset truth boundary |
| NEF | NEF audit | `AUTHORITATIVE` — NEF asset governance |
| NEF | NEF recovery | `AUTHORITATIVE` — NEF asset governance |
| GerChain | ledger engine | `AUTHORITATIVE` — operational value-flow ledger |
| GerChain | money engine | `AUTHORITATIVE` — operational money movement |
| GerChain | escrow engine | `AUTHORITATIVE` — operational escrow state |
| GerChain | witness engine | `AUTHORITATIVE` — witness/proof chain |
| GerChain | verification engine | `AUTHORITATIVE` — independent operational verification |
| GerChain | decision engine | `AUTHORITATIVE` — governed operational decision |
| GerChain | authorization engine | `AUTHORITATIVE` — execution authorization |
| GerChain | release engine | `AUTHORITATIVE` — release execution |
| GerChain | settlement engine | `AUTHORITATIVE` — settlement execution |
| GerChain | reconciliation engine | `AUTHORITATIVE` — value-flow reconciliation |
| GerChain | audit engine | `AUTHORITATIVE` — operational audit |
| GerChain | consensus engine | `AUTHORITATIVE` — governed consensus |
| GerChain | recovery engine | `AUTHORITATIVE` — operational recovery |
| EXIM | EXIM port | `BOUNDARY` — no operational engine ownership |
| I2B | I2B gateway | `BOUNDARY` — infrastructure-to-business routing |
| I2B | multi-connector | `BOUNDARY` — actor routing only |
| I2B | STATE / COMPANY / PERSON connectors | `BOUNDARY` — endpoint-specific integration only |
| Cross-layer | DEE → G-3 → NEF/GerChain → EXIM → I2B adapters | `BOUNDARY` — Layer → Adapter → Layer only |

## Explicit non-duplication invariants

The following authorities are singular:

1. one operational ledger authority;
2. one operational money-movement authority;
3. one operational escrow state authority;
4. one witness/proof authority;
5. one independent verification authority;
6. one release execution authority;
7. one settlement authority;
8. one authoritative NEF asset-truth authority;
9. adapters do not become operational engines;
10. G-3 does not become a second operational escrow engine;
11. NEF does not become a money, ledger, settlement, or release engine;
12. SHUUD is an application boundary and does not alter CORE ownership.

## Freeze decision

CORE may be declared frozen only when:

- the canonical architecture document is present and marked `FROZEN`;
- this reconciliation inventory is present;
- every listed capability has exactly one classification;
- `MISSING = 0`;
- `DUPLICATE = 0`;
- the singular-authority invariants are enforced by tests;
- the CORE gate workflow is green on the actual `main` ancestry;
- no SHUUD real-E2E implementation is used to satisfy a CORE requirement.

A capability that is absent from implementation but explicitly classified as `POLICY`, `BOUNDARY`, `COMPOSITE`, or `STRUCTURAL` is not a missing operational engine.

No new operational engine may be added solely to satisfy this gate.
