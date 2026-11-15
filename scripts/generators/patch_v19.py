"""v19: review round (ChatGPT + Google, Nov 14 night). Applied to index.html and staging/index.html.
- Checkout says what the monthly rate becomes after the sale, and shows the Fully Hosted price next to it.
- Estimator shows payback counting staff time AND cash-only payback.
- Trial buttons say "Request a branded trial"; site activity is attached to leads so we can see which product/demo led to an audit.
- Quote-driven businesses get a direct path to LeadDesk.
- Sale banner leads with the founding offer; the rounding note moves to the fine print.
- Packages: simple Client-Owned vs Fully Hosted comparison; billing rules move into an expandable panel.
- Forms: once a request is sent, the copy/email fallback buttons are hidden.
- Hero pipeline: space between step number and text."""
import os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def rep(t, a, b):
    assert t.count(a) == 1, f"{t.count(a)}x: {a[:110]}"
    return t.replace(a, b)

for rel in sys.argv[1:] or ['index.html', 'staging/index.html']:
    p = os.path.join(ROOT, rel); t = open(p).read()

    # hero pipeline spacing
    t = re.sub(r'<li><i>(\d)</i>(?=[^\s<]|<span)', r'<li><i>\1</i> ', t)

    # sale banner: offer first, rounding rule in the fine print
    t = rep(t, '<span class="sale-l2"><small id="saleRound">(sale prices are rounded down to the nearest $10)</small> <a href="#pricing">See prices →</a></span><small class="sale-fine" id="saleFine"></small>',
            '<span class="sale-l2">Founding clients (first 5): 25% off your first setup + your first month free · <a href="#pricing">See prices →</a></span><small class="sale-fine"><span id="saleRound">Sale prices are rounded down to the nearest $10.</span> <span id="saleFine"></span></small>')

    # estimator: two paybacks
    t = rep(t, '<div><b id="roiPayback">1.1 months</b> <small>to pay back the setup</small></div>',
            '<div><b id="roiPayback">1.1 months</b> <small>payback, counting staff time</small></div>\n          <div><b id="roiCashPayback">5.4 months</b> <small>cash-only payback (won-back profit minus tool costs)</small></div>')
    t = rep(t, '  $("#roiCash").textContent=(r.cash<0?"−":"")+money(Math.abs(r.cash))+"/mo";',
            '  $("#roiCash").textContent=(r.cash<0?"−":"")+money(Math.abs(r.cash))+"/mo";\n'
            '  $("#roiCashPayback").textContent = r.cash<=0 ? "No cash payback at these inputs" : (pl.setup/r.cash)<1 ? "Under 1 month" : `${(pl.setup/r.cash).toFixed(1)} months`;')

    # trial button wording
    t = rep(t, 'data-trial="${p.id}">14-day free trial</button>', 'data-trial="${p.id}">Request a branded trial</button>')
    t = rep(t, 'Tap <b>14-day free trial</b> on any product', 'Tap <b>Request a branded trial</b> on any product')

    # checkout: monthly after the sale + hosted alternative
    t = rep(t, '  if(mo) parts.push(`<b>Monthly:</b> ${money2(mo)}/mo, starting the month your tool goes live, plus usage billed by your own providers (usually under $40/mo per tool; Fully Hosted by request)`);',
            '''  if(mo){
    const host = it.tier ? (it.tier==="prop"?150:100)*(it.count||1) : 0;
    const after = f<1 ? ` (holiday rate for months billed through ${saleEndText()}, then ${money2(mo0)}/mo)` : "";
    parts.push(`<b>Monthly:</b> ${money2(mo)}/mo${after}, starting the month your tool goes live, plus usage billed by your own providers (usually under $40/mo per tool)`);
    if(host) parts.push(`<b>Or Fully Hosted:</b> ${money2(mo0+host)}/mo with usage included up to your allowance (by request)`);
  }''')
    t = rep(t, "el.innerHTML=parts.join(\" · \");", "el.innerHTML=parts.join(\"<br>\");")

    # packages: simple comparison, details tucked away
    a = t.find('      <p class="tier-foot"><b>You own the accounts and the data.</b>')
    b = t.find('</p>', a) + 4
    own = t[a:b]
    c = t.find('      <p class="tier-foot">* <b>Fully Hosted (by request):</b>')
    d = t.find('</p>', c) + 4
    hosted = t[c:d]
    assert a > 0 and c > b
    custom_start = t.find('      <p class="tier-foot"><b>Custom work is quoted as a fixed price</b>', b)
    custom_end = t.find('</p>', custom_start) + 4
    custom = t[custom_start:custom_end]
    block = ('      <div class="host-compare">\n'
             '        <div class="hc"><span class="chip live">Most popular</span><h4>Client-Owned</h4><p>Runs in accounts your business owns, so you keep your data. You pay usage (texts, AI, storage) straight to those providers, usually under $40/mo per tool.</p><p class="hc-price">The plan price above</p></div>\n'
             '        <div class="hc"><span class="chip">Done for you</span><h4>Fully Hosted</h4><p>I run everything, with nothing for you to set up or manage. Monthly usage is included up to a generous allowance.</p><p class="hc-price">Plan price + $100/mo per tool (+$150 per property tool)</p></div>\n'
             '      </div>\n'
             + custom + '\n'
             '      <details class="more" id="billingDetails"><summary>View Billing &amp; Hosting Details</summary>\n'
             + own.replace('<p class="tier-foot">', '<p class="tier-foot" style="margin-top:10px">') + '\n'
             + hosted.replace('<p class="tier-foot">* ', '<p class="tier-foot">') + '\n'
             '      </details>')
    t = t[:a] + block + t[d:]
    t = t.replace(custom + '\n' + block, block) if (custom + '\n' + block) in t else t
    # remove the original custom paragraph if it is still in its old place (between own and hosted)
    first = t.find(custom); second = t.find(custom, first + 1)
    if second > 0:
        t = t[:first] + t[first + len(custom) + 1:]
    t = rep(t, '.salebar .sale-l2 a{white-space:nowrap}',
            '.salebar .sale-l2 a{white-space:nowrap}.host-compare{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:18px 0 10px}'
            '.hc{border:1px solid var(--line);border-radius:14px;padding:16px;background:#fff}.hc h4{font-size:1.05rem;margin:8px 0 4px}.hc p{font-size:.9rem;color:var(--muted);margin:0 0 6px}'
            '.hc .hc-price{color:var(--ink);font-weight:700;margin:0}@media(max-width:640px){.host-compare{grid-template-columns:minmax(0,1fr)}}')

    # LeadDesk path for quote-driven businesses
    t = rep(t, '<p class="eyebrow" style="margin-top:6px">Featured · operations, customer questions, and bookings</p>',
            '<p class="hint" style="margin:0 0 14px">Quote-driven business, like contractors or cleaning services? <a href="#products" data-goto="service">Start with LeadDesk →</a> Appointment-based? <a href="#products" data-goto="salon">Start with BookDesk →</a></p>\n'
            '    <p class="eyebrow" style="margin-top:6px">Featured · operations, customer questions, and bookings</p>')
    t = rep(t, 'const prodCard = p=>`\n  <article class="prod${p.wide?" wide":""}">', 'const prodCard = p=>`\n  <article class="prod${p.wide?" wide":""}" id="p-${p.id}">')

    # site activity on leads (which product or demo led to the request)
    t = rep(t, '/* ---------- monthly plan cards ---------- */',
            '''function noteInterest(label){ try{ const k="rf-interest", a=JSON.parse(sessionStorage.getItem(k)||"[]"); if(a[a.length-1]!==label){ a.push(label); sessionStorage.setItem(k, JSON.stringify(a.slice(-8))); } }catch(e){} }
function interestTrail(){ try{ return JSON.parse(sessionStorage.getItem("rf-interest")||"[]").join(" → "); }catch(e){ return ""; } }
document.addEventListener("click", e=>{
  const g=e.target.closest("[data-goto]");
  if(g){ e.preventDefault(); const card=document.getElementById("p-"+g.dataset.goto), more=$("#moreProducts"); if(card && more && more.contains(card)) more.open=true; if(card){ card.scrollIntoView({behavior:"smooth", block:"center"}); card.classList.add("pulse"); setTimeout(()=>card.classList.remove("pulse"),1600); } noteInterest("path:"+g.dataset.goto); return; }
  const x=e.target.closest("[data-open-demo],[data-proto-link],.protolink,[data-buy],[data-trial]");
  if(!x) return;
  const id=x.dataset.openDemo||x.dataset.protoLink||x.dataset.buy||x.dataset.trial||(x.getAttribute("href")||"").replace(/^.*\\//,"");
  noteInterest((x.dataset.buy?"order:":x.dataset.trial?"trial:":"demo:")+id);
}, true);
/* ---------- monthly plan cards ---------- */''')
    t = rep(t, 'async function sendLead(form, data) {\n', 'async function sendLead(form, data) {\n  if (data && typeof data === "object" && !data["Site activity"] && interestTrail()) data["Site activity"] = interestTrail();\n')
    t = rep(t, '.prod .eta{', '.prod.pulse{box-shadow:0 0 0 3px var(--sky)}.prod .eta{')

    # forms: after a successful send, hide the fallback copy buttons
    t = rep(t, '$("#auditMail").hidden=true; }', '$("#auditMail").hidden=true; $("#auditCopy").hidden=true; }')
    t = rep(t, '$("#auditMail").hidden=false; }', '$("#auditMail").hidden=false; $("#auditCopy").hidden=false; }')
    t = rep(t, '$("#bMail").hidden=true; }', '$("#bMail").hidden=true; $("#bCopy").hidden=true; }')
    t = rep(t, '$("#bMail").hidden=false; }', '$("#bMail").hidden=false; $("#bCopy").hidden=false; }')

    open(p, 'w').write(t)
    print('v19 applied to', rel)

# pilot-request summary (live site before the Starter edition): same after-sale and hosted wording
for rel in sys.argv[1:] or ['index.html', 'staging/index.html']:
    p = os.path.join(ROOT, rel); t = open(p).read()
    a = '${m2?` + ${money2(m2)}/mo`:""}, plus usage billed by your own providers (usually under $40/mo per tool). Fully Hosted is available by request.`;'
    if a in t:
        t = t.replace(a, '${m2?` + ${money2(m2)}/mo`:""}${m2&&f2<1?` (holiday rate for months billed through ${saleEndText()}, then ${money2(m0)}/mo)`:""}, plus usage billed by your own providers (usually under $40/mo per tool).${m2&&it2.tier?`<br><b>Or Fully Hosted:</b> ${money2(m0+(it2.tier==="prop"?150:100)*(it2.count||1))}/mo with usage included up to your allowance (by request).`:" Fully Hosted is available by request."}`;')
        open(p, 'w').write(t)
        print('v19 pilot summary applied to', rel)
