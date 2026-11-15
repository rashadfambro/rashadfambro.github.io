"""Standalone prototype apps for the nine tools that previously only had a Demo Lab simulation.
Imported by gen_prototypes.py. Same shell, sample data only, nothing is sent."""

MORE = {}
MORE_FILES = {'chat': 'chat.html', 'property': 'workorders.html', 'resort': 'guests.html', 'salon': 'bookings.html',
              'housekeeping': 'housekeeping.html', 'package': 'packages.html', 'service': 'leads.html',
              'intake': 'intake.html', 'compliance': 'compliance.html'}

KPI_JS = r'''function kpis(sel,arr){$(sel).innerHTML=arr.map(k=>`<div class="card kpi"><div class="v">${k[1]}</div><div class="l">${k[0]}</div></div>`).join("")}
function approvals(sel,list,onOk,onEdit){$(sel).innerHTML=list.length?list.map(x=>`<div><div class="row"><span class="chip a">${esc(x.tag)}</span><b>${esc(x.to)}</b></div><textarea class="i" data-ed="${x.id}" style="min-height:60px;margin-top:6px">${esc(x.text)}</textarea><div class="row" style="margin-top:6px"><button class="btn ok sm" data-ap="${x.id}" type="button">Approve &amp; send</button><button class="btn alt sm" data-sk="${x.id}" type="button">Skip</button></div></div>`).join(""):'<p class="muted">Nothing waiting for approval.</p>';
 $$(sel+" [data-ap]").forEach(b=>b.onclick=()=>onOk(b.dataset.ap,$(`[data-ed="${b.dataset.ap}"]`).value,true));
 $$(sel+" [data-sk]").forEach(b=>b.onclick=()=>onOk(b.dataset.sk,"",false))}
'''

# ------------------------------------------------------------------ ChatDesk
MORE['chat'] = dict(name='ChatDesk', tag='Answers customer questions 24/7 from your own answers, and hands anything else to your team.',
tabs=[('try', 'Try the Chat'), ('answers', 'Your Answers'), ('handoffs', 'Handoffs to Approve'), ('results', 'Results')],
body='''
<section class="panel" id="try"><div class="grid g2">
 <div class="card"><h2>Customer View</h2><div id="log" class="list" style="max-height:340px;overflow:auto"></div>
  <form class="row" id="ask" style="margin-top:10px"><input class="i" id="q" placeholder="Ask a question, e.g. What are your hours?" style="flex:1" aria-label="Question"><button class="btn" type="submit">Send</button></form></div>
 <div class="card"><h2>How It Works</h2><p class="small">ChatDesk answers only from the answers you approve on the <b>Your Answers</b> tab. If it isn't sure, it says so, collects contact details, and sends the question to your team.</p><p class="small muted">Try: "hours", "parking", "price", or something it doesn't know.</p></div>
</div></section>
<section class="panel" id="answers" hidden><div class="card"><h2>Your Answers</h2><table><thead><tr><th>Question</th><th>Answer</th><th>Keywords</th><th></th></tr></thead><tbody id="faqRows"></tbody></table>
 <div class="grid g3" style="margin-top:12px"><div><label class="f" for="nq">Question</label><input class="i" id="nq"></div><div><label class="f" for="na">Answer</label><input class="i" id="na"></div><div><label class="f" for="nk">Keywords (comma separated)</label><input class="i" id="nk"></div></div>
 <div class="row" style="margin-top:8px"><button class="btn" id="addFaq" type="button">Add answer</button></div></div></section>
<section class="panel" id="handoffs" hidden><div class="card"><h2>Questions for Your Team</h2><p class="small muted">Write or edit the reply, then approve it. Nothing goes out without approval.</p><div class="list" id="hoList"></div></div></section>
<section class="panel" id="results" hidden><div class="grid g4" id="kp"></div></section>
''',
js=KPI_JS + r'''
const DEF={faq:[{q:"What are your hours?",a:"We're open Monday to Saturday, 9 AM to 6 PM.",k:"hours,open,close,time"},
 {q:"Is there parking?",a:"Yes, free parking is available behind the building.",k:"parking,park,car"},
 {q:"How much does it cost?",a:"Prices start at $45. We'll confirm your exact price before booking.",k:"price,cost,how much,rate"}],
 log:[],ho:[{id:"h1",to:"Jordan (jordan@example.com)",tag:"Unanswered question",q:"Do you take walk-ins on Sundays?",text:"Hi Jordan, thanks for asking! "}],asked:6,auto:4,sent:0};
let S=load(DEF);
function match(q){const t=q.toLowerCase();let best=null,score=0;S.faq.forEach(f=>{const s=f.k.split(",").filter(k=>k.trim()&&t.includes(k.trim().toLowerCase())).length;if(s>score){score=s;best=f}});return best}
function render(){$("#log").innerHTML=S.log.length?S.log.map(m=>`<div><b>${m.who==="bot"?esc(brand().name):"Customer"}:</b> ${esc(m.t)}</div>`).join(""):'<p class="muted small">Say hello to start.</p>';
 $("#faqRows").innerHTML=S.faq.map((f,i)=>`<tr><td>${esc(f.q)}</td><td>${esc(f.a)}</td><td class="small">${esc(f.k)}</td><td><button class="btn alt sm" data-del="${i}" type="button">Remove</button></td></tr>`).join("");
 $$("[data-del]").forEach(b=>b.onclick=()=>{S.faq.splice(+b.dataset.del,1);save();render()});
 approvals("#hoList",S.ho.map(h=>({...h,text:h.text,tag:h.tag+": "+h.q})),(id,txt,ok)=>{S.ho=S.ho.filter(h=>h.id!==id);if(ok)S.sent++;save();render();toast(ok?"Reply sent":"Skipped")});
 kpis("#kp",[["Questions asked",S.asked],["Answered automatically",S.asked?Math.round(S.auto/S.asked*100)+"%":"0%"],["Waiting for your team",S.ho.length],["Team replies sent",S.sent]])}
$("#ask").onsubmit=e=>{e.preventDefault();const q=$("#q").value.trim();if(!q)return;S.log.push({who:"c",t:q});S.asked++;const f=match(q);
 if(f){S.auto++;S.log.push({who:"bot",t:f.a})}else{S.log.push({who:"bot",t:"Good question. I'm not sure, so I've passed it to the team and they'll reply soon."});S.ho.push({id:"h"+Date.now(),to:"Website visitor",tag:"Unanswered question",q,text:"Thanks for your question! "})}
 $("#q").value="";save();render()};
$("#addFaq").onclick=()=>{const q=$("#nq").value.trim(),a=$("#na").value.trim(),k=$("#nk").value.trim();if(!q||!a){toast("Add a question and an answer");return}S.faq.push({q,a,k:k||q.toLowerCase()});["#nq","#na","#nk"].forEach(s=>$(s).value="");save();render();toast("Answer added")};
''')

