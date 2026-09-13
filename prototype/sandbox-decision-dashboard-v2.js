const API_BASE = window.SHUUD_API_BASE || "/api/v1/shuud";
const runBtn = document.getElementById("run");
const refreshBtn = document.getElementById("refreshKpi");
const eventsEl = document.getElementById("events");
const statusEl = document.getElementById("status");
const scopeButtons = [...document.querySelectorAll("[data-scope]")];
let currentScope = "all";

function addEvent(step, state, metric) {
  const existing = eventsEl.querySelector(".empty");
  if (existing) eventsEl.innerHTML = "";
  const tr = document.createElement("tr");
  tr.innerHTML = `<td>${step}</td><td>${state}</td><td>${metric}</td>`;
  eventsEl.appendChild(tr);
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers: { "content-type": "application/json", ...(options.headers || {}) } });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(`${response.status}: ${body.detail || response.statusText}`);
  return body;
}

const pct = (v) => `${(Number(v || 0) * 100).toFixed(1)}%`;
const seconds = (v) => v == null ? "—" : `${Number(v).toFixed(1)}s`;
const money = (v) => `${Number(v || 0).toFixed(0)} MNT`;
const minutes = (v) => `${Number(v || 0).toFixed(1)} мин`;

function renderDurableKpi(kpi) {
  document.getElementById("kpiTotal").textContent = kpi.total_cases ?? 0;
  document.getElementById("kpi120").textContent = pct(kpi.within_two_minutes_rate);
  document.getElementById("kpiAvg").textContent = seconds(kpi.average_clearance_seconds);
  document.getElementById("kpiMedian").textContent = seconds(kpi.median_clearance_seconds);
  document.getElementById("kpiSavedMinutes").textContent = minutes(kpi.total_time_saved_minutes);
  document.getElementById("kpiSavings").textContent = money(kpi.total_savings_mnt);
  document.getElementById("kpiInsurer").textContent = money(kpi.total_insurer_savings_mnt);
  document.getElementById("kpiRoad").textContent = money(kpi.total_public_road_savings_mnt);
  document.getElementById("cityBenefit").textContent = money(kpi.total_public_road_savings_mnt);
  document.getElementById("insurerBenefit").textContent = `${money(kpi.total_insurer_savings_mnt)} • approval ${pct(kpi.shiid_approval_rate)} • release ${pct(kpi.release_success_rate)}`;
  document.getElementById("userBenefit").textContent = money(kpi.total_vehicle_user_savings_mnt);
  document.getElementById("scopeCases").textContent = kpi.economic_measurement_cases ?? 0;
  document.getElementById("scopeCoverage").textContent = pct(kpi.economic_coverage_rate);
  document.getElementById("scopeMinutes").textContent = minutes(kpi.total_time_saved_minutes);
  const economicCases = Number(kpi.economic_measurement_cases || 0);
  document.getElementById("scopePerCase").textContent = economicCases ? money(Number(kpi.total_savings_mnt || 0) / economicCases) : "—";
  document.getElementById("kpiMeta").textContent = `Durable: ${kpi.measured_clearance_cases ?? 0} clearance measurement • ${kpi.economic_measurement_cases ?? 0} economic measurement • coverage ${pct(kpi.economic_coverage_rate)} • scope ${kpi.scope || "sandbox"}`;
}

async function loadDurableKpi() {
  try {
    const path = currentScope === "weekly" ? "/sandbox/kpi/weekly" : currentScope === "daily" ? "/sandbox/kpi/daily" : "/sandbox/kpi";
    renderDurableKpi(await api(path));
  } catch (error) {
    document.getElementById("kpiMeta").textContent = `KPI API error: ${error.message}`;
  }
}

function setScope(scope) {
  currentScope = scope;
  scopeButtons.forEach((button) => button.classList.toggle("active", button.dataset.scope === scope));
  loadDurableKpi();
}

