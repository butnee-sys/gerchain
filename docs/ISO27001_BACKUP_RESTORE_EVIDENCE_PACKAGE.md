# NEF–G-3–GerChain — Backup / Restore Evidence Package

**Status:** Evidence template — operational completion required
**Branch:** `docs/iso27001-alignment`

## 1. Objective

Demonstrate that scoped information and critical operational data are backed up, protected, retained and can be restored within defined recovery objectives.

## 2. Required evidence

### Backup register
- system/data set;
- owner;
- backup method;
- frequency;
- retention;
- storage location;
- protection/access controls;
- last successful backup verification.

### Restore test
- test date;
- source backup identifier;
- target environment;
- restoration procedure/version;
- result;
- integrity verification;
- observed recovery time;
- corrective action, if failed.

### Recovery objectives
- approved RPO;
- approved RTO;
- business owner;
- technical owner;
- dependency list;
- periodic review.

## 3. Technical boundary

GerChain CORE recovery mechanisms and transaction-integrity tests are supporting technical evidence. They do not, by themselves, establish organizational backup retention, ownership, restore scheduling or approved RPO/RTO.

## 4. Evidence protection

Backup credentials, encryption keys, tokens and production connection strings must never be stored in this document or ordinary repository evidence.

## 5. Acceptance test

Move from **MISSING** to **AVAILABLE** only after a real restore test is completed, recorded, reviewed and linked to the applicable control/risk.

## 6. Gate

**Current status: MISSING — operational backup/restore evidence not yet verified.**