# ------------------------------------------------------------------ WorkOrderDesk
MORE['property'] = dict(name='WorkOrderDesk', tag='Maintenance requests in one queue: sorted, prioritized, assigned, and residents kept updated.',
tabs=[('new', 'New Request'), ('orders', 'Work Orders'), ('approve', 'Updates to Approve'), ('results', 'Results')],
body='''
<section class="panel" id="new"><div class="grid g2"><div class="card"><h2>Resident Request</h2>
 <label class="f" for="unit">Unit</label><input class="i" id="unit" value="214">
 <label class="f" for="res">Resident</label><input class="i" id="res" value="Dana Lee">
 <label class="f" for="desc">What's wrong?</label><textarea class="i" id="desc">Water is leaking under the kitchen sink and the cabinet floor is wet.</textarea>
 <div class="row" style="margin-top:8px"><button class="btn" id="submit" type="button">Submit request</button></div></div>
 <div class="card"><h2>Automatic Triage</h2><div id="triage" class="out">Submit a request to see the category, priority, and drafted reply.</div></div></div></section>
<section class="panel" id="orders" hidden><div class="card"><h2>Work Orders</h2><table><thead><tr><th>#</th><th>Unit</th><th>Issue</th><th>Priority</th><th>Tech</th><th>Status</th><th></th></tr></thead><tbody id="rows"></tbody></table></div></section>
<section class="panel" id="approve" hidden><div class="card"><h2>Resident Updates Waiting for Approval</h2><div class="list" id="apList"></div></div></section>
<section class="panel" id="results" hidden><div class="grid g4" id="kp"></div></section>
''',
js=KPI_JS + r'''
const CATS=[["Plumbing","leak,water,sink,toilet,drain,pipe,faucet"],["Electrical","power,outlet,light,breaker,electric"],["HVAC","heat,ac,air,hot,cold,thermostat"],["Appliance","fridge,oven,stove,dishwasher,washer,dryer"],["Pest","bug,roach,mouse,ants,pest"],["General","door,lock,window,wall,paint"]];
const URG="flood,fire,smoke,gas,no heat,sparking,burst,sewage";
const TECHS=["Marcus","Priya","Sam"];
const DEF={n:104,orders:[{id:101,unit:"118",res:"Ken Ortiz",issue:"Bedroom outlet not working",cat:"Electrical",pri:"Normal",tech:"Priya",status:"In progress",hrs:20},
 {id:102,unit:"305",res:"Amy Chu",issue:"AC blowing warm air",cat:"HVAC",pri:"High",tech:"Marcus",status:"Assigned",hrs:6},
 {id:103,unit:"122",res:"Luis Vega",issue:"Dishwasher won't drain",cat:"Appliance",pri:"Normal",tech:"",status:"New",hrs:2}],ap:[],sent:0,closed:7};
let S=load(DEF);
function triage(t){t=t.toLowerCase();const c=(CATS.find(c=>c[1].split(",").some(k=>t.includes(k)))||["General"])[0];const pri=URG.split(",").some(k=>t.includes(k))?"Emergency":/leak|wet|no |not working|broken/.test(t)?"High":"Normal";return {c,pri}}
function render(){$("#rows").innerHTML=S.orders.map(o=>`<tr><td>${o.id}</td><td>${esc(o.unit)}</td><td>${esc(o.issue)}<div class="small muted">${esc(o.res)} · ${o.cat}</div></td><td><span class="chip ${o.pri==="Emergency"?"r":o.pri==="High"?"a":""}">${o.pri}</span></td>
 <td><select class="i" data-tech="${o.id}" aria-label="Technician"><option value="">Unassigned</option>${TECHS.map(t=>`<option ${o.tech===t?"selected":""}>${t}</option>`).join("")}</select></td><td>${o.status}</td>
 <td>${o.status==="Closed"?"":`<button class="btn sm" data-close="${o.id}" type="button">Close</button>`}</td></tr>`).join("");
 $$("[data-tech]").forEach(s=>s.onchange=()=>{const o=S.orders.find(x=>x.id==s.dataset.tech);o.tech=s.value;if(o.status==="New")o.status="Assigned";S.ap.push({id:"a"+Date.now(),to:`${o.res}, unit ${o.unit}`,tag:"Assigned",text:`Hi ${o.res.split(" ")[0]}, ${o.tech} from ${brand().name} maintenance will handle your ${o.cat.toLowerCase()} request (#${o.id}).`});save();render();toast("Assigned. Resident update drafted")});
 $$("[data-close]").forEach(b=>b.onclick=()=>{const o=S.orders.find(x=>x.id==b.dataset.close);o.status="Closed";S.closed++;S.ap.push({id:"c"+Date.now(),to:`${o.res}, unit ${o.unit}`,tag:"Closed",text:`Hi ${o.res.split(" ")[0]}, your request #${o.id} is complete. Reply here if anything still isn't right.`});save();render();toast("Closed. Resident update drafted")});
 approvals("#apList",S.ap,(id,txt,ok)=>{S.ap=S.ap.filter(a=>a.id!==id);if(ok)S.sent++;save();render();toast(ok?"Update sent":"Skipped")});
 const open=S.orders.filter(o=>o.status!=="Closed");kpis("#kp",[["Open work orders",open.length],["Emergencies open",open.filter(o=>o.pri==="Emergency").length],["Closed this month",S.closed],["Resident updates sent",S.sent]])}
$("#submit").onclick=()=>{const d=$("#desc").value.trim();if(!d){toast("Describe the issue");return}const t=triage(d),o={id:S.n++,unit:$("#unit").value,res:$("#res").value,issue:d.slice(0,60),cat:t.c,pri:t.pri,tech:"",status:"New",hrs:0};S.orders.unshift(o);
 const reply=`Hi ${o.res.split(" ")[0]}, we received your ${t.c.toLowerCase()} request for unit ${o.unit} (#${o.id}). ${t.pri==="Emergency"?"This is marked urgent and a technician is being dispatched now.":"We'll schedule a technician and confirm a time."}`;
 S.ap.push({id:"n"+o.id,to:`${o.res}, unit ${o.unit}`,tag:"Received",text:reply});
 $("#triage").innerHTML=`<b>Category:</b> ${t.c}\n<b>Priority:</b> ${t.pri}\n<b>Drafted reply (waiting for approval):</b>\n${esc(reply)}`;save();render();toast(`Work order #${o.id} created`)};
''')

