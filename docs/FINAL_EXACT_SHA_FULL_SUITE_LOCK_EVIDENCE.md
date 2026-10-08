# FINAL EXACT-SHA FULL-SUITE LOCK EVIDENCE

Date: 2026-10-08

## 1. Locked evidence commit

**Commit:** `90f8cef1a2f27a198a3d80e13f0c4c65106a455d`

This document is valid only for the exact commit above.


## 1A. Evidence document integrity / commit-role separation

This document is an **evidence record**, not the code commit whose state it verifies.

- **Verified code/evidence SHA:** `90f8cef1a2f27a198a3d80e13f0c4c65106a455d`
- **Evidence-document commit:** `d22cccb` (the commit that introduced this document)

These two SHAs MUST NOT be conflated. The evidence SHA identifies the repository state on which the listed verification runs were executed; the document commit identifies the version of this evidence record.

The document therefore does **not** claim that `d22cccb` itself was the tested code state. It records the verification performed against `90f8cef`.

## 1B. Current-state lock rule

The lock is valid only for the exact verified code/evidence SHA stated above. Any code, workflow, test, schema, runtime, or production-entrypoint change after that SHA invalidates the lock for the newer repository state until the full exact-SHA verification cycle is repeated.

A documentation-only commit may preserve the historical evidence record without changing the verified code SHA. A subsequent code change MUST NOT be described as covered by this historical lock.

## 2. Failure corrected

Predecessor evidence at `972db96e0ee3f913daed7f9bf7b5f6d944953d85` produced:

- `pytest -q`: **FAIL**
- collection stage: **24 errors**

Root causes identified:
1. missing `database.get_database_engine`
2. syntax corruption in `gerchain/web_ui.py`
3. missing `dee_security.contract_governance`

The correction commit `90f8cef1a2f27a198a3d80e13f0c4c65106a455d` restores the required compatibility/protected governance boundary and the affected test/runtime imports.

## 3. Exact-SHA verification

GitHub Actions runs associated with the exact SHA completed successfully:

- EAI PostgreSQL Production Proof — run `37802761971`
- core-gates — run `37802762044`
- production-postgresql-gate — run `37802762348`
- production-postgresql-reperformance — run `37802761968`
- Production PostgreSQL Re-performance — run `37802762197`
- production-postgres — run `37802762191`
- independent-postgresql-evidence — run `37802762163`
- DEE Security Gate — run `37802762009`
- CORE Operating Reconciliation — run `37802761988`
- CodeQL Advanced — run `37802762092`

## 4. Exact full-suite result

The exact-SHA `core-gates` runner executed the repository gate test command and reported:

**47 passed in 4.40s**

Therefore the previously observed 24 collection errors are no longer present on the exact evidence SHA.

## 5. PostgreSQL production proof

The exact-SHA production gate completed successfully through:

- Python syntax gate
- production factory and canonical persistence verification
- production entrypoint boot against PostgreSQL
- concurrent PostgreSQL migration bootstrap
- deep reconciliation tests
- EAI production re-performance
- real PostgreSQL production value-flow gate

The production PostgreSQL gate reported all steps successful.

## 6. Independent evidence

The exact-SHA independent PostgreSQL evidence run completed successfully:

- Independent persisted-value verification — **success**

## 7. Security / fundamental architecture evidence

The exact-SHA security and fundamental architecture gates completed successfully:

- DEE Security Gate — **success**
- CORE/fundamental architecture gate — **success**
- CodeQL Advanced — **success**
- CORE Operating Reconciliation — **success**

## 8. Lock decision

**FINAL EXACT-SHA FULL-SUITE: PASS**

**FINAL LOCK: AUTHORIZED FOR THIS EVIDENCE SHA**

The lock applies to the verified repository state represented by:

`90f8cef1a2f27a198a3d80e13f0c4c65106a455d`

Any subsequent code change invalidates this lock and requires a new exact-SHA verification cycle before a new FINAL LOCK can be issued.

## 9. Scope

This lock covers the verified fundamental architecture / EAI production evidence represented by the listed gates. It does not silently authorize unrelated future architectural changes.

**Rule: evidence first; lock second.**
