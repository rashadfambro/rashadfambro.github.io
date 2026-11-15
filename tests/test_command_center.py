"""Command Center (private Apps Script dashboard) checks.

CC01  summarize_ computes alerts, pipeline, clients and finances correctly from sample data.
CC02  Every callable server function checks that the signed-in user is the owner; no secrets in code.
CC03  The page renders every tab from sample data, escapes hostile text, and calls the right server
      functions for license actions, status changes, agent requests and ledger entries.
"""
import json, re, shutil, subprocess, pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CODE = ROOT / "command-center" / "Code.gs"
INDEX = ROOT / "command-center" / "Index.html.txt"
NODE = shutil.which("node")
pytestmark = [pytest.mark.regression]

NOW = "2026-11-20T17:00:00.000Z"
XSS = '<img src=x onerror="window.__xss=1">'
SAMPLE = {
    "leads": [
        {"_row": 2, "Received": "2026-11-19T10:00:00Z", "Status": "New", "Score": 72, "Form": "audit", "Business": "Glow Studio", "Email": "glow@example.com"},
        {"_row": 3, "Received": "2026-11-10T10:00:00Z", "Status": "Won", "Score": 50, "Form": "trial", "Business": XSS, "Email": "bx@example.com"},
        {"_row": 4, "Received": "2026-11-11T10:00:00Z", "Status": "Replied", "Score": 30, "Form": "website", "Business": "Sun Auto", "Email": "sun@example.com"},
    ],
    "prospects": [{"_row": 2, "Business": "702 PlumbAIR", "City": "Henderson", "Status": "Contacted"}],
    "licenses": [
        {"_row": 2, "Key": "RF-20261108-ABC123", "Tools": "salon", "Business": "Glow Studio", "Status": "Trial", "Plan": "Trial", "Ends / paid through": "2026-11-22T00:00:00Z"},
        {"_row": 3, "Key": "RFL-20261215-DEF456", "Tools": "property,package,chat", "Business": "Sunrise Apts", "Status": "Active", "Plan": "Growth (Founding)", "Ends / paid through": "2026-12-15T00:00:00Z"},
        {"_row": 4, "Key": "RFL-20261101-GHI789", "Tools": "service", "Business": "Sun Auto", "Status": "Past due", "Plan": "Essentials", "Ends / paid through": "2026-11-01T00:00:00Z"},
    ],
    "orders": [
        {"Received": "2026-11-05T10:00:00Z", "Order ID": "O1", "Status": "Paid", "Business": "Sunrise Apts", "Amount due": 4950},
        {"Received": "2026-11-19T10:00:00Z", "Order ID": "O2", "Status": "Awaiting payment", "Business": "Glow Studio", "Item": "BookDesk", "Amount due": 1350},
        {"Received": "2026-03-01T10:00:00Z", "Order ID": "O0", "Status": "Paid", "Business": "Old", "Amount due": 500},
    ],
    "finance": [
        {"Date": "2026-11-03T12:00:00Z", "Type": "Expense", "Category": "Software", "Amount": -40},
        {"Date": "2026-11-04T12:00:00Z", "Type": "Income", "Category": "Consulting", "Amount": 750},
    ],
    "requests": [
        {"Time": "2026-11-19T10:00:00Z", "Request ID": "Q1", "Agent": "project-manager", "Request": "Weekly status for Sunrise", "Status": "Done", "Updated": "2026-11-20T08:00:00Z"},
        {"Time": "2026-11-20T09:00:00Z", "Request ID": "Q2", "Agent": "release-manager", "Request": "Ship BookDesk 1.2", "Status": "New", "Updated": "2026-11-20T09:00:00Z"},
    ],
    "log": [],
}
CFG = {"PLAN_PRICES": {"std": {"Essentials": 50, "Growth": 90, "Pro": 150}, "prop": {"Essentials": 90, "Growth": 150, "Pro": 250}},
       "PROPERTY_TOOLS": ["property", "resort", "housekeeping", "package"]}


@pytest.mark.skipif(not NODE, reason="node not installed")
def test_CC01_summary_math(tmp_path):
    src = CODE.read_text()
    fn = re.search(r"function summarize_[\s\S]*?\n}\n", src).group(0)
    h = tmp_path / "s.js"
    h.write_text(fn + f"\nconsole.log(JSON.stringify(summarize_({json.dumps(SAMPLE)}, {json.dumps(NOW)}, {json.dumps(CFG)})));")
    s = json.loads(subprocess.run([NODE, str(h)], capture_output=True, text=True, check=True).stdout)
    kinds = [a["kind"] for a in s["alerts"]]
    assert kinds[0] == "Lead" or kinds[0] == "Past due"            # high-priority alerts first
    assert {"Lead", "Trial ending", "Past due", "Unpaid order", "Agent reply"} <= set(kinds), kinds
    assert s["pipeline"] == {"New": 1, "Won": 1, "Replied": 1}
    assert s["counts"]["activeClients"] == 2 and s["counts"]["trials"] == 1 and s["counts"]["founding"] == 1 and s["counts"]["openRequests"] == 1
    # Sunrise: Growth on 2 property tools (150 each) + ChatDesk (90) = 390; Sun Auto Essentials 50
    f = s["finance"]
    assert f["mrrEstimate"] == 440, f
    assert f["revenueMonth"] == 4950 + 750 and f["revenueYear"] == 4950 + 750 + 500
    assert f["costsMonth"] == 40 and f["profitYear"] == 4950 + 750 + 500 - 40
    assert s["conversion"] == 33


