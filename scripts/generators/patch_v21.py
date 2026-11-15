"""v21 (Nov 15, 2026): cross-industry positioning, outcome-first product lines, website service,
30-Day Customer Comeback, annual prepay, live founding-spot counter, shorter experience line.
Run from the repo root: python3 scripts/generators/patch_v21.py [file ...] (default index.html)."""
import sys

def sub(s, old, new, count=1):
    assert s.count(old) >= 1, "missing: " + old[:80]
    return s.replace(old, new, count)

def patch(s):
    # 1. Hero checkmarks: shorter experience line on its own row, plus three more points
    s = sub(s, '<li>17 years building software products and solutions with customers</li><li>Human-Approved AI</li><li>Virtual or On-site</li><li>Pilots within weeks</li><li>Integration with existing systems</li>',
            '<li class="hp-lead">17 years building software<span class="hp-long"> products and solutions</span></li><li>Any industry</li><li>Human-Approved AI</li><li>Free 14-day trial</li><li>You own your data</li><li>Fixed-price quotes</li><li>Remote-first, worldwide</li><li>Virtual or On-site</li><li>Pilots within weeks</li><li>Integration with existing systems</li>')
    s = sub(s, '.hero-points li::before{content:"✓";color:var(--mint);margin-right:7px;font-weight:800}',
            '.hero-points li::before{content:"✓";color:var(--mint);margin-right:7px;font-weight:800}\n.hero-points .hp-lead{flex-basis:100%;color:#dfe8f2}\n@media (max-width:480px){.hero-points .hp-long{display:none}}\n.prod .outcome{margin:2px 0 8px;font-weight:700;color:var(--sky,#7cc4ff)}\n.svc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin-top:16px}\n.svc-grid .card{display:flex;flex-direction:column;gap:8px}\n.svc-grid .card .btn{align-self:flex-start;margin-top:auto}')

    # 2. Search/social description: not property-only
    s = sub(s, 'custom applications and tools for property, hospitality, and small businesses. Free workflow audit.',
            'custom applications and tools for service businesses in any industry. Free workflow audit.')

    # 3. Industry examples: four different kinds of business instead of four property/hospitality ones
    a = s.index('<article class="card focus"><span class="chip">Hospitality</span> <h3>Hotels</h3>')
    b = s.index('</div>', s.index('<h3>Timeshares</h3>'))
    s = s[:a] + ('<article class="card focus"><span class="chip">Hospitality</span> <h3>Hotels &amp; Resorts</h3><ul><li>Guest requests routed to departments</li><li>Housekeeping &amp; maintenance queues</li><li>Pre-arrival messaging &amp; upsells staff approve</li><li>Review response drafting</li></ul></article>\n'
                 '      <article class="card focus"><span class="chip">Appointments</span> <h3>Salons, Spas &amp; Clinics</h3><ul><li>Online booking &amp; reminders</li><li>Waitlists that fill cancellations</li><li>Rebooking &amp; loyalty offers</li><li>More five-star reviews</li></ul></article>\n'
                 '      <article class="card focus"><span class="chip">Home &amp; local services</span> <h3>Contractors, Auto &amp; Cleaning</h3><ul><li>Missed calls answered by text</li><li>Quote follow-up that never slips</li><li>Job status updates for customers</li><li>Invoices &amp; payment reminders</li></ul></article>\n    ') + s[b:]

    # 4. Hero animation starts with a non-property example (static text matches the first sample)
    i = s.index('const heroSamples = [')
    j = s.index('];', i)
    lines = s[i:j].split('\n')
    head, rows = lines[0], [l.rstrip().rstrip(',') for l in lines[1:] if l.strip()]
    order = [2, 3, 0, 1]   # salon, contractor, apartment, resort
    s = s[:i] + head + '\n' + ',\n'.join(rows[k] for k in order) + '\n' + s[j:]
    first = rows[2]
    import re
    src = re.search(r'src:"([^"]*)"', first).group(1); text = re.search(r'text:"([^"]*)"', first).group(1)
    s = sub(s, '<small id="heroSrc">Apartment resident · text message</small><span id="heroText">“Water is leaking under my kitchen sink in Unit 204. I can be home after 3.”</span>',
            f'<small id="heroSrc">{src}</small><span id="heroText">{text}</span>')
    sort = re.search(r'sort:"([^"]*)"', first).group(1); draft = re.search(r'draft:"([^"]*)"', first).group(1)
    k = s.index('id="heroSort"'); k2 = s.index('>', k) + 1; k3 = s.index('<', k2); s = s[:k2] + sort + s[k3:]
    k = s.index('id="heroDraft"'); k2 = s.index('>', k) + 1; k3 = s.index('<', k2); s = s[:k2] + draft + s[k3:]

    # 5. Product order stays as Rashad set it (WorkOrderDesk, ChatDesk, BookDesk, then the rest).

    # 6. Outcome-first line on every product card
    s = sub(s, 'const DEMO_IDS=[', '''const OUTCOMES={chat:"Answer every website visitor, day or night",service:"Never lose a job to a missed call or a forgotten quote",salon:"Fill empty chairs and cut no-shows",
  property:"Fewer “any update?” calls and happier residents",resort:"Every guest request handled before it becomes a bad review",housekeeping:"Rooms turned faster, nothing missed between shifts",
  review:"More five-star Google reviews, every month",rewards:"Bring regulars back more often",invoice:"Get paid faster with less chasing",social:"Post every week without thinking about it",
  package:"No lost packages, no crowded mail room",staff:"New staff get answers without interrupting managers",insight:"Know your numbers every Monday morning",
  intake:"Qualified clients, complete paperwork, less phone time",compliance:"Never miss a deadline or an inspection"};
const DEMO_IDS=[''')
    s = sub(s, '<h3>${esc(p.name)}</h3><span class="price">', '<h3>${esc(p.name)}</h3>${OUTCOMES[p.id]?`<p class="outcome">${esc(OUTCOMES[p.id])}</p>`:""}<span class="price">')

    # 7. Website & growth services (approved Nov 15): buyable, sale-aware, client-owned hosting
    s = sub(s, '  care:{name:"Care & Growth Plan", monthly:150},',
            '  care:{name:"Care & Growth Plan", monthly:150},\n  site1:{name:"Launch Website (1 page)", price:500},\n  site5:{name:"Booking Website (up to 5 pages)", price:1500},\n  comeback:{name:"30-Day Customer Comeback", price:750},')
    s = sub(s, '    <div class="offers">',
            '''    <div class="svc" id="services">
      <h3 style="margin-top:30px">Websites &amp; Marketing Services</h3>
      <p class="hint" style="margin:4px 0 0">Built quickly with AI, finished and tested by me. Websites live in an account your business owns (your domain and hosting), so you're never locked in. For ongoing marketing, add SocialDesk (weekly posts) and ReviewDesk (more reviews) on a monthly plan.</p>
      <div class="svc-grid" id="svcGrid"></div>
    </div>
    <div class="offers">''')
    s = sub(s, '$("#pkgGrid").innerHTML = CONFIG.packages.map(',
            '''const SERVICES=[
  {id:"site1", chip:"Website", name:"Launch Website", price:"$500", desc:"A fast, mobile-friendly one-page site with your services, hours, reviews and a clear call or booking button, plus a Google Business Profile cleanup. Ready in about 1 week."},
  {id:"site5", chip:"Website", name:"Booking Website", price:"$1,500", desc:"Up to 5 pages with ChatDesk answering questions and BookDesk or LeadDesk capturing bookings and quotes (tool plans billed monthly). Ready in about 2–3 weeks."},
  {id:"comeback", chip:"Marketing", name:"30-Day Customer Comeback", price:"$750", desc:"Win back customers who haven't visited in 60+ days with a personal offer, start review requests after every visit, and get a month of social posts. Every booking it brings in is tracked and reported at day 30."}
];
$("#svcGrid").innerHTML = SERVICES.map(v=>`<article class="card"><span class="chip live" style="align-self:flex-start">${esc(v.chip)}</span><h3>${esc(v.name)}</h3><div class="price">${priceHTML(v.price)}</div><p>${esc(v.desc)}</p><button type="button" class="btn btn-line btn-sm" data-buy="${v.id}">Order now</button></article>`).join("")
  + `<article class="card"><span class="chip" style="align-self:flex-start">Optional</span><h3>Site Care</h3><div class="price">${priceHTML("$50/mo")}</div><p>Text and photo updates, new offers, and a monthly check that forms and links still work. Your site stays in your own hosting account; cancel anytime.</p></article>`;
$("#pkgGrid").innerHTML = CONFIG.packages.map(''', 1)

    # 8. Annual prepay (approved Nov 15)
    s = sub(s, '<p class="pricenote"><b>Payment plans:</b>',
            '<p class="pricenote"><b>Annual prepay:</b> pay 12 months of any plan up front and get 2 months free.<br><b>Payment plans:</b>')

    # 9. Founding spots update themselves from the lead engine
    s = sub(s, 'Founding clients (first 5): 25% off your first setup',
            'Founding clients (first 5<span class="fLeftWrap">, <span class="fLeft">5</span> left</span>): 25% off your first setup')
    s = sub(s, 'if (!CONFIG.foundingSpots) $("#founding").hidden = true;',
            '''if (!CONFIG.foundingSpots) $("#founding").hidden = true;
function showFounding(left){
  left=Math.max(0, Math.min(CONFIG.foundingSpots, left|0));
  $("#spots").textContent=left; $$(".fLeft").forEach(x=>x.textContent=left);
  if(!left){ $("#founding").hidden=true; $$(".sale-l2").forEach(x=>x.hidden=true); }
}
showFounding(CONFIG.foundingSpots);
if (CONFIG.backendUrl) fetch(CONFIG.backendUrl+"?stats=founding",{cache:"no-store"}).then(r=>r.json()).then(j=>{ if(j&&j.ok&&typeof j.foundingLeft==="number") showFounding(j.foundingLeft); }).catch(()=>{});''')
    return s

if __name__ == "__main__":
    for f in (sys.argv[1:] or ["index.html"]):
        src = open(f).read()
        out = patch(src)
        open(f, "w").write(out)
        print("patched", f)
