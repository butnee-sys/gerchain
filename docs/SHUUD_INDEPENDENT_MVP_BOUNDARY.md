# SHUUD INDEPENDENT MVP BOUNDARY

**Status:** PROPOSED AMENDMENT — TO BE LOCKED AFTER RE-PERFORMANCE  
**Scope:** SHUUD only  
**Parent architecture:** DE / DEE / G-3 / NEF / GerChain canonical infrastructure

## 1. Canonical decision

SHUUD is the **first independent Digital Economy MVP**.

SHUUD is **not part of the fundamental infrastructure**, not part of EAI, not part of PDEIZ, and not a canonical infrastructure engine.

The fundamental infrastructure remains:

```
DEE → G-3 → NEF + GERCHAIN
```

SHUUD exists independently and may consume approved capabilities through explicit interfaces.

## 2. Independence invariant

```
SHUUD ≠ FUNDAMENTAL INFRASTRUCTURE
SHUUD ≠ EAI
SHUUD ≠ G-3
SHUUD ≠ NEF
SHUUD ≠ GERCHAIN CORE
SHUUD ≠ PDEIZ
```

No SHUUD component may become an authoritative source for:

- asset truth;
- ledger truth;
- money balance truth;
- escrow truth;
- witness-chain truth;
- release authority;
- settlement truth;
- G-3 policy;
- PDEIZ protected-zone state.

## 3. Allowed relationship

Only this direction is permitted:

```
SHUUD MVP
    ↓
explicit contract / adapter
    ↓
approved infrastructure interface
    ↓
NEF / G-3 / GerChain capability
    ↓
result / evidence
    ↓
SHUUD
```

The infrastructure must not import SHUUD application state or depend on SHUUD for its own correctness.

## 4. No reverse dependency

The following are prohibited:

```
CORE → SHUUD implementation
NEF → SHUUD database
G-3 → SHUUD policy
Ledger → SHUUD state
Witness → SHUUD witness
EAI → SHUUD runtime
PDEIZ → SHUUD implementation
```

SHUUD may request a capability; it cannot redefine the capability.

## 5. MVP independence

SHUUD must be independently:

- started;
- tested;
- deployed;
- versioned;
- persisted;
- recovered;
- audited;
- released;
- failed;
- upgraded.

A SHUUD failure must not make the fundamental infrastructure fail.

A fundamental-infrastructure failure must not convert SHUUD state into authoritative infrastructure truth.

## 6. Current repository evidence

The current repository already contains a logical isolation contract at:

`docs/SHUUD_SANDBOX_ISOLATION.md`

That contract states that SHUUD Sandbox is not authoritative production truth and cannot mutate NEF, GerChain, or G-3 authority.

The current SHUUD integration shim also contains no direct GerChain/NEF imports and routes through `nef_gerchain_port`.

However, the current repository still physically contains the `shuud/` application package and SHUUD-specific tests/workflows.

Therefore:

**Logical isolation: IMPLEMENTED.**  
**Physical product/repository separation: NOT YET LOCKED.**

This distinction must not be hidden.

## 7. Separation target

The first independent SHUUD MVP should have:

```
SHUUD MVP
├── own application runtime
├── own application persistence
├── own tests
├── own CI
├── own release/version
└── explicit infrastructure client/adapter
```

The fundamental repository should retain only the stable contract required to consume SHUUD, if such a contract is needed.

## 8. Production gate

SHUUD may be called independently production-ready only after:

1. no core runtime imports SHUUD;
2. no core database depends on SHUUD tables;
3. no core authority depends on SHUUD state;
4. SHUUD can run independently;
5. SHUUD tests run independently;
6. SHUUD persistence is isolated;
7. SHUUD credentials are isolated;
8. SHUUD failure-injection proves no PDEIZ mutation;
9. interface contract is independently verified;
10. repository/product separation is re-performed.

## 9. Architectural consequence

SHUUD must not delay, modify, or redefine the production lock of the fundamental infrastructure.

The correct sequence is:

```
FUNDAMENTAL INFRASTRUCTURE
        ↓
EAI / CORE production proof
        ↓
LOCK FUNDAMENTAL INFRASTRUCTURE
        ↓
INDEPENDENT SHUUD MVP
        ↓
CONTRACT-BASED INTEGRATION
```

SHUUD is therefore the **first independent consumer/MVP**, not another layer of the infrastructure.