# ------------------------------------------------------------------ GuestDesk
MORE['resort'] = dict(name='GuestDesk', tag='Guest and owner requests routed to the right department, with replies your staff approve.',
tabs=[('inbox', 'Requests'), ('depts', 'Departments'), ('results', 'Results')],
body='''
<section class="panel" id="inbox"><div class="grid g2"><div class="card"><h2>New Guest Message</h2>
 <label class="f" for="room">Room</label><input class="i" id="room" value="1208"><label class="f" for="gname">Guest</label><input class="i" id="gname" value="Ms. Patel">
 <label class="f" for="msg">Message</label><textarea class="i" id="msg">Could we get two extra towels and a late checkout tomorrow?</textarea>
 <div class="row" style="margin-top:8px"><button class="btn" id="route" type="button">Route request</button></div></div>
 <div class="card"><h2>Replies Waiting for Approval</h2><div class="list" id="apList"></div></div></div></section>
<section class="panel" id="depts" hidden><div class="grid g3" id="board"></div></section>
<section class="panel" id="results" hidden><div class="grid g4" id="kp"></div></section>
''',
js=KPI_JS + r'''
const D=[["Housekeeping","towel,clean,sheets,pillow,linen,amenities"],["Front Desk","checkout,check-in,late,key,bill,invoice"],["Maintenance","broken,leak,ac,heat,tv,light,shower"],["Concierge","dinner,restaurant,tour,taxi,ticket,spa"],["Owner Services","owner,week,points,reservation,timeshare"]];
const DEF={req:[{id:1,room:"904",g:"Mr. Kim",t:"TV remote not working",d:["Maintenance"],done:false},{id:2,room:"1502",g:"Owner: Rivera",t:"Change my owner week to March",d:["Owner Services"],done:false}],ap:[],sent:0,done:5};
let S=load(DEF);
function route(t){t=t.toLowerCase();const r=D.filter(d=>d[1].split(",").some(k=>t.includes(k))).map(d=>d[0]);return r.length?r:["Front Desk"]}
function render(){$("#board").innerHTML=D.map(d=>{const items=S.req.filter(r=>!r.done&&r.d.includes(d[0]));return `<div class="card"><h3>${d[0]} <span class="chip">${items.length}</span></h3><div class="list">${items.map(r=>`<div class="small"><b>Room ${esc(r.room)}</b> · ${esc(r.g)}<br>${esc(r.t)}<div class="row" style="margin-top:4px"><button class="btn sm" data-done="${r.id}" type="button">Mark done</button></div></div>`).join("")||'<p class="muted small">Nothing open.</p>'}</div></div>`}).join("");
 $$("[data-done]").forEach(b=>b.onclick=()=>{const r=S.req.find(x=>x.id==b.dataset.done);r.done=true;S.done++;save();render();toast("Done")});
 approvals("#apList",S.ap,(id,txt,ok)=>{S.ap=S.ap.filter(a=>a.id!==id);if(ok)S.sent++;save();render();toast(ok?"Reply sent":"Skipped")});
 kpis("#kp",[["Open requests",S.req.filter(r=>!r.done).length],["Completed",S.done],["Replies sent",S.sent],["Departments",D.length]])}
$("#route").onclick=()=>{const t=$("#msg").value.trim();if(!t)return;const d=route(t),r={id:Date.now(),room:$("#room").value,g:$("#gname").value,t,d,done:false};S.req.unshift(r);
 S.ap.push({id:"g"+r.id,to:`${r.g}, room ${r.room}`,tag:d.join(" + "),text:`Hello ${r.g}, thank you for your message. I've shared your request with our ${d.join(" and ").toLowerCase()} team at ${brand().name} and we'll confirm shortly.`});save();render();toast("Routed to "+d.join(" + "))};
''')

