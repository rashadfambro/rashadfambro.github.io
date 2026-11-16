"""v24: feedback from Google and Codex reviews (Nov 15-16, 2026)."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else "index.html"
s = open(p, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:70])
    s = s.replace(a, b)

# 1. Founding "filled" text is no longer in the static page; JS writes it only when 0 spots are left
rep('<p class="founding-full" id="foundingFull" hidden>All 5 founding client spots are filled. Thank you to our first clients! The holiday and seasonal offers below still apply.</p>',
    '<p class="founding-full" id="foundingFull" hidden></p>')
rep('const full=!left; $("#founding").hidden=full; $("#foundingFull").hidden=!full;',
    'const full=!left; $("#founding").hidden=full; $("#foundingFull").hidden=!full; $("#foundingFull").textContent = full ? `All ${CONFIG.foundingSpots} founding client spots are filled. Thank you to our first clients! The holiday and seasonal offers below still apply.` : "";')

# 2. Regular monthly prices stated plainly in Section 09 (built from CONFIG)
rep('<div class="tier-grid" id="tierGrid"></div>',
    '<p class="tier-base" id="tierBase"></p>\n      <div class="tier-grid" id="tierGrid"></div>')
rep('$("#tierGrid").innerHTML = CONFIG.tiers.std.map(',
    '$("#tierBase").innerHTML = `<b>Regular monthly prices:</b> standard tools ${CONFIG.tiers.std.map(t=>"$"+t.price).join(" / ")} per tool; property &amp; hospitality tools ${CONFIG.tiers.prop.map(t=>"$"+t.price).join(" / ")} per property (Essentials / Growth / Pro); any 3 standard tools on Essentials $120/mo.${saleActive()?` Holiday rates below apply for your first 12 months when you order by ${saleEndText()}.`:""}`;\n$("#tierGrid").innerHTML = CONFIG.tiers.std.map(')
rep('.salebar .sale-l2 small{font-size:.8em}', '.salebar .sale-l2 small{font-size:.8em}.tier-base{margin:0 0 14px;font-size:.95rem}')

# 3. Clear confirmation toasts on every send, plus framing for Section 10
rep('if(sent){ $("#auditResult h4").textContent="Thanks — your request was received";',
    'toast(sent ? "Audit request sent. I’ll reply within one business day." : "Almost done: send the email draft below to finish your request");\n  if(sent){ $("#auditResult h4").textContent="Thanks — your request was received";')
rep('if(sent){ $("#bResult h4").textContent="Thanks — your request was received";',
    'toast(sent ? "Proposal request sent. I’ll reply within one business day." : "Almost done: send the email draft below to finish your request");\n  if(sent){ $("#bResult h4").textContent="Thanks — your request was received";')
rep('r.innerHTML=`<h4>Order received — thank you!</h4>',
    'toast("Order received. Nothing has been charged yet.");\n    r.innerHTML=`<h4>Order received — thank you!</h4>')
rep('$("#buyGo").disabled=true; const sent=await sendLead("trial", req); $("#buyGo").disabled=false; r.hidden=false;',
    '$("#buyGo").disabled=true; const sent=await sendLead("trial", req); $("#buyGo").disabled=false; r.hidden=false; toast(sent ? "Trial request sent. Your link arrives within one business day." : "Almost done: send the email draft below");')
rep('<p class="lede">Answer four quick questions. I’ll reply within one business day with next steps, a proposal, and an agreement you can sign electronically.</p>',
    '<p class="lede">For when you’re ready for a quote. Answer four quick questions and I’ll reply within one business day with a fixed-price proposal and an agreement you can sign electronically. Not sure yet? <a href="#audit">Start with the free audit</a>.</p>')

# 4. Trial copy: no payment details, no automatic charges
rep('Free for 14 days, no payment details needed. Within one business day',
    '<b>No payment details required. No automatic charges.</b> Within one business day')
rep("On day 14, choose a plan or let it expire; nothing is charged automatically.</p>",
    "On day 14 the trial simply expires unless you choose a paid plan.</p>")
rep('trial ? `Free for ${CONFIG.trialDays} days, then ${buyPriceText(it)}`',
    'trial ? `Free for ${CONFIG.trialDays} days. If you choose a paid plan: ${buyPriceText(it)}`', 2)

# 5. Bundle savings: say what it is compared against, on the card itself
rep('sv.title="Compared with buying each tool separately at today\'s holiday prices"; }',
    'sv.title="Compared with buying each tool separately at today\'s holiday prices"; const b=sv.nextSibling; if(b&&b.nodeType===3) b.textContent=b.textContent.replace("at regular prices)","at holiday prices)"); }')
s = s.replace(' vs. buying each tool separately). ', ' vs. buying each tool separately at regular prices). ')
open(p, "w", encoding="utf-8").write(s)
print("v24 applied")
