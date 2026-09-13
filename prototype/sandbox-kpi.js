const API_BASE = window.SHUUD_API_BASE || "/api/v1/shuud";
const runBtn = document.getElementById("run");
const batchEl = document.getElementById("batch");
const casesEl = document.getElementById("cases");
const statusEl = document.getElementById("status");

const MODEL = {
  baseline_seconds: 600,
  affected_vehicles: 2,
  vehicle_value_per_minute_mnt: 1000,
  insurer_cost_per_minute_mnt: 500,
  public_road_cost_per_minute_mnt: 800,
  escrow_amount_mnt: 500000
};

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function percent(value) {
  return `${Math.round(value * 100)}%`;
}

function formatMnt(value) {
  return `${Math.round(Number(value || 0)).toLocaleString("mn-MN")} MNT`;
}

function median(values) {
  if (!values.length) return null;
  const ordered = [...values].sort((a, b) => a - b);
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "content-type": "application/json", ...(options.headers || {}) }
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(`${response.status}: ${body.detail || response.statusText}`);
  }
  return body;
}

function resetAggregate() {
  setText("totalCases", "0");
  setText("passRate", "—");
  setText("avgClearance", "—");
  setText("medianClearance", "—");
  setText("releaseRate", "—");
  setText("approveRate", "—");
  setText("failedCases", "0");
  setText("totalSavings", "0 MNT");
  document.getElementById("progressBar").style.width = "0%";
  setText("progressText", `0 / ${batchEl.value}`);
  setText("caseState", "READY");
}

function addCaseRow(index, result) {
  const row = document.createElement("tr");
  if (result.error) {
    row.innerHTML = `<td>${index}</td><td colspan="6">ERROR: ${result.error}</td>`;
  } else {
    row.innerHTML = [
      index,
      result.incidentId,
      result.decision,
      `${Math.round(result.clearanceSeconds)}s`,
      result.withinTwoMinutes ? "PASS" : "FAIL",
      result.releaseState,
      formatMnt(result.savingsMnt)
    ].map(value => `<td>${value}</td>`).join("");
  }
  casesEl.appendChild(row);
}

async function runCase(index) {
  const incident = await api("/incidents", {
    method: "POST",
    body: JSON.stringify({
      location: "SANDBOX",
      vehicle_a: `KPI-${index}-A`,
      vehicle_b: `KPI-${index}-B`,
      description: `SHUUD 90-day sandbox aggregate case ${index}`
    })
  });

  const id = incident.incident_id;
  const evidenceRef = `KPI-${id}`;

  await api("/evidence", {
    method: "POST",
    body: JSON.stringify({
      incident_id: id,
      evidence_refs: [evidenceRef],
      gps_coordinates: "47.9184,106.9177",
      captured_at: new Date().toISOString(),
      vehicle_identity_refs: [`KPI-${index}-A`, `KPI-${index}-B`],
      consent_refs: [`CONSENT-${id}-A`, `CONSENT-${id}-B`],
      media_complete: true
    })
  });

  const decision = await api("/decisions", {
    method: "POST",
    body: JSON.stringify({
      incident_id: id,
      evidence_refs: [evidenceRef],
      damage_estimate_mnt: MODEL.escrow_amount_mnt,
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

  const clearance = await api("/metrics/clearance", {
    method: "POST",
    body: JSON.stringify({ incident_id: id })
  });

  const escrowId = `KPI-ESCROW-${id}`;
  await api("/escrows", {
    method: "POST",
    body: JSON.stringify({
      incident_id: id,
      escrow_id: escrowId,
      amount_mnt: MODEL.escrow_amount_mnt,
      settlement_provider: "NEF"
    })
  });

  const release = await api("/release", {
    method: "POST",
    body: JSON.stringify({ incident_id: id, escrow_id: escrowId })
  });

  const summary = await api(`/metrics/${encodeURIComponent(id)}/summary`, {
    method: "POST",
    body: JSON.stringify(MODEL)
  });

  return {
    incidentId: id,
    decision: decision.decision,
    clearanceSeconds: Number(clearance.elapsed_seconds),
    withinTwoMinutes: Boolean(clearance.within_two_minutes),
    releaseState: release.new_state,
    savingsMnt: Number(summary.economic_impact.total_savings_mnt || 0)
  };
}

async function runSession() {
  const count = Number(batchEl.value);
  runBtn.disabled = true;
  batchEl.disabled = true;
  statusEl.textContent = "RUNNING";
  casesEl.innerHTML = "";
  resetAggregate();

  const results = [];
  for (let index = 1; index <= count; index += 1) {
    try {
      const result = await runCase(index);
      results.push(result);
      addCaseRow(index, result);
    } catch (error) {
      const result = { error: error.message };
      results.push(result);
      addCaseRow(index, result);
    }
    document.getElementById("progressBar").style.width = `${(index / count) * 100}%`;
    setText("progressText", `${index} / ${count}`);
  }

  const completed = results.filter(result => !result.error);
  const failed = results.length - completed.length;
  const clearanceValues = completed.map(result => result.clearanceSeconds);
  const passCount = completed.filter(result => result.withinTwoMinutes).length;
  const releaseCount = completed.filter(result => result.releaseState === "RELEASED").length;
  const approveCount = completed.filter(result => result.decision === "APPROVE").length;
  const totalSavings = completed.reduce((sum, result) => sum + result.savingsMnt, 0);
  const avg = clearanceValues.length
    ? clearanceValues.reduce((sum, value) => sum + value, 0) / clearanceValues.length
    : null;
  const med = median(clearanceValues);

  setText("totalCases", String(results.length));
  setText("passRate", completed.length ? percent(passCount / completed.length) : "—");
  setText("avgClearance", avg === null ? "—" : `${avg.toFixed(1)}s`);
  setText("medianClearance", med === null ? "—" : `${med.toFixed(1)}s`);
  setText("releaseRate", completed.length ? percent(releaseCount / completed.length) : "—");
  setText("approveRate", completed.length ? percent(approveCount / completed.length) : "—");
  setText("failedCases", String(failed));
  setText("totalSavings", formatMnt(totalSavings));
  setText("caseState", failed ? "PARTIAL" : "COMPLETE");
  statusEl.textContent = failed ? "SESSION PARTIAL" : "SANDBOX COMPLETE";

  runBtn.disabled = false;
  batchEl.disabled = false;
}

runBtn.addEventListener("click", runSession);