# ------------------------------------------------------------------ BookDesk
MORE['salon'] = dict(name='BookDesk', tag='Online booking, reminders you approve, and a waitlist that fills cancellations.',
tabs=[('book', 'Book'), ('schedule', 'Schedule'), ('remind', 'Reminders to Approve'), ('results', 'Results')],
body='''
<section class="panel" id="book"><div class="grid g2"><div class="card"><h2>Customer Booking Page</h2>
 <label class="f" for="cname">Name</label><input class="i" id="cname" value="Jasmine">
 <label class="f" for="svc">Service</label><select class="i" id="svc"></select>
 <label class="f" for="stf">With</label><select class="i" id="stf"></select>
 <p class="f">Open times today</p><div class="row" id="slots"></div></div>
 <div class="card"><h2>Waitlist</h2><div class="list" id="wl"></div><div class="row" style="margin-top:8px"><input class="i" id="wname" placeholder="Name" style="flex:1" aria-label="Waitlist name"><button class="btn alt" id="addW" type="button">Add to waitlist</button></div></div></div></section>
<section class="panel" id="schedule" hidden><div class="card"><h2>Today</h2><table><thead><tr><th>Time</th><th>Customer</th><th>Service</th><th>With</th><th></th></tr></thead><tbody id="rows"></tbody></table></div></section>
<section class="panel" id="remind" hidden><div class="card"><h2>Reminders and Offers Waiting for Approval</h2><div class="list" id="apList"></div></div></section>
<section class="panel" id="results" hidden><div class="grid g4" id="kp"></div></section>
''',
js=KPI_JS + r'''
const SV=[["Haircut",45],["Color",120],["Beard trim",25]],ST=["Alex","Bri"],TIMES=["9:00","10:00","11:00","1:00","2:00","3:00","4:00"];
const DEF={b:[{t:"10:00",c:"Mike",s:"Haircut",w:"Alex"},{t:"2:00",c:"Sofia",s:"Color",w:"Bri"}],wl:["Tasha"],ap:[],sent:0,filled:0};
let S=load(DEF);
function render(){$("#svc").innerHTML=SV.map(s=>`<option>${s[0]}</option>`).join("");$("#stf").innerHTML=ST.map(s=>`<option>${s}</option>`).join("");slots();
 $("#wl").innerHTML=S.wl.length?S.wl.map(w=>`<div class="small">${esc(w)}</div>`).join(""):'<p class="muted small">Nobody waiting.</p>';
 $("#rows").innerHTML=TIMES.map(t=>S.b.filter(b=>b.t===t).map(b=>`<tr><td>${t}</td><td>${esc(b.c)}</td><td>${b.s}</td><td>${b.w}</td><td><button class="btn alt sm" data-cx="${t}|${b.w}" type="button">Cancel</button></td></tr>`).join("")).join("")||'<tr><td colspan="5" class="muted">No bookings yet.</td></tr>';
 $$("[data-cx]").forEach(x=>x.onclick=()=>{const [t,w]=x.dataset.cx.split("|");const b=S.b.find(y=>y.t===t&&y.w===w);S.b=S.b.filter(y=>y!==b);
  if(S.wl.length){const n=S.wl[0];S.ap.push({id:"w"+Date.now(),to:n,tag:"Waitlist offer",text:`Hi ${n}, a ${t} spot just opened with ${w} at ${brand().name}. Reply YES to book it.`,fill:{t,c:n,s:b.s,w}});toast("Cancelled. Offer drafted for "+n)}else toast("Cancelled");save();render()});
 approvals("#apList",S.ap,(id,txt,ok)=>{const a=S.ap.find(x=>x.id===id);S.ap=S.ap.filter(x=>x.id!==id);if(ok){S.sent++;if(a.fill){S.b.push(a.fill);S.wl.shift();S.filled++}}save();render();toast(ok?"Sent":"Skipped")});
 kpis("#kp",[["Bookings today",S.b.length],["Cancellations filled",S.filled],["Messages sent",S.sent],["On waitlist",S.wl.length]])}
function slots(){const w=$("#stf").value;$("#slots").innerHTML=TIMES.map(t=>{const taken=S.b.some(b=>b.t===t&&b.w===w);return `<button class="btn ${taken?"alt":""} sm" type="button" ${taken?"disabled":""} data-slot="${t}">${t}</button>`}).join("");
 $$("[data-slot]").forEach(b=>b.onclick=()=>{const c=$("#cname").value.trim()||"Guest",bk={t:b.dataset.slot,c,s:$("#svc").value,w:$("#stf").value};S.b.push(bk);
  S.ap.push({id:"r"+Date.now(),to:c,tag:"Reminder for tomorrow",text:`Hi ${c}, see you at ${bk.t} for your ${bk.s.toLowerCase()} with ${bk.w} at ${brand().name}. Reply C to change.`});save();render();toast(`Booked ${bk.t} with ${bk.w}`)})}
$("#stf").onchange=slots;$("#addW").onclick=()=>{const n=$("#wname").value.trim();if(n){S.wl.push(n);$("#wname").value="";save();render()}};
''')

