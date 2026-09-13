from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest


POSTGRES_DSN = os.getenv("SHUUD_POSTGRES_DSN")
pytestmark = pytest.mark.skipif(
    not POSTGRES_DSN,
    reason="SHUUD_POSTGRES_DSN is required for PostgreSQL process-restart E2E",
)


def _wait_for_server(url: str, process: subprocess.Popen[str], timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise AssertionError(
                f"uvicorn exited before becoming ready: code={process.returncode}\n"
                f"stdout={stdout}\nstderr={stderr}"
            )
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status < 500:
                    return
        except Exception as exc:  # pragma: no cover - timing dependent
            last_error = exc
        time.sleep(0.25)
    raise AssertionError(f"server did not become ready: {last_error}")


def _request(base_url: str, method: str, path: str, payload: dict) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8")
        raise AssertionError(f"HTTP {exc.code}: {details}") from exc


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_server(database_url: str, port: int) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env["SHUUD_PERSISTENCE_URL"] = database_url
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "shuud.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )


def _stop_server(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_shuud_survives_postgres_process_restart():
    database_url = POSTGRES_DSN
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    first = _start_server(database_url, port)
    incident_id = None
    escrow_id = None
    try:
        _wait_for_server(f"{base_url}/docs", first)

        status, incident = _request(
            base_url,
            "POST",
            "/api/v1/shuud/incidents",
            {
                "location": "Ulaanbaatar",
                "vehicle_a": "1234ABC",
                "vehicle_b": "5678DEF",
            },
        )
        assert status == 200
        incident_id = incident["incident_id"]
        escrow_id = f"ESC-{incident_id}"

        status, evidence = _request(
            base_url,
            "POST",
            "/api/v1/shuud/evidence",
            {
                "incident_id": incident_id,
                "evidence_refs": ["PHOTO-PG-001", "VIDEO-PG-001"],
                "gps_coordinates": "47.9184,106.9177",
                "captured_at": "2026-09-13T00:00:15+00:00",
                "vehicle_identity_refs": ["VIN-A", "VIN-B"],
                "consent_refs": ["CONSENT-A", "CONSENT-B"],
                "media_complete": True,
            },
        )
        assert status == 200
        assert evidence["state"] == "EVIDENCE_LOCKED"

        status, decision = _request(
            base_url,
            "POST",
            "/api/v1/shuud/decisions",
            {
                "incident_id": incident_id,
                "evidence_refs": ["PHOTO-PG-001", "VIDEO-PG-001"],
                "damage_estimate_mnt": 1_500_000,
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
        assert status == 200
        assert decision["decision"] == "APPROVE"

        status, escrow = _request(
            base_url,
            "POST",
            "/api/v1/shuud/escrows",
            {
                "incident_id": incident_id,
                "escrow_id": escrow_id,
                "amount_mnt": 1_500_000,
                "settlement_provider": "NEF",
            },
        )
        assert status == 200
        assert escrow["state"] == "LOCKED"
        assert escrow["currency"] == "MNT"
        assert escrow["settlement_provider"] == "NEF"
    finally:
        _stop_server(first)

    second = _start_server(database_url, port)
    try:
        _wait_for_server(f"{base_url}/docs", second)
        assert incident_id is not None
        assert escrow_id is not None
        status, release = _request(
            base_url,
            "POST",
            "/api/v1/shuud/release",
            {
                "incident_id": incident_id,
                "escrow_id": escrow_id,
            },
        )
        assert status == 200
        assert release["previous_state"] == "LOCKED"
        assert release["new_state"] == "RELEASED"
    finally:
        _stop_server(second)
