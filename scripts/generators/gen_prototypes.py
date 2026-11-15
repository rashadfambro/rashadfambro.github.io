"""Builds clickable prototypes (and trial workspaces) for all fifteen; originally the six 'Ready to build' Desk products into <repo>/prototypes/.
Each page is self-contained (inline CSS/JS), uses sample data only, sends nothing, and keeps state in
localStorage when available. Run: python3 gen_prototypes.py [target_root]"""
import os, sys, html

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'prototypes')
os.makedirs(OUT, exist_ok=True)

CSS = r"""
:root{--ink:#0d1a2d;--ink-3:#1d3454;--paper:#f5f8fc;--line:#d3dce7;--muted:#56606c;--text:#1a2533;--sky:#7cc4ff;--mint:#5fe0b5;--amber:#ffc46b;--rose:#ff8b8b;--brand:#2f7fe0;
--serif:"Source Serif 4",Georgia,serif;--sans:"Manrope",system-ui,-apple-system,"Segoe UI",sans-serif}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 var(--sans);color:var(--text);background:var(--paper)}
a{color:inherit}button,input,select,textarea{font:inherit}
header{background:var(--ink);color:#eef3f9;padding:14px 20px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
header .logo{width:38px;height:38px;border-radius:10px;background:var(--brand);display:grid;place-items:center;font-weight:800;color:#fff}
header h1{font:600 20px/1.1 var(--serif);margin:0}header .sub{font-size:12.5px;color:#a9bbd0}
header .sp{flex:1}header label{font-size:12px;color:#a9bbd0;display:flex;gap:6px;align-items:center}
header input[type=text]{background:#14263f;border:1px solid #2f4766;color:#fff;border-radius:8px;padding:6px 8px;width:170px}
header input[type=color]{width:34px;height:30px;border:0;background:none;padding:0}
.banner{background:#fff6e5;border-bottom:1px solid #f1d9a8;color:#6b4b00;font-size:13px;padding:8px 20px;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.banner a{font-weight:700}
main{max-width:1100px;margin:0 auto;padding:20px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}
.tabs button{border:1px solid var(--line);background:#fff;border-radius:999px;padding:7px 14px;font-weight:700;cursor:pointer;color:var(--text)}
.tabs button[aria-selected=true]{background:var(--ink);color:#fff;border-color:var(--ink)}
.panel[hidden]{display:none}
.grid{display:grid;gap:14px}.g2{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}
@media(max-width:800px){.g2,.g3,.g4{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px}
.card h2{font:600 18px/1.2 var(--serif);margin:0 0 10px}.card h3{font-size:14px;margin:0 0 6px}
.kpi .v{font:600 28px/1.1 var(--serif)}.kpi .l{font-size:12.5px;color:var(--muted)}.kpi .d{font-size:12.5px;font-weight:700}
.up{color:#0a7a52}.down{color:#b42318}
label.f{display:block;font-size:13px;font-weight:700;margin:8px 0 4px}
input.i,select.i,textarea.i{width:100%;border:1px solid var(--line);border-radius:9px;padding:8px 10px;background:#fff}
textarea.i{min-height:90px}
.btn{border:1px solid transparent;border-radius:9px;padding:8px 14px;font-weight:700;cursor:pointer;background:var(--ink);color:#fff}
.btn.alt{background:#fff;color:var(--ink);border-color:#a8b6c7}.btn.ok{background:#0a7a52}.btn.sm{padding:5px 10px;font-size:13px}
.btn:disabled{opacity:.45;cursor:default}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:8px 6px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.chip{display:inline-block;border-radius:999px;padding:2px 9px;font-size:12px;font-weight:700;background:#e9f0f8}
.chip.g{background:#dff7ee;color:#0a6a48}.chip.a{background:#fff1d6;color:#7a5200}.chip.r{background:#ffe3e3;color:#9b1c1c}
.muted{color:var(--muted)}.small{font-size:13px}
.list>div{border-bottom:1px solid var(--line);padding:10px 0}.list>div:last-child{border:0}
.sel{outline:2px solid var(--brand);border-radius:10px}
.out{background:#f2f6fb;border:1px dashed #a8b6c7;border-radius:10px;padding:12px;white-space:pre-wrap}
.bar{height:10px;border-radius:99px;background:#e9f0f8;overflow:hidden}.bar>i{display:block;height:100%;background:var(--brand)}
#toast{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);background:var(--ink);color:#fff;padding:10px 16px;border-radius:10px;font-weight:700;opacity:0;transition:opacity .2s;pointer-events:none;z-index:9}
#toast.on{opacity:1}
footer{max-width:1100px;margin:10px auto 30px;padding:0 20px;font-size:12.5px;color:var(--muted)}
.banner.trial{background:#e8f6ef;border-color:#b7e2cc;color:#0b4f36}.banner.trial.soon{background:#fff4e0;border-color:#f3d39a;color:#6b4100}.banner.trial.end{background:#ffe9e9;border-color:#f3c2c2;color:#7a1414}
#trialEnd{position:fixed;inset:0;background:rgba(13,26,45,.72);display:grid;place-items:center;z-index:20;padding:20px}
#trialEnd .card{max-width:520px}
body.embedded header,body.embedded .banner,body.embedded footer{display:none}
"""

