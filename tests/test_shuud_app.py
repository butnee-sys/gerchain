"""Integration checks for the standalone SHUUD application surface."""

from shuud.app import app


def test_shuud_app_exposes_lifecycle_and_sandbox_routes():
    paths = set(app.openapi()["paths"])

    assert "/api/v1/shuud/incidents" in paths
    assert "/api/v1/shuud/sandbox/kpi" in paths
    assert "/api/v1/shuud/sandbox/command" in paths
    assert "/api/v1/shuud/sandbox/config/{sandbox_id}/cases/{incident_id}" in paths


def test_shuud_app_keeps_static_mount_last():
    assert app.routes[-1].name == "shuud-web"
