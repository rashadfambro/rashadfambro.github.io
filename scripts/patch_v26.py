"""v26 (Nov 16, 2026): review fixes (dialog focus, billing/trial terms), website pricing, new bundles, multi-location and storage pricing, experience wording."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else "index.html"
s = open(p, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:80])
    s = s.replace(a, b)

# --- Order dialog: focus stays inside while open, returns to the button that opened it
rep('function openBuy(id, mode){\n  buyItem=id;', 'let buyOpener=null;\nfunction openBuy(id, mode){\n  if(document.activeElement && !$("#buyModal").contains(document.activeElement)) buyOpener=document.activeElement;\n  buyItem=id;')
rep('function closeBuy(){ $("#buyModal").hidden=true; }',
    'function closeBuy(){ $("#buyModal").hidden=true; if(buyOpener && document.contains(buyOpener)) { try{ buyOpener.focus({preventScroll:true}); }catch(e){} } buyOpener=null; }')
rep('document.addEventListener("keydown",e=>{ if(e.key==="Escape" && !$("#buyModal").hidden) closeBuy(); });',
    'document.addEventListener("keydown",e=>{ if($("#buyModal").hidden) return; if(e.key==="Escape"){ closeBuy(); return; }\n'
    '  if(e.key==="Tab"){ const f=[...$("#buyModal").querySelectorAll(\'a[href],button,input,select,textarea,[tabindex]:not([tabindex="-1"])\')].filter(x=>!x.disabled && x.offsetParent!==null && x.getAttribute("tabindex")!=="-1" && !x.closest("[aria-hidden=true]")); if(!f.length) return;\n'
    '    const first=f[0], last=f[f.length-1], a=document.activeElement, inside=$("#buyModal").contains(a);\n'
    '    if(e.shiftKey && (a===first || !inside)){ e.preventDefault(); last.focus(); } else if(!e.shiftKey && (a===last || !inside)){ e.preventDefault(); first.focus(); } } });')

# --- Trial: when the 14 days start, and the button matches the card
rep('$("#buyGo").textContent = trial ? "Start my free trial →"', '$("#buyGo").textContent = trial ? "Request my branded trial →"')
rep("Live connections to your accounts start when you choose a plan. On day 14 the trial simply expires unless you choose a paid plan.</p>",
    "Your 14 days start on the day the workspace link is emailed to you. Live connections to your accounts start when you choose a plan. On day 14 the trial simply expires unless you choose a paid plan.</p>")
rep("`Start Your Free ${CONFIG.trialDays}-Day Trial: ${it.name}`", "`Request Your Branded ${CONFIG.trialDays}-Day Trial: ${it.name}`")

# --- Billing start and installment dates
rep("starting the month your tool goes live, plus usage", "starting the day your Starter edition is delivered (1–3 business days after payment), plus usage")
rep("split any setup or project of $1,000+ into 3 interest-free monthly payments.", "split any setup or project of $1,000+ into 3 interest-free payments: the first at kickoff, then 30 and 60 days later. Monthly plans start the day your Starter edition is delivered.")
rep("can be split into 3 interest-free monthly payments, with the first payment at signing.", "can be split into 3 interest-free payments: the first at kickoff, then 30 and 60 days later.")
rep("split into <b>3 interest-free monthly payments</b> (first payment at signing).", "split into <b>3 interest-free payments</b>: the first at kickoff, then 30 and 60 days later.")
rep('<input type="radio" name="plan" value="3 monthly payments"> 3 interest-free monthly payments</label>', '<input type="radio" name="plan" value="3 monthly payments"> 3 interest-free payments (today, then 1 and 2 months later)</label>')

# --- Booking Website: the website only; tools priced separately, with a discount when ordered together
rep('desc:"Up to 5 pages with ChatDesk answering questions and BookDesk or LeadDesk capturing bookings and quotes (tool plans billed monthly). Ready in about 2–3 weeks."',
    'desc:"Up to 5 pages with a clear booking or quote button that connects to the booking system you already use. No monthly plan required. Add Desk tools at 10% off their setup when ordered with your website, or choose the Booking Website + Launch Bundle below. Ready in about 2–3 weeks."')
rep('site5:{name:"Booking Website (up to 5 pages)", price:1500},', 'site5:{name:"Booking Website (up to 5 pages)", price:1500},\n  sitebundle:{name:"Booking Website + Launch Bundle: website, ChatDesk + BookDesk setup", price:3500, tier:"std", count:2},\n  csbundle:{name:"Customer Service Bundle: ChatDesk + LeadDesk + ReviewDesk setup", price:3000, monthly:120, invoice:true},   // invoice until its Square links exist')
rep('bundleIds = {bundle:1, propbundle:1, hotelbundle:1};', 'bundleIds = {bundle:1, propbundle:1, hotelbundle:1, sitebundle:1, csbundle:1};')
rep('{bundle:2, propbundle:3, hotelbundle:3}[id]', '{bundle:2, propbundle:3, hotelbundle:3, sitebundle:2, csbundle:3}[id]')
rep('<option value="hotelbundle">Hotel Operations Bundle (1 property)</option></optgroup>', '<option value="hotelbundle">Hotel Operations Bundle (1 property)</option><option value="csbundle">Customer Service Bundle</option><option value="sitebundle">Booking Website + Launch Bundle</option></optgroup>')
rep('<article class="card"><span class="chip live">Credit</span> <h3>Assessment Credit</h3>',
    '<article class="card"><span class="chip live">Bundle</span> <h3>Customer Service Bundle</h3> <p><b>ChatDesk + LeadDesk + ReviewDesk setup for <span class="bprice" data-price="3000" data-parts="1500,1500,500">$3,000</span></b> (save <span class="bsave">$500</span> vs. buying each tool separately at regular prices). Answer every question, follow up on every inquiry, and get more reviews, then $120/mo for all three on Essentials.</p><button type="button" class="btn btn-line btn-sm" data-buy="csbundle" style="margin-top:12px">Order this bundle</button></article>\n'
    '      <article class="card"><span class="chip live">Bundle</span> <h3>Booking Website + Launch Bundle</h3> <p><b>A Booking Website plus ChatDesk + BookDesk setup for <span class="bprice" data-price="3500" data-parts="1500,2500">$3,500</span></b> (save <span class="bsave">$500</span> vs. buying the website and Launch Bundle separately at regular prices). A new site that answers questions and books appointments from day one, then $100/mo for both tools on Essentials.</p><button type="button" class="btn btn-line btn-sm" data-buy="sitebundle" style="margin-top:12px">Order this bundle</button></article>\n'
    '      <article class="card"><span class="chip live">Credit</span> <h3>Assessment Credit</h3>')
s = s.replace('b.textContent=b.textContent.replace("at regular prices)","at holiday prices)")', 'b.textContent=b.textContent.replace("separately at regular prices)","separately at holiday prices)")')

# --- Multi-location and extra storage
rep("beyond that, $10 per extra 1,000 conversations and $10 per extra 500 texts. Your data stays exportable at any time.</p>",
    "beyond that, $10 per extra 1,000 conversations, $10 per extra 500 texts and $10 per extra 5 GB of storage. Your data stays exportable at any time.</p>\n"
    "      <p class=\"tier-foot\"><b>Multiple locations:</b> the first location pays the normal setup; each additional location is $500 (Starter edition) or $1,000 (Connected edition) for its own branding, staff, hours and settings. Monthly plans are per location: 10% off locations 2–4, 20% off locations 5–9, and a custom quote for 10 or more. Chains get 20% off InsightDesk for an all-locations dashboard.</p>")

# --- Experience: grocery stores, business media systems, quick-service restaurants
rep("restaurants, retail store operations, in-store media, and defense communications.", "quick-service restaurants, grocery stores, business media systems, and defense communications.")
rep('<p class="co">In-store media, restaurant technology, defense communications &amp; retail store software</p>', '<p class="co">Business media systems, quick-service restaurant POS, defense communications &amp; grocery store software</p>')
rep('Led global test automation for in-store media,', 'Led global test automation for media systems used by many types of businesses,')
rep('tested restaurant point-of-sale systems and credit card certification', 'tested quick-service restaurant point-of-sale systems and credit card certification')
rep('shipped inventory apps used in 3,500 stores.', 'shipped audit and inventory apps used in 3,500 grocery stores.')
rep('<span>Restaurant POS</span>', '<span>Quick-Service Restaurant POS</span>')
rep('<span>Retail Store Operations</span><span>In-Store Media</span>', '<span>Grocery Stores</span><span>Business Media Systems</span>')
rep('restaurants, retail store operations, in-store media and defense communications.', 'quick-service restaurants, grocery stores, business media systems and defense communications.')
rep('function payLinkFor(id, method, plan){\n  if(isPilot(id)) return "";', 'function payLinkFor(id, method, plan){\n  if(isPilot(id) || (BUYABLE[id] && BUYABLE[id].invoice)) return "";')
open(p, "w", encoding="utf-8").write(s)
print("v26 applied")