def test_CC02_security_rules_in_code():
    src = CODE.read_text()
    assert re.search(r"function doGet\(\)\s*\{\s*if \(!isOwner_\(\)\)", src)
    public = re.findall(r"^function ([A-Za-z]+)\(", src, re.M)
    exempt = {"doGet", "dailyBrief", "setupCommandCenter"}          # triggers / editor-only
    for name in public:
        if name in exempt:
            continue
        body = re.search(r"^function " + name + r"\([^)]*\)\s*\{([\s\S]*?)\n\}", src, re.M).group(1)
        assert "guard_()" in body.split("\n")[1], f"{name} must call guard_() first"
    assert "XFrameOptionsMode.DENY" in src
    assert not re.search(r"(sk-ant-|AKfyc[\w-]{20,}|ADMIN_TOKEN\s*[:=]\s*['\"][^'\"]+)", src), "secrets must live in Script properties"
    html = INDEX.read_text()
    assert ".innerHTML" in html and "esc(" in html and "eval(" not in html


STUB = """
<script>
window.__calls = []; window.confirm = () => true;
const DATA = %s;
function runner(){ let ok = ()=>{}, no = ()=>{}, p;
  const r = { withSuccessHandler(f){ ok=f; return p; }, withFailureHandler(f){ no=f; return p; } };
  p = new Proxy(r, { get(t, k){ if (k in t) return t[k]; return (...a) => { window.__calls.push([k, ...a]); setTimeout(() => ok(k === "getDashboard" ? DATA : true), 0); }; } });
  return p;
}
window.google = { script: { get run(){ return runner(); } } };
</script>
"""


def test_CC03_page_renders_and_wires_actions(make_page, tmp_path):
    data = {
        "summary": {"alerts": [{"level": "high", "kind": "Past due", "text": XSS, "ref": "k"}], "pipeline": {"New": 1, "Won": 1},
                    "counts": {"newLeads": 1, "trials": 1, "activeClients": 2, "openRequests": 1, "prospects": 1, "leads": 3, "founding": 1},
                    "finance": {"mrrEstimate": 440, "revenueMonth": 5700, "revenueYear": 6200, "costsMonth": 40, "costsYear": 40, "profitYear": 6160}, "conversion": 33},
        "leads": SAMPLE["leads"], "prospects": SAMPLE["prospects"], "licenses": SAMPLE["licenses"], "orders": SAMPLE["orders"],
        "finance": SAMPLE["finance"], "requests": SAMPLE["requests"], "log": [{"Time": NOW, "Source": "command-center", "Action": "setup", "Target": XSS, "Result": "ok"}],
        "calendar": [{"title": "Audit: Glow Studio", "start": NOW, "end": NOW, "where": "Zoom"}],
        "inbox": [{"from": "Calendly", "subject": "New event: Glow Studio", "date": NOW, "business": True, "link": "https://mail.google.com/x"}],
        "agents": ["chief-of-staff", "project-manager", "release-manager"], "generated": NOW,
    }
    html = INDEX.read_text().replace("<head>", "<head>" + STUB % json.dumps(data), 1)
    f = tmp_path / "cc.html"; f.write_text(html)
    w = make_page(width=1200); pg = w.page
    pg.goto(f.as_uri()); pg.wait_for_selector(".kpi")
    assert "440" in pg.inner_text("main") and "Audit: Glow Studio" in pg.inner_text("main")
    assert "Today (1)" in pg.inner_text("#tabs")
    for t, expect in [("pipeline", "Glow Studio"), ("clients", "Record payment"), ("finance", "Ledger"), ("agents", "Send to agent team"), ("log", "setup")]:
        pg.click(f'[data-tab="{t}"]'); pg.wait_for_timeout(50)
        assert expect in pg.inner_text("main"), t
    assert pg.evaluate("window.__xss") is None and pg.locator("main img").count() == 0
    # license action → licenseAction(action, key)
    pg.click('[data-tab="clients"]'); pg.click('[data-act="pause"][data-key="RFL-20261215-DEF456"]'); pg.wait_for_timeout(50)
    # lead status → setLeadStatus(row, status)
    pg.click('[data-tab="pipeline"]'); pg.select_option('[data-lead="4"]', "Booked"); pg.wait_for_timeout(50)
    # agent request → addRequest(agent, priority, topic, text)
    pg.click('[data-tab="agents"]'); pg.select_option('#reqForm [name=agent]', "release-manager"); pg.fill('#reqForm [name=topic]', "BookDesk")
    pg.fill('#reqForm textarea', "Release BookDesk 1.2 to staging"); pg.click('#reqForm button[type=submit]'); pg.wait_for_timeout(50)
    # ledger → addFinance({...})
    pg.click('[data-tab="finance"]'); pg.fill('#finForm [name=amount]', "29"); pg.fill('#finForm [name=category]', "Software"); pg.click('#finForm button[type=submit]'); pg.wait_for_timeout(50)
    calls = pg.evaluate("window.__calls")
    names = [c[0] for c in calls]
    assert ["licenseAction", "pause", "RFL-20261215-DEF456"] in calls
    assert ["setLeadStatus", 4, "Booked"] in calls
    assert ["addRequest", "release-manager", "Normal", "BookDesk", "Release BookDesk 1.2 to staging"] in calls
    fin = [c for c in calls if c[0] == "addFinance"][0][1]
    assert fin["type"] == "Expense" and fin["amount"] == "29" and fin["category"] == "Software"
    assert names.count("getDashboard") >= 2          # reloads after each change
    assert not w.errors, w.errors
    pg.set_viewport_size({"width": 390, "height": 800})
    assert pg.evaluate("document.documentElement.scrollWidth <= 392")
