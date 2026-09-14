# DEE Architecture Reconciliation

**Date:** 2026-09-14
**Purpose:** implementation guard for the frozen DEE architecture.

## Required dependency direction

```text
SHUUD / SHIID
→ Application Adapter
→ I2B / Open Multi-Connector Gateway
→ Multi-Connector Adapter
→ Country / EXIM Connector Adapter
→ EXIM Port
→ G3 / NEF + GerChain
```

The application layer must not import or instantiate a concrete EXIM connector. The connector layer is the only layer that imports the versioned EXIM Port package.

## Current reconciliation

PR #52 removes the concrete EXIM connector dependency from `application_adapters/shuud.py` and moves composition to the gateway boundary. The executable guard in `tests/test_dee_freeze_boundary.py` prevents the forbidden direct import from returning silently.

## Acceptance rule

A future implementation change is architecture-compatible only if the dependency direction above remains true and the frozen `docs/DEE_ARCHITECTURE_FREEZE.md` rules remain satisfied.
