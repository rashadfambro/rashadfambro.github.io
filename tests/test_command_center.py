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
    "prospects": [{"_row": 2, "Business": "702 PlumbAIR", "Contact": "Dee Ortiz", "Email": "dee@example.com", "Phone": "702-555-0142", "City": "Henderson", "Tools to pitch": "LeadDesk", "Status": "Contacted", "Notes": "2026-11-15 walked in · 2026-11-16 left a card"},
                  {"_row": 3, "Business": XSS, "Email": "x@example.com", "Status": "Not contacted"}],
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
    assert "XFrameOptionsMode.DENY" not in src and "XFrameOptionsMode.DEFAULT" in src   # DENY does not exist in Apps Script (it crashed the live page)
    assert not re.search(r"(sk-ant-|AKfyc[\w-]{20,}|ADMIN_TOKEN\s*[:=]\s*['\"][^'\"]+)", src), "secrets must live in Script properties"
    html = INDEX.read_text()
    assert ".innerHTML" in html and "esc(" in html and "eval(" not in html
    # Google's page server treats "//" inside an inline script as a comment and cuts the rest of the line,
    # which broke the live page once (a web address in an email template). No "//" anywhere in the script.
    script = html[html.index("<script>"):]
    assert "//" not in script, [l.strip()[:80] for l in script.splitlines() if "//" in l]


