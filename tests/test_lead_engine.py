"""Lead engine (Apps Script) checks: syntax, and that the links it emails are accepted by the tool apps.

LE01  Code.gs parses as JavaScript.
LE02  trialKey_/licenseKey_ in Code.gs equal trialKey/licenseKey in every prototype.
LE03  A trial link built by Code.gs opens as a valid branded trial in the real app (browser).
LE04  A license link built by Code.gs opens as a licensed Starter edition in the real app (browser).
"""
import json, os, re, shutil, subprocess, pathlib, datetime
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CODE = ROOT / "lead-engine" / "Code.gs"
NODE = shutil.which("node")
pytestmark = [pytest.mark.regression, pytest.mark.skipif(not NODE, reason="node not installed")]

HARNESS = r"""
const fs=require('fs');
const src=fs.readFileSync(process.argv[2],'utf8');
const CFG={PROTOTYPES_URL:'https://rashadfambro.github.io/prototypes/'};
const m=src.match(/function trialHash_[\s\S]*?\nfunction ymd_/)[0].replace(/\nfunction ymd_$/,'');
const tools=src.match(/const TOOL_IDS[\s\S]*?const BUNDLE_TOOLS[^;]*;/)[0];
const helpers=src.match(/function toolsFrom_[\s\S]*?\nfunction toolNames_/)[0].replace(/\nfunction toolNames_$/,'');
const app=src.match(/function appLink_[\s\S]*?\n}\n/)[0];
eval(tools+m+helpers+app+';globalThis.T={trialKey_,licenseKey_,toolsFrom_,appLink_}');
const cases=JSON.parse(process.argv[3]);
console.log(JSON.stringify(cases.map(c=>c.fn==='link'?T.appLink_(c.kind,c.tools,c.biz,c.date,'#2f7fe0'):c.fn==='tools'?T.toolsFrom_(c.text):T[c.fn](...c.args))));
"""

def run_gs(cases, tmp_path):
    h = tmp_path / "h.js"; h.write_text(HARNESS)
    out = subprocess.run([NODE, str(h), str(CODE), json.dumps(cases)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)

def app_fn(page, tmp_path, expr):
    html = (ROOT / page).read_text()
    js = "\n".join(re.findall(r"^function (?:trialHash|trialKey|licenseKey)\(.*$", html, re.M))
    h = tmp_path / "a.js"; h.write_text(js + "\nconsole.log(JSON.stringify(" + expr + "))")
    return json.loads(subprocess.run([NODE, str(h)], capture_output=True, text=True, check=True).stdout)

def test_LE01_syntax():
    subprocess.run([NODE, "-e", f"new Function(require('fs').readFileSync({json.dumps(str(CODE))},'utf8'))"], check=True)

@pytest.mark.parametrize("page", sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "prototypes").glob("*.html") if p.name != "index.html"))
def test_LE02_key_parity(page, tmp_path):
    args = [["property,package,chat", "Sunrise Apartments ", "2026-11-15"], ["chat", "Café Olé", "2027-01-31"]]
    gs = run_gs([{"fn": "trialKey_", "args": a} for a in args] + [{"fn": "licenseKey_", "args": a} for a in args], tmp_path)
    app = app_fn(page, tmp_path, "[" + ",".join([f"trialKey(...{json.dumps(a)})" for a in args] + [f"licenseKey(...{json.dumps(a)})" for a in args]) + "]")
    assert gs == app

def test_LE02b_tools_from_package_names(tmp_path):
    got = run_gs([{"fn": "tools", "text": t} for t in [
        "WorkOrderDesk (Essentials plan)", "Property Management Bundle: WorkOrderDesk + PackageDesk + ChatDesk setup",
        "Launch Bundle: ChatDesk + BookDesk setup", "Hotel Operations Bundle: GuestDesk + HousekeepingDesk + WorkOrderDesk setup", "LeadDesk"]], tmp_path)
    assert got == ["property", "property,package,chat", "chat,salon", "resort,housekeeping,property", "service"]

