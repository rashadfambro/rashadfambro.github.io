"""v25 (Nov 16, 2026): test environment, About and stat wording, Title Case, tier lines, estimator number entry and all tools."""
import re, sys
p = sys.argv[1] if len(sys.argv) > 1 else "index.html"
s = open(p, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:80])
    s = s.replace(a, b)
SMALL = {"a","an","the","and","but","or","for","nor","on","at","to","by","of","in","with","as","vs","per","via","from"}
def tc(t):
    return re.sub(r"[A-Za-z][\w’'-]*", lambda m: m.group(0) if (m.start() > 0 and m.group(0).lower() in SMALL) else m.group(0)[0].upper() + m.group(0)[1:], t)

# --- Test environment: everything that is not the live site sends env:"staging" (TEST tabs, emails only to Rashad)
rep('async function sendLead(form, data) {',
    'const SITE_ENV = (location.hostname === "rashadfambro.github.io" && !/^\\/staging\\//.test(location.pathname)) ? "production" : "staging";\n'
    'if (SITE_ENV === "staging") document.addEventListener("DOMContentLoaded", () => { const b = document.createElement("div"); b.id = "envBadge"; b.textContent = "Test environment · test data only · emails go to Rashad"; document.body.appendChild(b); });\n'
    'async function sendLead(form, data) {')
rep('const payload = Object.assign({ type: "lead", form, source: LEAD_SRC.source, page: LEAD_SRC.page }, data);',
    'const payload = Object.assign({ type: "lead", env: SITE_ENV, form, source: LEAD_SRC.source, page: LEAD_SRC.page }, data);')
rep('fetch(CONFIG.backendUrl+"?stats=founding"', 'fetch(CONFIG.backendUrl+"?stats=founding&env="+((location.hostname==="rashadfambro.github.io"&&!/^\\/staging\\//.test(location.pathname))?"production":"staging")')
rep('.tier-base{margin:0 0 14px;font-size:.95rem}',
    '.tier-base{margin:0 0 14px;font-size:.95rem}#envBadge{position:fixed;left:10px;bottom:10px;z-index:60;background:#b42318;color:#fff;font:700 .72rem/1.3 var(--sans);padding:5px 9px;border-radius:8px;pointer-events:none;opacity:.92}.tier-foot .tl{display:block;margin-top:6px}.roi-num{width:92px;margin-left:auto;padding:4px 8px;border:1px solid var(--line);border-radius:8px;font:inherit;font-weight:700}.field label .roi-num{margin-top:0}')
# chat request
n = s.count('body: JSON.stringify({ type: "chat"')
if n: s = s.replace('body: JSON.stringify({ type: "chat"', 'body: JSON.stringify({ env: SITE_ENV, type: "chat"')

# --- Stats and About
rep('<p>Clients supported across 5 products</p>', '<p>Clients supported across multiple products and industries</p>')
rep('<p>Faster regression cycles delivered as a QA Director</p>', '<p>Faster software testing cycles, with fewer production issues</p>')
rep('the software products and solutions that solve them — across healthcare, finance, restaurants, retail, and defense. Most recently, as a Director of Quality Assurance, I led 50+ engineers supporting 80+ client organizations. Today I bring',
    'the software products and solutions that solve them across multiple industries, including: healthcare, finance &amp; payments, restaurants, retail store operations, in-store media, and defense communications. Most recently, as a Director of Quality Assurance, I led 50+ engineers supporting 80+ client organizations, with teams across 4 countries. Today, as an IT Software Consultant, I bring')
rep('<p class="co">Retail media, restaurant technology, defense &amp; retail software</p>',
    '<p class="co">In-store media, restaurant technology, defense communications &amp; retail store software</p>')
rep('Led global test automation for retail media,', 'Led global test automation for in-store media,')
rep('<span>Retail &amp; retail media</span>', '<span>Retail Store Operations</span><span>In-Store Media</span>')
rep('<span>Healthcare technology</span><span>Finance &amp; payments</span><span>Restaurant POS</span>', '<span>Healthcare Technology</span><span>Finance &amp; Payments</span><span>Restaurant POS</span>')
rep('<span>Defense communications</span></div>', '<span>Defense Communications</span></div>')
rep('with experience in healthcare, finance, restaurants, retail and defense.', 'with experience across multiple industries, including healthcare, finance and payments, restaurants, retail store operations, in-store media and defense communications.')

# --- Title Case
for a in ['02</span> About me', '05</span> Demo lab', '06</span> Savings estimator', '07</span> Free workflow audit', '08</span> How we work together', '10</span> Start a project', '12</span> Get in touch']:
    num, txt = a.split('</span> '); rep(a, num + '</span> ' + tc(txt))
for a in ['Featured · operations, customer questions, and bookings', 'Workflow customizations · Examples', 'Also serving · choose your industry',
          '<legend>Monthly plan</legend>', '<legend>How would you like to pay?</legend>', '<legend>Payment method</legend>',
          '<h4>Your trial is on its way!</h4>', '<h4>Order received — thank you!</h4>']:
    rep(a, tc(a))
