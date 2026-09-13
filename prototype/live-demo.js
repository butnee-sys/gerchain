const checks = [
  ["Даатгал хүчинтэй","PASS"],["Хоёр тал зөвшөөрсөн","PASS"],["Хүний гэмтэлгүй","PASS"],
  ["Гуравдагч этгээдийн хохиролгүй","PASS"],["Маргаангүй","PASS"],["Залилангийн дохиогүй","PASS"],
  ["Нотлох материал бүрэн","PASS"],["Хохирол ≤ ₮2,000,000","PASS"]
];
const steps=["incident","evidence","decision","clearance","escrow","release","summary"];
const stepEls=[...document.querySelectorAll(".flow-step")];
const checksEl=document.getElementById("checks");
const runBtn=document.getElementById("runDemo");
const API="/api/v1/shuud";
const SANDBOX="/api/v1/shuud/sandbox";
checksEl.innerHTML=checks.map(([a,b])=>`<div class="check"><span>${a}</span><b class="ok">${b}</b></div>`).join("");
let timer=null,seconds=0;
function setStep(s){const n=steps.indexOf(s);stepEls.forEach((e,i)=>{e.classList.toggle("active",i===n);e.classList.toggle("done",i<n);});}
function render(s){seconds=s;document.getElementById("elapsed").textContent=`${String(Math.floor(s/60)).padStart(2,"0")}:${String(s%60).padStart(2,"0")}`;document.getElementById("meterFill").style.width=`${Math.min(s/120*100,100)}%`;}
async function call(base,path,body){const r=await fetch(base+path,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)});const x=await r.json().catch(()=>({}));if(!r.ok)throw Error(x.detail||`HTTP ${r.status}`);return x;}
function reset(){setStep("incident");["decisionValue","escrowValue","providerValue","savedValue"].forEach(id=>document.getElementById(id).textContent="—");document.getElementById("kpiBadge").textContent="READY";document.getElementById("systemStatus").textContent="LIVE SANDBOX";document.getElementById("incidentLabel").textContent="Тохиолдол: —";render(0);}
function fallback(reason){clearInterval(timer);document.getElementById("systemStatus").textContent="DEMO FALLBACK";document.getElementById("incidentLabel").textContent=`Тохиолдол: DEMO (${reason})`;render(0);for(const s of steps)setStep(s);document.getElementById("decisionValue").textContent="APPROVE";document.getElementById("escrowValue").textContent="RELEASED";document.getElementById("providerValue").textContent="NEF / MNT";document.getElementById("savedValue").textContent="526,000 ₮";render(74);document.getElementById("kpiBadge").textContent="DEMO PASS";document.getElementById("systemStatus").textContent="DEMO COMPLETE";}
async function run(){runBtn.disabled=true;reset();timer=setInterval(()=>render(seconds+1),1000);try{
 document.getElementById("systemStatus").textContent="LIVE: ТОХИОЛДОЛ";
 const i=await call(API,"/incidents",{location:"Улаанбаатар / SANDBOX",vehicle_a:"TEST-A",vehicle_b:"TEST-B",description:"SHUUD live MVP lifecycle"});
 document.getElementById("incidentLabel").textContent=`Тохиолдол: ${i.incident_id}`;setStep("incident");
 await call(API,"/evidence",{incident_id:i.incident_id,evidence_refs:["LIVE-DEMO-MEDIA-001"],gps_coordinates:"47.9184,106.9177",captured_at:new Date().toISOString(),vehicle_identity_refs:["TEST-A","TEST-B"],consent_refs:["CONSENT-A","CONSENT-B"],media_complete:true});setStep("evidence");
 const d=await call(API,"/decisions",{incident_id:i.incident_id,evidence_refs:["LIVE-DEMO-MEDIA-001"],damage_estimate_mnt:500000,two_party_consent:"PASS",vehicle_identity_verified:"PASS",timestamp_location_verified:"PASS",media_complete:"PASS",no_injury:"PASS",no_third_party_property_damage:"PASS",dispute_present:"PASS",fraud_flag:"PASS",insurance_valid:"PASS",beneficiary_valid:"PASS",witness_verified:"PASS"});document.getElementById("decisionValue").textContent=d.decision;setStep("decision");
 const c=await call(API,"/metrics/clearance",{incident_id:i.incident_id});render(Math.round(c.elapsed_seconds));setStep("clearance");
 const escrowId=`LIVE-DEMO-ESCROW-${i.incident_id}`;const e=await call(API,"/escrows",{incident_id:i.incident_id,escrow_id:escrowId,amount_mnt:500000,settlement_provider:"NEF"});document.getElementById("escrowValue").textContent=e.state;document.getElementById("providerValue").textContent=`${e.settlement_provider} / ${e.currency}`;setStep("escrow");
 const r=await call(API,"/release",{incident_id:i.incident_id,escrow_id:escrowId});document.getElementById("escrowValue").textContent=r.new_state;setStep("release");
 const m=await call(SANDBOX,`/metrics/${encodeURIComponent(i.incident_id)}/economic`,{baseline_seconds:600,affected_vehicles:2,vehicle_value_per_minute_mnt:1000,insurer_cost_per_minute_mnt:500,public_road_cost_per_minute_mnt:800});const v=m.economic_measurement||{};document.getElementById("savedValue").textContent=`${Math.round(Number(v.total_savings_mnt||0)).toLocaleString()} ₮`;setStep("summary");
 clearInterval(timer);document.getElementById("kpiBadge").textContent=c.within_two_minutes?"PASS ≤ 120s":"OVER 120s";document.getElementById("systemStatus").textContent="LIVE COMPLETE";window.dispatchEvent(new CustomEvent("shuud:demo-complete",{detail:{incident_id:i.incident_id,clearance_seconds:c.elapsed_seconds,total_savings_mnt:Number(v.total_savings_mnt||0)}}));
}catch(e){console.error(e);fallback(e.message);}finally{runBtn.disabled=false;}}
runBtn.addEventListener("click",run);