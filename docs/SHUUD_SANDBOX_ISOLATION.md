# SHUUD + SANDBOX ISOLATION CONTRACT

Status: IMPLEMENTED / NOT LOCKED
Scope: SHUUD product/application testing only

## 1. Purpose

SHUUD Sandbox is an isolated execution and validation environment for SHUUD.
It is not part of the authoritative GerChain / NEF / G3 production truth.

The sandbox exists to test application behavior, integration contracts, failure
handling, timing, persistence adapters, and end-to-end flows without becoming
an alternative production authority.

## 2. Boundary

```
PROTECTED DIGITAL ECONOMIC INFRASTRUCTURE ZONE
NEF + G3 + GERCHAIN
        ^
        | controlled adapter / approved interface
        v
SHUUD APPLICATION
        |
        v
SHUUD SANDBOX
```

The SHUUD Sandbox may contain disposable application state, test fixtures,
mock providers, test PostgreSQL databases, synthetic identities, and
replayable test data.

## 3. Hard isolation rules

1. Sandbox data is never authoritative production truth.
2. Sandbox cannot mutate NEF authoritative asset truth.
3. Sandbox cannot mutate GerChain authoritative ledger truth.
4. Sandbox cannot mutate G3 policy or escrow-governance authority.
5. Sandbox cannot become a second Witness Chain.
6. Sandbox cannot become a second authoritative Ledger.
7. Sandbox cannot become a second Escrow Engine.
8. Sandbox cannot bypass approved adapters.
9. Sandbox value movement must use test credentials and isolated accounts.
10. Sandbox failures must not alter production state.
11. Production runtime must never silently fall back to sandbox state.
12. Sandbox tests must be reproducible and disposable.

## 4. SHUUD production boundary

SHUUD production requests follow:

SHUUD -> approved adapter/interface -> validation -> authorization ->
PDEIZ -> result

A request that attempts to alter protected-zone truth, policy, authority, or
core execution state directly is denied.

## 5. Sandbox boundary

SHUUD Sandbox follows:

SHUUD -> Sandbox Adapter -> isolated persistence/runtime -> evidence

No sandbox component is permitted to become an authority source for production.

## 6. Evidence

Every sandbox integration test that exercises a value-flow contract should
record:

- request/transaction identifier
- expected result
- actual result
- boundary used
- authorization decision
- witness/evidence reference where applicable
- cleanup/recovery result

Sandbox evidence supports development and validation; it does not replace
production PostgreSQL re-performance, CI evidence, or independent audit.

## 7. Production readiness gate

SHUUD Sandbox is considered isolated only when:

- no production imports depend on sandbox modules;
- no sandbox database is used by production runtime;
- no sandbox credentials are accepted by production;
- no sandbox state is read as authoritative;
- CI can run SHUUD sandbox tests independently from core production tests;
- failure/cleanup tests demonstrate no protected-zone mutation.

## 8. Canonical position

SHUUD Sandbox is therefore a **validation boundary**, not an economic
authority and not a new canonical architecture layer.