COMMON_JS = r"""
const $=(s,el=document)=>el.querySelector(s), $$=(s,el=document)=>[...el.querySelectorAll(s)];
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const money=n=>"$"+Number(n).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
const KEY="proto-"+document.body.dataset.proto;
function load(def){try{const v=localStorage.getItem(KEY);return v?JSON.parse(v):structuredClone(def)}catch(e){return structuredClone(def)}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}}
function toast(m){const t=$("#toast");t.textContent=m;t.classList.add("on");clearTimeout(toast.h);toast.h=setTimeout(()=>t.classList.remove("on"),2200)}
function brand(){let b={name:"Your Business",color:"#2f7fe0"};try{b=Object.assign(b,JSON.parse(localStorage.getItem("proto-brand")||"{}"))}catch(e){}return b}
function applyBrand(){const b=brand();$("#bizName").value=b.name;$("#bizColor").value=b.color;document.documentElement.style.setProperty("--brand",b.color);$(".logo").textContent=(b.name.trim()[0]||"Y").toUpperCase();$$("[data-biz]").forEach(e=>e.textContent=b.name)}
function setBrand(){const b={name:$("#bizName").value||"Your Business",color:$("#bizColor").value};try{localStorage.setItem("proto-brand",JSON.stringify(b))}catch(e){}applyBrand();if(typeof render==="function")render()}
function tabs(){$$(".tabs button").forEach(b=>b.addEventListener("click",()=>{$$(".tabs button").forEach(x=>x.setAttribute("aria-selected",x===b));$$(".panel").forEach(p=>p.hidden=p.id!==b.dataset.tab)}))}
const TRIAL_DAYS=14;
const DESK_BACKEND="https://script.google.com/macros/s/AKfycbzc37BsdGGlGZes-TCeo7p22rJe5USt2oPx0oxrlSA3Iw1FjllEjXwsitP03UXnF8tngw/exec";  // lead-engine web app URL (…/exec). Empty = no online check.
function remindOnce(key,html){try{const k="proto-remind-"+key+"-"+new Date().toISOString().slice(0,10);if(localStorage.getItem(k))return;localStorage.setItem(k,"1")}catch(e){return}
 if(document.body.classList.contains("embedded"))return;const o=document.createElement("div");o.id="trialRemind";o.style.cssText="position:fixed;inset:0;background:rgba(13,26,45,.55);display:grid;place-items:center;z-index:19;padding:20px";
 o.innerHTML=`<div class="card" role="dialog" aria-modal="true" aria-labelledby="trH" style="max-width:480px">${html}<div class="row"><a class="btn" href="../index.html#pricing">Choose a plan</a><button class="btn alt" type="button" id="trClose">Remind me tomorrow</button></div></div>`;
 document.body.appendChild(o);$("#trClose").onclick=()=>o.remove()}
async function onlineCheck(kind,key){if(!DESK_BACKEND||!key)return;try{const r=await fetch(DESK_BACKEND+"?check="+encodeURIComponent(kind)+"&key="+encodeURIComponent(key),{cache:"no-store"});const j=await r.json();
 if(j&&j.ok&&(j.status==="Paused"||j.status==="Canceled")){const o=document.createElement("div");o.id="trialEnd";o.innerHTML=`<div class="card" role="dialog" aria-modal="true" aria-labelledby="psH"><h2 id="psH">This License Is ${j.status==="Paused"?"Paused":"Canceled"}</h2><p class="small">Your data is safe on this device. Contact Rashad to turn it back on, or download a backup.</p><div class="row"><a class="btn" href="../index.html#contact">Contact Rashad</a><button class="btn alt" type="button" id="psExport">Download backup</button></div></div>`;document.body.appendChild(o);$("#psExport").onclick=exportData}}catch(e){}}
function trialHash(s){let h=2166136261;for(const c of s){h^=c.charCodeAt(0);h=Math.imul(h,16777619)}return (h>>>0).toString(36).toUpperCase().padStart(6,"0").slice(0,6)}
function trialKey(tools,biz,start){return "RF-"+start.replace(/-/g,"")+"-"+trialHash(tools+"|"+biz.trim().toLowerCase()+"|"+start)}
function readTrial(){const q=new URLSearchParams(location.search);
 if(q.get("trial")){const t={key:q.get("trial"),biz:q.get("biz")||"",color:q.get("color")||"#2f7fe0",start:q.get("start")||"",tools:q.get("tools")||document.body.dataset.proto};
  if(!/^\d{4}-\d{2}-\d{2}$/.test(t.start)||t.key!==trialKey(t.tools,t.biz,t.start))return {invalid:true};
  try{localStorage.setItem("proto-trial",JSON.stringify(t));localStorage.setItem("proto-brand",JSON.stringify({name:t.biz,color:t.color}))}catch(e){}return t}
 try{const t=JSON.parse(localStorage.getItem("proto-trial")||"null");if(t&&(t.tools.split(",").includes(document.body.dataset.proto)||document.body.dataset.proto==="suite"))return t}catch(e){}return null}
function trialDaysLeft(t){const s=new Date(t.start+"T00:00:00"),end=new Date(s.getTime()+TRIAL_DAYS*864e5);return Math.ceil((end-new Date())/864e5)}
function exportData(){const data={exported:new Date().toISOString(),brand:brand(),trial:readTrial(),tools:{}};
 try{for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k.startsWith("proto-"))data.tools[k]=localStorage.getItem(k)}}catch(e){}
 const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:"application/json"}));a.download=(document.body.classList.contains("licensed")?"desk-backup-":"desk-trial-data-")+new Date().toISOString().slice(0,10)+".json";a.click();toast("Your data was downloaded")}
function applyTrial(){if(new URLSearchParams(location.search).get("embed")==="1")document.body.classList.add("embedded");
 const t=readTrial(),b=$(".banner");if(!t||!b)return;
 if(t.invalid){b.classList.add("trial","end");$("#btext").innerHTML="<b>This trial link isn't valid.</b> Please use the exact link from your email, or ask for a new one.";return}
 const left=trialDaysLeft(t);b.classList.add("trial");
 if(left>0&&left<=3){b.classList.add("soon");remindOnce("trial",`<h2 id="trH">Your Trial Ends in ${left} Day${left===1?"":"s"}</h2><p class="small">Choose a plan to keep using it with ${esc(t.biz)}'s data, or let it end. Nothing is charged automatically, and you can download your data anytime.</p>`)}
 onlineCheck("trial",t.key);
 if(left>0){$("#btext").innerHTML=`<b>Free ${TRIAL_DAYS}-day trial for ${esc(t.biz)}</b> · ${left} day${left===1?"":"s"} left · your entries stay in this browser · live connections to your own accounts start when you choose a plan`;}
 else{b.classList.add("end");$("#btext").innerHTML=`<b>Your trial for ${esc(t.biz)} has ended.</b> Your entries are still here and you can download them.`;
  const o=document.createElement("div");o.id="trialEnd";o.innerHTML=`<div class="card" role="dialog" aria-modal="true" aria-labelledby="teH"><h2 id="teH">Your ${TRIAL_DAYS}-Day Trial Has Ended</h2><p class="small">Thanks for trying it, ${esc(t.biz)}. Nothing is charged automatically. Choose a plan to keep going with live connections to your own accounts, or download what you entered.</p><div class="row"><a class="btn" href="../index.html#pricing">Choose a plan</a><button class="btn alt" type="button" id="teExport">Download my data</button><a class="btn alt" href="../index.html#audit">Talk to Rashad</a></div></div>`;document.body.appendChild(o);$("#teExport").onclick=exportData}
 const x=document.createElement("button");x.type="button";x.className="btn alt sm";x.textContent="Download my data";x.onclick=exportData;b.appendChild(x)}
function licenseKey(tools,biz,until){return "RFL-"+until.replace(/-/g,"")+"-"+trialHash("L|"+tools+"|"+biz.trim().toLowerCase()+"|"+until)}
function readLicense(){const q=new URLSearchParams(location.search);
 if(q.get("license")){const l={key:q.get("license"),biz:q.get("biz")||"",color:q.get("color")||"#2f7fe0",until:q.get("until")||"",tools:q.get("tools")||document.body.dataset.proto};
  if(!/^\d{4}-\d{2}-\d{2}$/.test(l.until)||l.key!==licenseKey(l.tools,l.biz,l.until))return {invalid:true};
  try{localStorage.setItem("proto-license",JSON.stringify(l));localStorage.setItem("proto-brand",JSON.stringify({name:l.biz,color:l.color}));localStorage.removeItem("proto-trial")}catch(e){}return l}
 try{const l=JSON.parse(localStorage.getItem("proto-license")||"null");if(l&&(l.tools.split(",").includes(document.body.dataset.proto)||document.body.dataset.proto==="suite"))return l}catch(e){}return null}
function licenseDaysLeft(l){return Math.ceil((new Date(l.until+"T23:59:59")-new Date())/864e5)}
function restoreData(file){const r=new FileReader();r.onload=()=>{try{const d=JSON.parse(r.result);if(!d||typeof d.tools!=="object")throw 0;
  Object.entries(d.tools).forEach(([k,v])=>{if(k.startsWith("proto-")&&k!=="proto-license"&&k!=="proto-trial")localStorage.setItem(k,v)});toast("Backup restored");setTimeout(()=>location.reload(),600)}catch(e){toast("That file isn't a Desk backup")}};r.readAsText(file)}
function starterCopy(e){const b=e.target.closest("button");if(!b||!/^Approve/.test(b.textContent.trim()))return;
 const box=b.closest(".list>div, .card, [data-post]"),ta=box&&box.querySelector("textarea");if(!ta||!ta.value.trim())return;
 try{navigator.clipboard&&navigator.clipboard.writeText(ta.value)}catch(err){}setTimeout(()=>toast("Approved and copied: paste it into your text or email app"),2300)}
function applyLicense(){const l=readLicense(),b=$(".banner");if(!l||!b)return false;
 if(l.invalid){b.classList.add("trial","end");$("#btext").innerHTML="<b>This license link isn't valid.</b> Please use the exact link from your welcome email.";return true}
 document.body.classList.add("licensed");const left=licenseDaysLeft(l);onlineCheck("license",l.key);if(left>=0&&left<=5)b.classList.add("soon");b.classList.add("trial");
 const lock=left<-30;if(left<0)b.classList.add("end");
 $("#btext").innerHTML=left>=0?`<b>Starter edition · licensed to ${esc(l.biz)}</b> · ${left<=5?`<b>renews in ${left} day${left===1?"":"s"} (${esc(l.until)})</b>`:`renews ${esc(l.until)}`} · data is saved on this device: download a backup weekly · approved messages are copied for you to send`
  :`<b>Your license renewal is past due${lock?"":` (${-left} day${left===-1?"":"s"})`}.</b> ${lock?"The app is paused until the plan is renewed; your data is kept.":"Please renew to keep updates and support."}`;
 const d=document.createElement("button");d.type="button";d.className="btn alt sm";d.textContent="Download backup";d.onclick=exportData;b.appendChild(d);
 const lab=document.createElement("label");lab.className="btn alt sm";lab.textContent="Restore backup";const f=document.createElement("input");f.type="file";f.accept="application/json";f.hidden=true;f.onchange=()=>f.files[0]&&restoreData(f.files[0]);lab.appendChild(f);b.appendChild(lab);
 const rs=$("#reset");if(rs)rs.hidden=true;
 document.addEventListener("click",starterCopy,true);
 if(lock){const o=document.createElement("div");o.id="trialEnd";o.innerHTML=`<div class="card" role="dialog" aria-modal="true" aria-labelledby="lkH"><h2 id="lkH">Your Plan Needs Renewal</h2><p class="small">Your data is safe and still on this device. Renew your monthly plan to unlock the app, or download a backup.</p><div class="row"><a class="btn" href="../index.html#pricing">Renew my plan</a><button class="btn alt" type="button" id="lkExport">Download backup</button></div></div>`;document.body.appendChild(o);$("#lkExport").onclick=exportData}
 return true}
document.addEventListener("DOMContentLoaded",()=>{if(new URLSearchParams(location.search).get("embed")==="1")document.body.classList.add("embedded");if(!applyLicense())applyTrial();tabs();applyBrand();$("#bizName").addEventListener("input",setBrand);$("#bizColor").addEventListener("input",setBrand);
 $("#reset").addEventListener("click",()=>{try{localStorage.removeItem(KEY)}catch(e){}S=structuredClone(DEF);render();toast("Sample data restored")});render()});
"""

