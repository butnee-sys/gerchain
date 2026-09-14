# GerChain CORE — Audit Lock Status

**Document status:** Working audit record  
**Scope:** GerChain CORE only  
**SHUUD:** Explicitly out of CORE assurance scope  
**Frozen PwC baseline:** `274f45c83ce088e2229a2628e3a80403a68503df`  
**Current main commit under audit:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## 1. Current disposition

| Control / area | Status | Basis |
|---|---|---|
| Atomic release / idempotency | GREEN | CORE test and PostgreSQL evidence retained |
| PostgreSQL concurrency | GREEN | CORE-only PostgreSQL workflow and successful evidence |
| `GC-RES-003` abandoned PROCESSING recovery | GREEN | PR #63 merged; dedicated recovery tests |
| Operating DB reconciliation | GREEN | PR #64 merged; reconciliation tests and workflow |
| CORE/SHUUD scope boundary | GREEN | CORE-only PostgreSQL workflow + scope-boundary evidence; PR #67 |
| DEE cryptographic controls | GREEN | Key-management and security test evidence retained |
| CodeQL | GREEN | Successful security workflow evidence |
| Post-merge main CORE CI | GREEN | Main commit `621e7e2...` has successful CORE workflow evidence |
| Main branch governance | GREEN / VERIFIED | Active `CORE-main-protection` ruleset, ID `23342561`; required CORE checks configured |
| PwC evidence baseline | FROZEN | Baseline SHA retained; no false promotion |
| `GC-IDM-001` IAM/MFA organizational evidence | MISSING | Organizational IAM/MFA evidence is not independently retained |
| `GC-IDM-002` privileged access governance | MISSING | Role assignment/review/access-governance evidence is not independently retained |
| `GC-IND-001` independent re-performance | OPEN | Independent reviewer re-performance record not yet retained |

## 2. Remaining closure gates

### GC-IDM-001 — IAM/MFA

Obtain dated, organization-level evidence showing privileged-account inventory and MFA enforcement. Source-code security tests, CODEOWNERS, or a ruleset do not substitute for this evidence.

### GC-IDM-002 — Privileged access governance

Obtain privileged-role assignment/approval, periodic access review, joiner-mover-leaver or equivalent removal evidence, and administrative access traceability.

### GC-IND-001 — Independent re-performance

An independent reviewer must reproduce the material CORE controls against the frozen audited commit, retain raw output, and sign/date the conclusion with their independence identified.

## 3. Lock rule

The technical CORE baseline is verified, but the **formal CORE audit lock is NOT declared** until `GC-IDM-001`, `GC-IDM-002`, and `GC-IND-001` are GREEN, or formally accepted as audit exceptions by the responsible authority.

## 4. Non-negotiable principles

1. Source-code presence is not organizational control evidence.
2. A test PASS is not proof of organizational IAM/MFA governance.
3. SHUUD is not included in CORE control conclusions.
4. Frozen PwC documents are not silently rewritten to claim later evidence.
5. Final conclusions must identify the exact audited commit or retained evidence artifact.
6. Ambiguous states remain OPEN/MISSING rather than being promoted to PASS.
