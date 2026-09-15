# GerChain CORE — SBOM Evidence Requirements

## Purpose

Record the software supply-chain inventory for the GerChain CORE assurance package without exposing proprietary source code.

## Required evidence

- SPDX-format SBOM generated from the repository dependency graph or controlled CI.
- Dependency name and version.
- Direct/transitive relationship where available.
- Package identifier.
- License information where available.
- Generation date and repository commit SHA.
- Tool and tool version used to generate the SBOM.
- Evidence artifact checksum.

## Acceptance rule

The SBOM is evidence of dependency transparency. It is not a security certification and does not grant any license to the proprietary GerChain CORE source code.

## Scope exclusion

SHUUD dependencies are not included in the CORE assurance SBOM unless a future scope decision explicitly expands the assurance boundary.