def shell(pid, name, tagline, tabs, body, js):
    tabs_html = ''.join(f'<button type="button" data-tab="{t[0]}" aria-selected="{"true" if i==0 else "false"}">{html.escape(t[1])}</button>' for i, t in enumerate(tabs))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://formsubmit.co https://script.google.com https://script.googleusercontent.com; frame-src 'self' https://calendly.com; object-src 'none'; base-uri 'self'; form-action 'self' https://formsubmit.co"><meta name="referrer" content="strict-origin-when-cross-origin"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} Prototype · Rashad Fambro Consulting</title>
<meta name="description" content="{html.escape(tagline)} Clickable prototype with sample data.">
<link rel="icon" href="../icon.svg"><link rel="canonical" href="https://rashadfambro.github.io/prototypes/{FILES[pid]}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style></head>
<body data-proto="{pid}">
<header><div class="logo">Y</div><div><h1>{name} <span class="sub">for <span data-biz>Your Business</span></span></h1><div class="sub">{html.escape(tagline)}</div></div><span class="sp"></span>
<label>Brand name <input type="text" id="bizName" aria-label="Business name"></label><label>Color <input type="color" id="bizColor" aria-label="Brand color"></label></header>
<div class="banner"><span id="btext"><b>Prototype</b> · sample data · nothing is sent to anyone. Every client version is branded and set up around your workflow.</span><span class="sp"></span>
<a href="../index.html#products">← Back to products</a><a href="../index.html#audit">Book a free audit</a><button type="button" class="btn alt sm" id="reset">Reset sample data</button></div>
<main><nav class="tabs" aria-label="{name} sections">{tabs_html}</nav>
{body}
</main>
<footer>Built by Rashad Fambro Consulting. People stay in control: nothing goes to customers without approval.</footer>
<div id="toast" role="status" aria-live="polite"></div>
<script>{COMMON_JS}
{js}</script></body></html>
'''

P = {}

# ---------------------------------------------------------------- RewardsDesk
P['rewards'] = dict(name='RewardsDesk', tag='Points by phone number, automatic offers you approve, and repeat-visit results.',
tabs=[('checkout','Checkout'),('customers','Customers'),('offers','Offers to Approve'),('results','Results')],
body='''
<section class="panel" id="checkout"><div class="grid g2">
 <div class="card"><h2>At the Register</h2>
  <label class="f" for="phone">Customer phone number</label><div class="row"><input class="i" id="phone" placeholder="e.g. 555-0142" style="flex:1"><button class="btn" id="lookup" type="button">Look up</button></div>
  <div id="who" class="small" style="margin-top:10px"></div>
  <div id="joinBox" hidden><label class="f" for="jname">First name</label><input class="i" id="jname">
   <label class="small"><input type="checkbox" id="joptin" checked> Customer agrees to receive reward texts (reply STOP to end)</label><br>
   <label class="small" id="ageRow"><input type="checkbox" id="jage"> ID checked: customer is of legal age</label>
   <div class="row" style="margin-top:8px"><button class="btn" id="join" type="button">Join rewards</button></div></div>
  <div id="buyBox" hidden><label class="f" for="amt">Purchase amount ($)</label><div class="row"><input class="i" id="amt" type="number" min="0" step="0.01" value="24.50" style="flex:1"><button class="btn ok" id="addPts" type="button">Add points</button></div></div>
  <div id="rewardBox" style="margin-top:12px"></div>
 </div>
 <div class="card"><h2>Program Rules</h2>
  <p class="small">1 point per $1. <b id="ruleTxt"></b></p>
  <label class="f" for="thr">Points for a reward</label><input class="i" id="thr" type="number" min="10" step="10">
  <label class="f" for="rv">Reward value ($ off)</label><input class="i" id="rv" type="number" min="1">
  <label class="small" style="display:block;margin-top:10px"><input type="checkbox" id="agerestr"> Age-restricted products (ask for ID at sign-up)</label>
  <p class="muted small">Texts go only to customers who opted in. Owners approve every offer before it is sent.</p>
 </div></div></section>
<section class="panel" id="customers" hidden><div class="card"><h2>Members</h2><table><thead><tr><th>Name</th><th>Phone</th><th>Points</th><th>Visits</th><th>Last visit</th><th>Texts</th></tr></thead><tbody id="custRows"></tbody></table></div></section>
<section class="panel" id="offers" hidden><div class="card"><h2>Offers Waiting for Your Approval</h2><p class="small muted">Drafted automatically from birthdays, lapsed regulars, and milestones.</p><div class="list" id="offerList"></div></div></section>
<section class="panel" id="results" hidden><div class="grid g4" id="kpis"></div><div class="card" style="margin-top:14px"><h2>Top Customers</h2><table><thead><tr><th>Name</th><th>Visits</th><th>Points</th></tr></thead><tbody id="topRows"></tbody></table></div></section>
''',
js=r'''
const M=new Date().getMonth()+1;
const DEF={thr:100,rv:10,age:false,sent:[],cust:[
 {name:"Maria",phone:"555-0142",points:86,visits:9,last:3,bday:M,opt:true},
 {name:"Devon",phone:"555-0177",points:140,visits:14,last:6,bday:4,opt:true},
 {name:"Aisha",phone:"555-0190",points:22,visits:2,last:51,bday:9,opt:true},
 {name:"Tom",phone:"555-0105",points:61,visits:7,last:63,bday:M,opt:false},
 {name:"Lena",phone:"555-0123",points:12,visits:1,last:20,bday:1,opt:true},
 {name:"Chris",phone:"555-0168",points:97,visits:11,last:2,bday:7,opt:true}]};
let S=load(DEF), cur=null;
const norm=p=>p.replace(/\D/g,"").slice(-7);
function offersList(){const b=brand().name,o=[];
 S.cust.forEach(c=>{if(c.bday===M)o.push({id:"bd-"+c.phone,c,kind:"Birthday",text:`Happy birthday, ${c.name}! Enjoy $${S.rv} off your next visit at ${b} this month.`});
  if(c.last>45)o.push({id:"wm-"+c.phone,c,kind:"We miss you",text:`Hi ${c.name}, it's been a while! Here's double points on your next visit to ${b} this week.`});
  if(c.points>=S.thr)o.push({id:"rw-"+c.phone,c,kind:"Reward ready",text:`${c.name}, you've earned $${S.rv} off at ${b}. Show this text at checkout.`});});
 return o.filter(x=>!S.sent.includes(x.id))}
function render(){$("#thr").value=S.thr;$("#rv").value=S.rv;$("#agerestr").checked=S.age;$("#ageRow").hidden=!S.age;
 $("#ruleTxt").textContent=`Every ${S.thr} points = $${S.rv} off.`;
 $("#custRows").innerHTML=S.cust.map(c=>`<tr><td>${esc(c.name)}</td><td>${esc(c.phone)}</td><td>${c.points}</td><td>${c.visits}</td><td>${c.last} days ago</td><td>${c.opt?'<span class="chip g">Opted in</span>':'<span class="chip">No texts</span>'}</td></tr>`).join("");
 const o=offersList();$("#offerList").innerHTML=o.length?o.map(x=>`<div><div class="row"><span class="chip a">${x.kind}</span><b>${esc(x.c.name)}</b>${x.c.opt?"":'<span class="chip r">Not opted in: will not be texted</span>'}</div><textarea class="i" data-txt="${x.id}" style="min-height:60px;margin-top:6px">${esc(x.text)}</textarea><div class="row" style="margin-top:6px"><button class="btn ok sm" data-ok="${x.id}" type="button">Approve &amp; send</button><button class="btn alt sm" data-skip="${x.id}" type="button">Skip</button></div></div>`).join(""):'<p class="muted">All caught up. New offers appear as customers hit milestones.</p>';
 $$("[data-ok]").forEach(b=>b.onclick=()=>{const x=o.find(y=>y.id===b.dataset.ok);S.sent.push(x.id);save();render();toast(x.c.opt?`Sent to ${x.c.name}`:`Skipped: ${x.c.name} has not opted in`)});
 $$("[data-skip]").forEach(b=>b.onclick=()=>{S.sent.push(b.dataset.skip);save();render();toast("Skipped")});
 const n=S.cust.length,rep=S.cust.filter(c=>c.visits>=2).length,pts=S.cust.reduce((a,c)=>a+c.points,0);
 $("#kpis").innerHTML=[["Members",n],["Repeat-visit rate",Math.round(rep/n*100)+"%"],["Points outstanding",pts],["Offers sent",S.sent.length]].map(k=>`<div class="card kpi"><div class="v">${k[1]}</div><div class="l">${k[0]}</div></div>`).join("");
 $("#topRows").innerHTML=[...S.cust].sort((a,b)=>b.visits-a.visits).slice(0,5).map(c=>`<tr><td>${esc(c.name)}</td><td>${c.visits}</td><td>${c.points}</td></tr>`).join("");
 showCur()}
