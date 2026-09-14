# CORE / SHUUD Scope Boundary

## Purpose

Keep SHUUD application validation separate from GerChain CORE assurance.

## CORE scope

CORE PostgreSQL gates cover GerChain transaction, escrow, ledger, witness, idempotency, recovery and related infrastructure controls.

A failure in a SHUUD application test must not make a CORE infrastructure control appear failed.

## SHUUD scope

SHUUD has its own PostgreSQL persistence, API, sandbox, restart-recovery and application-level end-to-end tests. Those tests remain in SHUUD-specific workflows.

## Audit rule

PwC-style CORE evidence excludes SHUUD. SHUUD is an application built on GerChain CORE and is not part of the frozen CORE audit baseline unless explicitly brought into scope later.

## Frozen baseline

CORE audit baseline: `274f45c83ce088e2229a2628e3a80403a68503df`
