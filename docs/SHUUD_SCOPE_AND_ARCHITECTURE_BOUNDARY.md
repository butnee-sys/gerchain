# SHUUD — Standalone Product Scope and Architecture Boundary

## 1. Purpose

This document formally separates SHUUD from GerChain CORE while preserving SHUUD as a first-class product/application layer.

## 2. Architecture boundary

NEF = Asset Truth.

G-3 Escrow = Condition Truth.

GerChain CORE = Value-Flow Truth infrastructure.

SHUUD = application/product layer consuming approved GerChain CORE capabilities.

SHUUD is not a CORE subsystem and must not be used to define the security, reliability, or audit status of GerChain CORE.

## 3. SHUUD scope

SHUUD assurance covers, separately:

- SHUUD Web
- SHUUD App
- SHUUD API
- SHUUD Command Layer
- SHUUD Sandbox
- SHUUD E2E flows
- SHUUD business logic
- insurer integration
- road-operation integration
- user-facing workflows
- SHUUD-specific security, performance and availability evidence

## 4. CORE exclusion

The following SHUUD results are excluded from CORE assurance calculations:

- SHUUD workflow failures
- SHUUD application tests
- SHUUD API/E2E failures
- SHUUD Sandbox results
- SHUUD-specific PostgreSQL/application tests

A SHUUD failure does not automatically constitute a GerChain CORE failure.

## 5. Assurance model

CORE and SHUUD maintain separate assurance registers, evidence sets and readiness decisions.

CORE assurance remains based on:
- CORE technical controls
- CORE CI gates
- PostgreSQL integrity/concurrency
- reconciliation
- cryptographic controls
- dependency/SBOM evidence
- repository security hygiene
- independent technical re-performance

SHUUD assurance is evaluated independently against its own product risks and acceptance criteria.

## 6. CORE interface boundary

SHUUD may consume approved CORE capabilities only through defined interfaces. SHUUD must not directly manipulate CORE persistence structures or bypass CORE integrity controls.

If SHUUD requires a capability that does not exist, the request enters the CORE change-control process rather than being implemented by bypassing CORE.

## 7. Change-control rule

SHUUD changes must not modify GerChain CORE solely to satisfy SHUUD application requirements. CORE changes require the existing protected-branch governance and CORE evidence gates.

## 8. Claims policy

SHUUD is a product implementation using GerChain infrastructure. It is not evidence that GerChain CORE itself is certified, independently audited, or compliant with any external standard.

## 9. Future integration

If SHUUD or another application requires additional CORE capability, that requirement is treated as a separately reviewed CORE change. Scope expansion must be explicitly approved and recorded; it must never occur implicitly through application development.