async function runCase() {
  runBtn.disabled = true;
  statusEl.textContent = "RUNNING";
  eventsEl.innerHTML = `<tr class="empty"><td colspan="3">Case ажиллаж байна…</td></tr>`;
  try {
    const incident = await api("/incidents", { method: "POST", body: JSON.stringify({ location: "SANDBOX", vehicle_a: "KPI-A", vehicle_b: "KPI-B", description: "SHUUD sandbox KPI case" }) });
    const id = incident.incident_id;
    document.getElementById("incident").textContent = id;
    addEvent("Incident", "CREATED", id);
    const evidenceRef = `KPI-${id}`;
    await api("/evidence", { method: "POST", body: JSON.stringify({ incident_id: id, evidence_refs: [evidenceRef], gps_coordinates: "47.9184,106.9177", captured_at: new Date().toISOString(), vehicle_identity_refs: ["KPI-A", "KPI-B"], consent_refs: ["CONSENT-A", "CONSENT-B"], media_complete: true }) });
    addEvent("Evidence", "LOCKED", "complete");
    const decision = await api("/decisions", { method: "POST", body: JSON.stringify({ incident_id: id, evidence_refs: [evidenceRef], damage_estimate_mnt: 500000, two_party_consent: "PASS", vehicle_identity_verified: "PASS", timestamp_location_verified: "PASS", media_complete: "PASS", no_injury: "PASS", no_third_party_property_damage: "PASS", dispute_present: "PASS", fraud_flag: "PASS", insurance_valid: "PASS", beneficiary_valid: "PASS", witness_verified: "PASS" }) });
    addEvent("SHIID", decision.decision, `rule ${decision.rule_version}`);
    const clearance = await api("/metrics/clearance", { method: "POST", body: JSON.stringify({ incident_id: id }) });
    const caseSeconds = Math.max(0, Math.round(Number(clearance.elapsed_seconds || 0)));
    document.getElementById("clearance").textContent = `${caseSeconds}s`;
    document.getElementById("within").textContent = clearance.within_two_minutes ? "PASS" : "FAIL";
    document.getElementById("targetBar").style.width = `${Math.min((caseSeconds / 120) * 100, 100)}%`;
    addEvent("Clearance", clearance.within_two_minutes ? "PASS" : "OVER TARGET", `${caseSeconds}s`);
    const escrowId = `KPI-ESCROW-${id}`;
    const escrow = await api("/escrows", { method: "POST", body: JSON.stringify({ incident_id: id, escrow_id: escrowId, amount_mnt: 500000, settlement_provider: "NEF" }) });
    addEvent("Escrow", escrow.state, `${escrow.currency} / ${escrow.settlement_provider}`);
    const release = await api("/release", { method: "POST", body: JSON.stringify({ incident_id: id, escrow_id: escrowId }) });
    addEvent("Release", release.new_state, "settled");
    const economic = await api(`/sandbox/metrics/${encodeURIComponent(id)}/economic`, { method: "POST", body: JSON.stringify({ baseline_seconds: 600, affected_vehicles: 2, vehicle_value_per_minute_mnt: 1000, insurer_cost_per_minute_mnt: 500, public_road_cost_per_minute_mnt: 800 }) });
    const savings = economic.economic_measurement.total_savings_mnt;
    document.getElementById("saved").textContent = money(savings);
    document.getElementById("caseState").textContent = "COMPLETE";
    statusEl.textContent = "SANDBOX COMPLETE";
    addEvent("Measurement", economic.persisted ? "PERSISTED" : "NOT PERSISTED", `${savings} MNT savings`);
    await loadDurableKpi();
  } catch (error) {
    statusEl.textContent = "ERROR";
    document.getElementById("caseState").textContent = "ERROR";
    eventsEl.innerHTML = `<tr><td colspan="3">${error.message}</td></tr>`;
  } finally { runBtn.disabled = false; }
}

scopeButtons.forEach((button) => button.addEventListener("click", () => setScope(button.dataset.scope)));
runBtn.addEventListener("click", runCase);
refreshBtn.addEventListener("click", loadDurableKpi);
loadDurableKpi();
