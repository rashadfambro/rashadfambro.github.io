import re, json, html, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from products_data import PRODUCTS, COMMON
_ORDER = ["workorder","chat","book","guest","housekeeping","rewards","invoice","lead","package","social","review","staff","insight","intake","compliance"]
PRODUCTS = sorted(PRODUCTS, key=lambda p: _ORDER.index(p["id"]))
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SITE = 'https://rashadfambro.github.io/'
e = html.escape

def shell(title, desc, canonical, body, depth=0):
    up = '../' * depth
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://formsubmit.co https://script.google.com https://script.googleusercontent.com; frame-src https://calendly.com; object-src 'none'; base-uri 'self'; form-action 'self' https://formsubmit.co"><meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<link rel="manifest" href="{up}manifest.webmanifest">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canonical}"><meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230d1a2d'/%3E%3Ctext x='32' y='42' text-anchor='middle' font-family='Georgia,serif' font-size='28' fill='%237cc4ff'%3ERF%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root{{--ink:#0d1a2d;--ink2:#14263f;--sky:#7cc4ff;--sky2:#b9e0ff;--mint:#5fe0b5;--paper:#f5f8fc;--soft:#e9f0f8;--line:#d3dce7;--muted:#56606c;--text:#1a2533;--serif:"Source Serif 4",Georgia,serif;--sans:"Manrope",system-ui,sans-serif}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--text);font:16px/1.6 var(--sans)}}
a{{color:inherit}}h1,h2,h3{{font-family:var(--serif);font-weight:600;letter-spacing:-.02em;line-height:1.1;margin:0;font-variant-ligatures:no-common-ligatures}}
.wrap{{width:min(1100px,calc(100% - 40px));margin-inline:auto}}
.mast{{background:var(--ink);color:#eef3f9;position:sticky;top:0;z-index:5}}
.bar{{display:flex;justify-content:space-between;align-items:center;gap:16px;min-height:66px}}
.brand{{display:flex;gap:10px;align-items:center;text-decoration:none;line-height:1.15}}
.mark{{width:38px;height:38px;border-radius:10px;background:linear-gradient(140deg,var(--sky),#3d8bff);color:var(--ink);display:grid;place-items:center;font:600 .95rem var(--serif)}}
.brand b{{display:block;font-size:.95rem}}.brand small{{color:#a9bbd0;font-size:.72rem;font-weight:600}}
.btn{{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:10px 18px;border-radius:10px;font-weight:750;font-size:.9rem;text-decoration:none;border:1px solid transparent}}
.btn-p{{background:var(--sky);color:var(--ink)}}.btn-d{{background:var(--ink);color:#fff}}.btn-l{{border-color:#a8b6c7;background:#fff;color:var(--ink)}}
.hero{{background:var(--ink);color:#eef3f9;padding:56px 0 48px}}
.hero h1{{font-size:clamp(2.2rem,5vw,3.6rem);margin:10px 0 14px}}.hero p{{color:#c3cfdd;max-width:62ch;font-size:1.06rem}}
.eb{{font:800 .72rem var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--sky2)}}
.sec{{padding:48px 0}}
.toc{{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}}.toc a{{border:1px solid #4a6283;border-radius:999px;padding:6px 12px;font-size:.84rem;font-weight:700;text-decoration:none;color:#dfe8f2}}
.prod{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:clamp(20px,3vw,32px);margin-bottom:22px;scroll-margin-top:80px}}
.prod .top{{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:baseline}}
.prod h2{{font-size:clamp(1.7rem,3vw,2.2rem)}}.tag{{color:#1e5fa8;font-weight:700}}.price{{font-weight:800;color:#0d6a4b;background:#dcf8ee;border-radius:999px;padding:4px 12px;font-size:.85rem}}
.who{{color:var(--muted);margin:6px 0 16px}}
.cols{{display:grid;grid-template-columns:1.1fr .9fr;gap:24px}}
h3{{font-size:1.1rem;margin:0 0 8px}}
ol.flow{{margin:0;padding-left:20px}}ol.flow li{{margin-bottom:6px}}
.ben{{display:grid;gap:10px}}.ben div{{background:var(--soft);border-radius:10px;padding:10px 14px;font-size:.93rem}}.ben b{{display:block;font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;color:#3b5878}}
.ben .h{{background:#effcf7;border:1px solid #a9e8d1}}
.card{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
ul.tick{{list-style:none;padding:0;margin:0}}ul.tick li{{padding-left:24px;position:relative;margin-bottom:6px}}ul.tick li::before{{content:"✓";position:absolute;left:0;color:#0d8a5f;font-weight:800}}
.cta{{background:var(--ink);color:#fff;border-radius:18px;padding:clamp(22px,4vw,36px);display:flex;justify-content:space-between;gap:20px;align-items:center;flex-wrap:wrap}}
.cta h2{{font-size:clamp(1.5rem,3vw,2.1rem)}}.cta p{{color:#c3cfdd;margin:6px 0 0}}
.foot{{background:#08121f;color:#8ea3bc;font-size:.84rem;padding:22px 0;margin-top:48px}}.foot a{{text-decoration:none}}
@media(max-width:760px){{.cols,.grid2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div id="sb" hidden style="background:linear-gradient(90deg,#ffc46b,#ffd99a);color:#0d1a2d;text-align:center;font-size:.88rem;padding:8px 12px"><b>Holiday &amp; New Year Sale:</b> 10% or more off all listed products and services through January 31, 2027 (rounded down to the nearest $10). <a href="{up}index.html#pricing" style="font-weight:800">See prices →</a></div><script>if(new Date()<=new Date("2027-01-31T23:59:59"))document.getElementById("sb").hidden=false;</script>
<header class="mast"><div class="wrap bar"><a class="brand" href="{up}index.html"><span class="mark">RF</span><span><b>Rashad Fambro Consulting</b><small>IT Software Consultant · Automation &amp; AI</small></span></a><span style="display:flex;gap:10px;align-items:center"><a href="{up}index.html" style="color:#c7d4e2;font-weight:700;text-decoration:none;font-size:.9rem">Home</a><a class="btn btn-p" href="{up}index.html#audit">Free audit →</a></span></div></header>
{body}
<button id="toTop" type="button" aria-label="Back to top" hidden style="position:fixed;left:20px;bottom:20px;z-index:20;display:flex;align-items:center;gap:6px;background:#fff;color:#0d1a2d;border:1px solid #b9c7d7;border-radius:999px;padding:10px 14px;font:800 .85rem var(--sans);cursor:pointer;box-shadow:0 10px 30px -12px #0d1a2d88">↑ Top</button>
<script>(function(){{var b=document.getElementById("toTop");function u(){{b.hidden=window.scrollY<600;}}window.addEventListener("scroll",u,{{passive:true}});u();b.addEventListener("click",function(){{window.scrollTo({{top:0,behavior:"smooth"}});}});}})();</script>
<footer class="foot"><div class="wrap">© 2026 Rashad Fambro Consulting · <a href="{up}index.html">Home</a> · <a href="{up}products.html">Product Guide</a> · <a href="{up}index.html#pricing">Pricing</a> · <a href="{up}index.html#contact">Contact</a> · <a href="{up}privacy.html">Privacy Policy</a></div></footer>
</body></html>
'''

CTA = lambda up, extra='': f'''<div class="cta"><div><h2>See What This Would Look Like for You</h2><p>Free 30-minute workflow audit — virtual, or on-site by request. Founding clients get 25% off their first setup and the first month free.</p></div><div style="display:flex;gap:10px;flex-wrap:wrap"><a class="btn btn-p" href="{up}index.html{extra or '#audit'}">Book a free audit →</a><a class="btn btn-l" href="{up}index.html#pricing">See pricing</a></div></div>'''

# ---------------- product guide ----------------
toc = ''.join(f'<a href="#{p["id"]}">{e(p["name"])}</a>' for p in PRODUCTS)
blocks = []
for p in PRODUCTS:
    blocks.append(f'''<article class="prod" id="{p['id']}">
  <div class="top"><div><h2>{e(p['name'])}</h2><div class="tag">{e(p['tag'])}</div></div><span class="price">{e(p['price'])}</span></div>
  <p class="who"><b>Built for:</b> {e(p['who'])}</p>
  <div class="cols">
    <div><h3>How It Works</h3><ol class="flow">{''.join(f'<li>{e(x)}</li>' for x in p['flow'])}</ol></div>
    <div class="ben">
      <div><b>Saves Money</b>{e(p['money'])}</div>
      <div><b>Wins More Business</b>{e(p['business'])}</div>
      <div><b>Boosts Productivity</b>{e(p['productivity'])}</div>
      <div class="h"><b>Human in the Loop</b>{e(p['human'])}</div>
    </div>
  </div>
</article>''')
body = f'''<section class="hero"><div class="wrap"><span class="eb">Product Guide</span><h1>AI Tools That Help Your Business Earn More and Your Team Move Faster</h1><p>Each product is a ready-to-adapt solution, branded for your business and delivered as a managed service. Below: how each one works, how it saves money, how it wins more business, and where people stay in control. Every tool includes a free 14-day trial, and fully managed monthly plans start at $80.</p><div class="toc">{toc}</div></div></section>
<section class="sec"><div class="wrap">
<div class="grid2" style="margin-bottom:26px">
  <div class="card"><h3>Branded for Your Business</h3><p>{e(COMMON['brand'])}</p></div>
  <div class="card"><h3>Managed SaaS Releases</h3><p>{e(COMMON['releases'])}</p></div>
</div>
{''.join(blocks)}
{CTA('')}
</div></section>'''
open(f'{ROOT}/products.html', 'w').write(shell('Product Guide | Rashad Fambro Consulting — AI Tools for Small Business',
    'How ChatDesk, BookDesk, LeadDesk, RewardsDesk and other AI tools work, save money, win business, and keep humans in the loop.', SITE + 'products.html', body))

# ---------------- industry pages ----------------
src = open(f'{ROOT}/index.html').read()
ind_block = src[src.index('const INDUSTRIES = ['):src.index('];', src.index('const INDUSTRIES = ['))]
inds = []
for line in ind_block.splitlines():
    line = line.strip().rstrip(',')
    if not line.startswith('{k:'): continue
    js = re.sub(r'(\{|, )(\w+):', r'\1"\2":', line)
    inds.append(json.loads(js))
land = {}
lb = src[src.index('const LANDINGS = {'):src.index('};', src.index('const LANDINGS = {'))]
for m in re.finditer(r'"(for-[\w-]+)":\s*\{ who: "([^"]+)", line: "([^"]+)", ind: "(\w+)"', lb):
    land.setdefault(m.group(4), (m.group(1), m.group(2), m.group(3)))
demo_to_prod = {"property": "workorder", "resort": "guest", "salon": "book", "service": "lead", "intake": "intake", "compliance": "compliance", "chat": "chat"}
extra_prod = {"smoke": ["rewards"], "nails": ["rewards", "review"], "barbers": ["rewards", "review"], "restaurants": ["review", "rewards"], "cleaning": ["invoice"], "contractors": ["invoice"],
              "fitness": ["rewards"], "str": ["housekeeping", "review"], "timeshare": ["housekeeping", "workorder", "package"], "apartments": ["package", "chat"], "hotels": ["housekeeping", "workorder", "package", "intake"], "dental": ["review"], "autorepair": ["review"], "storage": ["invoice"]}
P = {p['id']: p for p in PRODUCTS}
os.makedirs(f'{ROOT}/industries', exist_ok=True)
slugs = []
for x in inds:
    if x['k'] == 'other': continue
    hashname, who, line = land.get(x['k'], (None, x['n'].lower(), None))
    slug = (hashname[4:] if hashname else re.sub(r'[^a-z0-9]+', '-', x['n'].lower()).strip('-'))
    prods = [demo_to_prod[x['demo']]] + extra_prod.get(x['k'], [])
    prods = [P[i] for i in dict.fromkeys(prods)]
    pcards = ''.join(f'<div class="card"><h3>{e(p["name"])}</h3><span class="price" style="font-size:.75rem;display:inline-block;margin-bottom:8px">{e(p["price"])}</span><p class="tag" style="margin:0 0 6px">{e(p["tag"])}</p><p style="margin:0;color:var(--muted)">{e(p["business"])}</p><p style="margin:10px 0 0"><a href="../products.html#{p["id"]}">How {e(p["name"])} works →</a></p></div>' for p in prods)
    title = f'AI & Automation for {x["n"]} | Rashad Fambro Consulting'
    desc = f'AI tools and workflow automation for {who}: ' + '; '.join(w.lower() for w in x['wins'][:3]) + '. Free workflow audit.'
    body = f'''<section class="hero"><div class="wrap"><span class="eb">Industries · {e(x["n"])}</span><h1>AI &amp; Automation for {e(x["n"])}</h1><p>{e(line or "")} I help {e(who)} earn more and get more done with AI tools and automation — branded for your business, with your team approving what matters.</p><div style="margin-top:22px;display:flex;gap:10px;flex-wrap:wrap"><a class="btn btn-p" href="../index.html{'#'+hashname if hashname else '#audit'}">See the tailored demo →</a><a class="btn btn-l" href="../index.html#audit">Book a free audit</a></div></div></section>
<section class="sec"><div class="wrap">
<div class="grid2">
  <div class="card"><h3>Where Time and Money Get Lost</h3><ul class="tick">{''.join(f'<li>{e(t)}</li>' for t in x["pains"])}</ul></div>
  <div class="card"><h3>Quick Wins</h3><ul class="tick">{''.join(f'<li>{e(t)}</li>' for t in x["wins"])}</ul></div>
</div>
<h2 style="margin:36px 0 16px;font-size:clamp(1.6rem,3vw,2.2rem)">Recommended Tools</h2>
<div class="grid2">{pcards}</div>
<div class="grid2" style="margin:26px 0">
  <div class="card"><h3>How We Work Together</h3><ol class="flow"><li>Free 30-minute discovery call (virtual)</li><li>Workflow audit — virtual or on-site — with a one-page summary</li><li>Fixed-price proposal</li><li>Build, test with your team, and launch in 2–6 weeks</li><li>30-day results review</li></ol></div>
  <div class="card"><h3>People Stay in Control</h3><p>AI drafts, sorts, and suggests. Your staff approves prices, promises, and anything sensitive — and every action is logged. Tools are branded for your business and kept current through tested, managed releases.</p></div>
</div>
{CTA('../', '#'+hashname if hashname else '')}
</div></section>'''
    open(f'{ROOT}/industries/{slug}.html', 'w').write(shell(title, desc, f'{SITE}industries/{slug}.html', body, depth=1))
    slugs.append((slug, x['n']))

# industries index
links = ''.join(f'<a class="card" style="text-decoration:none;display:block" href="{s}.html"><h3>{e(n)}</h3><span class="tag">AI &amp; automation for {e(n.lower())} →</span></a>' for s, n in slugs)
body = f'''<section class="hero"><div class="wrap"><span class="eb">Industries</span><h1>AI &amp; Automation by Industry</h1><p>Practical AI tools for property, hospitality, and local businesses — branded for you, with people in control.</p></div></section>
<section class="sec"><div class="wrap"><div class="grid2">{links}</div><div style="margin-top:26px">{CTA('../')}</div></div></section>'''
open(f'{ROOT}/industries/index.html', 'w').write(shell('Industries | Rashad Fambro Consulting', 'AI tools and automation for apartments, hotels, salons, contractors, law and dental offices, smoke shops, and more.', SITE + 'industries/', body, depth=1))


# privacy policy
PRIV = """<section class="hero"><div class="wrap"><span class="eb">Privacy</span><h1>Privacy Policy</h1><p>Plain-English answers about what this website collects, why, and the choices you have. Effective November 13, 2026.</p></div></section>
<section class="sec"><div class="wrap" style="max-width:820px">
<div class="card" style="margin-bottom:18px"><h2 style="font-size:1.5rem;margin-bottom:8px">The Short Version</h2><ul class="tick">
<li>I collect only what you choose to send me: your name, business, email, and details about your request.</li>
<li>I use it to reply, prepare your audit or quote, and deliver services you sign up for.</li>
<li>I never sell your information or share it for advertising.</li>
<li>No analytics trackers or advertising cookies run on this site.</li>
<li>Email me any time to see, correct, or delete your information.</li></ul></div>
<div class="card"><h2 style="font-size:1.4rem;margin-bottom:8px">Who I Am</h2>
<p>This website is run by Rashad Fambro, doing business as Rashad Fambro Consulting (the business name may change; this policy will be updated when it does). Contact: <a href="mailto:rashadfambro@gmail.com">rashadfambro@gmail.com</a>.</p>
<h2 style="font-size:1.4rem;margin:22px 0 8px">What I Collect</h2>
<ul class="tick">
<li><b>Forms you submit</b> (free audit, project request, trial, order, savings estimator): name, business name, email, phone if you add it, industry, team size, the workflow you describe, notes, and meeting preferences.</li>
<li><b>Where you came from:</b> if you arrive through a tracked link (for example <code>?utm_source=linkedin</code> or <code>?ref=walk-in</code>), that label is sent with your form so I know which outreach worked.</li>
<li><b>Chat assistant:</b> the guided chat runs in your browser. Your messages are sent to me only if you choose to send your details. If the AI chat mode is turned on in the future, chat messages will be processed by Anthropic’s Claude service to generate replies.</li>
<li><b>Bookings:</b> when you book a meeting, Calendly collects your name, email, and answers to its questions.</li>
<li><b>Payments:</b> PayPal and Square process payments. I receive confirmation of what was paid, but never your full card or bank details.</li>
<li><b>Your browser:</b> the product prototypes save your demo changes in your own browser (local storage) so they stay while you try them. Nothing from the prototypes is sent to me.</li></ul>
<h2 style="font-size:1.4rem;margin:22px 0 8px">How I Use It</h2>
<ul class="tick"><li>To reply to you, schedule meetings, and prepare audits, proposals, and invoices.</li><li>To deliver, support, and improve services you sign up for.</li><li>To send a small number of follow-ups about your request. Reply “stop” any time and they end.</li><li>To keep basic business and tax records.</li></ul>
<h2 style="font-size:1.4rem;margin:22px 0 8px">Services That Help Run This Site</h2>
<p>These providers handle information only to provide their service: GitHub Pages (website hosting), FormSubmit (delivers form submissions by email), Google (Gmail, Calendar, Sheets, and the fonts this site loads), Calendly (scheduling), PayPal and Square (payments), and, if enabled, Anthropic (AI chat). Each has its own privacy policy. Like most websites, the hosting and font providers may receive your IP address and browser details when pages load.</p>
<h2 style="font-size:1.4rem;margin:22px 0 8px">Client Data in My Tools</h2>
<p>If your business uses one of my Desk tools, the data your customers, residents, or guests provide belongs to your business. It is handled under our written agreement: used only to run the tool, kept confidential, never sold, and exported or deleted when you ask.</p>
<h2 style="font-size:1.4rem;margin:22px 0 8px">How Long I Keep It</h2>
<p>Inquiries that don’t become projects are deleted within 24 months of the last contact. Client records are kept for the length of our work together plus any period required for tax or legal reasons. You can ask for earlier deletion at any time.</p>
<h2 style="font-size:1.4rem;margin:22px 0 8px">Your Choices and Rights</h2>
<p>Wherever you live, you can ask to see, correct, export, or delete the information I hold about you, and to stop follow-up messages. Email <a href="mailto:rashadfambro@gmail.com">rashadfambro@gmail.com</a> and I’ll respond within 30 days. Depending on where you live (for example the EU, UK, or California), you may have additional rights under local law, and you can contact your local data protection authority.</p>
<h2 style="font-size:1.4rem;margin:22px 0 8px">Security</h2>
<p>Information is stored in password-protected accounts with two-step sign-in where available, and only I have access. No method of sending information over the internet is perfectly secure, so please don’t send passwords or payment card numbers through the forms.</p>
<h2 style="font-size:1.4rem;margin:22px 0 8px">Children</h2>
<p>This site is for businesses and isn’t directed to anyone under 16.</p>
<h2 style="font-size:1.4rem;margin:22px 0 8px">Changes</h2>
<p>If this policy changes, the effective date at the top will change too. Significant changes will be noted on the home page.</p>
</div></div></section>"""
open(f'{ROOT}/privacy.html', 'w').write(shell('Privacy Policy | Rashad Fambro Consulting', 'What Rashad Fambro Consulting collects through this website, how it is used, the services involved, and how to see, correct, or delete your information.', SITE + 'privacy.html', PRIV))

# sitemap
urls = [SITE, SITE + 'products.html', SITE + 'privacy.html', SITE + 'industries/'] + [f'{SITE}industries/{s}.html' for s, _ in slugs]
open(f'{ROOT}/sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{u}</loc><changefreq>monthly</changefreq></url>\n' for u in urls) + '</urlset>\n')

# footer links on home page
home = open(f'{ROOT}/index.html').read()
foot_links = '<div class="wrap foot-ind"><span>Industries:</span> ' + ' · '.join(f'<a href="industries/{s}.html">{e(n)}</a>' for s, n in slugs) + ' · <a href="products.html">Product Guide</a></div>'
if 'foot-ind' not in home:
    home = home.replace('<footer class="footer">', '<footer class="footer">\n  ' + foot_links, 1)
    home = home.replace('.footer a:hover{color:#fff}', '.footer a:hover{color:#fff}\n.foot-ind{padding-top:20px;font-size:.8rem;line-height:1.9;border-bottom:1px solid #1d3454;padding-bottom:16px}\n.foot-ind span{font-weight:800;color:#c3cfdd}', 1)
    open(f'{ROOT}/index.html', 'w').write(home)

# markdown overviews
md = ['# Product Overviews — Rashad Fambro Consulting', '', COMMON['brand'], '', COMMON['releases'], '']
for p in PRODUCTS:
    md += [f'## {p["name"]} — {p["tag"]}', f'**Built for:** {p["who"]}  ', f'**Pricing:** {p["price"]}', '', '**User workflow**']
    md += [f'{i}. {s}' for i, s in enumerate(p['flow'], 1)]
    md += ['', f'- **Saves money:** {p["money"]}', f'- **Wins more business:** {p["business"]}', f'- **Increases productivity:** {p["productivity"]}', f'- **Human in the loop:** {p["human"]}', '']
os.environ.get('OVERVIEWS_OUT') and open(os.environ['OVERVIEWS_OUT'], 'w').write('\n'.join(md))  # business doc lives outside the public repo
print(len(slugs), 'industry pages;', len(PRODUCTS), 'products')