function showCur(){$("#rewardBox").innerHTML="";if(!cur){return}
 $("#who").innerHTML=`<b>${esc(cur.name)}</b> · ${cur.points} points · ${cur.visits} visits`;$("#buyBox").hidden=false;$("#joinBox").hidden=true;
 if(cur.points>=S.thr)$("#rewardBox").innerHTML=`<div class="out" id="rewardReady"><b>Reward ready:</b> $${S.rv} off. <button class="btn sm" id="redeem" type="button">Redeem now</button></div>`,$("#redeem").onclick=()=>{cur.points-=S.thr;save();render();toast(`Redeemed $${S.rv} off for ${cur.name}`)}}
$("#lookup").onclick=()=>{const p=norm($("#phone").value);if(p.length<7){toast("Enter a phone number");return}
 cur=S.cust.find(c=>norm(c.phone)===p)||null;
 if(cur){showCur()}else{$("#who").innerHTML="New customer: invite them to join.";$("#joinBox").hidden=false;$("#buyBox").hidden=true;$("#rewardBox").innerHTML=""}};
$("#join").onclick=()=>{const name=$("#jname").value.trim();if(!name){toast("Add a first name");return}
 if(S.age&&!$("#jage").checked){toast("Check ID before joining");return}
 cur={name,phone:$("#phone").value.trim(),points:0,visits:0,last:0,bday:0,opt:$("#joptin").checked};S.cust.push(cur);save();render();toast(`${name} joined`)};
$("#addPts").onclick=()=>{if(!cur)return;const pts=Math.floor(Number($("#amt").value)||0);cur.points+=pts;cur.visits+=1;cur.last=0;save();render();toast(`+${pts} points for ${cur.name}`)};
$("#thr").onchange=()=>{S.thr=Math.max(10,Number($("#thr").value)||100);save();render()};
$("#rv").onchange=()=>{S.rv=Math.max(1,Number($("#rv").value)||10);save();render()};
$("#agerestr").onchange=()=>{S.age=$("#agerestr").checked;save();render()};
''')

# ---------------------------------------------------------------- ReviewDesk
P['review'] = dict(name='ReviewDesk', tag='Invite every customer to leave a review, offer everyone a private feedback option, and reply to every review.',
tabs=[('inbox','Review Inbox'),('ask','Ask for Reviews'),('trends','Trends')],
body='''
<section class="panel" id="inbox"><div class="grid g2">
 <div class="card"><div class="row" style="justify-content:space-between"><h2>Reviews</h2><label class="small"><input type="checkbox" id="onlyOpen" checked> Needs a reply</label></div><div class="list" id="revList"></div></div>
 <div class="card"><h2>Drafted Reply</h2><div id="revSel" class="small muted">Pick a review to see the drafted reply.</div>
  <textarea class="i" id="reply" hidden></textarea><div class="row" style="margin-top:8px"><button class="btn ok" id="post" type="button" hidden>Approve &amp; post reply</button></div>
  <p class="small muted">Nothing posts until you approve it. Low ratings are drafted with an apology and an offer to talk offline.</p></div></div></section>
<section class="panel" id="ask" hidden><div class="grid g2">
 <div class="card"><h2>Send a Review Request</h2><label class="f" for="cname">Customer name</label><input class="i" id="cname" value="Jordan">
  <p class="small">Preview what the customer sees, then pick how they rated the visit:</p>
  <div class="out" id="askMsg"></div>
  <div class="row" style="margin-top:8px" id="stars"></div>
  <div id="askResult" style="margin-top:10px"></div></div>
 <div class="card"><h2>Private Feedback</h2><p class="small muted">Any customer can send private feedback. Everyone still gets the same link to leave a public review.</p><div class="list" id="privList"></div></div></div></section>
<section class="panel" id="trends" hidden><div class="grid g3" id="rkpis"></div><div class="card" style="margin-top:14px"><h2>Average Rating by Month</h2><div id="chart"></div></div></section>
''',
js=r'''
const DEF={sel:null,priv:[],rev:[
 {id:1,name:"Sam P.",stars:5,src:"Google",text:"Fast, friendly staff and the place was spotless. Will be back!",replied:false},
 {id:2,name:"Rita K.",stars:2,src:"Google",text:"Waited 25 minutes past my appointment time and nobody told me why.",replied:false},
 {id:3,name:"Jon M.",stars:4,src:"Yelp",text:"Good service, a little pricey but worth it.",replied:false},
 {id:4,name:"Bea L.",stars:5,src:"Google",text:"Ask for Nina, she is amazing.",replied:true,reply:"Thank you, Bea! We'll pass this on to Nina."},
 {id:5,name:"Ola D.",stars:1,src:"Yelp",text:"Rude at the front desk and my order was wrong.",replied:false}],
 months:[["Jun",4.1],["Jul",4.2],["Aug",4.0],["Sep",4.3],["Oct",4.4],["Nov",4.5]]};
let S=load(DEF);
function draft(r){const b=brand().name,first=r.name.split(" ")[0];
 if(r.stars>=4){let x=`Thank you, ${first}! We're so glad you had a great visit`;if(/staff|friendly|nina|team/i.test(r.text))x+=" and we'll share your kind words with the team";if(/price|pricey|cost/i.test(r.text))x+=". We work hard to make every visit worth it";return x+`. See you next time at ${b}!`}
 let x=`${first}, we're sorry your visit didn't meet expectations.`;if(/wait|late|minutes/i.test(r.text))x+=" Waiting past your appointment time isn't okay, and we're fixing how we keep guests updated.";if(/rude|staff|desk/i.test(r.text))x+=" How you were treated matters to us, and we've shared this with our manager.";if(/wrong|order|mistake/i.test(r.text))x+=" We'd like to make your order right.";
 return x+` Please reach out to us directly so we can make it up to you. — The ${b} team`}
function render(){const only=$("#onlyOpen").checked;
 $("#revList").innerHTML=S.rev.filter(r=>!only||!r.replied).map(r=>`<div data-r="${r.id}" class="${S.sel===r.id?"sel":""}" style="cursor:pointer;padding:10px"><div class="row"><b>${"★".repeat(r.stars)}${"☆".repeat(5-r.stars)}</b><span class="chip">${r.src}</span>${r.replied?'<span class="chip g">Replied</span>':'<span class="chip a">Needs reply</span>'}</div><div><b>${esc(r.name)}</b>: ${esc(r.text)}</div>${r.replied?`<div class="small muted">Reply: ${esc(r.reply)}</div>`:""}</div>`).join("")||'<p class="muted">Every review has a reply.</p>';
 $$("[data-r]").forEach(d=>d.onclick=()=>{S.sel=Number(d.dataset.r);render()});
 const r=S.rev.find(x=>x.id===S.sel);
 if(r&&!r.replied){$("#revSel").innerHTML=`Replying to <b>${esc(r.name)}</b> (${r.stars}★)`;$("#reply").hidden=false;$("#post").hidden=false;if($("#reply").dataset.for!==String(r.id)){$("#reply").value=draft(r);$("#reply").dataset.for=r.id}}else{$("#reply").hidden=true;$("#post").hidden=true;$("#revSel").textContent="Pick a review that needs a reply."}
 $("#askMsg").textContent=`Hi ${$("#cname").value||"there"}, thanks for visiting ${brand().name}! How did we do? Tap a star.`;
 $("#stars").innerHTML=[1,2,3,4,5].map(n=>`<button class="btn alt sm" data-star="${n}" type="button">${n}★</button>`).join("");
 $$("[data-star]").forEach(b=>b.onclick=()=>{const n=Number(b.dataset.star),c=$("#cname").value||"Customer";
  const both=`<div class="row" style="margin-top:6px"><span class="chip">Leave a Google review</span><span class="chip">Send private feedback</span></div>`;
  $("#askResult").innerHTML=`<div class="out"><b>Shown to ${esc(c)}:</b> ${n>=4?"Thank you!":"Thank you for telling us."} We'd love to hear more. You can leave a public review, send us private feedback, or both.${both}</div><p class="small muted">Every customer sees the same two options, whatever their rating.</p>`;
  if(n<=3){S.priv.unshift({c,n});save();render();toast("Same options shown; follow-up flagged for you")}else toast("Same options shown to every customer")});
 $("#privList").innerHTML=S.priv.length?S.priv.map(p=>`<div><b>${esc(p.c)}</b> rated ${p.n}★ <span class="chip a">Call back</span></div>`).join(""):'<p class="muted small">None yet. Ratings of 1–3 stars are flagged here for a follow-up call.</p>';
 const avg=(S.rev.reduce((a,r)=>a+r.stars,0)/S.rev.length).toFixed(1),rate=Math.round(S.rev.filter(r=>r.replied).length/S.rev.length*100);
 $("#rkpis").innerHTML=[["Average rating (inbox)",avg+"★"],["Reviews answered",rate+"%"],["Follow-ups flagged",S.priv.length]].map(k=>`<div class="card kpi"><div class="v">${k[1]}</div><div class="l">${k[0]}</div></div>`).join("");
 const W=600,H=200,bw=60;$("#chart").innerHTML=`<svg viewBox="0 0 ${W} ${H+30}" role="img" aria-label="Average rating by month" style="width:100%;max-width:640px">${S.months.map((m,i)=>{const h=(m[1]-3)/2*H,x=30+i*(bw+30);return `<rect x="${x}" y="${H-h}" width="${bw}" height="${h}" rx="6" fill="var(--brand)"/><text x="${x+bw/2}" y="${H-h-6}" text-anchor="middle" font-size="13" fill="#1a2533">${m[1].toFixed(1)}</text><text x="${x+bw/2}" y="${H+20}" text-anchor="middle" font-size="12" fill="#56606c">${m[0]}</text>`}).join("")}</svg><p class="small muted">Axis starts at 3.0 stars to show the change.</p>`}
