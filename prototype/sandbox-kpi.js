const API_BASE = window.SHUUD_API_BASE || "/api/v1/shuud";
const runBtn = document.getElementById("run");
const eventsEl = document.getElementById("events");
const statusEl = document.getElementById("status");

function addEvent(step, state, metric) {
  const existing = eventsEl.querySelector(".empty");
  if (existing) eventsEl.innerHTML = "";
  const tr = document.createElement("tr");
  tr.innerHTML = `<td>${step}</td><td>${state}</td><td>${metric}</td>`;
  eventsEl.appendChild(tr);
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "content-type": "application/json", ...(options.headers || {}) }
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(`${response.status}: ${body.detail || response.statusText}`);
  return body;
}

async function runCase() {
  runBtn.disabled = true;
  statusEl.textContent = "RUNNING";
  eventsEl.innerHTML = `<tr class="empty"><td colspan="3">Case ажиллаж байна…</td></tr>`;
  try {
    const incident = await api("/incidents", {
      method: "POST",
      body: JSON.stringify({
        location: "SANDBOX",
        vehicle_a: "KPI-A",
        vehicle_b: "KPI-B",
        description: "SHUUD sandbox KPI case"
      })
    });
    const id = incident.incident_id;
    document.getElementById("incident").textContent = id;
    addEvent("Incident", "CREATED", id);

    const evidenceRef = `KPI-${id}`;
    await api("/evidence", {
      method: "POST",
      body: JSON.stringify({
        incident_id: id,
        evidence_refs: [evidenceRef],
        gps_coordinates: "47.9184,106.9177",
        captured_at: new Date().toISOString(),
        vehicle_identity_refs: ["KPI-A", "KPI-B"],
        consent_refs: ["CONSENT-A", "CONSENT-B"],
        media_complete: true
      })
    });
    addEvent("Evidence", "LOCKED", "complete");

    const decision = await api("/decisions", {
      method: "POST",
      body: JSON.stringify({
        incident_id: id,
        evidence_refs: [evidenceRef],
        damage_estimate_mnt: 500000,
        two_party_consent: "PASS",
        vehicle_identity_verified: "PASS",
        timestamp_location_verified: "PASS",
        media_complete: "PASS",
        no_injury: "PASS",
        no_third_party_property_damage: "PASS",
        dispute_present: "PASS",
        fraud_flag: "PASS",
        insurance_valid: "PASS",
        beneficiary_valid: "PASS",
        witness_verified: "PASS"
      })
    });
    addEvent("SHIID", decision.decision, `rule ${decision.rule_version}`);

    const clearance = await api("/metrics/clearance", {
      method: "POST",
      body: JSON.stringify({ incident_id: id })
    });
    const seconds = Math.max(0, Math.round(clearance.elapsed_seconds));
    document.getElementById("clearance").textContent = `${seconds}s`;
    document.getElementById("within").textContent = clearance.within_two_minutes ? "PASS" : "FAIL";
    document.getElementById("targetBar").style.width = `${Math.min((seconds / 120) * 100, 100)}%`;
    addEvent("Clearance", clearance.within_two_minutes ? "PASS" : "OVER TARGET", `${seconds}s`);

    const escrowId = `KPI-ESCROW-${id}`;
    const escrow = await api("/escrows", {
      method: "POST",
      body: JSON.stringify({
        incident_id: id,
        escrow_id: escrowId,
        amount_mnt: 500000,
        settlement_provider: "NEF"
      })
    });
    addEvent("Escrow", escrow.state, `${escrow.currency} / ${escrow.settlement_provider}`);

    const release = await api("/release", {
      method: "POST",
      body: JSON.stringify({ incident_id: id, escrow_id: escrowId })
    });
    addEvent("Release", release.new_state, "settled");

    const summary = await api(`/metrics/${encodeURIComponent(id)}/summary`, {
      method: "POST",
      body: JSON.stringify({
        baseline_seconds: 600,
        affected_vehicles: 2,
        vehicle_value_per_minute_mnt: 1000,
        insurer_cost_per_minute_mnt: 500,
        public_road_cost_per_minute_mnt: 800
      })
    });
    const savings = summary.economic_impact.total_savings_mnt;
    document.getElementById("saved").textContent = `${savings} MNT`;
    document.getElementById("caseState").textContent = "COMPLETE";
    statusEl.textContent = "SANDBOX COMPLETE";
    addEvent("Measurement", "COMPLETE", `${savings} MNT savings`);
  } catch (error) {
    statusEl.textContent = "ERROR";
    document.getElementById("caseState").textContent = "ERROR";
    eventsEl.innerHTML = `<tr><td colspan="3">${error.message}</td></tr>`;
  } finally {
    runBtn.disabled = false;
  }
}

runBtn.addEventListener("click", runCase);