# ------------------------------------------------------------------ HousekeepingDesk
MORE['housekeeping'] = dict(name='HousekeepingDesk', tag='Room status at a glance, fair assignments, and inspections before rooms go back on sale.',
tabs=[('board', 'Room Board'), ('assign', 'Assignments'), ('results', 'Results')],
body='''
<section class="panel" id="board"><div class="card"><h2>Rooms</h2><p class="small muted">Click a room to move it to the next step: Dirty → Cleaning → Inspect → Ready.</p><div class="grid g4" id="rooms"></div></div></section>
<section class="panel" id="assign" hidden><div class="card"><h2>Today's Assignments</h2><div class="row"><button class="btn" id="auto" type="button">Assign dirty rooms evenly</button></div><div class="grid g3" id="att" style="margin-top:12px"></div></div></section>
<section class="panel" id="results" hidden><div class="grid g4" id="kp"></div></section>
''',
js=KPI_JS + r'''
const STEPS=["Dirty","Cleaning","Inspect","Ready"],CH={Dirty:"r",Cleaning:"a",Inspect:"",Ready:"g"},AT=["Rosa","Kim","Ade"];
const DEF={rooms:[101,102,103,104,105,106,201,202,203,204,205,206].map((n,i)=>({n,st:STEPS[i%4],who:""})),done:0};
let S=load(DEF);
function render(){$("#rooms").innerHTML=S.rooms.map(r=>`<button class="card" style="text-align:left;cursor:pointer" data-room="${r.n}" type="button"><b>Room ${r.n}</b><br><span class="chip ${CH[r.st]}">${r.st}</span><div class="small muted">${r.who||"Unassigned"}</div></button>`).join("");
 $$("[data-room]").forEach(b=>b.onclick=()=>{const r=S.rooms.find(x=>x.n==b.dataset.room);const i=STEPS.indexOf(r.st);r.st=STEPS[(i+1)%4];if(r.st==="Ready")S.done++;if(r.st==="Dirty")r.who="";save();render();toast(`Room ${r.n}: ${r.st}`)});
 $("#att").innerHTML=AT.map(a=>{const mine=S.rooms.filter(r=>r.who===a&&r.st!=="Ready");return `<div class="card"><h3>${a} <span class="chip">${mine.length}</span></h3><div class="small">${mine.map(r=>`Room ${r.n} (${r.st})`).join("<br>")||'<span class="muted">No rooms</span>'}</div></div>`}).join("");
 kpis("#kp",[["Ready to sell",S.rooms.filter(r=>r.st==="Ready").length],["Dirty",S.rooms.filter(r=>r.st==="Dirty").length],["Waiting inspection",S.rooms.filter(r=>r.st==="Inspect").length],["Turned today",S.done]])}
$("#auto").onclick=()=>{let i=0;S.rooms.filter(r=>r.st==="Dirty"&&!r.who).forEach(r=>{const load=AT.map(a=>S.rooms.filter(x=>x.who===a&&x.st!=="Ready").length);r.who=AT[load.indexOf(Math.min(...load))];i++});save();render();toast(i?`Assigned ${i} rooms`:"No unassigned dirty rooms")};
''')

