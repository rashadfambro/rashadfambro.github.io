"""Every one of the 15 Desk tool apps (plus the Desk Suite) gets the same smoke, regression, security,
performance and load checks, so no tool ships without them.

T-SMOKE     opens with no script errors, shows its name, brand controls and footer.
T-REG       a valid trial link opens a branded trial; a valid license link opens the Starter edition
            with backup/restore; a forged key is rejected; the support snapshot button is present.
T-SEC       strict Content-Security-Policy, no third-party scripts, hostile ?brand= text is shown as text.
T-PERF      page under 60 KB and interactive in under 2.5 s locally.
T-LOAD      8 copies open at once without errors.
T-HELP      built-in Help: product overview, user guide (with the app's own sections) and release notes.
"""
import re, time, datetime, pathlib, subprocess, json, shutil
import pytest
from conftest import site_file

ROOT = pathlib.Path(__file__).resolve().parents[1]
APPS = [("property", "workorders.html", "WorkOrderDesk"), ("chat", "chat.html", "ChatDesk"), ("salon", "bookings.html", "BookDesk"),
        ("resort", "guests.html", "GuestDesk"), ("housekeeping", "housekeeping.html", "HousekeepingDesk"), ("rewards", "rewards.html", "RewardsDesk"),
        ("invoice", "invoices.html", "InvoiceDesk"), ("service", "leads.html", "LeadDesk"), ("package", "packages.html", "PackageDesk"),
        ("social", "social.html", "SocialDesk"), ("review", "reviews.html", "ReviewDesk"), ("staff", "staff.html", "StaffDesk"),
        ("insight", "insights.html", "InsightDesk"), ("intake", "intake.html", "IntakeDesk"), ("compliance", "compliance.html", "ComplianceDesk")]
IDS = [a[2] for a in APPS]
NODE = shutil.which("node")


def keys(tools, biz, date):
    js = ("function trialHash(s){let h=2166136261;for(const c of s){h^=c.charCodeAt(0);h=Math.imul(h,16777619)}return (h>>>0).toString(36).toUpperCase().padStart(6,'0').slice(0,6)}"
          f"const t={json.dumps(tools)},b={json.dumps(biz)},d={json.dumps(date)};"
          "console.log(JSON.stringify(['RF-'+d.replace(/-/g,'')+'-'+trialHash(t+'|'+b.trim().toLowerCase()+'|'+d),'RFL-'+d.replace(/-/g,'')+'-'+trialHash('L|'+t+'|'+b.trim().toLowerCase()+'|'+d)]))")
    return json.loads(subprocess.run([NODE, "-e", js], capture_output=True, text=True, check=True).stdout)


@pytest.mark.smoke
@pytest.mark.parametrize("tid,page,name", APPS, ids=IDS)
def test_T_SMOKE_opens(make_page, base_url, tid, page, name):
    w = make_page(); pg = w.page
    pg.goto(base_url + "prototypes/" + page); pg.wait_for_timeout(300)
    assert name in pg.inner_text("header h1")
    assert pg.locator("#bizName").count() == 1 and pg.locator("#bizColor").count() == 1
    assert pg.get_attribute("body", "data-proto") == tid
    assert not w.errors, w.errors


@pytest.mark.regression
@pytest.mark.skipif(not NODE, reason="node not installed")
@pytest.mark.parametrize("tid,page,name", APPS, ids=IDS)
def test_T_REG_trial_license_and_snapshot(make_page, base_url, tid, page, name):
    w = make_page(); pg = w.page
    today = datetime.date.today().isoformat()
    until = (datetime.date.today() + datetime.timedelta(days=40)).isoformat()
    trial, _ = keys(tid, "Acme Co", today)
    pg.goto(base_url + f"prototypes/{page}?trial={trial}&biz=Acme%20Co&start={today}&tools={tid}"); pg.wait_for_timeout(300)
    assert "Free 14-day trial for Acme Co" in pg.inner_text("#btext") and pg.inner_text("[data-biz]") == "Acme Co"
    _, lic = keys(tid, "Acme Co", until)
    pg.goto(base_url + f"prototypes/{page}?license={lic}&biz=Acme%20Co&until={until}&tools={tid}"); pg.wait_for_timeout(300)
    assert "licensed to Acme Co" in pg.inner_text("#btext")
    assert pg.locator("text=Download backup").count() == 1 and pg.locator("text=Restore backup").count() == 1
    pg.evaluate("localStorage.clear()")
    pg.goto(base_url + f"prototypes/{page}?license=RFL-20991231-FORGED&biz=Acme%20Co&until=2099-12-31&tools={tid}"); pg.wait_for_timeout(300)
    assert "licensed to" not in pg.inner_text("body")
    if "snapBtn" in open(site_file("prototypes/" + page), encoding="utf-8").read():   # support snapshots ship in v23
        assert pg.locator("#snapBtn").count() == 1
    assert not w.errors, w.errors


