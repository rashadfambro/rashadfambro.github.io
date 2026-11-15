"""v18: review polish (Google + ChatGPT, Nov 14 evening). Applied to both index.html and staging/index.html.
Bundle cards show holiday prices, checkout opens at the top with focus on its title, no sideways scroll at 430 px,
sale-banner link never wraps its arrow, estimator counts usage for every tool in a bundle (and offers the Hotel bundle)."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def rep(t, a, b):
    assert t.count(a) == 1, f"{t.count(a)}x: {a[:100]}"
    return t.replace(a, b)

for rel in sys.argv[1:] or ['index.html', 'staging/index.html']:
    p = os.path.join(ROOT, rel); t = open(p).read()
    for name, price, parts, save in [('ChatDesk + BookDesk', 2500, '1500,1500', 500), ('GuestDesk + HousekeepingDesk + WorkOrderDesk', 8000, '3500,3500,3500', 2500),
                                     ('WorkOrderDesk + PackageDesk + ChatDesk', 5500, '3500,2000,1500', 1500)]:
        t = rep(t, f'<b>{name} setup for ${price:,}</b> (save ${save:,})',
                f'<b>{name} setup for <span class="bprice" data-price="{price}" data-sum="{parts}">${price:,}</span></b> (save <span class="bsave">${save:,}</span>)')
    t = rep(t, '$("#buyModal").hidden=false; setTimeout(()=>$("#buy_name").focus(),30);',
            '$("#buyModal").hidden=false; $("#buyModal").scrollTop=0; $("#buyForm").scrollTop=0; setTimeout(()=>{ $("#buyForm").scrollTop=0; $("#buyTitle").focus({preventScroll:true}); },30);')
    t = rep(t, '<h3 id="buyTitle">', '<h3 id="buyTitle" tabindex="-1">')
    t = rep(t, '@media(max-width:420px){.profile li.nowrap{white-space:normal}}', '@media(max-width:640px){.profile li.nowrap{white-space:normal;font-size:inherit}}')
    t = rep(t, '.salebar .sale-l2{display:block;margin-top:2px}', '.salebar .sale-l2{display:block;margin-top:2px}.salebar .sale-l2 a{white-space:nowrap}#buyTitle:focus{outline:none}')
    t = rep(t, '  return {setup: it.price||0, monthly, tools: it.count||1};',
            '  return {setup: it.price||0, monthly, tools: it.count||({bundle:2, propbundle:3, hotelbundle:3}[id])||1};')
    t = rep(t, '<option value="propbundle">Property Management Bundle</option></select>',
            '<option value="propbundle">Property Management Bundle</option><option value="hotelbundle">Hotel Operations Bundle (1 property)</option></select>')
    t = rep(t, '/* ---------- monthly plan cards ---------- */',
            '''function bundleSalePrices(){ if(!saleActive()) return;
  $$(".bprice").forEach(el=>{ const p=+el.dataset.price, s=saleAmt(p), sum=el.dataset.parts.split(",").reduce((a,v)=>a+saleAmt(+v),0);
    el.innerHTML=`<s class="was">${money(p)}</s> ${money(s)}`; const sv=el.closest("p").querySelector(".bsave"); if(sv) sv.textContent=money(sum-s); }); }
bundleSalePrices();
/* ---------- monthly plan cards ---------- */''')
    open(p, 'w').write(t)
    print('v18 applied to', rel)