rep('<h4>One last step: press Send</h4>', '<h4>One Last Step: Press Send</h4>', 2)
s = re.sub(r'sector:"([^"]*)"', lambda m: 'sector:"' + tc(m.group(1)) + '"', s)
s = re.sub(r'(<p class="eyebrow"[^>]*>)(Standard tools|Property &amp; hospitality tools)(</p>)', lambda m: m.group(1) + tc(m.group(2)) + m.group(3), s)

# --- Plans section: standard and property tools on their own lines
rep('<p class="tier-foot">Standard tools: <abbr', '<p class="tier-foot"><span class="tl"><b>Standard Tools:</b> <abbr')
rep('<abbr title="owner dashboard and weekly summary">InsightDesk</abbr>. Property &amp; hospitality tools (priced per property): <abbr',
    '<abbr title="owner dashboard and weekly summary">InsightDesk</abbr>.</span><span class="tl"><b>Property &amp; Hospitality Tools</b> (priced per property): <abbr')
rep('<abbr title="recurring checklists and deadlines">ComplianceDesk</abbr>. <b>Small Business Suite:</b> any 3 standard tools on Essentials for $120/mo.</p>',
    '<abbr title="recurring checklists and deadlines">ComplianceDesk</abbr>.</span><span class="tl"><b>Small Business Suite:</b> any 3 standard tools on Essentials for $120/mo.</span></p>')
rep('`<b>Regular monthly prices:</b> standard tools ${CONFIG.tiers.std.map(t=>"$"+t.price).join(" / ")} per tool; property &amp; hospitality tools ${CONFIG.tiers.prop.map(t=>"$"+t.price).join(" / ")} per property (Essentials / Growth / Pro); any 3 standard tools on Essentials $120/mo.${saleActive()?` Holiday rates below apply for your first 12 months when you order by ${saleEndText()}.`:""}`',
    '`<b>Regular Monthly Prices</b> (Essentials / Growth / Pro)<span class="tl">Standard tools: ${CONFIG.tiers.std.map(t=>"$"+t.price).join(" / ")} per tool</span><span class="tl">Property &amp; hospitality tools: ${CONFIG.tiers.prop.map(t=>"$"+t.price).join(" / ")} per property</span><span class="tl">Small Business Suite: any 3 standard tools on Essentials for $120/mo</span>${saleActive()?`<span class="tl">Holiday rates below apply for your first 12 months when you order by ${saleEndText()}.</span>`:""}`')
rep('.tier-base{margin:0 0 14px;font-size:.95rem}', '.tier-base{margin:0 0 14px;font-size:.95rem}.tier-base .tl{display:block;margin-top:4px}')

# --- Savings estimator: type a number or use the slider; every tool and bundle in the list
rep('$$(".roi input[type=range]").forEach(i=>i.addEventListener("input",roi));',
    '$$(".roi input[type=range]").forEach(i=>{ const n=document.createElement("input"); n.type="number"; n.className="roi-num"; n.min=i.min; n.max=i.max; n.step=i.step||1; n.value=i.value; n.id=i.id+"n"; n.setAttribute("aria-label",(i.labels[0]?i.labels[0].firstChild.textContent.trim():"Value")+" (type a number)"); n.inputMode="decimal";\n'
    '  const out=i.labels[0]&&i.labels[0].querySelector("output"); if(out) out.hidden=true; i.labels[0].appendChild(n);\n'
    '  n.addEventListener("input",()=>{ if(n.value==="") return; let v=+n.value; if(!isFinite(v)) return; v=Math.max(+i.min,Math.min(+i.max,v)); i.value=v; roi(); });\n'
    '  n.addEventListener("change",()=>{ n.value=i.value; });\n'
    '  i.addEventListener("input",()=>{ n.value=i.value; roi(); }); });')
rep('<select id="roiTool"><option value="chat">ChatDesk</option><option value="service">LeadDesk</option><option value="salon">BookDesk</option><option value="property">WorkOrderDesk (1 property)</option><option value="bundle">Launch Bundle</option><option value="propbundle">Property Management Bundle</option><option value="hotelbundle">Hotel Operations Bundle (1 property)</option></select>',
    '<select id="roiTool"></select>')
rep('function roiPlan(id){',
    '$("#roiTool").innerHTML = `<optgroup label="Tools">${FEATURED.concat(MORE_ORDER).map(id=>PRODUCTS.find(p=>p.id===id)).filter(Boolean).map(p=>`<option value="${p.id}">${p.name}${p.tier==="prop"?" (1 property)":""}</option>`).join("")}</optgroup><optgroup label="Bundles"><option value="bundle">Launch Bundle</option><option value="propbundle">Property Management Bundle</option><option value="hotelbundle">Hotel Operations Bundle (1 property)</option></optgroup>`;\n$("#roiTool").value="chat";\nfunction roiPlan(id){')
open(p, "w", encoding="utf-8").write(s)
print("v25 applied")
