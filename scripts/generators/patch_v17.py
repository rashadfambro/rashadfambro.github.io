"""v17 (staging): Starter edition, so every tool can be bought and delivered now.
Starter = the branded, licensed tool app (data on the client's device, backup/restore, approved messages copied to send).
Connected = live texting, email and calendar in the client's own accounts, built to order in 3–8 weeks.
Run once from the repo root against index.html: python3 scripts/generators/patch_v17.py"""
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def rep(t, a, b, many=False):
    n = t.count(a)
    assert n >= 1, f"missing: {a[:110]}"
    assert many or n == 1, f"{n}x: {a[:110]}"
    return t.replace(a, b)

p = os.path.join(ROOT, 'index.html'); t = open(p).read()

t = rep(t, 'status:"Prototype"', 'status:"Starter ready"', many=True)
t = rep(t, 'function isPilot(id){ if(id==="pilot") return true; const p=PRODUCTS.find(x=>x.id===id); return !!p && p.status!=="Live on this site"; }',
        'function isPilot(id){ return id==="pilot"; }')
t = rep(t, '<span class="eta">${p.status==="Live on this site"?"Ready now · about 1–2 weeks to launch":"Built to order · 3–8 weeks to launch"}</span>',
        '<span class="eta">${p.status==="Live on this site"?"Ready now · about 1–2 weeks to launch":"Starter edition in 1–3 business days · Connected edition in 3–8 weeks"}</span>')
t = rep(t, '${p.status==="Live on this site"?"Request order":"Request a pilot"}', 'Order now')
t = rep(t, '${p.id==="pilot"?"Request a pilot":"Request order"}', '${p.id==="pilot"?"Request a pilot":"Order now"}')
t = rep(t, 'style="margin-top:12px">Request this bundle</button>', 'style="margin-top:12px">Order this bundle</button>', many=True)
t = rep(t, 'style="margin-top:10px">Request this bundle</button>', 'style="margin-top:10px">Order this bundle</button>')
t = rep(t, '$("#buyEyebrow").textContent = trial ? "Free Trial" : pilot ? "Request a Pilot" : "Request an Order";',
        '$("#buyEyebrow").textContent = trial ? "Free Trial" : pilot ? "Request a Pilot" : "Order Online";\n'
        '  const prod = PRODUCTS.find(x=>x.id===id), bundleIds = {bundle:1, propbundle:1, hotelbundle:1};\n'
        '  $("#deliveryNote").innerHTML = trial||pilot ? "" : prod && prod.status==="Live on this site" ? "<b>What you get:</b> ChatDesk set up on your website and branded for your business, typically live in 1–2 weeks."\n'
        '    : (prod || bundleIds[id]) ? "<b>What you get:</b> the <b>Starter edition</b>, branded for your business, within 1–3 business days of payment" + (bundleIds[id] ? ", with every tool in one Desk Suite app" : "") + ". Then the <b>Connected edition</b> (live texting, email and calendar in your own accounts) in 3–8 weeks, checked against a written acceptance checklist with your team." : "";\n'
        '  $("#deliveryNote").hidden = !$("#deliveryNote").innerHTML;')
t = rep(t, '<p class="hint" id="pilotNote" hidden>', '<p class="hint" id="deliveryNote" hidden></p>\n    <p class="hint" id="pilotNote" hidden>')
t = rep(t, 'No payment now. I’ll reply within one business day to confirm scope and a launch date (built-to-order tools take 3–8 weeks, including testing with your team).',
        'No payment now. I’ll reply within one business day to confirm scope and a launch date (custom builds typically take 3–8 weeks, including testing with your team).')

t = rep(t, '<p class="lede">Start with the tool that matches your biggest bottleneck. Each one is a working prototype I tailor to your business, so you’re not paying to start from scratch. All demos use fictional data.</p>',
        '<p class="lede">Start with the tool that matches your biggest bottleneck. Every tool is available now as a <b>Starter edition</b>, branded for your business within days, and grows into the <b>Connected edition</b> that works inside your own accounts. Related tools run together as one Desk Suite. All demos use fictional data.</p>')

t = rep(t, '<details><summary>How Long Until My Tool Is Live?</summary><p>ChatDesk is ready now and typically launches in 1–2 weeks. Tools marked “Built to order” are finished for your business when you sign: 3–8 weeks to launch, including 1–2 weeks of testing with your team. Your trial workspace shows exactly how it will work while it’s being built, and founding clients get 25% off for helping shape it.</p></details>',
        '<details><summary>How Long Until My Tool Is Live?</summary><p>ChatDesk typically launches on your website in 1–2 weeks. Every other tool starts with the <b>Starter edition</b>, branded for your business, within 1–3 business days of payment. The <b>Connected edition</b>, with live texting, email, and calendar in your own accounts, follows in 3–8 weeks, including 1–2 weeks of testing with your team. Founding clients get 25% off for helping shape it.</p></details>\n'
        '      <details><summary>What Exactly Am I Buying?</summary><p>You can see it before you pay: your free trial workspace is the same app you receive, branded for your business. After you order, you get the <b>Starter edition</b> to use right away (it saves to your device, with one-click backup, and copies approved messages for you to send), plus a written scope and acceptance checklist for the <b>Connected edition</b>. The Connected edition is finished when it passes that checklist with your team. Packages run as one Desk Suite app, and you can add tools to it later.</p></details>')

open(p, 'w').write(t)
t = open(p).read()
t = rep(t, 'if(method==="Square") return CONFIG.squareLinks[`${id}:${amt}`]||"";', 'if(method==="Square") return CONFIG.squareLinks[`${id}:${amt}`]||CONFIG.squareLinks[String(amt)]||"";')
open(p, 'w').write(t)
print('v17 applied')
