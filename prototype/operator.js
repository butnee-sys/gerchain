const API_BASE = window.SHUUD_API_BASE || "/api/v1/shuud";
const steps = ["incident", "evidence", "decision", "clearance", "escrow", "release", "summary"];
const stepEls = [...document.querySelectorAll(".flow-step")];
const checks = [
  "Даатгал хүчинтэй", "Хоёр тал зөвшөөрсөн", "Хүний гэмтэлгүй",
  "Гуравдагч этгээдийн хохиролгүй", "Маргаангүй", "Залилангийн дохиогүй",
  "Нотлох материал бүрэн", "Хохирол ≤ ₮2,000,000"
];
const checksEl = document.getElementById("checks");
const logEl = document.getElementById("log");
const runBtn = document.getElementById("runCase");

checksEl.innerHTML = checks.map(label => `<div class="check"><span>${label}</span><b class="ok">PASS</b></div>`).join("");

let seconds = 0;
let timer = null;

function setStep(current) {
  const idx = steps.indexOf(current);
  stepEls.forEach((el, i) => {
    el.classList.toggle("active", i === idx);
    el.classList.toggle("done", i < idx);
  });
}

function renderElapsed(value) {
  const safe = Math.max(0, Math.round(value));
  const m = String(Math.floor(safe / 60)).padStart(2, "0");
  const s = String(safe % 60).padStart(2, "0");
  document.getElementById("elapsed").textContent = `${m}:${s}`;
  document.getElementById("meterFill").style.width = `${Math.min((safe / 120) * 100, 100)}%`;
}

function logEvent(message, state = "PASS") {
  const row = document.createElement("div");
  row.className = "check";
  row.innerHTML = `<span>${message}</span><b class="ok">${state}</b>`;
  logEl.prepend(row);
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

function startClock() {
  clearInterval(timer);
  timer = setInterval(() => {
    seconds += 1;
    renderElapsed(seconds);
  }, 1000);
}

function reset() {
  clearInterval(timer);
  seconds = 0;
  renderElapsed(0);
  setStep("incident");
  logEl.innerHTML = "";
  document.getElementById("incidentValue").textContent = "—";
  document.getElementById("decisionValue").textContent = "—";
  document.getElementById("escrowValue").textContent = "—";
  document.getElementById("providerValue").textContent = "—";
  document.getElementById("savedValue").textContent = "—";
  document.getElementById("clearanceValue").textContent = "—";
  document.getElementById("incidentLabel").textContent = "—";
  document.getElementById("systemStatus").textContent = "RUNNING";
  document.getElementById("kpiBadge").textContent = "LIVE";
}

async function runCase() {
  runBtn.disabled = true;
  reset();
  startClock();
  try {
    const incident = await api("/incidents", {
      method: "POST",
      body: JSON.stringify({
        location: "СБД / Энхтайвны өргөн чөлөө",
        vehicle_a: "UB-TEST-A",
        vehicle_b: "UB-TEST-B",
        description: "SHUUD minor incident — хүний гэмтэлгүй, маргаангүй"
      })
    });
    const id = incident.incident_id;
    document.getElementById("incidentValue").textContent = id;
    document.getElementById("incidentLabel").textContent = `Incident: ${id}`;
    logEvent(`Бүртгэл: ${id} үүсэв`);

    const evidenceRef = `OPERATOR-${id}`;
    await api("/evidence", {
      method: "POST",
      body: JSON.stringify({
        incident_id: id,
        evidence_refs: [evidenceRef],
        gps_coordinates: "47.9184,106.9177",
        captured_at: new Date().toISOString(),
        vehicle_identity_refs: ["UB-TEST-A", "UB-TEST-B"],
        consent_refs: ["CONSENT-A", "CONSENT-B"],
        media_complete: true
      })
    });
    setStep("evidence");
    logEvent("Баримт, байршил, хоёр талын зөвшөөрөл баталгаажив");

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
    setStep("decision");
    document.getElementById("decisionValue").textContent = decision.decision;
    logEvent(`SHIID: ${decision.decision} · дүрэм ${decision.rule_version}`);

    if (decision.decision !== "APPROVE") {
      throw new Error(`SHIID ${decision.decision}: ${decision.reasons?.join(", ") || "шийдвэрийн шалгуур хангагдсангүй"}`);
    }

    const clearance = await api("/metrics/clearance", {
      method: "POST",
      body: JSON.stringify({ incident_id: id })
    });
    seconds = Math.max(0, Math.round(clearance.elapsed_seconds));
    renderElapsed(seconds);
    setStep("clearance");
    document.getElementById("clearanceValue").textContent = `${seconds} сек`;
    logEvent(`Зам чөлөөлөлт: ${seconds} сек`, clearance.within_two_minutes ? "PASS" : "WARN");

    const escrowId = `OPERATOR-ESCROW-${id}`;
    const escrow = await api("/escrows", {
      method: "POST",
      body: JSON.stringify({
        incident_id: id,
        escrow_id: escrowId,
        amount_mnt: 500000,
        settlement_provider: "NEF"
      })
    });
    setStep("escrow");
    document.getElementById("escrowValue").textContent = escrow.state;
    document.getElementById("providerValue").textContent = escrow.settlement_provider || "NEF";
    logEvent(`Эскроу: ₮500,000 · ${escrow.settlement_provider || "NEF"} · ${escrow.state}`);

    const release = await api("/release", {
      method: "POST",
      body: JSON.stringify({ incident_id: id, escrow_id: escrowId })
    });
    setStep("release");
    document.getElementById("escrowValue").textContent = release.new_state;
    logEvent(`Төлбөр: ${release.new_state} · баталгаажсан`);

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
    setStep("summary");
    document.getElementById("savedValue").textContent = `${summary.economic_impact.total_savings_mnt} MNT`;
    clearInterval(timer);
    document.getElementById("kpiBadge").textContent = clearance.within_two_minutes ? "PASS ≤ 120s" : "OVER 120s";
    document.getElementById("systemStatus").textContent = "CASE COMPLETE";
    logEvent(`Эдийн засгийн үр нөлөө: ${summary.economic_impact.total_savings_mnt} MNT хэмнэлт`);
  } catch (error) {
    clearInterval(timer);
    document.getElementById("kpiBadge").textContent = "ERROR";
    document.getElementById("systemStatus").textContent = "SANDBOX ERROR";
    logEvent(error.message, "ERROR");
    console.error(error);
  } finally {
    runBtn.disabled = false;
  }
}

runBtn.addEventListener("click", runCase);
