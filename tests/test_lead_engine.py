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
    for s in subjects + [owner]:  # emoji never reach a subject (send_ also cleans them)
        assert not re.search(r"[\U0001F300-\U0001FAFF☀-➿↻]", s), s


def test_LE07_every_email_is_clean_and_correct():
    """Runs the real Code.gs against a simulated Sheet/Gmail (tests/email_harness.js) and checks every email it sends."""
    out = subprocess.run([NODE, str(ROOT / "tests" / "email_harness.js"), str(CODE)], capture_output=True, text=True, check=True).stdout
    mails = json.loads(out)["mails"]
    labels = {m["label"] for m in mails}
    assert {"lead: audit", "lead: project", "lead: order", "lead: trial", "licenses: daily run", "license: activated",
            "license: renewed", "license: canceled", "license: resend", "follow-ups", "weekly digest"} <= labels, labels
    for m in mails:
        for f in ("subject", "body"):
            s = m[f]
            assert re.fullmatch(r"[\x09\x0a\x0d\x20-\x7e]*", s), (m["label"], f, [c for c in s if ord(c) > 126][:5])
            for bad in ("undefined", "null", "NaN", "[object", "Invalid Date", "  ,"):
                assert bad not in s, (m["label"], f, bad)
        assert 5 < len(m["subject"]) <= 110 and m["subject"] == m["subject"].strip(), m["subject"]
        if m["to"] != "rashadfambro@gmail.com" and m["kind"] == "email":
            assert "Rashad Fambro" in m["body"] and "https://rashadfambro.github.io/" in m["body"], m["subject"]
    subj = lambda label: [m["subject"] for m in mails if m["label"] == label]
    # orders get an order confirmation, not the audit reply; trials and orders get no audit draft or audit follow-ups
    assert any(s.startswith("Order received") for s in subj("lead: order"))
    assert not any(m["kind"] == "draft" for m in mails if m["label"] in ("lead: order", "lead: trial"))
    fu = [m["to"] for m in mails if m["label"] == "follow-ups"]
    assert "ana@example.com" not in fu and "tom@example.com" not in fu and fu.count("maria@example.com") == 3
    daily = subj("licenses: daily run")
    for want in ("trial ends in 3 days", "trial ends in 1 day", "trial has ended", "plan renews", "Past due:", "license is paused"):
        assert any(want in s for s in daily), (want, daily)
    alerts = [m["subject"] for m in mails if m["to"] == "rashadfambro@gmail.com"]
    assert any(s.startswith("[Lead] ") for s in alerts) and any(s.startswith("[Trial] ") for s in alerts) and any(s.startswith("[Order] ") for s in alerts)


def test_LE08_payments_status_sync_admin_and_backups():
    """Payment emails are matched to orders and issue a license; statuses move forward from Gmail activity
    (never backward, never touching Lost); bad admin tokens are refused and logged; backups keep 30 copies."""
    out = subprocess.run([NODE, str(ROOT / "tests" / "email_harness.js"), str(CODE)], capture_output=True, text=True, check=True).stdout
    d = json.loads(out); r = d["result"]
    assert r["orderStatus"] == "Paid" and r["orderKey"].startswith("RFL-") and r["licenseActive"]
    assert r["checkActive"]["valid"] and r["checkActive"]["status"] == "Active"
    pay = [m for m in d["mails"] if m["label"] == "payments"]
    assert any(m["to"] == "ana@example.com" and "link for Glow Studio" in m["subject"] for m in pay)
    assert any(m["to"] == "rashadfambro@gmail.com" and "match it by hand ($999.00)" in m["subject"] for m in pay)
    assert r["statuses"] == {"Replied Co": "Replied", "Booked Co": "Booked", "Proposal Co": "Proposal sent", "Stop Co": "Do not contact",
                             "Sent Co": "Contacted", "Lost Co": "Lost", "Quiet Co": "Not contacted"}
    assert r["adminBad"] == {"ok": False, "error": "unauthorized"} and r["adminLogged"]
    assert r["backups"] == {"kept": 30, "trashed": 2}


def test_LE09_staging_test_environment_is_isolated():
    """env:"staging" requests (staging site, local runs, staging apps) write only to TEST tabs, never email a
    customer (every email goes to the owner, tagged [TEST to ...]), and still get the daily reminder checks."""
    out = subprocess.run([NODE, str(ROOT / "tests" / "email_harness.js"), str(CODE)], capture_output=True, text=True, check=True).stdout
    t = json.loads(out)["result"]["test"]
    r = json.loads(out)["result"]
    assert r["testPost"]["ok"]
    assert {"TEST Leads", "TEST Licenses", "TEST Orders"} <= set(t["tabs"]), t["tabs"]
    assert t["prodUnchanged"] and t["allToOwner"] and t["tagged"] >= 3 and t["reminder"]
    assert t["check"] is True and t["checkInProd"] == "Unknown"      # production has no record of test licenses
    assert t["cleared"]
