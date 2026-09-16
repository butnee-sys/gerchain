# CORE Revalidation Gate v1.0

Status: REVALIDATION BASELINE — not GREEN/LOCK by itself

## Purpose

Revalidate the complete CORE after the Digital Model and Traceability Matrix changes, without introducing SHUUD into CORE.

## Hard boundary

SHUUD remains completely isolated until CORE reaches GREEN and is explicitly LOCKED.

## Required chain

Concept → Model → Contract → Code → Test → Evidence → Risk Closed → Freeze → GREEN → LOCK

## Revalidation gates

1. Authority — authoritative actor, scope, delegation, expiry, and execution ownership are traceable.
2. Protection — protection boundaries are explicit and do not permit authority bypass.
3. Witness — value-flow evidence is authoritative, reproducible, and linked to execution state.
4. Audit — audit truth is independently traceable to the governed execution/evidence chain.
5. PostgreSQL Authority — production release authority remains durable PostgreSQL state.
6. Concurrency — concurrent release attempts preserve exactly-once economic effect.
7. Outbox — PROCESSING lease, recovery, replay, and terminal handling are proven.
8. Recovery — crash/failure recovery preserves atomicity and replay safety.
9. NEF Truth — only validated authoritative NEF asset truth can cross into GerChain.
10. EXIM/I2B — external boundaries remain adapter/port governed with no CORE bypass.
11. Model Traceability — every canonical model element has Model → Contract → Code → Test → Evidence coverage or an explicitly recorded gap.

## GREEN rule

GREEN is permitted only when all required gates have current evidence on the revalidated branch/commit. Historical success on an earlier commit is baseline evidence, not current GREEN evidence.

## LOCK rule

LOCK is permitted only after GREEN, final risk review, and confirmation that no SHUUD dependency or workaround exists inside CORE.

## SHUUD rule

No SHUUD code, route, product logic, test, or architecture dependency may be used to close a CORE gate.
