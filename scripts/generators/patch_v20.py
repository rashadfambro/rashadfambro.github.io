"""v20 (staging first): Nov 15 review fixes + in-app reminders + online license check.
- Bundle savings say what they compare against ("vs. buying each tool separately at today's prices").
- Long cash-only paybacks read in years ("About 33 years").
- FAQ: "Tap Order now" (the button label), not "Tap Buy".
- Tool apps: trial banner turns amber in the last 3 days and shows a once-a-day reminder dialog; licensed apps
  show a renewal note in the last 5 days.
- Tool apps: if the lead engine URL is set (DESK_BACKEND), the app checks the license/trial status online, so
  Paused or Canceled licenses lock right away; offline or not set = works as before."""
import os, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def rep(t, a, b, many=False):
    n = t.count(a)
    assert n >= 1 and (many or n == 1), f"{n}x: {a[:110]}"
    return t.replace(a, b)

# ---------- index.html (root; synced to staging by the release script)
p = os.path.join(ROOT, 'index.html'); t = open(p).read()
t = rep(t, '(save <span class="bsave">', '(save <span class="bsave">', many=True)
t = re.sub(r'\(save (<span class="bsave">[^<]*</span>)\)', r'(save \1 vs. buying each tool separately)', t)
t = rep(t, '''    el.innerHTML=`<s class="was">${money(p)}</s> ${money(s)}`; const sv=el.closest("p").querySelector(".bsave"); if(sv) sv.textContent=money(sum-s); }); }''',
        '''    el.innerHTML=`<s class="was">${money(p)}</s> ${money(s)}`; const sv=el.closest("p").querySelector(".bsave"); if(sv){ sv.textContent=money(sum-s); sv.title="Compared with buying each tool separately at today's holiday prices"; } }); }''')
t = rep(t, '''  $("#roiCashPayback").textContent = r.cash<=0 ? "No cash payback at these inputs" : (pl.setup/r.cash)<1 ? "Under 1 month" : `${(pl.setup/r.cash).toFixed(1)} months`;''',
        '''  const cm = r.cash>0 ? pl.setup/r.cash : 0;
  $("#roiCashPayback").textContent = r.cash<=0 ? "No cash payback at these inputs" : cm<1 ? "Under 1 month" : cm<=24 ? `${cm.toFixed(1)} months` : `About ${Math.round(cm/12)} years`;''')
t = rep(t, 'Yes. Tap <b>Buy</b> on any product or package,', 'Yes. Tap <b>Order now</b> on any tool, or <b>Order this bundle</b> on a package,')
open(p, 'w').write(t)
print('v20 index applied')

# ---------- tool apps (generator)
g = os.path.join(ROOT, 'scripts/generators/gen_prototypes.py'); s = open(g).read()
s = rep(s, '.banner.trial{background:#e8f6ef;border-color:#b7e2cc;color:#0b4f36}',
        '.banner.trial{background:#e8f6ef;border-color:#b7e2cc;color:#0b4f36}.banner.trial.soon{background:#fff4e0;border-color:#f3d39a;color:#6b4100}')
s = rep(s, 'const TRIAL_DAYS=14;',
        'const TRIAL_DAYS=14;\nconst DESK_BACKEND="";  // lead-engine web app URL (…/exec). Empty = no online check.\n'
        'function remindOnce(key,html){try{const k="proto-remind-"+key+"-"+new Date().toISOString().slice(0,10);if(localStorage.getItem(k))return;localStorage.setItem(k,"1")}catch(e){return}\n'
        ' if(document.body.classList.contains("embedded"))return;const o=document.createElement("div");o.id="trialRemind";o.style.cssText="position:fixed;inset:0;background:rgba(13,26,45,.55);display:grid;place-items:center;z-index:19;padding:20px";\n'
        ' o.innerHTML=`<div class="card" role="dialog" aria-modal="true" aria-labelledby="trH" style="max-width:480px">${html}<div class="row"><a class="btn" href="../index.html#pricing">Choose a plan</a><button class="btn alt" type="button" id="trClose">Remind me tomorrow</button></div></div>`;\n'
        ' document.body.appendChild(o);$("#trClose").onclick=()=>o.remove()}\n'
        'async function onlineCheck(kind,key){if(!DESK_BACKEND||!key)return;try{const r=await fetch(DESK_BACKEND+"?check="+encodeURIComponent(kind)+"&key="+encodeURIComponent(key),{cache:"no-store"});const j=await r.json();\n'
        ' if(j&&j.ok&&(j.status==="Paused"||j.status==="Canceled")){const o=document.createElement("div");o.id="trialEnd";o.innerHTML=`<div class="card" role="dialog" aria-modal="true" aria-labelledby="psH"><h2 id="psH">This License Is ${j.status==="Paused"?"Paused":"Canceled"}</h2><p class="small">Your data is safe on this device. Contact Rashad to turn it back on, or download a backup.</p><div class="row"><a class="btn" href="../index.html#contact">Contact Rashad</a><button class="btn alt" type="button" id="psExport">Download backup</button></div></div>`;document.body.appendChild(o);$("#psExport").onclick=exportData}}catch(e){}}')
s = rep(s, ' if(left>0){$("#btext").innerHTML=`<b>Free ${TRIAL_DAYS}-day trial for ${esc(t.biz)}</b> · ${left} day${left===1?"":"s"} left',
        ' if(left>0&&left<=3){b.classList.add("soon");remindOnce("trial",`<h2 id="trH">Your Trial Ends in ${left} Day${left===1?"":"s"}</h2><p class="small">Choose a plan to keep using it with ${esc(t.biz)}\'s data, or let it end. Nothing is charged automatically, and you can download your data anytime.</p>`)}\n'
        ' onlineCheck("trial",t.key);\n'
        ' if(left>0){$("#btext").innerHTML=`<b>Free ${TRIAL_DAYS}-day trial for ${esc(t.biz)}</b> · ${left} day${left===1?"":"s"} left')
s = rep(s, ' document.body.classList.add("licensed");const left=licenseDaysLeft(l);',
        ' document.body.classList.add("licensed");const left=licenseDaysLeft(l);onlineCheck("license",l.key);if(left>=0&&left<=5)b.classList.add("soon");')
s = rep(s, '`<b>Starter edition · licensed to ${esc(l.biz)}</b> · renews ${esc(l.until)} · ',
        '`<b>Starter edition · licensed to ${esc(l.biz)}</b> · ${left<=5?`<b>renews in ${left} day${left===1?"":"s"} (${esc(l.until)})</b>`:`renews ${esc(l.until)}`} · ')
open(g, 'w').write(s)
print('v20 generator applied')