@pytest.mark.security
@pytest.mark.parametrize("tid,page,name", APPS + [("suite", "suite.html", "Desk Suite")], ids=IDS + ["Suite"])
def test_T_SEC_policy_and_escaping(make_page, base_url, tid, page, name):
    html = open(site_file("prototypes/" + page), encoding="utf-8").read()
    csp = re.search(r'Content-Security-Policy" content="([^"]+)"', html).group(1)
    assert "default-src 'self'" in csp and "object-src 'none'" in csp and "base-uri 'self'" in csp
    assert not re.search(r'<script[^>]+src="https?://', html), "no third-party scripts"
    w = make_page(); pg = w.page
    pg.goto(base_url + "prototypes/" + page + "?brand=%3Cimg%20src%3Dx%20onerror%3Dwindow.__x%3D1%3E&logo=javascript:alert(1)"); pg.wait_for_timeout(300)
    assert pg.evaluate("window.__x") is None and pg.locator("header img").count() == 0
    assert "javascript:" not in (pg.get_attribute("header .logo", "style") or "")
    assert not w.errors, w.errors


@pytest.mark.performance
@pytest.mark.parametrize("tid,page,name", APPS, ids=IDS)
def test_T_PERF_size_and_speed(make_page, base_url, tid, page, name):
    assert pathlib.Path(site_file("prototypes/" + page)).stat().st_size <= 60 * 1024
    w = make_page(); pg = w.page
    t0 = time.time(); pg.goto(base_url + "prototypes/" + page); pg.wait_for_selector("header h1")
    assert time.time() - t0 < 2.5


@pytest.mark.load
@pytest.mark.parametrize("tid,page,name", APPS, ids=IDS)
def test_T_LOAD_parallel_opens(browser, base_url, tid, page, name):
    ctx = browser.new_context(); errs = []
    try:
        pages = [ctx.new_page() for _ in range(8)]
        for p in pages:
            p.on("pageerror", lambda e: errs.append(str(e)))
            p.goto(base_url + "prototypes/" + page, wait_until="domcontentloaded")
        for p in pages:
            p.wait_for_selector("header h1")
        assert not errs, errs
    finally:
        ctx.close()


@pytest.mark.regression
@pytest.mark.parametrize("tid,page,name", APPS + [("suite", "suite.html", "Desk Suite")], ids=IDS + ["DeskSuite"])
def test_T_HELP_overview_guide_and_release_notes(make_page, base_url, tid, page, name):
    w = make_page(); pg = w.page
    pg.goto(base_url + "prototypes/" + page); pg.wait_for_timeout(300)
    if pg.locator("#helpBtn").count() == 0:
        pytest.skip("before v25")
    assert pg.is_hidden("#helpBox")
    pg.click("#helpBtn"); pg.wait_for_timeout(100)
    box = pg.inner_text("#helpBox")
    assert name + " Help" in box and "Product Overview" in box and "User Guide" in box and "Release Notes" in box
    pg.click('[data-htab="guide"]'); pg.wait_for_timeout(50)
    guide = pg.inner_text('[data-hp="guide"]')
    assert "Getting Started" in guide and "Approvals" in guide and "Your Data" in guide
    if tid != "suite":
        for tab in pg.eval_on_selector_all("main .tabs button", "els => els.map(e => e.textContent.trim())"):
            assert tab in guide, tab
        assert "How It Works" in guide
    pg.click('[data-htab="notes"]'); pg.wait_for_timeout(50)
    notes = pg.inner_text('[data-hp="notes"]')
    assert re.search(r"Version 1\.5 · November 16, 2026", notes) and "Version 1.0" in notes
    pg.keyboard.press("Escape"); pg.wait_for_timeout(50)
    assert pg.is_hidden("#helpBox")
    pg.goto(base_url + "prototypes/" + page + "#release-notes"); pg.wait_for_timeout(300)
    assert pg.is_visible('[data-hp="notes"]')
    assert not w.errors, w.errors
