# NEF–G-3–GerChain — ISO/IEC 27001 Evidence Status Model

**Status:** Controlled governance definition
**Branch:** `docs/iso27001-alignment`

## Statuses

| Status | Meaning |
|---|---|
| `AVAILABLE_OBJECTIVE` | Objective evidence exists, is traceable, reviewed and accepted. |
| `DOCUMENTED_REQUIREMENT` | Requirement/procedure/template exists, but operation is not yet evidenced. |
| `PARTIAL` | Some objective evidence exists, but the closure criteria are incomplete. |
| `MISSING` | Required evidence has not been supplied or verified. |
| `NOT_STARTED` | Required activity has not yet been performed. |
| `EXTERNAL` | Evidence must be obtained from an external party/independent assessor. |
| `OPEN` | Closure decision remains unresolved. |

## Non-equivalence rule

`DOCUMENTED_REQUIREMENT` must never be interpreted as `AVAILABLE_OBJECTIVE`.

A procedure, template, policy draft or requirement document demonstrates that a control has been designed or planned. It does not prove that the control is operating effectively.

## Promotion rule

Evidence may be promoted only when:

`Source → Owner → Date/Version → Traceability → Review → Decision`

are all present.

## Final readiness rule

No ISO/IEC 27001 certification or full-conformity claim may be made solely from repository documentation. Organizational operation and independent assessment remain required.