STUB = """
<script>
window.__calls = []; window.confirm = () => true;
const DATA = %s;
function runner(){ let ok = ()=>{}, no = ()=>{}, p;
  const r = { withSuccessHandler(f){ ok=f; return p; }, withFailureHandler(f){ no=f; return p; } };
  p = new Proxy(r, { get(t, k){ if (k in t) return t[k]; return (...a) => { window.__calls.push([k, ...a]); setTimeout(() => ok(k === "getDashboard" || k === "getExtras" ? DATA : true), 0); }; } });
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
    pg.goto(f.as_uri()); pg.wait_for_selector(".kpi"); pg.wait_for_selector("text=Audit: Glow Studio")
    assert "440" in pg.inner_text("main") and "Audit: Glow Studio" in pg.inner_text("main")
    assert "Today (1)" in pg.inner_text("#tabs")
    for t, expect in [("pipeline", "Glow Studio"), ("clients", "Record payment"), ("finance", "Ledger"), ("agents", "Send to agent team"), ("log", "setup")]:
        pg.click(f'[data-tab="{t}"]'); pg.wait_for_timeout(50)
        assert expect in pg.inner_text("main"), t
    assert pg.evaluate("window.__xss") is None and pg.locator("main img").count() == 0
    # license action → licenseAction(action, key)
    pg.click('[data-tab="clients"]'); pg.click('[data-act="pause"][data-key="RFL-20261215-DEF456"]'); pg.wait_for_timeout(50)
    # pipeline board: stages, search, open a prospect, edit, note, email, trial, move
    pg.click('[data-tab="pipeline"]'); pg.wait_for_timeout(50)
    board = pg.inner_text(".board")
    for stage in ("New", "Contacted", "Replied", "Booked", "Trial", "Proposal sent", "Client (Won)", "Closed"):
        assert stage in board, stage
    assert pg.locator('.pc[data-open="prospect"]').count() == 2 and pg.locator('.pc[data-open="lead"]').count() == 3
    pg.fill("#pq", "plumb"); pg.wait_for_timeout(50)
    assert pg.locator(".pc").count() == 1
    pg.click('.pc[data-open="prospect"][data-row="2"]'); pg.wait_for_timeout(50)
    d = pg.inner_text("#drawer")
    assert "702 PlumbAIR" in d and "Call 702-555-0142" in d and "left a card" in d
    assert pg.get_attribute('#drawer a[href^="tel:"]', "href") == "tel:7025550142"
    pg.fill('#cForm [name="Next step"]', "Demo Thursday"); pg.select_option('#cForm [name=Status]', "Booked"); pg.click('#cForm button[type=submit]'); pg.wait_for_timeout(50)
    pg.fill('#nForm [name=note]', "Owner wants pricing"); pg.click('#nForm button[type=submit]'); pg.wait_for_timeout(50)
    pg.select_option("#mTpl", "intro"); pg.wait_for_timeout(30)
    assert "702 PlumbAIR" in pg.input_value('#mForm [name=subject]') and "Hi Dee" in pg.input_value('#mForm textarea')
    pg.click('#mForm [data-mode="draft"]'); pg.wait_for_timeout(50)
    pg.select_option("#mTpl", "follow"); pg.wait_for_timeout(30)
    pg.click('#mForm [data-mode="send"]'); pg.wait_for_timeout(50)
    pg.click('#tForm button[type=submit]'); pg.wait_for_timeout(50)
    pg.click('#drawer [data-stage="Won"]'); pg.wait_for_timeout(50)
    pg.click("#dClose"); pg.fill("#pq", ""); pg.wait_for_timeout(50)
    pg.click("#addP"); pg.fill("#aForm [name=Business]", "New Walk-in Cafe"); pg.fill("#aForm [name=Phone]", "702-555-0199"); pg.click("#aForm button[type=submit]"); pg.wait_for_timeout(80)
    assert pg.is_hidden("#drawer")
    # drag a lead card to Booked
    pg.drag_and_drop('.pc[data-open="lead"][data-row="4"]', '[data-drop="Booked"]'); pg.wait_for_timeout(50)
    # agent request → addRequest(agent, priority, topic, text)
    pg.click('[data-tab="agents"]'); pg.select_option('#reqForm [name=agent]', "release-manager"); pg.fill('#reqForm [name=topic]', "BookDesk")
    pg.fill('#reqForm textarea', "Release BookDesk 1.2 to staging"); pg.click('#reqForm button[type=submit]'); pg.wait_for_timeout(50)
    # ledger → addFinance({...})
    pg.click('[data-tab="finance"]'); pg.fill('#finForm [name=amount]', "29"); pg.fill('#finForm [name=category]', "Software"); pg.click('#finForm button[type=submit]'); pg.wait_for_timeout(50)
    # themes: dark by default, switchable to 3 others, saved to the account
    assert pg.get_attribute("html", "data-theme") == "dark"
    for th in ("light", "midnight", "contrast"):
        pg.select_option("#theme", th); pg.wait_for_timeout(30)
        assert pg.get_attribute("html", "data-theme") == th
        bg = pg.evaluate("getComputedStyle(document.body).backgroundColor"); ink = pg.evaluate("getComputedStyle(document.body).color")
        assert bg != ink, th
    # live / test data switch
    pg.select_option("#env", "test"); pg.wait_for_timeout(50)
    assert pg.evaluate("document.body.classList.contains('testenv')") and "TEST" in pg.inner_text("#updated")
    calls = pg.evaluate("window.__calls")
    assert ["getDashboard", "test"] in calls
    assert ["setTheme", "contrast"] in calls
    names = [c[0] for c in calls]
    assert ["licenseAction", "pause", "RFL-20261215-DEF456", "live"] in calls
    ref = {"row": 2, "email": "dee@example.com"}
    saves = [c for c in calls if c[0] == "saveContact"]
    assert ["saveContact", "prospect", ref, {"Contact": "Dee Ortiz", "Business": "702 PlumbAIR", "Email": "dee@example.com", "Phone": "702-555-0142", "City": "Henderson", "Tools to pitch": "LeadDesk", "Next step": "Demo Thursday", "Industry": "", "Status": "Booked"}, "live"] in saves, saves
    assert ["saveContact", "prospect", ref, {"Status": "Won"}, "live"] in saves
    assert ["saveContact", "lead", {"row": 4, "email": "sun@example.com"}, {"Status": "Booked"}, "live"] in saves
    assert ["addNote", "prospect", ref, "Owner wants pricing", "live"] in calls
    em = [c for c in calls if c[0] == "emailContact"]
    assert [c[5] for c in em] == ["draft", "send"] and all(c[1] == "prospect" and c[2] == ref and "Hi Dee" in c[4] for c in em)
    assert ["startTrial", "prospect", ref, "LeadDesk", "live"] in calls
    add = [c for c in calls if c[0] == "addProspect"][0]
    assert add[1]["Business"] == "New Walk-in Cafe" and add[1]["Phone"] == "702-555-0199" and add[2] == "live"
    assert ["getDashboard", "live"] in calls
    assert ["addRequest", "release-manager", "Normal", "BookDesk", "Release BookDesk 1.2 to staging"] in calls
    fin = [c for c in calls if c[0] == "addFinance"][0][1]
    assert fin["type"] == "Expense" and fin["amount"] == "29" and fin["category"] == "Software"
    assert names.count("getDashboard") >= 2          # reloads after each change
    assert not w.errors, w.errors
    pg.set_viewport_size({"width": 390, "height": 800})
    assert pg.evaluate("document.documentElement.scrollWidth <= 392")


@pytest.mark.skipif(not NODE, reason="node not installed")
def test_CC04_server_functions_owner_and_stranger():
    """Runs command-center/Code.gs in a simulated Google account (tests/cc_harness.js)."""
    out = subprocess.run([NODE, str(ROOT / "tests" / "cc_harness.js"), str(CODE)], capture_output=True, text=True, check=True).stdout
    d = json.loads(out.strip().splitlines()[-1])
    e = d["errors"]
    assert d["page"] == "INDEX" and "Not Authorized" in d["strangerPage"]
    assert d["leadAfter"] == "Booked" and e["badStatus"] == "Unknown status" and e["badRow"] == "Bad row"
    assert d["requests"] == [["release-manager", "High", "New"], ["chief-of-staff", "Normal", "New"]] and e["emptyReq"]
    assert d["finance"] == [["Expense", -29]] and e["badAmount"]
    assert d["fetches"][0]["payload"] == {"type": "admin", "env": "production", "token": "x" * 32, "action": "pause", "key": "RFL-20261220-AAAAAA"}
    assert e["badKey"] == "Bad license key" and e["badAction"] == "Unknown action"
    assert d["themeAfter"] == "contrast" and e["badTheme"]
    for fn in ("getDashboard", "getExtras", "licenseAction", "setLeadStatus", "addRequest", "addFinance", "setTheme", "saveContact", "addNote", "addProspect", "emailContact", "startTrial"):
        assert e["stranger:" + fn] == "Not authorized", fn
    assert d["fetchesAfterStranger"] == 3
    # business-only inbox: personal, bank and shopping mail never appear
    assert d["dashHasNoInbox"] and d["batchCalls"] == 1          # dashboard returns fast; email loads in one batch afterwards
    assert d["inbox"] == ["New Event: Glow Studio", "Re: Quick idea", "[Lead] Glow Studio (score 72)", "You received $250.00"]
    # prospects: add, edit (only allowed fields), notes, email, trial, safety
    assert d["addP"]["ok"] and e["addNoBiz"] and e["addBadEmail"]
    a = d["afterSave"]
    assert a["contact"] == "Lee Park-Jones" and a["status"] == "Booked" and a["next"] == "Demo Thursday" and a["source"] == "Command Center" and a["notesHasEdit"]
    assert e["badStage"] == "Unknown status" and "moved" in e["wrongPerson"] and d["noteSaved"]
    m = d["afterEmail"]["mail"]
    assert d["afterEmail"]["status"] == "Contacted" and m["kind"] == "sent" and m["to"] == "lee@example.com" and m["subject"] == "Quick idea for Sunrise - cafe"
    assert re.fullmatch(r"[\x09\x0a\x0d\x20-\x7e]*", m["subject"] + m["body"])
    assert d["draft"]["kind"] == "draft" and "not to be emailed" in e["dnc"]
    t = d["trialFetch"]
    assert t["type"] == "lead" and t["form"] == "trial" and t["env"] == "production" and t["Email"] == "lee@example.com" and t["Package"] == "WorkOrderDesk" and d["afterTrial"] == "Trial"
    assert d["leadWon"] == "Won"
    # test data stays in TEST tabs and its email goes only to the owner
    assert d["testMail"]["to"] == "rashadfambro@gmail.com" and d["testMail"]["subject"].startswith("[TEST to customer@example.com]")
    assert d["testTrialEnv"] == "staging" and d["testDash"] == {"env": "test", "prospects": ["Staging Spa"]} and d["liveProspects"] == ["Sunrise Apartments"]
    assert d["triggers"] == ["dailyBrief"] and d["log"][:2] == ["setup", "lead:status"]
    brief = d["mails"][0]
    assert brief["subject"].startswith("[Daily brief]") and re.fullmatch(r"[\x09\x0a\x0d\x20-\x7e]*", brief["subject"] + brief["body"])
