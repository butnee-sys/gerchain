# NEF–G-3–GerChain — Privileged Access Evidence Package

**Status:** Evidence template — organizational completion required

## 1. Required register

For each privileged identity record:

- account/identity;
- privileged role;
- system/environment;
- business/technical owner;
- authorization reference;
- MFA status;
- purpose and permitted actions;
- last review;
- revocation/expiry status.

## 2. Operating evidence

The evidence set should demonstrate:

- approval before privileged access;
- least-privilege assignment;
- separation of duties where appropriate;
- periodic review;
- emergency/break-glass access handling;
- timely removal or downgrade;
- logging and review of privileged activity where applicable.

## 3. CORE linkage

Protected GitHub branches, required reviews and CI controls support development governance but do not replace the organizational privileged-account register and periodic review.

## 4. Secrets rule

Never store privileged credentials, tokens, private keys or recovery codes in the repository.

## 5. Acceptance test

Status may move from **MISSING** to **AVAILABLE** only after an authorized reviewer verifies the complete controlled register and records the decision.

## 6. Gate

**Current status: MISSING — privileged-access evidence not yet supplied/verified.**
