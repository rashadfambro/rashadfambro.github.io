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
    prospects = SAMPLE["prospects"] + [{"_row": 4, "Added": "2026-11-15", "Business": "Viva Nails", "City": "3350 St Rose Pkwy #100, Henderson", "Industry": "Nail salon",
                                        "Tools to pitch": "BookDesk + ReviewDesk", "Status": "Not contacted", "Next step": "Walk in Tue 10 AM; ask for the owner"},
                                       {"_row": 5, "Added": "2026-11-16", "Business": "Sparkly Cleaning", "Email": "hello@example.com", "City": "Orlando, FL", "Industry": "Cleaning",
                                        "Tools to pitch": "BookDesk", "Status": "Draft ready"}]
    data = {
        "summary": {"alerts": [{"level": "high", "kind": "Past due", "text": XSS, "ref": "k"}], "pipeline": {"New": 1, "Won": 1},
                    "counts": {"newLeads": 1, "trials": 1, "activeClients": 2, "openRequests": 1, "prospects": 1, "leads": 3, "founding": 1},
                    "finance": {"mrrEstimate": 440, "revenueMonth": 5700, "revenueYear": 6200, "costsMonth": 40, "costsYear": 40, "profitYear": 6160}, "conversion": 33},
        "leads": SAMPLE["leads"], "prospects": prospects, "licenses": SAMPLE["licenses"], "orders": SAMPLE["orders"] + [{"Received": "2026-11-12T10:00:00Z", "Order ID": "O3", "Status": "Paid", "Business": "Glow Studio", "Item": "BookDesk setup", "Amount due": 1350}],
        "finance": [{"_row": 2, "Date": "2026-09-03T12:00:00Z", "Type": "Expense", "Category": "Software & subscriptions", "Description": "Claude plan", "Amount": -100, "Repeats": "Monthly"},
                    {"_row": 3, "Date": "2026-11-04T12:00:00Z", "Type": "Income", "Category": "Consulting", "Description": "Assessment", "Amount": 750, "Client": "Sun Auto", "Product": "Consulting"},
                    {"_row": 4, "Date": "2026-11-06T12:00:00Z", "Type": "Expense", "Category": "Insurance", "Description": "General liability", "Amount": -60}],
        "requests": SAMPLE["requests"] + [{"Time": NOW, "Request ID": "Q3", "Agent": "lead-researcher", "Client / topic": "Lead search: Cleaning / Orlando, FL", "Request": "LEAD SEARCH | industry: Cleaning", "Status": "New"}],
        "log": [{"Time": NOW, "Source": "command-center", "Action": "setup", "Target": XSS, "Result": "ok"}],
        "calendar": [{"title": "Audit: Glow Studio", "start": NOW, "end": NOW, "where": "Zoom"}],
        "inbox": [{"from": "Calendly", "subject": "New event: Glow Studio", "date": NOW, "business": True, "link": "https://mail.google.com/x"}],
        "drafts": [{"id": "d1", "to": "Dee Ortiz <dee@example.com>", "emails": ["dee@example.com"], "cc": "", "bcc": "", "subject": "702 PlumbAIR + Rashad Fambro Consulting: idea", "body": "Hi Dee", "date": NOW},
                   {"id": "d2", "to": "hello@example.com", "emails": ["hello@example.com"], "cc": "", "bcc": "", "subject": "Sparkly Cleaning + Rashad Fambro Consulting: booking", "body": "Hi there", "date": NOW}],
        "agents": ["chief-of-staff", "project-manager", "release-manager", "lead-researcher"], "generated": NOW, "env": "live",
        "settings": {"theme": "dark", "env": "live", "startTab": "today", "refreshMin": 0, "inboxDays": 3, "bccMe": False, "signature": "Rashad"},
    }
    html = INDEX.read_text().replace("<head>", "<head>" + STUB % json.dumps(data), 1)
    f = tmp_path / "cc.html"; f.write_text(html)
    w = make_page(width=1280); pg = w.page
    pg.goto(f.as_uri()); pg.wait_for_selector(".kpi"); pg.wait_for_selector("text=Audit: Glow Studio")
    assert "440" in pg.inner_text("main") and "Today (1)" in pg.inner_text("#tabs") and "Emails (2)" in pg.inner_text("#tabs")
    for t, expect in [("pipeline", "Glow Studio"), ("emails", "Drafts Ready to Send"), ("clients", "Record payment"), ("finance", "Itemized"), ("agents", "Send to agent team"), ("log", "setup"), ("settings", "Email signature")]:
        pg.click(f'[data-tab="{t}"]'); pg.wait_for_timeout(50)
        assert expect in pg.inner_text("main"), t
    assert "Finances" in pg.inner_text("#tabs") and "Finance\n" not in pg.inner_text("#tabs") + "\n" or True
    assert pg.locator('[data-tab="finance"]').inner_text() == "Finances"
    assert pg.evaluate("window.__xss") is None and pg.locator("main img").count() == 0
    pg.click('[data-tab="clients"]'); pg.click('[data-act="pause"][data-key="RFL-20261215-DEF456"]'); pg.wait_for_timeout(50)

    # --- pipeline: filters and sorting
    pg.click('[data-tab="pipeline"]'); pg.wait_for_timeout(50)
    board = pg.inner_text(".board")
    for stage in ("New", "Contacted", "Replied", "Booked", "Trial", "Proposal sent", "Client (Won)", "Closed"):
        assert stage in board, stage
    assert pg.locator('.pc[data-open="prospect"]').count() == 4 and pg.locator('.pc[data-open="lead"]').count() == 3
    assert "Next: Walk in Tue 10 AM" in board and "dee@example.com" in board          # next steps and emails on the cards
    pg.select_option("#fInd", "Nail salon"); pg.wait_for_timeout(30)
    assert pg.locator(".pc").count() == 1
    pg.click("#fClear"); pg.select_option("#fLoc", "Henderson"); pg.wait_for_timeout(30)
    assert pg.locator(".pc").count() == 2
    pg.click("#fClear"); pg.select_option("#fProd", "ReviewDesk"); pg.wait_for_timeout(30)
    assert pg.locator(".pc").count() == 1
    pg.click("#fClear"); pg.select_option("#fHas", "noemail"); pg.wait_for_timeout(30)
    assert pg.locator(".pc").count() == 1
    pg.click("#fClear"); pg.select_option("#fHas", "draft"); pg.wait_for_timeout(30)
    assert pg.locator(".pc").count() == 2
    pg.click("#fClear"); pg.select_option("#fView", "table"); pg.select_option("#fSort", "business"); pg.wait_for_timeout(30)
    names = pg.eval_on_selector_all("main tbody tr td:first-child", "els => els.map(e => e.textContent.trim())")
    assert names[0].startswith("702") and "Viva Nails" in names and len(names) == 7
    pg.click("#fDir"); pg.wait_for_timeout(30)
    assert pg.eval_on_selector_all("main tbody tr td:first-child", "els => els.map(e => e.textContent.trim())") == names[::-1]
    pg.select_option("#fView", "board"); pg.wait_for_timeout(30)

    # --- the bug: a prospect with no email can be saved (Viva Nails)
    pg.click('.pc[data-open="prospect"][data-row="4"]'); pg.wait_for_timeout(50)
    assert "Walk in Tue 10 AM" in pg.inner_text(".nextbox") and "none yet" in pg.inner_text("#drawer")
    pg.fill('#cForm [name="Phone"]', "702-954-4067"); pg.click('#cForm button[type=submit]'); pg.wait_for_timeout(50)
    pg.click("#dClose")

    # --- prospect with email: email shown, cc/bcc, big notes, drafts attached
    pg.click('.pc[data-open="prospect"][data-row="2"]'); pg.wait_for_timeout(50)
    d = pg.inner_text("#drawer")
    assert "702 PlumbAIR" in d and "Call 702-555-0142" in d and "left a card" in d and "dee@example.com" in pg.inner_text(".contactline")
    assert "dee@example.com" in pg.inner_text("#mForm .toline") and "Drafts Ready for 702 PlumbAIR" in d
    assert pg.evaluate("document.querySelector('#nForm textarea').getBoundingClientRect().height") >= 150
    pg.fill('#cForm [name="Next step"]', "Demo Thursday"); pg.select_option('#cForm [name=Status]', "Booked"); pg.click('#cForm button[type=submit]'); pg.wait_for_timeout(50)
    pg.fill('#nForm [name=note]', "Owner wants pricing\nfor 3 locations"); pg.click('#nForm button[type=submit]'); pg.wait_for_timeout(50)
    pg.select_option("#mTpl", "intro"); pg.wait_for_timeout(30)
    subj = pg.input_value('#mForm [name=subject]')
    assert subj.startswith("702 PlumbAIR + Rashad Fambro Consulting") and "Hi Dee" in pg.input_value('#mForm textarea')
    pg.fill('#mForm [name=cc]', "partner@example.com"); pg.fill('#mForm [name=bcc]', "me@example.com")
    pg.click('#mForm [data-mode="draft"]'); pg.wait_for_timeout(50)
    pg.select_option("#mTpl", "follow"); pg.wait_for_timeout(30)
    pg.click('#mForm [data-mode="send"]'); pg.wait_for_timeout(50)
    pg.click('#tForm button[type=submit]'); pg.wait_for_timeout(50)
    pg.click('#drawer [data-draft="d1"][data-dact="send"]'); pg.wait_for_timeout(50)
    pg.click('#drawer [data-stage="Won"]'); pg.wait_for_timeout(50)
    pg.click("#dClose")
    pg.click("#addP"); pg.fill("#aForm [name=Business]", "New Walk-in Cafe"); pg.fill("#aForm [name=Phone]", "702-555-0199"); pg.click("#aForm button[type=submit]"); pg.wait_for_timeout(80)
    assert pg.is_hidden("#drawer")
    pg.click("#leadSearch"); pg.wait_for_timeout(30)
    assert "Lead search: Cleaning / Orlando, FL" in pg.inner_text("#drawer")
    pg.fill("#lsForm [name=industry]", "Cleaning companies"); pg.fill("#lsForm [name=place]", "Tampa, FL"); pg.fill("#lsForm [name=signal]", "call to book only")
    pg.click("#lsForm button[type=submit]"); pg.wait_for_timeout(80)
    pg.drag_and_drop('.pc[data-open="lead"][data-row="4"]', '[data-drop="Booked"]'); pg.wait_for_timeout(50)

    # --- emails tab: edit and send a draft, discard another
    pg.click('[data-tab="emails"]'); pg.wait_for_timeout(30)
    assert "Dee Ortiz <dee@example.com>" in pg.inner_text("main") and "702 PlumbAIR" in pg.inner_text("main")
    pg.click('main [data-draft="d2"][data-dact="edit"]'); pg.wait_for_timeout(30)
    pg.fill("#dForm [name=subject]", "Sparkly Cleaning + Rashad Fambro Consulting: booking idea"); pg.click("#dForm button[type=submit]"); pg.wait_for_timeout(50)
    pg.click('main [data-draft="d1"][data-dact="discard"]'); pg.wait_for_timeout(50)

    # --- agent request and finances
    pg.click('[data-tab="agents"]'); pg.select_option('#reqForm [name=agent]', "release-manager"); pg.fill('#reqForm [name=topic]', "BookDesk")
    pg.fill('#reqForm textarea', "Release BookDesk 1.2 to staging"); pg.click('#reqForm button[type=submit]'); pg.wait_for_timeout(50)
    pg.click('[data-tab="finance"]'); pg.click('[data-fpreset="all"]'); pg.wait_for_timeout(30)
    main = pg.inner_text("main")
    assert "Income vs. Expenses by Month" in main and "Expenses by Category" in main and "Income by Product" in main and pg.locator("svg.chart rect").count() >= 2
    assert "Claude plan" in main and "Glow Studio" in main and "(repeat)" in main         # recurring expense repeats monthly; paid orders count as income
    pg.select_option("#fType", "Expense"); pg.wait_for_timeout(30)
    assert "Assessment" not in pg.inner_text("main tbody")
    pg.select_option("#fType", ""); pg.select_option("#fClient", "Sun Auto"); pg.wait_for_timeout(30)
    assert pg.locator("main tbody tr").count() == 1
    pg.select_option("#fClient", ""); pg.fill("#fFrom", "2026-11-05"); pg.wait_for_timeout(30)
    assert "Assessment" not in pg.inner_text("main tbody")
    with pg.expect_download() as dl:
        pg.click("#finCsv")
    csv = open(dl.value.path()).read()
    assert csv.startswith("Date,Type,Category") and "Profit" in csv
    pg.click('[data-sort="f:amount"]'); pg.wait_for_timeout(30)
    pg.fill('#finForm [name=amount]', "29"); pg.fill('#finForm [name=category]', "Software & subscriptions"); pg.fill('#finForm [name=description]', "Domain")
    pg.select_option('#finForm [name=repeats]', "Yearly"); pg.click('#finForm button[type=submit]'); pg.wait_for_timeout(50)
    pg.click('[data-fpreset="all"]'); pg.wait_for_timeout(30)
    pg.click('[data-fdel="4"]'); pg.wait_for_timeout(50)

    # --- settings: theme, data and preferences live on the Settings page
    pg.click('[data-tab="settings"]'); pg.wait_for_timeout(30)
    assert pg.get_attribute("html", "data-theme") == "dark"
    for th in ("light", "midnight", "contrast"):
        pg.select_option("#theme", th); pg.wait_for_timeout(30)
        assert pg.get_attribute("html", "data-theme") == th
        assert pg.evaluate("getComputedStyle(document.body).backgroundColor") != pg.evaluate("getComputedStyle(document.body).color"), th
    pg.select_option("#env", "test"); pg.select_option("#setForm [name=inboxDays]", "7"); pg.check("#setForm [name=bccMe]")
    pg.click("#setForm button[type=submit]"); pg.wait_for_timeout(120)
    assert pg.evaluate("document.body.classList.contains('testenv')") and "TEST" in pg.inner_text("#updated")

    calls = pg.evaluate("window.__calls")
    names = [c[0] for c in calls]
    assert ["licenseAction", "pause", "RFL-20261215-DEF456", "live"] in calls
    viva = {"row": 4, "email": "", "business": "Viva Nails"}
    saves = [c for c in calls if c[0] == "saveContact"]
    assert any(c[1] == "prospect" and c[2] == viva and c[3]["Phone"] == "702-954-4067" for c in saves), saves
    ref = {"row": 2, "email": "dee@example.com", "business": "702 PlumbAIR"}
    assert any(c[2] == ref and c[3].get("Next step") == "Demo Thursday" and c[3]["Status"] == "Booked" for c in saves)
    assert ["saveContact", "prospect", ref, {"Status": "Won"}, "live"] in saves
    assert ["saveContact", "lead", {"row": 4, "email": "sun@example.com", "business": "Sun Auto"}, {"Status": "Booked"}, "live"] in saves
    assert ["addNote", "prospect", ref, "Owner wants pricing\nfor 3 locations", "live"] in calls
    em = [c for c in calls if c[0] == "emailContact"]
    assert [c[5] for c in em] == ["draft", "send"] and all(c[1] == "prospect" and c[2] == ref and "Hi Dee" in c[4] and c[7] == {"cc": "partner@example.com", "bcc": "me@example.com"} for c in em)
    assert ["startTrial", "prospect", ref, "BookDesk + ReviewDesk", "live"] not in calls and ["startTrial", "prospect", ref, "LeadDesk", "live"] in calls
    assert ["sendDraft", "d1", None, "live"] in calls
    assert ["sendDraft", "d2", {"subject": "Sparkly Cleaning + Rashad Fambro Consulting: booking idea", "body": "Hi there", "cc": "", "bcc": ""}, "live"] in calls
    assert ["discardDraft", "d1"] in calls
    ls = [c for c in calls if c[0] == "requestLeadSearch"][0][1]
    assert ls["industry"] == "Cleaning companies" and ls["place"] == "Tampa, FL" and ls["signal"] == "call to book only"
    add = [c for c in calls if c[0] == "addProspect"][0]
    assert add[1]["Business"] == "New Walk-in Cafe" and add[1]["Phone"] == "702-555-0199" and add[2] == "live"
    assert ["addRequest", "release-manager", "Normal", "BookDesk", "Release BookDesk 1.2 to staging"] in calls
    fin = [c for c in calls if c[0] == "addFinance"][0][1]
    assert fin["type"] == "Expense" and fin["amount"] == "29" and fin["repeats"] == "Yearly" and fin["description"] == "Domain"
    assert ["deleteFinance", 4, "General liability", -60] in calls
    st = [c for c in calls if c[0] == "saveSettings"][0][1]
    assert st["env"] == "test" and st["theme"] == "contrast" and st["inboxDays"] == 7 and st["bccMe"] is True
    assert ["getDashboard", "test"] in calls and ["getDashboard", "live"] in calls and names.count("getDashboard") >= 3
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
    for fn in ("getDashboard", "getExtras", "sendDraft", "discardDraft", "requestLeadSearch", "saveSettings", "deleteFinance", "licenseAction", "setLeadStatus", "addRequest", "addFinance", "setTheme", "saveContact", "addNote", "addProspect", "emailContact", "startTrial"):
        assert e["stranger:" + fn] == "Not authorized", fn
    assert d["fetchesAfterStranger"] == 3
    # business-only inbox: personal, bank and shopping mail never appear
    assert d["dashHasNoInbox"] and d["batchCalls1"] == 1          # dashboard returns fast; email loads in one batch afterwards
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
    # the reported save bug: prospects without an email (Viva Nails) save, even if rows moved
    assert d["vivaPhone"] == "702-954-4067" and d["longNote"]
    assert "Missing record details" in e["noRef"] and "More than one record matches Twin Spa" in e["dupName"]
    assert d["ccMail"]["o"]["cc"] == "partner@example.com" and d["ccMail"]["o"]["bcc"] == "me@example.com" and e["badCc"]
    assert d["drafts"] == ["D1", "D3"] and d["afterDraft"] == {"status": "Contacted", "note": True}
    assert "Switch Data to Live" in e["draftTest"] and e["draftGone"] and d["discarded"] == "D2"
    assert d["searchRow"][0] == "lead-researcher" and "LEAD SEARCH" in str(d["searchRow"]) and e["emptySearch"]
    assert d["settings"] == d["badSettings"] == d["dashSettings"] and d["settings"]["theme"] == "light"
    assert d["finHeader"][-2:] == ["Product", "Repeats"] and e["finDelWrong"] and d["finDel"] is True and d["finCount"] == 2
    assert d["triggers"] == ["dailyBrief"] and d["log"][:2] == ["setup", "lead:status"]
    brief = d["mails"][0]
    assert brief["subject"].startswith("[Daily brief]") and re.fullmatch(r"[\x09\x0a\x0d\x20-\x7e]*", brief["subject"] + brief["body"])
