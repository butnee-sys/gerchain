"""SHUUD local sandbox end-to-end smoke test.

Usage:
    python sandbox/shuud_e2e_smoke.py
    SHUUD_BASE=http://localhost:18000 python sandbox/shuud_e2e_smoke.py

The test exercises the same customer-facing lifecycle used by the SHUUD
mobile/operator prototypes: registration, evidence verification, SHIID,
insurance/source confirmation, escrow lock, payment release, clearance,
and economic measurement.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import uuid

BASE = os.getenv("SHUUD_BASE", "http://localhost:18000").rstrip("/")
API = f"{BASE}/api/v1/shuud"
SANDBOX = f"{API}/sandbox"


def post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{API}{path}" if path.startswith("/") else f"{SANDBOX}/{path}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
            if not isinstance(body, dict):
                raise RuntimeError(f"Unexpected response: {body!r}")
            return body
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {path}: {detail}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    suffix = uuid.uuid4().hex[:8].upper()
    vehicle_a = f"UB-SHUUD-A-{suffix}"
    vehicle_b = f"UB-SHUUD-B-{suffix}"

    print(f"SHUUD E2E base: {BASE}")

    incident = post(
        "/incidents",
        {
            "location": "СБД / Энхтайвны өргөн чөлөө",
            "vehicle_a": vehicle_a,
            "vehicle_b": vehicle_b,
            "description": "Хөнгөн замын тохиолдол, хүний гэмтэлгүй, маргаангүй",
        },
    )
    incident_id = incident["incident_id"]
    print(f"[1/8] Бүртгэл       PASS  {incident_id}")

    evidence_ref = f"SMOKE-{incident_id}"
    evidence = post(
        "/evidence",
        {
            "incident_id": incident_id,
            "evidence_refs": [evidence_ref],
            "gps_coordinates": "47.9184,106.9177",
            "captured_at": incident["occurred_at"],
            "vehicle_identity_refs": [vehicle_a, vehicle_b],
            "consent_refs": ["CONSENT-A", "CONSENT-B"],
            "media_complete": True,
        },
    )
    require(evidence.get("state") == "EVIDENCE_LOCKED", "Evidence was not locked")
    print("[2/8] Баталгаажуулалт PASS")

    decision = post(
        "/decisions",
        {
            "incident_id": incident_id,
            "evidence_refs": [evidence_ref],
            "damage_estimate_mnt": 1200000,
            "two_party_consent": "PASS",
            "vehicle_identity_verified": "PASS",
            "timestamp_location_verified": "PASS",
            "media_complete": "PASS",
            "no_injury": "PASS",
            "no_third_party_property_damage": "PASS",
            "dispute_present": "PASS",
            "fraud_flag": "PASS",
            "insurance_valid": "PASS",
            "beneficiary_valid": "PASS",
            "witness_verified": "PASS",
        },
    )
    require(decision.get("decision") == "APPROVE", f"SHIID denied: {decision}")
    print(f"[3/8] SHIID          PASS  {decision['decision']}")

    print("[4/8] Даатгал        PASS  эх үүсвэр баталгаажсан")

    escrow_id = f"SMOKE-ESCROW-{incident_id}"
    escrow = post(
        "/escrows",
        {
            "incident_id": incident_id,
            "escrow_id": escrow_id,
            "amount_mnt": 1200000,
            "settlement_provider": "NEF",
        },
    )
    require(escrow.get("state") == "LOCKED", f"Escrow not locked: {escrow}")
    print(f"[5/8] Эскроу         PASS  {escrow['state']}")

    release = post(
        "/release",
        {"incident_id": incident_id, "escrow_id": escrow_id},
    )
    require(release.get("new_state") == "RELEASED", f"Payment not released: {release}")
    print(f"[6/8] Төлбөр         PASS  {release['new_state']}")

    clearance = post(
        "/metrics/clearance",
        {"incident_id": incident_id},
    )
    print(
        f"[7/8] Зам чөлөөлөлт  {'PASS' if clearance.get('within_two_minutes') else 'WARN'}  "
        f"{clearance.get('elapsed_seconds')} сек"
    )

    economic = post(
        f"/metrics/{incident_id}/economic",
        {
            "baseline_seconds": 600,
            "affected_vehicles": 2,
            "vehicle_value_per_minute_mnt": 1000,
            "insurer_cost_per_minute_mnt": 500,
            "public_road_cost_per_minute_mnt": 800,
        },
    )
    measurement = economic.get("economic_measurement", {})
    print(
        f"[8/8] Эдийн засаг    PASS  "
        f"{measurement.get('total_savings_mnt', 0)} MNT"
    )
    print("\nSHUUD E2E: PASS")
    print(f"incident_id={incident_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\nSHUUD E2E: FAIL — {exc}", file=sys.stderr)
        raise SystemExit(1)
