#!/usr/bin/env python3
"""One-command, fail-closed audit and narrowly scoped repair for production wiring.

Usage:
  python scripts/production_self_repair.py --check
  python scripts/production_self_repair.py --fix

Only a recognized legacy entrypoint constructor mismatch is auto-repaired.
Unknown or architecture-level drift is reported and left untouched.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "production_entrypoint.py"
FACTORY = ROOT / "services" / "gerchain_runtime_factory.py"


def diagnose(entrypoint: str, factory: str) -> list[str]:
    issues: list[str] = []
    if "ProductionRuntimeConfig" not in entrypoint:
        issues.append("ENTRYPOINT_CONFIG_IMPORT_MISSING")
    if "ProductionRuntimeFactory(" not in entrypoint or "factory.create()" not in entrypoint:
        issues.append("ENTRYPOINT_FACTORY_INSTANCE_CONTRACT")
    if "def create(self)" not in factory:
        issues.append("FACTORY_CREATE_SIGNATURE_DRIFT")
    if "configure_canonical_ledger(self.session_factory)" not in factory:
        issues.append("FACTORY_CANONICAL_AUTHORITY_DRIFT")
    if "initialize_canonical_postgres_schema(self.engine)" not in factory:
        issues.append("FACTORY_MIGRATION_GATE_DRIFT")
    if "require_canonical_ledger_authority()" not in factory:
        issues.append("FACTORY_FAIL_CLOSED_GATE_MISSING")
    return issues


def repair_entrypoint(entrypoint: str) -> tuple[str, bool]:
    """Repair only the exact known class-call/instance-method mismatch."""
    if "ProductionRuntimeFactory.create(" not in entrypoint:
        return entrypoint, False

    old = re.compile(
        r"    runtime = ProductionRuntimeFactory\.create\(\s*"
        r"escrow_id=escrow_id,\s*amount=amount,\s*currency=currency,\s*"
        r"witness_id=witness_id,\s*engine=engine,\s*session_factory=session_factory,\s*\)\s*",
        re.MULTILINE,
    )
    replacement = (
        "    factory = ProductionRuntimeFactory(\n"
        "        ProductionRuntimeConfig(\n"
        "            database_url=database_url,\n"
        "            escrow_id=escrow_id,\n"
        "            amount=amount,\n"
        "            currency=currency,\n"
        "            witness_id=witness_id,\n"
        "        ),\n"
        "        engine=engine,\n"
        "        session_factory=session_factory,\n"
        "    )\n"
        "    runtime = factory.create()\n"
    )
    updated, count = old.subn(replacement, entrypoint, count=1)
    if count != 1:
        raise RuntimeError(
            "ENTRYPOINT_FACTORY_INSTANCE_CONTRACT detected, but source did not match "
            "the one approved repair template; no changes written."
        )
    if "ProductionRuntimeConfig" not in updated:
        updated = updated.replace(
            "from services.gerchain_runtime_factory import ProductionRuntimeFactory",
            "from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory",
        )
    return updated, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="diagnose all known wiring invariants")
    mode.add_argument("--fix", action="store_true", help="apply only the approved deterministic repair")
    args = parser.parse_args()

    entrypoint = ENTRYPOINT.read_text(encoding="utf-8")
    factory = FACTORY.read_text(encoding="utf-8")

    if args.fix:
        try:
            updated, changed = repair_entrypoint(entrypoint)
        except RuntimeError as exc:
            print(f"BLOCKED: {exc}", file=sys.stderr)
            return 2
        if changed:
            ENTRYPOINT.write_text(updated, encoding="utf-8")
            entrypoint = updated
            print("REPAIRED: production entrypoint now uses the factory instance contract.")
        else:
            print("NO SAFE REPAIR NEEDED: no recognized legacy class-call pattern found.")

    issues = diagnose(entrypoint, factory)
    if issues:
        print("BLOCKED: production wiring invariants failed:")
        for issue in issues:
            print(f" - {issue}")
        print("Unknown drift is not auto-edited. Fix the source, then rerun --check.")
        return 1

    print("PASS: production entrypoint/factory wiring invariants are consistent.")
    print("NOTE: this is a static wiring check, not PostgreSQL boot or production-readiness proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