$("#post").onclick=()=>{const r=S.rev.find(x=>x.id===S.sel);if(!r)return;r.replied=true;r.reply=$("#reply").value;S.sel=null;save();render();toast("Reply approved and posted")};
$("#onlyOpen").onchange=render;$("#cname").oninput=render;
''')

# ---------------------------------------------------------------- SocialDesk
P['social'] = dict(name='SocialDesk', tag='A month of on-brand posts drafted for approval, plus instant replies to common DMs.',
tabs=[('plan','Content Calendar'),('dms','DM Auto-Replies'),('setup','Brand Voice')],
body='''
<section class="panel" id="plan"><div class="card"><div class="row" style="justify-content:space-between"><h2>This Month's Posts</h2><div class="row"><button class="btn" id="gen" type="button">Draft this month</button><button class="btn ok" id="sched" type="button">Schedule approved posts</button></div></div>
 <p class="small muted" id="planNote"></p><div class="grid g3" id="posts"></div></div></section>
<section class="panel" id="dms" hidden><div class="grid g2">
 <div class="card"><h2>Keyword Replies</h2><table><thead><tr><th>Keyword</th><th>Auto-reply</th></tr></thead><tbody id="kwRows"></tbody></table></div>
 <div class="card"><h2>Test a DM</h2><label class="f" for="dm">Message from a follower</label><input class="i" id="dm" value="what's the price for a cut?"><div class="row" style="margin-top:8px"><button class="btn" id="testDm" type="button">See the reply</button></div><div class="out" id="dmOut" style="margin-top:10px">The reply appears here.</div></div></div></section>
<section class="panel" id="setup" hidden><div class="card"><h2>Brand Voice</h2><div class="grid g3">
 <div><label class="f" for="ind">Industry</label><select class="i" id="ind"><option value="salon">Salon or barbershop</option><option value="restaurant">Restaurant</option><option value="apartments">Apartment community</option><option value="contractor">Contractor</option><option value="retail">Retail shop</option></select></div>
 <div><label class="f" for="tone">Tone</label><select class="i" id="tone"><option>Friendly</option><option>Professional</option><option>Playful</option></select></div>
 <div><label class="f" for="offer">Offer to feature</label><input class="i" id="offer"></div></div>
 <p class="small muted">Change these, then go back to the calendar and draft the month again.</p></div></section>
''',
js=r'''
const DEF={ind:"salon",tone:"Friendly",offer:"10% off your first visit",posts:[],kw:[["PRICE","Thanks for asking! Our full price list is here: [link]. Want to book?"],["BOOK","You can book in under a minute here: [booking link]"],["HOURS","We're open Tue–Sat, 9–7. See you soon!"],["HELP","Thanks for reaching out — a team member will reply shortly."]]};
let S=load(DEF);
const IDEAS={salon:["the 3 questions to ask before a color change","what happens during a first visit","how to keep a fresh cut looking sharp for weeks","meet the team member behind your favorite style"],
 restaurant:["the dish our regulars order most","what's new on the menu this month","how our kitchen preps for Friday night","the story behind our signature recipe"],
 apartments:["5 ways to make move-in day easier","how to submit a maintenance request in under a minute","community events this month","a resident favorite amenity"],
 contractor:["the #1 sign it's time to repair, not replace","before and after from a recent project","what to ask any contractor before you hire","how we keep job sites clean"],
 retail:["new arrivals this week","staff picks of the month","how our rewards program works","a quick gift guide"]};
const TYPES=["Tip","Behind the scenes","Offer","FAQ"],TAGS={salon:"#salon #hairgoals #selfcare",restaurant:"#foodie #localeats #supportlocal",apartments:"#apartmentliving #community #home",contractor:"#homeimprovement #renovation #beforeandafter",retail:"#shoplocal #newarrivals #giftideas"};
function voice(t){return S.tone==="Professional"?t:S.tone==="Playful"?t+" ✨":t+" 💙"}
function gen(){const b=brand().name,ideas=IDEAS[S.ind],d=new Date(),y=d.getFullYear(),m=d.getMonth(),posts=[];let n=0;
 for(let day=1;day<=28&&posts.length<12;day++){const dt=new Date(y,m,day);if(![1,3,5].includes(dt.getDay()))continue;const type=TYPES[n%4],idea=ideas[n%4];
  const cap=type==="Offer"?`${S.offer} at ${b}. Tap the link in bio or DM us BOOK to claim it.`:type==="FAQ"?`You asked: ${idea}? Here's the answer, straight from the ${b} team.`:type==="Tip"?`Quick tip from ${b}: ${idea}.`:`Behind the scenes at ${b}: ${idea}.`;
  posts.push({date:dt.toDateString().slice(0,10),type,cap:voice(cap),tags:TAGS[S.ind],status:"Draft"});n++}
 S.posts=posts;save();render();toast("12 posts drafted for your review")}
function render(){$("#ind").value=S.ind;$("#tone").value=S.tone;$("#offer").value=S.offer;
 const a=S.posts.filter(p=>p.status!=="Draft").length;$("#planNote").textContent=S.posts.length?`${S.posts.length} posts · ${a} approved or scheduled. Edit any caption before approving.`:"Click “Draft this month” to create 12 posts (Mon/Wed/Fri) in your brand voice.";
 $("#posts").innerHTML=S.posts.map((p,i)=>`<div class="card" data-post="${i}"><div class="row" style="justify-content:space-between"><b>${p.date}</b><span class="chip ${p.status==="Draft"?"a":"g"}">${p.status}</span></div><div class="small muted">${p.type}</div><textarea class="i" data-cap="${i}" style="min-height:96px;margin-top:6px">${esc(p.cap)}</textarea><div class="small muted">${p.tags}</div><div class="row" style="margin-top:6px"><button class="btn ok sm" data-app="${i}" type="button" ${p.status!=="Draft"?"disabled":""}>Approve</button></div></div>`).join("");
 $$("[data-cap]").forEach(t=>t.oninput=()=>{S.posts[t.dataset.cap].cap=t.value;save()});
 $$("[data-app]").forEach(b=>b.onclick=()=>{S.posts[b.dataset.app].status="Approved";save();render()});
 $("#kwRows").innerHTML=S.kw.map((k,i)=>`<tr><td><b>${k[0]}</b></td><td><input class="i" data-kw="${i}" value="${esc(k[1])}"></td></tr>`).join("");
 $$("[data-kw]").forEach(t=>t.oninput=()=>{S.kw[t.dataset.kw][1]=t.value;save()})}
$("#gen").onclick=gen;
$("#sched").onclick=()=>{let n=0;S.posts.forEach(p=>{if(p.status==="Approved"){p.status="Scheduled";n++}});save();render();toast(n?`${n} posts scheduled`:"Approve some posts first")};
$("#testDm").onclick=()=>{const t=$("#dm").value.toLowerCase(),map={PRICE:/price|cost|how much/,BOOK:/book|appointment|available|schedule/,HOURS:/hour|open|close/};
 const hit=S.kw.find(k=>map[k[0]]&&map[k[0]].test(t));$("#dmOut").innerHTML=hit?`<b>Auto-reply (${hit[0]}):</b> ${esc(hit[1])}`:"<b>No keyword matched.</b> This DM goes to your inbox for a person to answer."};
