const checks = [
  ["Даатгал хүчинтэй","PASS"],["Хоёр тал зөвшөөрсөн","PASS"],["Хүний гэмтэлгүй","PASS"],
  ["Гуравдагч этгээдийн хохиролгүй","PASS"],["Маргаангүй","PASS"],["Залилангийн дохиогүй","PASS"],
  ["Нотлох материал бүрэн","PASS"],["Хохирол ≤ ₮2,000,000","PASS"]
];

const steps = ["incident","evidence","decision","clearance","escrow","release","summary"];
const stepEls = [...document.querySelectorAll(".flow-step")];
const checksEl = document.getElementById("checks");
const runBtn = document.getElementById("runDemo");
const API_BASE = window.SHUUD_API_BASE || "/api/v1/shuud";

checksEl.innerHTML = checks.map(([label,status]) => `<div class="check"><span>${label}</span><b class="ok">${status}</b></div>`).join("");

let timer = null;
let seconds = 0;

function setStep(current){
  const idx = steps.indexOf(current);
  stepEls.forEach((el,i)=>{
    el.classList.toggle("active",i===idx);
    el.classList.toggle("done",i<idx);
  });
}

function renderElapsed(s){
  const m = String(Math.floor(s/60)).padStart(2,"0");
  const sec = String(s%60).padStart(2,"0");
  document.getElementById("elapsed").textContent = `${m}:${sec}`;
  document.getElementById("meterFill").style.width = `${Math.min((s/120)*100,100)}%`;
}

function pause(ms){ return new Promise(r=>setTimeout(r,ms)); }

async function api(path, options = {}){
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "content-type": "application/json", ...(options.headers || {}) }
  });
  const body = await response.json().catch(() => ({}));
  if(!response.ok){
    const detail = body.detail || response.statusText || `HTTP ${response.status}`;
    throw new Error(`${response.status}: ${detail}`);
  }
  return body;
}

function resetUi(){
  setStep("incident");
  document.getElementById("decisionValue").textContent = "—";
  document.getElementById("escrowValue").textContent = "—";
  document.getElementById("providerValue").textContent = "—";
  document.getElementById("savedValue").textContent = "—";
  document.getElementById("kpiBadge").textContent = "READY";
  document.getElementById("systemStatus").textContent = "LIVE SANDBOX";
  document.getElementById("incidentLabel").textContent = "Incident: —";
  seconds = 0;
  renderElapsed(0);
}

function startTimer(){
  clearInterval(timer);
  timer = setInterval(()=>{ seconds += 1; renderElapsed(seconds); },1000);
}

async function runLive(){
  runBtn.disabled = true;
  resetUi();
  startTimer();

  try{
    document.getElementById("systemStatus").textContent = "LIVE: INCIDENT";
    const incident = await api("/incidents", {
      method: "POST",
      body: JSON.stringify({
        location: "SANDBOX",
        vehicle_a: "TEST-A",
        vehicle_b: "TEST-B",
        description: "SHUUD live prototype lifecycle"
      })
    });
    const incidentId = incident.incident_id;
    document.getElementById("incidentLabel").textContent = `Incident: ${incidentId}`;
    setStep("incident");

    document.getElementById("systemStatus").textContent = "LIVE: EVIDENCE";
    await api("/evidence", {
      method: "POST",
      body: JSON.stringify({
        incident_id: incidentId,
        evidence_refs: ["LIVE-DEMO-MEDIA-001"],
        gps_coordinates: "47.9184,106.9177",
        captured_at: new Date().toISOString(),
        vehicle_identity_refs: ["TEST-A","TEST-B"],
        consent_refs: ["CONSENT-A","CONSENT-B"],
        media_complete: true
      })
    });
    setStep("evidence");

    document.getElementById("systemStatus").textContent = "LIVE: SHIID";
    const decision = await api("/decisions", {
      method: "POST",
      body: JSON.stringify({
        incident_id: incidentId,
        evidence_refs: ["LIVE-DEMO-MEDIA-001"],
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
    document.getElementById("decisionValue").textContent = decision.decision;
    setStep("decision");

    document.getElementById("systemStatus").textContent = "LIVE: CLEARANCE";
    const clearance = await api("/metrics/clearance", {
      method: "POST",
      body: JSON.stringify({ incident_id: incidentId })
    });
    seconds = Math.max(0, Math.round(clearance.elapsed_seconds));
    renderElapsed(seconds);
    setStep("clearance");

    document.getElementById("systemStatus").textContent = "LIVE: ESCROW";
    const escrowId = `LIVE-DEMO-ESCROW-${incidentId}`;
    const escrow = await api("/escrows", {
      method: "POST",
      body: JSON.stringify({
        incident_id: incidentId,
        escrow_id: escrowId,
        amount_mnt: 500000,
        settlement_provider: "NEF"
      })
    });
    document.getElementById("escrowValue").textContent = escrow.state;
    document.getElementById("providerValue").textContent = `${escrow.settlement_provider} / ${escrow.currency}`;
    setStep("escrow");

    document.getElementById("systemStatus").textContent = "LIVE: RELEASE";
    const release = await api("/release", {
      method: "POST",
      body: JSON.stringify({ incident_id: incidentId, escrow_id: escrowId })
    });
    document.getElementById("escrowValue").textContent = release.new_state;
    setStep("release");

    document.getElementById("systemStatus").textContent = "LIVE: MEASUREMENT";
    const summary = await api(`/metrics/${encodeURIComponent(incidentId)}/summary`, {
      method: "POST",
      body: JSON.stringify({
        baseline_seconds: 600,
        affected_vehicles: 2,
        vehicle_value_per_minute_mnt: 1000,
        insurer_cost_per_minute_mnt: 500,
        public_road_cost_per_minute_mnt: 800
      })
    });
    document.getElementById("savedValue").textContent = `${summary.economic_impact.total_savings_mnt} MNT`;
    setStep("summary");

    clearInterval(timer);
    document.getElementById("kpiBadge").textContent = clearance.within_two_minutes ? "PASS ≤ 120s" : "OVER 120s";
    document.getElementById("systemStatus").textContent = "LIVE COMPLETE";
  } catch(error){
    clearInterval(timer);
    document.getElementById("kpiBadge").textContent = "API ERROR";
    document.getElementById("systemStatus").textContent = "SANDBOX ERROR";
    console.error("SHUUD live demo failed:", error);
    await runDemoFallback(error.message);
  } finally {
    runBtn.disabled = false;
  }
}

async function runDemoFallback(reason = "API unavailable"){
  document.getElementById("systemStatus").textContent = "DEMO FALLBACK";
  document.getElementById("incidentLabel").textContent = `Incident: DEMO (${reason})`;
  seconds = 0;
  renderElapsed(0);
  startTimer();

  for(const step of steps){
    setStep(step);
    if(step === "decision") document.getElementById("decisionValue").textContent = "APPROVE";
    if(step === "escrow"){
      document.getElementById("escrowValue").textContent = "LOCKED";
      document.getElementById("providerValue").textContent = "NEF / MNT";
    }
    if(step === "release") document.getElementById("escrowValue").textContent = "RELEASED";
    await pause(step === "clearance" ? 900 : 650);
  }

  clearInterval(timer);
  seconds = 74;
  renderElapsed(seconds);
  document.getElementById("savedValue").textContent = "526 sec";
  document.getElementById("kpiBadge").textContent = "DEMO PASS";
  document.getElementById("systemStatus").textContent = "DEMO COMPLETE";
}

runBtn.addEventListener("click", runLive);