# ------------------------------------------------------------------ PackageDesk
MORE['package'] = dict(name='PackageDesk', tag='Log packages in seconds, text residents a pickup code, and track what is still waiting.',
tabs=[('log', 'Log a Package'), ('waiting', 'Waiting for Pickup'), ('approve', 'Texts to Approve'), ('results', 'Results')],
body='''
<section class="panel" id="log"><div class="grid g2"><div class="card"><h2>New Package</h2>
 <label class="f" for="res">Resident</label><select class="i" id="res"></select>
 <label class="f" for="car">Carrier</label><select class="i" id="car"><option>UPS</option><option>FedEx</option><option>USPS</option><option>Amazon</option><option>DHL</option></select>
 <label class="f" for="sz">Size</label><select class="i" id="sz"><option>Small</option><option>Medium</option><option>Large</option><option>Cold storage</option></select>
 <div class="row" style="margin-top:8px"><button class="btn" id="add" type="button">Log package</button></div></div>
 <div class="card"><h2>Pickup</h2><label class="f" for="code">Pickup code</label><div class="row"><input class="i" id="code" placeholder="e.g. 4821" style="flex:1"><button class="btn ok" id="pick" type="button">Release package</button></div><div id="pickOut" class="small" style="margin-top:8px"></div></div></div></section>
<section class="panel" id="waiting" hidden><div class="card"><h2>Waiting for Pickup</h2><table><thead><tr><th>Code</th><th>Resident</th><th>Carrier</th><th>Size</th><th>Days</th></tr></thead><tbody id="rows"></tbody></table></div></section>
<section class="panel" id="approve" hidden><div class="card"><h2>Resident Texts Waiting for Approval</h2><div class="list" id="apList"></div></div></section>
<section class="panel" id="results" hidden><div class="grid g4" id="kp"></div></section>
''',
js=KPI_JS + r'''
const RES=["Dana Lee · 214","Ken Ortiz · 118","Amy Chu · 305","Luis Vega · 122"];
const DEF={p:[{code:"3107",r:RES[1],car:"Amazon",sz:"Medium",d:4},{code:"5592",r:RES[2],car:"UPS",sz:"Small",d:1}],ap:[],sent:0,out:12};
let S=load(DEF);
function render(){$("#res").innerHTML=RES.map(r=>`<option>${r}</option>`).join("");
 $("#rows").innerHTML=S.p.map(p=>`<tr><td><b>${p.code}</b></td><td>${esc(p.r)}</td><td>${p.car}</td><td>${p.sz}</td><td>${p.d>=3?`<span class="chip a">${p.d}</span>`:p.d}</td></tr>`).join("")||'<tr><td colspan="5" class="muted">Nothing waiting.</td></tr>';
 approvals("#apList",S.ap,(id,txt,ok)=>{S.ap=S.ap.filter(a=>a.id!==id);if(ok)S.sent++;save();render();toast(ok?"Text sent":"Skipped")});
 kpis("#kp",[["Waiting",S.p.length],["Waiting 3+ days",S.p.filter(p=>p.d>=3).length],["Picked up",S.out],["Texts sent",S.sent]])}
$("#add").onclick=()=>{let code;do{code=String(1000+Math.floor(Math.random()*9000))}while(S.p.some(p=>p.code===code));const p={code,r:$("#res").value,car:$("#car").value,sz:$("#sz").value,d:0};S.p.unshift(p);
 S.ap.push({id:"p"+code,to:p.r,tag:"Package arrived",text:`Hi ${p.r.split(" ")[0]}, a ${p.car} package (${p.sz.toLowerCase()}) is ready at the ${brand().name} office. Pickup code: ${code}.`});save();render();toast("Logged. Pickup code "+code)};
$("#pick").onclick=()=>{const c=$("#code").value.trim(),p=S.p.find(x=>x.code===c);if(!p){$("#pickOut").innerHTML='<span class="chip r">Code not found</span>';return}S.p=S.p.filter(x=>x!==p);S.out++;$("#pickOut").innerHTML=`<span class="chip g">Released</span> to ${esc(p.r)}`;$("#code").value="";save();render()};
''')

# ------------------------------------------------------------------ LeadDesk
MORE['service'] = dict(name='LeadDesk', tag='Every inquiry from your connected channels in one place, with fast first replies and follow-ups you approve.',
tabs=[('inbox', 'New Inquiries'), ('pipeline', 'Pipeline'), ('approve', 'Replies to Approve'), ('results', 'Results')],
body='''
<section class="panel" id="inbox"><div class="grid g2"><div class="card"><h2>New Inquiry</h2>
 <label class="f" for="nm">Name</label><input class="i" id="nm" value="Carla">
 <label class="f" for="src">Came from</label><select class="i" id="src"><option>Website form</option><option>Google</option><option>Facebook</option><option>Phone (missed call)</option><option>Text</option></select>
 <label class="f" for="need">What they need</label><textarea class="i" id="need">Need a quote to repaint two bedrooms next month.</textarea>
 <div class="row" style="margin-top:8px"><button class="btn" id="add" type="button">Add inquiry</button></div></div>
 <div class="card"><h2>How It Works</h2><p class="small">Each inquiry gets a drafted first reply within minutes. You approve it, then LeadDesk reminds you to follow up on day 2, 5 and 10 until the job is booked or closed.</p></div></div></section>
<section class="panel" id="pipeline" hidden><div class="grid g4" id="board"></div></section>
<section class="panel" id="approve" hidden><div class="card"><h2>Replies and Follow-Ups Waiting for Approval</h2><div class="list" id="apList"></div></div></section>
<section class="panel" id="results" hidden><div class="grid g4" id="kp"></div></section>
''',
js=KPI_JS + r'''
const STG=["New","Contacted","Quoted","Booked"];
const DEF={l:[{id:1,n:"Ray",src:"Google",need:"Fence repair estimate",st:"Quoted"},{id:2,n:"Mina",src:"Website form",need:"Kitchen backsplash install",st:"Contacted"}],ap:[],sent:0,lost:1};
let S=load(DEF);
function render(){$("#board").innerHTML=STG.map(s=>`<div class="card"><h3>${s} <span class="chip">${S.l.filter(l=>l.st===s).length}</span></h3><div class="list">${S.l.filter(l=>l.st===s).map(l=>`<div class="small"><b>${esc(l.n)}</b> · ${l.src}<br>${esc(l.need)}<div class="row" style="margin-top:4px">${s!=="Booked"?`<button class="btn sm" data-mv="${l.id}" type="button">Move to ${STG[STG.indexOf(s)+1]}</button>`:""}${s!=="Booked"?`<button class="btn alt sm" data-fu="${l.id}" type="button">Draft follow-up</button>`:""}</div></div>`).join("")||'<p class="muted small">None.</p>'}</div></div>`).join("");
 $$("[data-mv]").forEach(b=>b.onclick=()=>{const l=S.l.find(x=>x.id==b.dataset.mv);l.st=STG[STG.indexOf(l.st)+1];save();render();toast(`${l.n}: ${l.st}`)});
 $$("[data-fu]").forEach(b=>b.onclick=()=>{const l=S.l.find(x=>x.id==b.dataset.fu);S.ap.push({id:"f"+Date.now(),to:l.n,tag:"Follow-up",text:`Hi ${l.n}, just checking in on your ${l.need.toLowerCase()}. Would you like to pick a time this week? – ${brand().name}`});save();render();toast("Follow-up drafted")});
 approvals("#apList",S.ap,(id,txt,ok)=>{S.ap=S.ap.filter(a=>a.id!==id);if(ok){S.sent++;const l=S.l.find(x=>"n"+x.id===id);if(l&&l.st==="New")l.st="Contacted"}save();render();toast(ok?"Sent":"Skipped")});
 const tot=S.l.length+S.lost;kpis("#kp",[["Open inquiries",S.l.filter(l=>l.st!=="Booked").length],["Booked",S.l.filter(l=>l.st==="Booked").length],["Win rate",tot?Math.round(S.l.filter(l=>l.st==="Booked").length/tot*100)+"%":"0%"],["Replies sent",S.sent]])}
$("#add").onclick=()=>{const l={id:Date.now(),n:$("#nm").value.trim()||"New lead",src:$("#src").value,need:$("#need").value.trim(),st:"New"};S.l.unshift(l);
 S.ap.push({id:"n"+l.id,to:`${l.n} (${l.src})`,tag:"First reply",text:`Hi ${l.n}, thanks for reaching out to ${brand().name}! Happy to help with: ${l.need} When's a good time for a quick call?`});save();render();toast("Inquiry added. First reply drafted")};
''')

