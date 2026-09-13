const checks = [
  ["Даатгал хүчинтэй","PASS"],["Хоёр тал зөвшөөрсөн","PASS"],["Хүний гэмтэлгүй","PASS"],
  ["Гуравдагч этгээдийн хохиролгүй","PASS"],["Маргаангүй","PASS"],["Залилангийн дохиогүй","PASS"],
  ["Нотлох материал бүрэн","PASS"],["Хохирол ≤ ₮2,000,000","PASS"]
];

const steps = ["incident","evidence","decision","clearance","escrow","release","summary"];
const stepEls = [...document.querySelectorAll(".flow-step")];
const checksEl = document.getElementById("checks");
const runBtn = document.getElementById("runDemo");

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

async function runDemo(){
  runBtn.disabled = true;
  document.getElementById("systemStatus").textContent = "RUNNING";
  document.getElementById("kpiBadge").textContent = "LIVE DEMO";
  document.getElementById("incidentLabel").textContent = "Incident: INC-DEMO-001";
  seconds = 0; renderElapsed(0);
  timer = setInterval(()=>{seconds += 1; renderElapsed(seconds)},1000);

  for(const step of steps){
    setStep(step);
    if(step==="decision") document.getElementById("decisionValue").textContent="APPROVE";
    if(step==="escrow"){document.getElementById("escrowValue").textContent="LOCKED";document.getElementById("providerValue").textContent="NEF / MNT";}
    if(step==="release") document.getElementById("escrowValue").textContent="RELEASED";
    if(step==="summary") document.getElementById("savedValue").textContent="410 sec";
    await pause(step==="clearance"?900:650);
  }

  clearInterval(timer);
  seconds = 74;
  renderElapsed(seconds);
  document.getElementById("savedValue").textContent = "526 sec";
  document.getElementById("kpiBadge").textContent = "PASS";
  document.getElementById("systemStatus").textContent = "DEMO COMPLETE";
  runBtn.disabled = false;
}

runBtn.addEventListener("click", runDemo);
