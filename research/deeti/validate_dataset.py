"""DEETI Evidence Dataset v1 validator.

This script performs schema/integrity checks only. It does not infer causality
and does not alter the empirical dataset.
"""

from __future__ import annotations

import csv
from pathlib import Path

DATA = Path(__file__).parent / "data" / "deeti_evidence_v1.csv"

REQUIRED = [
    "observation_id", "domain", "jurisdiction", "period",
    "et_trust", "et_transparency", "et_fulfilment", "eti",
    "transaction_value", "transaction_complexity", "verification_time",
    "completion_time", "settlement_delay", "failure_flag", "dispute_flag",
    "evidence_complete", "condition_verified", "correct_settlement",
    "direct_cost", "control_group", "data_source", "source_version",
]

SCORES = ["et_trust", "et_transparency", "et_fulfilment", "eti"]
BINARY = ["failure_flag", "dispute_flag", "evidence_complete", "condition_verified", "correct_settlement"]


def as_float(row: dict[str, str], field: str, line: int) -> float:
    try:
        value = float(row[field])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"line {line}: {field} must be numeric") from exc
    return value


def validate() -> int:
    with DATA.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        missing = [f for f in REQUIRED if f not in fields]
        if missing:
            raise ValueError(f"missing required fields: {missing}")

        rows = 0
        for line, row in enumerate(reader, start=2):
            rows += 1
            if not row["observation_id"].strip():
                raise ValueError(f"line {line}: observation_id is empty")
            if not row["data_source"].strip() or not row["source_version"].strip():
                raise ValueError(f"line {line}: data provenance is required")

            scores = {field: as_float(row, field, line) for field in SCORES[:3]}
            eti = as_float(row, "eti", line)
            for field, value in scores.items():
                if not 0 <= value <= 1:
                    raise ValueError(f"line {line}: {field} must be in [0,1]")
            expected = sum(scores.values()) / 3
            if abs(eti - expected) > 1e-9:
                raise ValueError(f"line {line}: eti does not equal mean(et_trust, et_transparency, et_fulfilment)")

            for field in BINARY:
                if row[field] not in {"0", "1"}:
                    raise ValueError(f"line {line}: {field} must be 0 or 1")

    print(f"VALID: {DATA} ({rows} observations)")
    if rows == 0:
        print("STATUS: schema-only; no empirical observations loaded")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
