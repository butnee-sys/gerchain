# EA-35.13 PostgreSQL re-performance trigger

This marker intentionally contains no runtime or architecture change.

Purpose:
- trigger the branch-scoped PostgreSQL production proof workflows;
- capture fresh evidence against the current branch tip;
- do not treat prior workflow failures as current GREEN evidence.

Gate remains NOT LOCKED until the fresh PostgreSQL runs complete successfully.


## 2026-10-06 verification trigger
The EA-35 PostgreSQL production smoke workflow is the authoritative CI execution gate for this re-performance. The gate must pass on the current branch head before production evidence is treated as verified.

## 2026-10-06 verification trigger — production runtime correction
The production runtime construction was corrected to instantiate ProductionRuntimeFactory with ProductionRuntimeConfig and to establish Canonical Ledger authority. This marker requires a fresh PostgreSQL gate against that corrected branch state.

## 2026-10-06 verification trigger — fresh current-tip evidence
This trigger exists solely to force fresh CI evidence against the current branch tip after the production runtime and migration hardening changes. Prior runs remain historical evidence only.


## 2026-10-06 verification trigger — final current-tip re-performance
This evidence-only revision requires fresh exact-SHA PostgreSQL production, independent PostgreSQL evidence, CORE reconciliation, and CodeQL execution against the resulting commit. No previous SHA is reused as current proof.

Decision rule: EA-35 remains VERIFIED / NOT LOCKED until the resulting exact SHA has fresh successful canonical production evidence and the final lock gaps are reviewed.
