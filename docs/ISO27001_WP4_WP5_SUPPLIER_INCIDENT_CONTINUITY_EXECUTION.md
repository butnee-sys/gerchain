# ISO/IEC 27001:2023 — WP4/WP5 Supplier, Incident and Continuity Execution

**Status:** Controlled execution checklist  
**Branch:** `docs/iso27001-alignment`  
**CORE baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## Objective

Close the next critical organizational controls around suppliers, incidents, backup, continuity, logging and monitoring while preserving the frozen CORE assurance baseline.

## Control groups

### WP4 — Supplier / cloud / ICT supply chain

- A.5.19 Supplier relationships
- A.5.20 Supplier agreements
- A.5.21 ICT supply chain
- A.5.22 Supplier-service monitoring and change
- A.5.23 Cloud-service security

### WP5 — Incident / continuity / recovery / evidence

- A.5.24 Incident planning and preparation
- A.5.25 Event assessment and decision
- A.5.26 Incident response
- A.5.27 Lessons learned
- A.5.28 Evidence collection
- A.5.29 Security during disruption
- A.5.30 ICT readiness for business continuity
- A.8.13 Information backup
- A.8.14 Redundancy
- A.8.15 Logging
- A.8.16 Monitoring activities

## Required objective evidence

### Supplier evidence

1. Complete supplier register.
2. Identify information, system and access dependencies.
3. Perform security due diligence proportional to risk.
4. Verify security clauses and incident-notification obligations.
5. Record supplier-service review and material changes.
6. Document cloud shared-responsibility boundaries where cloud services are used.
7. Record offboarding and access/data return or deletion.

### Incident evidence

1. Approved incident-response procedure.
2. Reporting channel and incident register.
3. Severity/classification criteria.
4. Triage and decision records.
5. Containment, recovery and notification records where applicable.
6. At least one controlled exercise/tabletop or equivalent operational test.
7. Post-exercise lessons and corrective actions.

### Continuity and backup evidence

1. Backup inventory and owner.
2. Backup frequency, retention and protected storage.
3. Integrity verification.
4. Actual restore test with dated result.
5. RPO/RTO definitions and test evidence.
6. Continuity dependencies and recovery priorities.
7. Redundancy assessment where required by availability risk.

### Logging and monitoring evidence

1. Log-source inventory.
2. Retention and access rules.
3. Monitoring responsibilities.
4. Alert/response records where applicable.
5. Time synchronization requirements and evidence.
6. Protection against unauthorized alteration or deletion.

## CORE supporting evidence

Existing GerChain CORE mechanisms such as Witness/audit records, reconciliation, recovery, transaction integrity and automated checks may support these controls. They do not replace the required organizational procedures, ownership, records or exercises.

## Acceptance rule

A control moves from GAP/PARTIAL only after objective evidence satisfies:

`Source → Owner → Date/Version → Traceability → Review → Decision`

## Security restriction

No secrets, passwords, private keys, API tokens, recovery codes or production credentials may be stored in this repository.

## Current status

**OPEN.** Requirement documents exist; actual organizational and operational evidence remains to be collected and reviewed.
