"""FastAPI application for the Bug Triage environment."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from openenv.core.env_server import create_fastapi_app

from .models import BugTriageAction, BugTriageObservation
from .env import BugTriageEnvironment

app: FastAPI = create_fastapi_app(BugTriageEnvironment, BugTriageAction, BugTriageObservation)

UI_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bug Triage Environment</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
.ctr{max-width:920px;margin:0 auto;padding:2rem 1.5rem}
h1{font-size:2rem;margin-bottom:.5rem;background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{color:#94a3b8;margin-bottom:1.5rem;font-size:1.05rem}
.badge{display:inline-block;background:#1e293b;border:1px solid #334155;padding:.25rem .75rem;border-radius:999px;font-size:.8rem;color:#38bdf8;margin-right:.5rem;margin-bottom:.5rem}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:1.5rem;margin-bottom:1.25rem}
.card h2{font-size:1.15rem;color:#f1f5f9;margin-bottom:.75rem}
.card p{color:#94a3b8;line-height:1.6;font-size:.95rem}
.flow{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;margin:1rem 0}
.fs{background:#0f172a;border:1px solid #334155;border-radius:8px;padding:.5rem 1rem;font-size:.85rem;color:#cbd5e1}
.fa{color:#475569;font-size:1.2rem}
.btn-row{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.75rem;align-items:center}
.btn{padding:.5rem 1rem;border-radius:8px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;cursor:pointer;font-size:.85rem;transition:all .15s;font-family:inherit}
.btn:hover{border-color:#38bdf8;color:#38bdf8}
.btn:active{transform:scale(.97)}
.btn.pri{background:#1e40af;border-color:#2563eb;color:#fff}
.btn.pri:hover{background:#2563eb}
.btn.grn{background:#166534;border-color:#22c55e;color:#4ade80}
.btn.grn:hover{background:#15803d}
.btn.amb{background:#78350f;border-color:#f59e0b;color:#fbbf24}
.btn.amb:hover{background:#92400e}
.btn.red{background:#7f1d1d;border-color:#ef4444;color:#f87171}
.btn.red:hover{background:#991b1b}
.btn:disabled{opacity:.4;cursor:not-allowed}
.log{background:#0f172a;border:1px solid #334155;border-radius:8px;padding:1rem;font-family:'SF Mono','Fira Code',monospace;font-size:.78rem;color:#94a3b8;max-height:350px;overflow-y:auto;white-space:pre-wrap;word-break:break-word;line-height:1.5}
.log .req{color:#fbbf24}.log .res{color:#4ade80}.log .err{color:#f87171}.log .dim{color:#475569}.log .info{color:#38bdf8}
.bc{background:#0f172a;border:1px solid #334155;border-radius:8px;padding:1rem;margin:.75rem 0}
.bc h4{color:#f1f5f9;font-size:.95rem;margin-bottom:.5rem}
.bc .meta{color:#64748b;font-size:.8rem}
.bc .desc{color:#cbd5e1;font-size:.85rem;margin-top:.5rem;line-height:1.5}
.inv-box{margin-top:.5rem;padding:.5rem;background:#1e293b;border-radius:6px;font-size:.82rem}
.inv-label{display:inline-block;padding:.15rem .5rem;border-radius:4px;font-size:.72rem;margin-right:.25rem;font-weight:600}
.inv-label.done{background:#064e3b;color:#6ee7b7}
.inv-label.avail{background:#1e3a5f;color:#38bdf8;cursor:pointer}
.inv-label.avail:hover{background:#1e40af}
.budget-bar{height:6px;background:#334155;border-radius:3px;margin-top:.5rem;overflow:hidden}
.budget-fill{height:100%;background:linear-gradient(90deg,#38bdf8,#818cf8);border-radius:3px;transition:width .3s}
.score-box{text-align:center;padding:1.5rem}
.score-big{font-size:2.5rem;font-weight:700}
.score-big.good{color:#4ade80}.score-big.mid{color:#fbbf24}.score-big.bad{color:#f87171}
.endpoints{display:grid;grid-template-columns:1fr 1fr;gap:.75rem}
.ep{background:#0f172a;border:1px solid #334155;border-radius:8px;padding:.75rem 1rem;cursor:pointer;transition:border-color .2s}
.ep:hover{border-color:#475569}
.ep code{color:#38bdf8;font-size:.9rem}
.ep .m{font-size:.7rem;font-weight:700;padding:.15rem .4rem;border-radius:4px;margin-right:.5rem}
.ep .m.post{background:#166534;color:#4ade80}
.ep .m.get{background:#1e3a5f;color:#38bdf8}
.ep .m.ws{background:#4c1d95;color:#a78bfa}
.ep .d{color:#64748b;font-size:.8rem;display:block;margin-top:.25rem}
.status{margin-top:2rem;text-align:center;padding:1rem;background:#022c22;border:1px solid #065f46;border-radius:8px}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#4ade80;margin-right:.5rem;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
a{color:#38bdf8;text-decoration:none}a:hover{text-decoration:underline}
select.btn{appearance:auto;padding:.4rem .5rem}
</style>
</head>
<body>
<div class="ctr">
<h1>Bug Triage &amp; Fix Recommendation</h1>
<p class="sub">Multi-step investigation RL environment for training AI agents</p>
<span class="badge">OpenEnv</span>
<span class="badge">3 Tasks</span>
<span class="badge">30 Bug Pool</span>
<span class="badge">Investigation Budget</span>

<div class="card" style="margin-top:1.5rem">
<h2>How It Works</h2>
<p>The agent receives a brief bug report and must decide: <b>investigate</b> (logs, related bugs, reporter) to gather more information, or <b>triage</b> (classify type, severity, fix). Investigation costs budget &mdash; efficient agents score higher.</p>
<div class="flow">
<div class="fs">&#128027; Brief Bug</div><div class="fa">&rarr;</div>
<div class="fs">&#128269; Investigate?</div><div class="fa">&rarr;</div>
<div class="fs">&#128214; More Info</div><div class="fa">&rarr;</div>
<div class="fs">&#9989; Triage</div><div class="fa">&rarr;</div>
<div class="fs">&#127942; Score</div>
</div>
</div>

<!-- Interactive Panel -->
<div class="card">
<h2>&#9889; Try It Live</h2>
<p style="color:#94a3b8;font-size:.9rem;margin-bottom:1rem">Click a task to start an episode. Investigate bugs, then triage them &mdash; all API calls happen in real time via WebSocket.</p>
<div class="btn-row">
<button class="btn grn" onclick="resetEp('easy')">&#9654; Easy</button>
<button class="btn amb" onclick="resetEp('medium')">&#9654; Medium</button>
<button class="btn red" onclick="resetEp('hard')">&#9654; Hard</button>
<button class="btn" onclick="doHealth()">&#128154; Health</button>
<button class="btn" onclick="doState()">&#128202; State</button>
<button class="btn" onclick="clr()" style="margin-left:auto">Clear</button>
</div>
<div id="bug-area"></div>
<div id="act-area" style="display:none">
<div class="btn-row">
<span style="color:#64748b;font-size:.8rem">Investigate:</span>
<button class="btn" id="b-logs" onclick="doInv('logs')">&#128220; Logs</button>
<button class="btn" id="b-related" onclick="doInv('related')">&#128279; Related</button>
<button class="btn" id="b-reporter" onclick="doInv('reporter')">&#128100; Reporter</button>
</div>
<div class="btn-row">
<span style="color:#64748b;font-size:.8rem">Triage:</span>
<select id="s-type" class="btn"><option value="ui">ui</option><option value="backend">backend</option><option value="security">security</option></select>
<select id="s-sev" class="btn"><option value="low">low</option><option value="medium">medium</option><option value="high">high</option><option value="critical">critical</option></select>
<input id="s-fix" class="btn" placeholder="fix suggestion (hard)" style="flex:1;min-width:140px;background:#0f172a;color:#e2e8f0;border:1px solid #334155">
<button class="btn pri" onclick="doTriage()">&#10004; Submit Triage</button>
</div>
</div>
<div class="log" id="log"><span class="dim">Click a task button above to start an episode...</span></div>
</div>

<div class="card">
<h2>API Endpoints</h2>
<div class="endpoints">
<div class="ep" onclick="doHealth()"><span class="m get">GET</span><code>/health</code><span class="d">Health check (click to try)</span></div>
<div class="ep" onclick="resetEp('easy')"><span class="m post">POST</span><code>/reset</code><span class="d">Start episode (click to try)</span></div>
<div class="ep" onclick="doState()"><span class="m get">GET</span><code>/state</code><span class="d">Current state (click to try)</span></div>
<div class="ep"><span class="m post">POST</span><code>/step</code><span class="d">Investigate or triage</span></div>
<div class="ep"><span class="m ws">WS</span><code>/ws</code><span class="d">WebSocket (stateful)</span></div>
<div class="ep" onclick="window.open('/docs','_blank')"><span class="m get">GET</span><code>/docs</code><span class="d">Swagger UI (click to open)</span></div>
</div>
</div>

<div class="status"><span class="dot"></span> Environment is running</div>
</div>

<script>
const L=document.getElementById('log'),B=document.getElementById('bug-area'),A=document.getElementById('act-area');
let ws=null,obs=null;

function log(t,c){const d=document.createElement('div');if(c)d.className=c;d.textContent=t;L.appendChild(d);L.scrollTop=L.scrollHeight}
function clr(){L.innerHTML='';B.innerHTML='';A.style.display='none'}

function getWS(){
  return new Promise((ok,no)=>{
    if(ws&&ws.readyState===1){ok(ws);return}
    const p=location.protocol==='https:'?'wss:':'ws:';
    ws=new WebSocket(p+'//'+location.host+'/ws');
    ws.onopen=()=>ok(ws);
    ws.onerror=e=>{log('WebSocket error','err');no(e)};
    ws.onclose=()=>{ws=null};
  });
}

async function send(msg){
  const s=await getWS();
  return new Promise(ok=>{s.onmessage=e=>ok(JSON.parse(e.data));s.send(JSON.stringify(msg))});
}

async function resetEp(task){
  log('','dim');log('POST /reset  {"task":"'+task+'"}','req');
  try{
    const r=await send({type:'reset',data:{task:task}});
    obs=r.data?.observation||r.data||{};
    log(JSON.stringify(obs,null,2),'res');
    renderBug();
  }catch(e){log('Error: '+e.message,'err')}
}

async function doInv(target){
  log('','dim');log('POST /step  investigate: "'+target+'"','req');
  try{
    const r=await send({type:'step',data:{action_type:'investigate',investigate_target:target,bug_type:'',severity:'',fix_suggestion:''}});
    obs=r.data?.observation||r.data||{};
    log(JSON.stringify(obs,null,2),'res');
    renderBug();
  }catch(e){log('Error: '+e.message,'err')}
}

async function doTriage(){
  const bt=document.getElementById('s-type').value;
  const sv=document.getElementById('s-sev').value;
  const fx=document.getElementById('s-fix').value||'';
  log('','dim');log('POST /step  triage: type='+bt+' sev='+sv,'req');
  try{
    const r=await send({type:'step',data:{action_type:'triage',bug_type:bt,severity:sv,fix_suggestion:fx,investigate_target:''}});
    obs=r.data?.observation||r.data||{};
    const done=r.data?.done||obs.done;
    const reward=r.data?.reward??obs.reward??0;
    log(JSON.stringify(obs,null,2),'res');
    if(obs.step_score>0)log('Step score: '+obs.step_score.toFixed(3),'info');
    if(done){
      log('Episode complete! Final reward: '+(typeof reward==='number'?reward.toFixed(3):reward),'info');
      A.style.display='none';
      const cls=reward>=.8?'good':reward>=.5?'mid':'bad';
      B.innerHTML='<div class="score-box"><div class="score-big '+cls+'">'+(typeof reward==='number'?reward.toFixed(3):reward)+'</div><div style="color:#94a3b8;margin-top:.5rem">Episode Score</div><button class="btn" style="margin-top:1rem" onclick="clr()">Start New Episode</button></div>';
    }else{renderBug()}
  }catch(e){log('Error: '+e.message,'err')}
}

async function doHealth(){
  log('','dim');log('GET /health','req');
  try{const r=await fetch('/health');log(JSON.stringify(await r.json()),'res')}catch(e){log('Error: '+e.message,'err')}
}

async function doState(){
  log('','dim');log('GET /state (from session)','req');
  if(!obs){log('No active episode. Click a task button to start one first.','err');return}
  try{
    const state={
      task_name: obs.task_name||'',
      current_bug: (obs.current_bug_index||0)+'/'+(obs.bugs_total||0),
      investigations_used: (obs.investigations_used||0)+'/'+(obs.investigation_budget||0),
      phase: obs.phase||'',
      done: obs.done||false,
      last_step_score: obs.step_score||0,
      reward: obs.reward||0
    };
    log(JSON.stringify(state,null,2),'res');
  }catch(e){log('Error: '+e.message,'err')}
}

function renderBug(){
  if(!obs||!obs.bug_report){B.innerHTML='';A.style.display='none';return}
  const b=obs.bug_report,id_=obs.investigations_done||[],ia=obs.available_investigations||[];
  const bu=obs.investigations_used||0,bt=obs.investigation_budget||0;
  let inv='';
  id_.forEach(i=>{inv+='<div class="inv-box"><span class="inv-label done">'+i.target+'</span> <span style="color:#cbd5e1">'+i.content+'</span></div>'});
  let avail='';
  ia.forEach(t=>{avail+='<span class="inv-label avail" onclick="doInv(\''+t+'\')">'+t+'</span> '});
  const pct=bt>0?((bu/bt)*100):0;
  B.innerHTML='<div class="bc">'+
    '<h4>Bug '+(obs.current_bug_index||'')+'/'+(obs.bugs_total||'')+': '+(b.title||'')+'</h4>'+
    '<div class="meta">'+(b.affected_component||'')+' &middot; '+(b.reporter_role||'')+' &middot; '+(b.frequency||'')+'</div>'+
    '<div class="desc">'+(b.brief_description||b.description||'')+'</div>'+
    inv+
    (avail?'<div style="margin-top:.5rem"><span style="color:#64748b;font-size:.75rem">Click to investigate: </span>'+avail+'</div>':'')+
    (bt>0?'<div style="color:#64748b;font-size:.75rem;margin-top:.5rem">Budget: '+bu+'/'+bt+'</div><div class="budget-bar"><div class="budget-fill" style="width:'+pct+'%"></div></div>':'')+
    '</div>';
  A.style.display='block';
  document.getElementById('b-logs').disabled=!ia.includes('logs');
  document.getElementById('b-related').disabled=!ia.includes('related');
  document.getElementById('b-reporter').disabled=!ia.includes('reporter');
}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def root():
    return UI_HTML
