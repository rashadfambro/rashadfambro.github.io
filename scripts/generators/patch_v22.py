"""v22 (Nov 15, 2026): demo lab covers every message-based tool plus links to all 15 full apps; demos use the
visitor's business name; founding offer is replaced by a "spots filled" note at zero; holiday monthly rate is
locked for 12 months for sale orders; client-implementation checkmark; tool apps accept ?brand=&color=&logo=
for pitch previews and open full screen from the home screen.  Run from the repo root on index.html (root)."""
import re, sys

p = sys.argv[1] if len(sys.argv) > 1 else "index.html"
s = open(p, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    assert s.count(old) >= 1, old[:80]
    s = s.replace(old, new, count)

# 1. Checkmark
rep('<li class="hp-lead">', '<li class="hp-lead">', 1)
rep('<li>Any industry</li>', '<li>Any industry</li><li>Client implementations &amp; support</li>')

# 2. Founding: show a "filled" note at zero
rep('    <div class="founding" id="founding">',
    '    <p class="founding-full" id="foundingFull" hidden>All 5 founding client spots are filled. Thank you to our first clients! The holiday and seasonal offers below still apply.</p>\n    <div class="founding" id="founding">')
rep("  if(!left){ $(\"#founding\").hidden=true; $$(\".sale-l2\").forEach(x=>x.hidden=true); }",
    "  const full=!left; $(\"#founding\").hidden=full; $(\"#foundingFull\").hidden=!full;\n"
    "  $$(\".sale-l2\").forEach(x=>{ if(full){ x.innerHTML='Founding client spots: all 5 filled. Thank you! <a href=\"#pricing\">See prices &rarr;</a>'; } });\n"
    "  const bf=$(\"#b_found\"); if(bf){ const lab=bf.closest(\"label\"); if(lab) lab.hidden=full; if(full) bf.checked=false; }")
rep(".founding p{color:#c3cfdd}", ".founding p{color:#c3cfdd}.founding-full{margin:18px 0 0;padding:12px 16px;border:1px dashed var(--line);border-radius:12px;background:#fff;font-weight:600;text-align:center}")

# 3. Holiday monthly rate: locked for the first 12 months for anyone who orders during the sale
rep("(holiday rate for months billed through ${saleEndText()}, then ${money2(m0)}/mo)",
    "(holiday rate locked for your first 12 months when you order by ${saleEndText()}, then ${money2(m0)}/mo)")
rep("(holiday rate for months billed through ${saleEndText()}, then ${money2(mo0)}/mo)",
    "(holiday rate locked for your first 12 months when you order by ${saleEndText()}, then ${money2(mo0)}/mo)")
rep("% or more off all listed products and services through ${saleEndText()}`;",
    "% or more off all listed products and services through ${saleEndText()}. Monthly plans keep the holiday rate for 12 months`;")

# 4. Demo lab: business name, more tools, links to every full app
rep('''          <span class="chip soon">Simulation</span>
        </div>''', '''          <span class="chip soon">Simulation</span>
        </div>
        <label class="lab-biz" for="labBiz">Your business name <input id="labBiz" type="text" maxlength="60" placeholder="e.g. Glow Studio" autocomplete="organization"></label>''')
rep('''        <p class="status" id="labStatus" role="status">''', '''        <p class="hint lab-full" id="labFull"></p>
        <p class="status" id="labStatus" role="status">''')
rep(".lab-actions{", ".lab-biz{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:.85rem;font-weight:700;margin:0 0 10px}.lab-biz input{flex:1;min-width:180px;max-width:320px;padding:7px 10px;border:1px solid var(--line);border-radius:8px;font:inherit}.lab-full{margin:10px 0 0}.lab-all{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px}.lab-all a{font-size:.8rem;font-weight:700;padding:5px 10px;border:1px solid var(--line);border-radius:999px;text-decoration:none;color:var(--ink);background:#fff}.lab-actions{")

NEW_DEMOS = r'''  chat:{sector:"Any business with a website", title:"ChatDesk", label:"Website chat", short:"Customer questions",
    samples:["Hi, are you open on Sunday and do you take walk-ins?","How much is a basic oil change and how long does it take?","Do you offer payment plans? I'm interested but want to know the options first."],
    cats:[["Hours & location",/open|hours|close|sunday|saturday|holiday|where are you|address|parking/i,"Website assistant · approved answer"],["Pricing",/how much|price|cost|rate|quote|payment plan|financ/i,"Website assistant · price list"],["Booking",/book|appointment|walk.?in|availability|schedule/i,"Website assistant · booking link"],["Needs a person",/complain|refund|problem|manager|speak to|lawyer|medical/i,"Owner / front desk"]],
    def:["General question","Front desk"],
    urgent:/today|now|asap|urgent|tonight/i,
    reply:(d)=>`Thanks for asking! ${d.cat==="Pricing"?"Here are our current prices from the approved price list:":d.cat==="Hours & location"?"Here are our hours and how to find us:":d.cat==="Booking"?"You can grab the next open time here:":"I'm passing this to a team member, who will reply shortly."} [approved answer inserted]`,
    checks:(d)=>["Answers come only from the approved answer list", d.cat==="Needs a person"?"A person replies; nothing is promised automatically":"Keep prices and hours current in the answer list", "Unanswered questions become a lead for follow-up"]},
  review:{sector:"Reviews & reputation", title:"ReviewDesk", label:"Reviews", short:"Review replies",
    samples:["5 stars. Fast, friendly and they explained everything. Ask for Jordan!","2 stars. Waited 40 minutes past my appointment and nobody said sorry.","4 stars. Great work, a little pricey, but I'll be back."],
    cats:[["Low rating (1-2 stars)",/\b[12] stars?|waited|rude|never|worst|disappointed|nobody/i,"Owner · personal reply first"],["Mixed (3-4 stars)",/\b[34] stars?|but|pricey|a little/i,"Manager · thank and address"],["Top rating (5 stars)",/\b5 stars?|great|amazing|love|best|friendly/i,"Drafted thank-you"]],
    def:["Review","Manager"],
    urgent:/\b[12] stars?|rude|refund|never again|worst/i,
    reply:(d)=>d.cat.startsWith("Low")?"Thank you for telling us, and I'm sorry about the wait. That's not the experience we want for you. I'd like to make it right; please reach me directly at [phone or email].":d.cat.startsWith("Mixed")?"Thank you for the kind words and the honest feedback! We appreciate you, and we'll see you next time.":`Thank you so much! We'll pass your kind words along${d.staff?" to "+d.staff:""}. See you next time!`,
    checks:(d)=>["The owner approves every public reply", d.cat.startsWith("Low")?"Reach out privately before replying publicly":"Never offer discounts in exchange for reviews", "Every customer gets the same review invitation, happy or not"]},
  social:{sector:"Social media", title:"SocialDesk", label:"Social & DMs", short:"DM replies",
    samples:["PRICE - how much for a full set?","Do you have any openings this Saturday? DM me","DEMO please, saw your post about the booking tool"],
    cats:[["Keyword: PRICE",/\bprice\b|how much|cost/i,"Auto-reply with price list link"],["Keyword: DEMO / TRIAL",/\bdemo\b|\btrial\b/i,"Auto-reply with demo link"],["Booking request",/opening|available|book|appointment|saturday|sunday|today|tomorrow/i,"Booking link + staff follow-up"]],
    def:["General DM","Owner inbox"],
    urgent:/today|tonight|asap/i,
    reply:(d)=>d.cat.startsWith("Keyword: PRICE")?"Thanks for reaching out! Here's our current price list: [link]. Want me to save you a spot?":d.cat.startsWith("Keyword: DEMO")?"Thanks! Here's a 2-minute demo and a free trial link: [link]. Any questions, just reply here.":"We'd love to see you! Here are the next open times: [booking link]. Reply with the one that works.",
    checks:()=>["The owner approves each new reply template","Keyword replies use approved wording only","Booking requests also land in the lead list"]},
  staff:{sector:"Team & HR", title:"StaffDesk", label:"Staff questions", short:"Handbook & shifts",
    samples:["Can I swap my Saturday shift with Jess? I have a family thing.","How many sick days do I get per year?","I'll be 20 minutes late tomorrow, car trouble."],
    cats:[["Shift swap",/swap|switch|cover|trade|shift/i,"Manager approval"],["Policy question",/sick|vacation|pto|policy|handbook|dress code|break/i,"Handbook answer"],["Late / absence",/late|absent|can't make|sick today|call out/i,"Manager · schedule update"]],
    def:["Staff question","Manager"],
    urgent:/today|tomorrow|tonight|late/i,
    reply:(d)=>d.cat==="Shift swap"?"Got it. I've sent your swap request to your manager. You'll get a confirmation once it's approved.":d.cat==="Policy question"?"From the employee handbook: [approved policy text]. Questions? Your manager can help.":"Thanks for the heads-up. Your manager has been notified and the schedule is updated.",
    checks:()=>["Answers come only from your handbook","Managers approve every swap","No personal or medical details are stored"]},
  rewards:{sector:"Loyalty & repeat visits", title:"RewardsDesk", label:"Rewards", short:"Points & offers",
    samples:["How many points do I have? My number is 555-201-3344.","Can I use my free drink reward today?","I keep forgetting my punch card, can it be on my phone?"],
    cats:[["Points balance",/points|balance|how many/i,"Rewards lookup"],["Redeem reward",/use my|redeem|free|reward/i,"Front counter · verify"],["Sign up",/punch card|sign up|join|phone/i,"Rewards signup"]],
    def:["Rewards question","Front counter"],
    urgent:/today|now/i,
    reply:(d)=>d.cat==="Points balance"?"You have [points] points: 2 more visits until your next reward!":d.cat==="Redeem reward"?"Yes! Show this text at the counter and we'll apply your reward.":"Good news: your rewards live on your phone number now. No card needed. You're signed up!",
    checks:()=>["Staff verifies the phone number before applying a reward","Customers opt in to texts","Offers follow your reward rules"]},
  invoice:{sector:"Invoices & payments", title:"InvoiceDesk", label:"Invoices", short:"Payment questions",
    samples:["Can I pay invoice 1042 next Friday instead?","I already paid by card yesterday, why did I get a reminder?","Can you resend the invoice? I can't find it."],
    cats:[["Payment extension",/next (?:week|friday|month)|instead|extension|later|split/i,"Owner approval"],["Already paid",/already paid|paid yesterday|paid by/i,"Bookkeeping · match payment"],["Resend invoice",/resend|can't find|copy|send again/i,"Auto-resend"]],
    def:["Billing question","Bookkeeping"],
    urgent:/today|overdue|final notice/i,
    reply:(d)=>d.cat==="Payment extension"?"Thanks for letting us know. I've asked the owner to confirm the new date and will reply shortly.":d.cat==="Already paid"?"Thank you! We're matching your payment now, and you'll get a receipt once it's confirmed. Sorry for the extra reminder.":"Here's a fresh link to your invoice: [secure link].",
    checks:()=>["The owner approves any change to due dates","Payments are matched before reminders stop","Card numbers are never typed into messages"]},
'''
rep("\n};\nlet demoKey=", ",\n" + NEW_DEMOS.rstrip().rstrip(",") + "\n};\nlet demoKey=")

# business name: used in drafts and in the full-app link; links to every app
APPS = [("property","workorders","WorkOrderDesk"),("chat","chat","ChatDesk"),("salon","bookings","BookDesk"),("resort","guests","GuestDesk"),("housekeeping","housekeeping","HousekeepingDesk"),
        ("rewards","rewards","RewardsDesk"),("invoice","invoices","InvoiceDesk"),("service","leads","LeadDesk"),("package","packages","PackageDesk"),("social","social","SocialDesk"),
        ("review","reviews","ReviewDesk"),("staff","staff","StaffDesk"),("insight","insights","InsightDesk"),("intake","intake","IntakeDesk"),("compliance","compliance","ComplianceDesk")]
app_js = "const LAB_APPS=" + "{" + ",".join(f'{k}:["{f}","{n}"]' for k, f, n in APPS) + "};\n"
rep("function setDemo(k){\n", app_js + '''function labBiz(){ const v=($("#labBiz")&&$("#labBiz").value||"").trim().slice(0,60); return v; }
function appLink(k){ const a=LAB_APPS[k]; if(!a) return ""; const b=labBiz(); return `prototypes/${a[0]}.html${b?`?brand=${encodeURIComponent(b)}`:""}`; }
function labFull(){ const a=LAB_APPS[demoKey]; $("#labFull").innerHTML = (a?`<a href="${appLink(demoKey)}">Open the full ${esc(a[1])} app${labBiz()?" for "+esc(labBiz()):""} &rarr;</a>`:"") +
  `<span class="lab-all" aria-label="Every tool as a full app"><b style="font-size:.8rem;align-self:center">All 15 tools as full apps:</b>${Object.keys(LAB_APPS).map(k=>`<a href="${appLink(k)}">${esc(LAB_APPS[k][1])}</a>`).join("")}</span>`; }
try{ const saved=localStorage.getItem("lab-biz"); if(saved && $("#labBiz")) $("#labBiz").value=saved; }catch(_){}
$("#labBiz").addEventListener("input",()=>{ try{ localStorage.setItem("lab-biz", labBiz()); }catch(_){} labFull(); if(demoState!=="idle") $("#labRun").click(); });
function setDemo(k){
''')
rep("  resetDemo();\n}\n$(\"#labPick\").addEventListener", "  resetDemo(); labFull();\n}\n$(\"#labPick\").addEventListener")
rep('  $("#labDraft").textContent="Draft reply\\n\\n"+reply;',
    '  const biz=labBiz(); if(biz){ reply=reply.replace(/\\bour office\\b/g, biz).replace(/\\bwe’d love\\b/i,"We’d love"); reply += `\\n\\n— ${biz}`; }\n  $("#labDraft").textContent="Draft reply"+(biz?" from "+biz:"")+"\\n\\n"+reply;')

rep('<small>0${i+1} · ${esc(d.label)}</small>', '<small>${String(i+1).padStart(2,"0")} · ${esc(d.label)}</small>')
open(p, "w", encoding="utf-8").write(s)
print("v22 applied to", p)
