const API_BASE = window.SHUUD_API_BASE || "/api/v1/shuud";
const start = document.getElementById("start");
const status = document.getElementById("status");
const log = document.getElementById("log");

function addLog(label, body, ok = true){
  const row = document.createElement("div");
  row.style.cssText = "padding:10px 12px;border:1px solid #e4e9e6;border-radius:10px;background:#fbfcfb;margin-top:8px";
  row.innerHTML = `<b>${label}</b><br><small>${body}</small>${ok ? ' <strong style="color:#2d6a4f">PASS</strong>' : ' <strong style="color:#a53b35">ERROR</strong>'}`;
  log.prepend(row);
}

async function api(path, options = {}){
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {"content-type":"application/json", ...(options.headers || {})}
  });
  const body = await response.json().catch(() => ({}));
  if(!response.ok) throw new Error(`${response.status}: ${body.detail || response.statusText}`);
  return body;
}

async function run(){
  start.disabled = true;
  status.textContent = "RUNNING";
  log.innerHTML = "";
  try{
    const incident = await api("/incidents", {method:"POST", body:JSON.stringify({location:"SANDBOX",vehicle_a:"TEST-A",vehicle_b:"TEST-B",description:"Operator sandbox case"})});
    const id = incident.incident_id;
    document.getElementById("incidentId").textContent = id;
    document.getElementById("caseState").textContent = "INCIDENT_CREATED";
    addLog("Incident", id);

    await api("/evidence", {method:"POST", body:JSON.stringify({incident_id:id,evidence_refs:["OPERATOR-MEDIA-001"],gps_coordinates:"47.9184,106.9177",captured_at:new Date().toISOString(),vehicle_identity_refs:["TEST-A","TEST-B"],consent_refs:["CONSENT-A","CONSENT-B"],media_complete:true})});
    document.getElementById("caseState").textContent = "EVIDENCE_LOCKED";
    addLog("Evidence", "Нотлох материал түгжигдсэн");

    const decision = await api("/decisions", {method:"POST", body:JSON.stringify({incident_id:id,evidence_refs:["OPERATOR-MEDIA-001"],damage_estimate_mnt:500000,two_party_consent:"PASS",vehicle_identity_verified:"PASS",timestamp_location_verified:"PASS",media_complete:"PASS",no_injury:"PASS",no_third_party_property_damage:"PASS",dispute_present:"PASS",fraud_flag:"PASS",insurance_valid:"PASS",beneficiary_valid:"PASS",witness_verified:"PASS"})});
    document.getElementById("decision").textContent = decision.decision;
    document.getElementById("caseState").textContent = "SHIID_" + decision.decision;
    addLog("SHIID", decision.decision);

    const clearance = await api("/metrics/clearance", {method:"POST", body:JSON.stringify({incident_id:id})});
    document.getElementById("clearance").textContent = `${Math.round(clearance.elapsed_seconds)}s`;
    document.getElementById("target").textContent = clearance.within_two_minutes ? "≤ 120s PASS" : "> 120s";
    document.getElementById("caseState").textContent = "CLEARED";
    addLog("Clearance", `${Math.round(clearance.elapsed_seconds)} секунд`);

    const escrowId = `OPERATOR-ESCROW-${id}`;
    const escrow = await api("/escrows", {method:"POST", body:JSON.stringify({incident_id:id,escrow_id:escrowId,amount_mnt:500000,settlement_provider:"NEF"})});
    document.getElementById("escrow").textContent = escrow.state;
    document.getElementById("provider").textContent = "NEF / MNT";
    addLog("Escrow", escrow.state);

    const release = await api("/release", {method:"POST", body:JSON.stringify({incident_id:id,escrow_id:escrowId})});
    document.getElementById("escrow").textContent = release.new_state;
    document.getElementById("caseState").textContent = "RELEASED";
    addLog("Release", release.new_state);

    const summary = await api(`/metrics/${encodeURIComponent(id)}/summary`, {method:"POST", body:JSON.stringify({baseline_seconds:600,affected_vehicles:2,vehicle_value_per_minute_mnt:1000,insurer_cost_per_minute_mnt:500,public_road_cost_per_minute_mnt:800})});
    document.getElementById("savings").textContent = `${summary.economic_impact.total_savings_mnt} MNT`;
    document.getElementById("caseState").textContent = "COMPLETE";
    status.textContent = "LIVE COMPLETE";
    addLog("Measurement", `${summary.economic_impact.total_savings_mnt} MNT savings`);
  }catch(error){
    status.textContent = "API ERROR";
    addLog("API", error.message, false);
  }finally{ start.disabled = false; }
}
start.addEventListener("click", run);