$("#ind").onchange=()=>{S.ind=$("#ind").value;save()};$("#tone").onchange=()=>{S.tone=$("#tone").value;save()};$("#offer").oninput=()=>{S.offer=$("#offer").value;save()};
''')

# ---------------------------------------------------------------- StaffDesk
P['staff'] = dict(name='StaffDesk', tag='Staff get answers from your handbook, managers approve shift swaps, and new hires follow a checklist.',
tabs=[('askt','Ask the Handbook'),('book','Handbook'),('swaps','Shift Swaps'),('onboard','Onboarding')],
body='''
<section class="panel" id="askt"><div class="grid g2">
 <div class="card"><h2>Ask a Question</h2><label class="f" for="q">What do you need to know?</label><input class="i" id="q" value="How do I close the register?"><div class="row" style="margin-top:8px"><button class="btn" id="askBtn" type="button">Ask</button></div><div class="out" id="ans" style="margin-top:10px">Answers come only from your handbook, with the source shown.</div></div>
 <div class="card"><h2>Questions for a Manager</h2><p class="small muted">When the handbook doesn't cover it, the question goes to a manager instead of a guess.</p><div class="list" id="mgrQ"></div></div></div></section>
<section class="panel" id="book" hidden><div class="grid g2"><div class="card"><h2>Policies &amp; SOPs</h2><div class="list" id="sops"></div></div>
 <div class="card"><h2>Add a Policy</h2><label class="f" for="st">Title</label><input class="i" id="st"><label class="f" for="sb">Text</label><textarea class="i" id="sb"></textarea><div class="row" style="margin-top:8px"><button class="btn" id="addSop" type="button">Add to handbook</button></div></div></div></section>
<section class="panel" id="swaps" hidden><div class="grid g2"><div class="card"><h2>Request a Swap</h2>
 <label class="f" for="sf">Your name</label><input class="i" id="sf" value="Jasmine"><label class="f" for="sto">Covering teammate</label><input class="i" id="sto" value="Marcus"><label class="f" for="sd">Shift</label><input class="i" id="sd" value="Saturday 2–10 PM"><div class="row" style="margin-top:8px"><button class="btn" id="reqSwap" type="button">Send to manager</button></div></div>
 <div class="card"><h2>Manager Approval</h2><div class="list" id="swapList"></div></div></div></section>
<section class="panel" id="onboard" hidden><div class="card"><div class="row" style="justify-content:space-between"><h2>New Hires</h2><div class="row"><input class="i" id="nh" placeholder="New hire name" style="width:200px"><button class="btn" id="addNh" type="button">Add</button></div></div><div class="grid g2" id="hires"></div></div></section>
''',
js=r'''
const STEPS=["Paperwork and ID","Read the handbook","Shadow a shift","POS and register training","Safety walkthrough","First solo shift"];
const DEF={mq:[],swaps:[{from:"Leo",to:"Priya",shift:"Friday 6–11 PM",status:"Pending"}],hires:[{name:"Avery",done:[0,1]}],sops:[
 {t:"Closing the register",b:"Count the drawer with a second person, record totals on the closing sheet, drop cash over $200 in the safe, and lock the drawer. Report any difference over $5 to the manager on duty."},
 {t:"Opening checklist",b:"Arrive 20 minutes early, turn off the alarm, check the schedule, stock the front, and open the register with $150 starting cash."},
 {t:"Calling out sick",b:"Call the manager on duty at least 2 hours before your shift. Texts alone don't count. Two no-call no-shows end employment."},
 {t:"Refunds and returns",b:"Refunds within 14 days with a receipt to the original payment. Store credit without a receipt. Anything over $100 needs a manager."},
 {t:"Dress code",b:"Black top with the company logo, clean closed-toe shoes, name tag visible."},
 {t:"Safety incidents",b:"Make the area safe, help the injured person, tell the manager right away, and fill in an incident form before the end of the shift."}]};
let S=load(DEF);
const words=s=>s.toLowerCase().match(/[a-z]{3,}/g)||[];
function answer(q){const qs=new Set(words(q).filter(w=>!["how","what","the","for","can","does","you","need","know","when","with","about","our"].includes(w)));let best=null,score=0;
 S.sops.forEach(s=>{const sw=words(s.t+" "+s.b);let n=0;qs.forEach(w=>{if(sw.some(x=>x.startsWith(w.slice(0,5))))n++});if(n>score){score=n;best=s}});return score>=1?best:null}
function render(){
 $("#sops").innerHTML=S.sops.map(s=>`<div><b>${esc(s.t)}</b><div class="small">${esc(s.b)}</div></div>`).join("");
 $("#mgrQ").innerHTML=S.mq.length?S.mq.map(q=>`<div>${esc(q)} <span class="chip a">Waiting for a manager</span></div>`).join(""):'<p class="muted small">None right now.</p>';
 $("#swapList").innerHTML=S.swaps.map((w,i)=>`<div><b>${esc(w.from)}</b> → <b>${esc(w.to)}</b> · ${esc(w.shift)} <span class="chip ${w.status==="Approved"?"g":w.status==="Declined"?"r":"a"}">${w.status}</span>${w.status==="Pending"?`<div class="row" style="margin-top:6px"><button class="btn ok sm" data-ap="${i}" type="button">Approve</button><button class="btn alt sm" data-de="${i}" type="button">Decline</button></div>`:""}</div>`).join("");
 $$("[data-ap]").forEach(b=>b.onclick=()=>{S.swaps[b.dataset.ap].status="Approved";save();render();toast("Swap approved; schedule updated")});
 $$("[data-de]").forEach(b=>b.onclick=()=>{S.swaps[b.dataset.de].status="Declined";save();render()});
 $("#hires").innerHTML=S.hires.map((h,i)=>{const pct=Math.round(h.done.length/STEPS.length*100);return `<div class="card"><div class="row" style="justify-content:space-between"><b>${esc(h.name)}</b><span class="small">${pct}% done</span></div><div class="bar" style="margin:8px 0"><i style="width:${pct}%"></i></div>${STEPS.map((s,j)=>`<label class="small" style="display:block"><input type="checkbox" data-h="${i}" data-s="${j}" ${h.done.includes(j)?"checked":""}> ${s}</label>`).join("")}</div>`}).join("");
 $$("[data-h]").forEach(c=>c.onchange=()=>{const h=S.hires[c.dataset.h],j=Number(c.dataset.s);h.done=c.checked?[...new Set([...h.done,j])]:h.done.filter(x=>x!==j);save();render()})}
$("#askBtn").onclick=()=>{const q=$("#q").value.trim();if(!q)return;const s=answer(q);
 if(s){$("#ans").innerHTML=`<b>${esc(s.b)}</b><div class="small muted" style="margin-top:6px">From your handbook: “${esc(s.t)}”</div>`}else{S.mq.unshift(q);save();render();$("#ans").innerHTML="<b>The handbook doesn't cover that.</b> I've sent your question to a manager instead of guessing."}};
$("#addSop").onclick=()=>{const t=$("#st").value.trim(),b=$("#sb").value.trim();if(!t||!b){toast("Add a title and text");return}S.sops.push({t,b});$("#st").value=$("#sb").value="";save();render();toast("Added to the handbook")};
$("#reqSwap").onclick=()=>{S.swaps.unshift({from:$("#sf").value,to:$("#sto").value,shift:$("#sd").value,status:"Pending"});save();render();toast("Sent to the manager for approval")};
$("#addNh").onclick=()=>{const n=$("#nh").value.trim();if(!n)return;S.hires.push({name:n,done:[]});$("#nh").value="";save();render()};
''')

# ---------------------------------------------------------------- InvoiceDesk
P['invoice'] = dict(name='InvoiceDesk', tag='Approved quotes become invoices, reminders go out on schedule, and you see who owes what.',
tabs=[('quotes','Quotes'),('invoices','Invoices'),('remind','Reminders to Approve'),('aging','Who Owes What')],
body='''
<section class="panel" id="quotes"><div class="card"><h2>Quotes</h2><table><thead><tr><th>Client</th><th>Work</th><th>Total</th><th>Status</th><th></th></tr></thead><tbody id="qRows"></tbody></table></div></section>
<section class="panel" id="invoices" hidden><div class="grid g2"><div class="card"><h2>Invoices</h2><table><thead><tr><th>#</th><th>Client</th><th>Total</th><th>Due</th><th>Status</th></tr></thead><tbody id="iRows"></tbody></table></div>
 <div class="card"><h2>Invoice Preview</h2><div id="preview" class="small muted">Pick an invoice to preview it.</div></div></div></section>
