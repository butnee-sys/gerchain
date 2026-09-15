# NEF–G-3–GerChain — Cryptographic Key Management Requirements

**Status:** Controlled requirements — evidence pending

## 1. Purpose

Define the organizational evidence required to demonstrate controlled cryptographic key lifecycle management for the NEF–G-3–GerChain ISMS scope.

## 2. Required lifecycle

`Generate → Register → Protect → Distribute → Use → Rotate → Revoke → Archive/Destroy`

The exact mechanism shall be selected according to risk and the actual production environment.

## 3. Required evidence

- key inventory;
- key purpose and owner;
- system/service association;
- classification and sensitivity;
- generation method;
- storage/custody mechanism;
- access authorization;
- rotation schedule or risk-based justification;
- compromise/revocation procedure;
- backup/recovery arrangements where applicable;
- destruction/retirement evidence;
- emergency response procedure;
- periodic review.

## 4. Separation of environments

Development, testing and production credentials/keys shall be distinguished. Production secrets must not be committed to the repository or ordinary presentation/archive media.

## 5. Technical evidence boundary

Cryptographic implementation visible in GerChain code/tests can demonstrate technical behavior. It does not, by itself, prove organizational key custody, access approval, rotation governance or incident response.

## 6. Required evidence owner

A named security/technical owner and a reviewer shall be assigned before this control can be closed.

## 7. Gate

**Cryptographic key management: MISSING — objective organizational evidence required.**