# ------------------------------------------------------------------ IntakeDesk
MORE['intake'] = dict(name='IntakeDesk', tag='Secure intake forms that collect everything up front and flag what is missing.',
tabs=[('builder', 'Form Builder'), ('client', 'Client View'), ('subs', 'Submissions'), ('results', 'Results')],
body='''
<section class="panel" id="builder"><div class="card"><h2>Your Intake Form</h2><table><thead><tr><th>Field</th><th>Required</th><th></th></tr></thead><tbody id="fields"></tbody></table>
 <div class="row" style="margin-top:10px"><input class="i" id="nf" placeholder="New field, e.g. Insurance provider" style="flex:1" aria-label="New field"><label class="small"><input type="checkbox" id="nr" checked> Required</label><button class="btn" id="addF" type="button">Add field</button></div></div></section>
<section class="panel" id="client" hidden><div class="card"><h2>New Client Form · <span data-biz>Your Business</span></h2><form id="cf"></form><div class="row" style="margin-top:8px"><button class="btn" id="submit" type="button">Submit</button></div><p class="small muted">Sample data only. In a real setup, files and answers save to your own secure storage.</p></div></section>
<section class="panel" id="subs" hidden><div class="card"><h2>Submissions</h2><div class="list" id="subList"></div></div><div class="card" style="margin-top:14px"><h2>Requests Waiting for Approval</h2><div class="list" id="apList"></div></div></section>
<section class="panel" id="results" hidden><div class="grid g4" id="kp"></div></section>
''',
js=KPI_JS + r'''
const DEF={f:[{n:"Full name",r:true},{n:"Email",r:true},{n:"Phone",r:true},{n:"Reason for visit",r:true},{n:"Photo ID uploaded",r:true}],subs:[{id:1,who:"Grace Ford",vals:{"Full name":"Grace Ford","Email":"grace@example.com","Phone":"","Reason for visit":"New client consult","Photo ID uploaded":""}}],ap:[],sent:0};
let S=load(DEF);
const missing=s=>S.f.filter(f=>f.r&&!String(s.vals[f.n]||"").trim()).map(f=>f.n);
function render(){$("#fields").innerHTML=S.f.map((f,i)=>`<tr><td>${esc(f.n)}</td><td>${f.r?"Yes":"No"}</td><td><button class="btn alt sm" data-rm="${i}" type="button">Remove</button></td></tr>`).join("");
 $$("[data-rm]").forEach(b=>b.onclick=()=>{S.f.splice(+b.dataset.rm,1);save();render()});
 $("#cf").innerHTML=S.f.map((f,i)=>`<label class="f" for="cf${i}">${esc(f.n)}${f.r?" *":""}</label><input class="i" id="cf${i}" data-fn="${esc(f.n)}">`).join("");
 $("#subList").innerHTML=S.subs.map(s=>{const m=missing(s);return `<div><b>${esc(s.who)}</b> ${m.length?`<span class="chip r">Missing: ${esc(m.join(", "))}</span> <button class="btn sm" data-req="${s.id}" type="button">Draft request</button>`:'<span class="chip g">Complete</span>'}</div>`}).join("")||'<p class="muted">No submissions yet.</p>';
 $$("[data-req]").forEach(b=>b.onclick=()=>{const s=S.subs.find(x=>x.id==b.dataset.req);S.ap.push({id:"q"+Date.now(),to:s.who,tag:"Missing items",text:`Hi ${s.who.split(" ")[0]}, thanks for completing your intake with ${brand().name}. We still need: ${missing(s).join(", ")}. You can add them using the same secure link.`});save();render();toast("Request drafted")});
 approvals("#apList",S.ap,(id,txt,ok)=>{S.ap=S.ap.filter(a=>a.id!==id);if(ok)S.sent++;save();render();toast(ok?"Sent":"Skipped")});
 const done=S.subs.filter(s=>!missing(s).length).length;kpis("#kp",[["Submissions",S.subs.length],["Complete",done],["Missing items",S.subs.length-done],["Requests sent",S.sent]])}
$("#addF").onclick=()=>{const n=$("#nf").value.trim();if(!n)return;S.f.push({n,r:$("#nr").checked});$("#nf").value="";save();render();toast("Field added")};
$("#submit").onclick=()=>{const vals={};$$("#cf [data-fn]").forEach(i=>vals[i.dataset.fn]=i.value);const s={id:Date.now(),who:vals["Full name"]||"New client",vals};S.subs.unshift(s);save();render();const m=missing(s);toast(m.length?`Submitted. Missing: ${m.length}`:"Submitted. Complete")};
''')