<section class="panel" id="remind" hidden><div class="card"><h2>Reminders Due Today</h2><p class="small muted">Schedule: 3 days before the due date, on the due date, then 7 and 14 days late. You approve each one.</p><div class="list" id="rList"></div></div></section>
<section class="panel" id="aging" hidden><div class="grid g4" id="ageK"></div><div class="card" style="margin-top:14px"><h2>Open Balances</h2><table><thead><tr><th>Client</th><th>Invoice</th><th>Amount</th><th>Days overdue</th></tr></thead><tbody id="aRows"></tbody></table></div></section>
''',
js=r'''
const DEF={sel:null,sentR:[],next:1043,quotes:[
 {id:"Q-212",client:"Harbor Dental",work:"Office deep clean (3,200 sq ft)",total:640,status:"Approved"},
 {id:"Q-213",client:"Lopez Residence",work:"Move-out clean, 3 bed / 2 bath",total:385,status:"Approved"},
 {id:"Q-214",client:"Summit Realty",work:"Weekly office cleaning (4 visits)",total:880,status:"Waiting on client"}],
 inv:[{no:1038,client:"Greenway Apartments",total:1250,issued:-30,due:-16,status:"Sent"},
  {no:1039,client:"Bright Smiles Pediatrics",total:420,issued:-17,due:-3,status:"Sent"},
  {no:1040,client:"Oak Street Cafe",total:275,issued:-11,due:3,status:"Sent"},
  {no:1041,client:"Patel Family",total:190,issued:-20,due:-6,status:"Paid"},
  {no:1042,client:"Northside Gym",total:560,issued:-14,due:0,status:"Sent"}]};
let S=load(DEF);
const day=o=>{const d=new Date();d.setDate(d.getDate()+o);return d.toLocaleDateString("en-US",{month:"short",day:"numeric"})};
function reminders(){const r=[];S.inv.filter(i=>i.status==="Sent").forEach(i=>{const late=-i.due;let kind=null;
 if(i.due===3)kind="Friendly heads-up (due in 3 days)";else if(i.due===0)kind="Due today";else if(late>=7&&late<14)kind="7 days past due";else if(late>=14)kind="14+ days past due";
 if(kind){const id=i.no+"-"+kind;if(!S.sentR.includes(id))r.push({id,i,kind})}});return r}
function msg(r){const b=brand().name,f=r.i.client;return r.kind.startsWith("Friendly")?`Hi ${f}, a quick reminder that invoice #${r.i.no} for ${money(r.i.total)} is due on ${day(r.i.due)}. Pay here: [pay link]. Thank you! — ${b}`:
 r.kind==="Due today"?`Hi ${f}, invoice #${r.i.no} for ${money(r.i.total)} is due today. Pay here: [pay link]. Thanks for your business! — ${b}`:
 `Hi ${f}, invoice #${r.i.no} for ${money(r.i.total)} was due on ${day(r.i.due)}. If it's already on the way, thank you! If not, you can pay here: [pay link], or reply to set up a plan. — ${b}`}
function render(){
 $("#qRows").innerHTML=S.quotes.map((q,i)=>`<tr><td>${esc(q.client)}</td><td>${esc(q.work)}</td><td>${money(q.total)}</td><td><span class="chip ${q.status==="Approved"?"g":q.status==="Invoiced"?"":"a"}">${q.status}</span></td><td>${q.status==="Approved"?`<button class="btn sm" data-conv="${i}" type="button">Create invoice</button>`:""}</td></tr>`).join("");
 $$("[data-conv]").forEach(b=>b.onclick=()=>{const q=S.quotes[b.dataset.conv];q.status="Invoiced";const inv={no:S.next++,client:q.client,total:q.total,issued:0,due:14,status:"Draft",work:q.work};S.inv.unshift(inv);S.sel=inv.no;save();render();toast(`Invoice #${inv.no} drafted from ${q.id}`)});
 $("#iRows").innerHTML=S.inv.map(i=>`<tr data-inv="${i.no}" style="cursor:pointer" class="${S.sel===i.no?"sel":""}"><td>${i.no}</td><td>${esc(i.client)}</td><td>${money(i.total)}</td><td>${day(i.due)}</td><td><span class="chip ${i.status==="Paid"?"g":i.status==="Draft"?"a":i.due<0?"r":""}">${i.status==="Sent"&&i.due<0?"Overdue":i.status}</span></td></tr>`).join("");
 $$("[data-inv]").forEach(t=>t.onclick=()=>{S.sel=Number(t.dataset.inv);render()});
 const s=S.inv.find(i=>i.no===S.sel);
 $("#preview").innerHTML=s?`<div class="out" style="white-space:normal"><div class="row" style="justify-content:space-between"><b data-biz>${esc(brand().name)}</b><b>Invoice #${s.no}</b></div><div class="small">Bill to: ${esc(s.client)}<br>Issued ${day(s.issued)} · Due ${day(s.due)}</div><table style="margin:8px 0"><tr><td>${esc(s.work||"Services")}</td><td style="text-align:right">${money(s.total)}</td></tr><tr><th>Total</th><th style="text-align:right">${money(s.total)}</th></tr></table><div class="small">Pay online: [pay link] · card, PayPal, or bank transfer</div></div>
  <div class="row" style="margin-top:8px">${s.status==="Draft"?`<button class="btn ok" id="sendInv" type="button">Approve &amp; send</button>`:""}${s.status==="Sent"?`<button class="btn alt" id="markPaid" type="button">Mark paid</button>`:""}</div>`:"Pick an invoice to preview it.";
 if($("#sendInv"))$("#sendInv").onclick=()=>{s.status="Sent";save();render();toast(`Invoice #${s.no} sent with a pay link`)};
 if($("#markPaid"))$("#markPaid").onclick=()=>{s.status="Paid";save();render();toast(`#${s.no} marked paid`)};
 const r=reminders();$("#rList").innerHTML=r.length?r.map(x=>`<div><div class="row"><span class="chip a">${x.kind}</span><b>${esc(x.i.client)}</b> · #${x.i.no}</div><textarea class="i" style="min-height:70px;margin-top:6px">${esc(msg(x))}</textarea><div class="row" style="margin-top:6px"><button class="btn ok sm" data-rs="${x.id}" type="button">Approve &amp; send</button><button class="btn alt sm" data-rk="${x.id}" type="button">Skip today</button></div></div>`).join(""):'<p class="muted">No reminders due today.</p>';
 $$("[data-rs]").forEach(b=>b.onclick=()=>{S.sentR.push(b.dataset.rs);save();render();toast("Reminder sent")});
 $$("[data-rk]").forEach(b=>b.onclick=()=>{S.sentR.push(b.dataset.rk);save();render()});
 const open=S.inv.filter(i=>i.status==="Sent"),sum=f=>money(open.filter(f).reduce((a,i)=>a+i.total,0));
 $("#ageK").innerHTML=[["Not yet due",sum(i=>i.due>=0)],["1–30 days late",sum(i=>i.due<0&&i.due>=-30)],["31+ days late",sum(i=>i.due<-30)],["Paid this month",money(S.inv.filter(i=>i.status==="Paid").reduce((a,i)=>a+i.total,0))]].map(k=>`<div class="card kpi"><div class="v">${k[1]}</div><div class="l">${k[0]}</div></div>`).join("");
 $("#aRows").innerHTML=open.sort((a,b)=>a.due-b.due).map(i=>`<tr><td>${esc(i.client)}</td><td>#${i.no}</td><td>${money(i.total)}</td><td>${i.due<0?-i.due:"—"}</td></tr>`).join("")}
''')

# ---------------------------------------------------------------- InsightDesk
P['insight'] = dict(name='InsightDesk', tag='Your key numbers on one page and a plain-English summary every Monday.',
tabs=[('dash','Dashboard'),('summary','Weekly Summary'),('alerts','Alerts'),('impact','Before & After')],
body='''
<section class="panel" id="dash"><div class="row" style="justify-content:space-between;margin-bottom:10px"><b id="wk"></b><button class="btn alt sm" id="nextWk" type="button">Show next week →</button></div>
 <div class="grid g4" id="kp"></div><div class="card" style="margin-top:14px"><h2>Revenue by Week</h2><div id="revChart"></div></div></section>
<section class="panel" id="summary" hidden><div class="card"><h2>Monday Summary</h2><div class="out" id="sumTxt" style="white-space:normal"></div><p class="small muted">Sent every Monday morning by email. The numbers come straight from your tools; people make the decisions.</p></div></section>
<section class="panel" id="alerts" hidden><div class="card"><h2>Needs Attention</h2><div class="list" id="alList"></div></div></section>
<section class="panel" id="impact" hidden><div class="card"><h2>Since the Booking Assistant Launched (Week 5)</h2><table><thead><tr><th>Measure</th><th>Weeks 1–4 average</th><th>Since launch</th><th>Change</th></tr></thead><tbody id="baRows"></tbody></table><p class="small muted">Sample data for illustration.</p></div></section>
''',
js=r'''
const W=[{rev:8200,book:118,leads:31,resp:42,open:6,rating:4.3},{rev:8650,book:121,leads:29,resp:38,open:5,rating:4.3},{rev:7900,book:109,leads:35,resp:47,open:9,rating:4.2},{rev:8400,book:117,leads:30,resp:40,open:7,rating:4.3},
 {rev:9100,book:131,leads:36,resp:9,open:3,rating:4.4},{rev:9550,book:138,leads:38,resp:7,open:2,rating:4.5},{rev:9300,book:134,leads:33,resp:8,open:4,rating:4.5},{rev:9900,book:142,leads:41,resp:6,open:2,rating:4.6},
 {rev:9600,book:139,leads:44,resp:31,open:8,rating:4.5},{rev:10200,book:147,leads:39,resp:7,open:3,rating:4.6}];