def _open(make_page, base_url, link):
    w = make_page()
    w.page.goto(link.replace("https://rashadfambro.github.io/prototypes/", base_url + "prototypes/"))
    w.page.wait_for_selector(".banner"); w.page.wait_for_timeout(200)
    text = w.page.inner_text(".banner"); assert not w.errors, w.errors
    return text

def test_LE03_trial_link_opens(make_page, base_url, tmp_path):
    start = datetime.date.today().isoformat()
    link = run_gs([{"fn": "link", "kind": "trial", "tools": "property", "biz": "Sunrise Apartments", "date": start}], tmp_path)[0]
    text = _open(make_page, base_url, link["url"])
    assert "Sunrise Apartments" in text and "isn't valid" not in text and "days left" in text

def test_LE04_license_link_opens(make_page, base_url, tmp_path):
    until = (datetime.date.today() + datetime.timedelta(days=31)).isoformat()
    link = run_gs([{"fn": "link", "kind": "license", "tools": "chat,salon", "biz": "Glow Studio", "date": until}], tmp_path)[0]
    assert "suite.html" in link["url"]
    text = _open(make_page, base_url, link["url"])
    assert "licensed to Glow Studio" in text and "isn't valid" not in text


STATUS_HARNESS = r"""
const fs=require('fs'); const src=fs.readFileSync(process.argv[2],'utf8');
const pick=(re)=>{const m=src.match(re); if(!m) throw new Error('missing '+re); return m[0];};
const fn=pick(/function detectStatus_[\s\S]*?\n}\n/), rank=pick(/const STATUS_RANK = [^;]*;/);
const cases=JSON.parse(process.argv[3]); const out=[];
for (const c of cases) {
  globalThis.GmailApp={search:(q)=>c.hits.some(h=>q.indexOf(h)>=0)?[1]:[]};
  globalThis.Utilities={formatDate:()=> '2026/11/01'}; globalThis.Session={getScriptTimeZone:()=> 'UTC'};
  const detectStatus_=eval('('+fn.replace('function detectStatus_','function')+')');
  out.push(detectStatus_(c.email,new Date(),c.won||{},c.trial||{}));
}
const STATUS_RANK=eval('('+rank.replace(/^const STATUS_RANK = /,'').replace(/;$/,'')+')'); console.log(JSON.stringify({out, rank:STATUS_RANK}));
"""

def test_LE05_pipeline_status_detection(tmp_path):
    h = tmp_path / "s.js"; h.write_text(STATUS_HARNESS)
    e = "owner@example.com"
    cases = [
        {"email": e, "hits": [], "won": {e: True}},
        {"email": e, "hits": ["(STOP OR unsubscribe)"]},
        {"email": e, "hits": ["subject:proposal"]},
        {"email": e, "hits": [], "trial": {e: True}},
        {"email": e, "hits": ["from:calendly.com"]},
        {"email": e, "hits": ["-from:me"]},
        {"email": e, "hits": ["in:sent to:" + e + " after:"]},
        {"email": e, "hits": []},
    ]
    res = json.loads(subprocess.run([NODE, str(h), str(CODE), json.dumps(cases)], capture_output=True, text=True, check=True).stdout)
    assert res["out"] == ["Won", "Do not contact", "Proposal sent", "Trial", "Booked", "Replied", "Contacted", ""]
    r = res["rank"]
    assert r["New"] < r["Contacted"] < r["Replied"] < r["Booked"] < r["Trial"] < r["Proposal sent"] < r["Won"]

def test_LE06_subjects_are_plain_text():
    src = CODE.read_text()
    subjects = re.findall(r"(?:sendEmail|mail_)\([^,]+,\s*('(?:[^'\\]|\\.)*'|[^,]+),", src)
    owner = re.search(r"function notifyOwner_[\s\S]*?const subject = ([^;]+);", src).group(1)
    for s in subjects + [owner]:
        assert not re.search(r"[\U0001F300-\U0001FAFF☀-➿↻]", s), s
