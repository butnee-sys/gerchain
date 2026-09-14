# GerChain CORE — IAM / MFA / Privileged Access Evidence

## Purpose

This document records the assurance boundary for IAM, MFA, and privileged-access evidence for GerChain CORE.

## Control status

The following controls remain **MISSING** until independently verifiable evidence is retained:

- `GC-IDM-001` — identity and access management
- `GC-IDM-002` — privileged access / MFA

Source-code authorization checks are not treated as proof of organizational MFA, account ownership, or privileged-access governance.

## Evidence required

1. GitHub repository access and role inventory.
2. MFA enforcement evidence for privileged accounts.
3. Privileged-role assignment and review evidence.
4. Administrative access logging / audit trail.
5. Joiner-mover-leaver or equivalent access review evidence.
6. Evidence retention tied to the audited CORE baseline.

## Fail-closed rule

No control is marked PASS merely because a security mechanism exists in source code. PASS requires externally verifiable operational evidence or an independently re-performed control test.

## Scope boundary

This document covers **GerChain CORE only**. SHUUD application users, workflows, API tests, sandbox evidence, and application-level access controls are outside this CORE evidence scope unless the audit scope is formally expanded.

## Current baseline

Frozen PwC documentation baseline:

`274f45c83ce088e2229a2628e3a80403a68503df`

PR #63 and PR #64 are implementation changes layered on the CORE assurance path; neither changes the rule above.