const DEF={i:7};let S=load(DEF);
const pct=(a,b)=>Math.round((a-b)/b*100);
function delta(a,b,lowerBetter){const p=pct(a,b),good=lowerBetter?p<0:p>0;return `<span class="d ${p===0?"":good?"up":"down"}">${p>0?"+":""}${p}% vs last week</span>`}
function render(){const c=W[S.i],p=W[S.i-1];$("#wk").textContent=`Week ${S.i+1} of 10 (sample data)`;$("#nextWk").disabled=S.i>=W.length-1;
 $("#kp").innerHTML=[["Revenue",money(c.rev).replace(".00",""),delta(c.rev,p.rev)],["Bookings",c.book,delta(c.book,p.book)],["New leads",c.leads,delta(c.leads,p.leads)],["Avg. first reply",c.resp+" min",delta(c.resp,p.resp,true)]].map(k=>`<div class="card kpi"><div class="l">${k[0]}</div><div class="v">${k[1]}</div>${k[2]}</div>`).join("");
 const shown=W.slice(0,S.i+1),max=Math.max(...W.map(w=>w.rev)),H=180,bw=44;
 $("#revChart").innerHTML=`<svg viewBox="0 0 640 ${H+30}" role="img" aria-label="Revenue by week" style="width:100%;max-width:680px">${shown.map((w,i)=>{const h=w.rev/max*H,x=20+i*(bw+18);return `<rect x="${x}" y="${H-h}" width="${bw}" height="${h}" rx="5" fill="${i===S.i?"var(--brand)":"#b9cde3"}"/><text x="${x+bw/2}" y="${H+18}" text-anchor="middle" font-size="12" fill="#56606c">W${i+1}</text>`}).join("")}</svg>`;
 const b=brand().name,up=c.rev>=p.rev,lines=[`<p><b>Good morning! Here's last week at ${esc(b)}.</b></p>`,
  `<p>Revenue was ${money(c.rev).replace(".00","")}, ${up?"up":"down"} ${Math.abs(pct(c.rev,p.rev))}% from the week before, on ${c.book} bookings.</p>`,
  `<p>You received ${c.leads} new leads and the average first reply took ${c.resp} minutes${c.resp>20?", which is slower than usual":""}.</p>`,
  `<p>${c.open?`${c.open} leads still have no follow-up.`:"Every lead got a follow-up."} Average rating: ${c.rating}★.</p>`,
  `<p><b>One thing to do this week:</b> ${c.resp>20?"check who covers messages during busy hours; replies slowed down.":c.open>4?"follow up with the open leads before Wednesday.":"keep doing what you're doing, and ask this week's customers for reviews."}</p>`];
 $("#sumTxt").innerHTML=lines.join("");
 const al=[];if(c.resp>20)al.push(["Replies slowed down",`Average first reply is ${c.resp} minutes (goal: under 15).`,"r"]);if(c.open>4)al.push(["Leads waiting",`${c.open} leads have no follow-up after 24 hours.`,"a"]);if(c.rev<p.rev)al.push(["Revenue dipped",`Down ${Math.abs(pct(c.rev,p.rev))}% from last week.`,"a"]);
 $("#alList").innerHTML=al.length?al.map(a=>`<div><span class="chip ${a[2]}">${a[0]}</span> ${a[1]}</div>`).join(""):'<p class="muted">Nothing needs attention this week.</p>';
 const avg=(a,k)=>a.reduce((s,w)=>s+w[k],0)/a.length,pre=W.slice(0,4),post=W.slice(4,S.i+1);
 $("#baRows").innerHTML=[["Avg. first reply (min)","resp",true],["Bookings per week","book"],["Revenue per week","rev"],["Average rating","rating"]].map(m=>{const a=avg(pre,m[1]),z=post.length?avg(post,m[1]):a,ch=pct(z,a);const f=v=>m[1]==="rev"?money(Math.round(v)).replace(".00",""):m[1]==="rating"?v.toFixed(2):Math.round(v);return `<tr><td>${m[0]}</td><td>${f(a)}</td><td>${post.length?f(z):"—"}</td><td class="${(m[2]?ch<0:ch>0)?"up":"down"}">${post.length?(ch>0?"+":"")+ch+"%":"—"}</td></tr>`}).join("")}
$("#nextWk").onclick=()=>{if(S.i<W.length-1){S.i++;save();render()}};
''')

from protos_more import MORE, MORE_FILES
P.update(MORE)
ORDER = ['property', 'chat', 'salon', 'resort', 'housekeeping', 'rewards', 'invoice', 'service', 'package', 'social', 'review', 'staff', 'insight', 'intake', 'compliance']
FILES = {'rewards': 'rewards.html', 'review': 'reviews.html', 'social': 'social.html', 'staff': 'staff.html', 'invoice': 'invoices.html', 'insight': 'insights.html', **MORE_FILES}
for k in ORDER:
    p = P[k]
    open(os.path.join(OUT, FILES[k]), 'w', encoding='utf-8').write(shell(k, p['name'], p['tag'], p['tabs'], p['body'], p['js']))

cards = ''.join(f'<a class="card" href="{FILES[k]}" style="text-decoration:none"><h2>{P[k]["name"]}</h2><p class="small">{html.escape(P[k]["tag"])}</p><span class="chip g">Open the prototype →</span></a>' for k in ORDER)
idx = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://formsubmit.co https://script.google.com https://script.googleusercontent.com; frame-src 'self' https://calendly.com; object-src 'none'; base-uri 'self'; form-action 'self' https://formsubmit.co"><meta name="referrer" content="strict-origin-when-cross-origin"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Product Prototypes · Rashad Fambro Consulting</title>
<meta name="description" content="Clickable prototypes of the Desk product suite, with sample data."><link rel="icon" href="../icon.svg"><link rel="canonical" href="https://rashadfambro.github.io/prototypes/">
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet"><style>{CSS}</style></head>
<body><header><div class="logo" style="background:var(--sky);color:var(--ink)">RF</div><div><h1>Product Prototypes</h1><div class="sub">Rashad Fambro Consulting · try each tool with sample data</div></div></header>
<div class="banner"><span>Each prototype uses sample data and sends nothing. Put your own business name in the header to see it branded.</span><span class="sp"></span><a href="../index.html#products">← Back to the website</a></div>
<main><div class="grid g3">{cards}</div>
<div class="card" style="margin-top:14px"><h2>Packages Open as One Product</h2><p class="small">Bundles open in the <a href="suite.html?tools=property,package,chat">Desk Suite</a>: one brand and one menu for every tool in the package.</p></div></main>
<footer>Built by Rashad Fambro Consulting. People stay in control: nothing goes to customers without approval.</footer></body></html>
'''
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(idx)
print('wrote', sorted(os.listdir(OUT)))

# ---------------------------------------------------------------- Desk Suite (a package installs as one product)
import json as _json
NAMES = {k: P[k]['name'] for k in ORDER}
suite_js = "const FILES=" + _json.dumps(FILES) + ";const NAMES=" + _json.dumps(NAMES) + ";" + r"""
const q=new URLSearchParams(location.search),tools=(q.get("tools")||"property,package,chat").split(",").filter(t=>FILES[t]);
function render(){$("#nav").innerHTML=tools.map((t,i)=>`<button type="button" data-tool="${t}" aria-selected="${i===0}">${NAMES[t]}</button>`).join("");
 $$("#nav button").forEach(x=>x.onclick=()=>{$$("#nav button").forEach(y=>y.setAttribute("aria-selected",y===x));$("#app").src=FILES[x.dataset.tool]+"?embed=1";$("#app").title=NAMES[x.dataset.tool]});
 if(!$("#app").getAttribute("src")){$("#app").src=FILES[tools[0]]+"?embed=1";$("#app").title=NAMES[tools[0]]}}
const DEF={};let S={};"""
suite_body = ('<section class="panel" id="suite"><nav class="tabs" id="nav" aria-label="Tools in this package"></nav>'
              '<iframe id="app" title="Desk tool" style="width:100%;height:78vh;border:1px solid var(--line);border-radius:14px;background:#fff"></iframe></section>')
FILES['suite'] = 'suite.html'
_page = shell('suite', 'Desk Suite', 'Every tool in your package in one app, with one brand and one sign-in.', [('suite', 'Your Tools')], suite_body, suite_js)
_page = _page.replace('<nav class="tabs" aria-label="Desk Suite sections"><button type="button" data-tab="suite" aria-selected="true">Your Tools</button></nav>', '')
open(os.path.join(OUT, 'suite.html'), 'w', encoding='utf-8').write(_page)
print('wrote suite.html')