# ------------------------------------------------------------------ ComplianceDesk
MORE['compliance'] = dict(name='ComplianceDesk', tag='Recurring checklists, deadlines with reminders, and a log you can show an inspector.',
tabs=[('today', "Today's Checklist"), ('deadlines', 'Deadlines'), ('log', 'Audit Log'), ('results', 'Results')],
body='''
<section class="panel" id="today"><div class="card"><h2>Today's Checklist</h2><label class="f" for="ini">Your initials</label><input class="i" id="ini" value="RF" style="max-width:120px"><div class="list" id="tasks" style="margin-top:10px"></div></div></section>
<section class="panel" id="deadlines" hidden><div class="card"><h2>Upcoming Deadlines</h2><table><thead><tr><th>Item</th><th>Due in</th><th></th></tr></thead><tbody id="dl"></tbody></table>
 <div class="row" style="margin-top:10px"><input class="i" id="dn" placeholder="e.g. Fire extinguisher inspection" style="flex:1" aria-label="Deadline"><input class="i" id="dd" type="number" min="1" value="30" style="width:90px" aria-label="Days until due"><button class="btn" id="addD" type="button">Add</button></div></div></section>
<section class="panel" id="log" hidden><div class="card"><h2>Audit Log</h2><table><thead><tr><th>When</th><th>Item</th><th>By</th></tr></thead><tbody id="lg"></tbody></table></div></section>
<section class="panel" id="results" hidden><div class="grid g4" id="kp"></div></section>
''',
js=KPI_JS + r'''
const DEF={t:[{n:"Check ID for every age-restricted sale",done:false},{n:"Post required notices at the counter",done:false},{n:"Log refrigerator temperatures",done:false},{n:"Confirm unit inspection files are complete",done:false}],
 d:[{n:"Annual unit inspections (HUD)",days:12},{n:"Business license renewal",days:45},{n:"Staff ID-check training refresher",days:5}],log:[]};
let S=load(DEF);
function render(){$("#tasks").innerHTML=S.t.map((t,i)=>`<div class="row"><label style="flex:1"><input type="checkbox" data-t="${i}" ${t.done?"checked disabled":""}> ${esc(t.n)}</label>${t.done?`<span class="chip g">Done · ${esc(t.by)}</span>`:""}</div>`).join("");
 $$("[data-t]").forEach(c=>c.onchange=()=>{const t=S.t[+c.dataset.t],by=$("#ini").value.trim()||"—";t.done=true;t.by=by;S.log.unshift({w:new Date().toLocaleString(),n:t.n,by});save();render();toast("Logged")});
 $("#dl").innerHTML=[...S.d].sort((a,b)=>a.days-b.days).map(d=>`<tr><td>${esc(d.n)}</td><td><span class="chip ${d.days<=7?"r":d.days<=30?"a":"g"}">${d.days} days</span></td><td><button class="btn sm" data-dd="${esc(d.n)}" type="button">Mark done</button></td></tr>`).join("");
 $$("[data-dd]").forEach(b=>b.onclick=()=>{S.d=S.d.filter(x=>x.n!==b.dataset.dd);S.log.unshift({w:new Date().toLocaleString(),n:b.dataset.dd,by:$("#ini").value||"—"});save();render();toast("Deadline completed and logged")});
 $("#lg").innerHTML=S.log.map(l=>`<tr><td class="small">${esc(l.w)}</td><td>${esc(l.n)}</td><td>${esc(l.by)}</td></tr>`).join("")||'<tr><td colspan="3" class="muted">Nothing logged yet.</td></tr>';
 kpis("#kp",[["Today's tasks done",`${S.t.filter(t=>t.done).length}/${S.t.length}`],["Due within 7 days",S.d.filter(d=>d.days<=7).length],["Upcoming deadlines",S.d.length],["Log entries",S.log.length]])}
$("#addD").onclick=()=>{const n=$("#dn").value.trim();if(!n)return;S.d.push({n,days:Math.max(1,+$("#dd").value||30)});$("#dn").value="";save();render();toast("Deadline added")};
''')
