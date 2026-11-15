import re
"""Regression suite: full feature coverage. Scenario IDs match TESTING.md."""
import datetime, os, re
from urllib.parse import urljoin, urlparse
import pytest
from conftest import ROOT, OWNER_EMAIL, ONLINE, SITE_PATH, site_file

pytestmark = pytest.mark.regression

SMALL = set("a an the and but or nor for so yet as at by in of off on per to via vs".split())
EMPLOYERS = ["MedeAnalytics", "Benefitfocus", "Mood Media", "XPIENT", "Harris RF", "MIT Group", "Nationwide"]
SALE_DAY = datetime.datetime(2026, 12, 15, 12, 0, 0)
AFTER_SALE = datetime.datetime(2027, 2, 15, 12, 0, 0)


def all_html():
    base = site_file("")
    out = []
    for dp, dirs, fs in os.walk(base):
        if SITE_PATH == "/" and os.path.relpath(dp, ROOT).split(os.sep)[0] in ("staging", "tests", ".git", ".github", "scripts"):
            continue
        out += [os.path.join(dp, f) for f in fs if f.endswith(".html")]
    return out


# ---------------- price helpers: tests read prices from the site's CONFIG so they hold for any price change ----------------

def wait_js(pg, expr, timeout=5000):
    """Poll a JS expression with evaluate() (wait_for_function needs eval, which the site's CSP blocks)."""
    import time
    end = time.time() + timeout / 1000
    while time.time() < end:
        if pg.evaluate("() => { try { return !!(" + expr + "); } catch (e) { return false; } }"):
            return
        pg.wait_for_timeout(100)
    raise AssertionError("timed out waiting for: " + expr)


def is_v15(pg):
    """Staged release (featured tools, new estimator). Remove this helper after the promote."""
    return pg.locator("#prodGridMore").count() > 0

def dollars(n):
    import math
    return "${:,}".format(int(math.floor(n + 0.5)))   # rounds half up, like the site's JavaScript


def sale_price(v, pct=10):
    """Sale prices round down to the nearest $10, matching saleAmt() on the site."""
    import math
    return int(math.floor(v * (100 - pct) / 1000) * 10)


def site_prices(pg):
    return pg.evaluate("""() => ({
      pkg: Object.fromEntries(CONFIG.packages.map(p => [p.id, p.price])),
      assess: BUYABLE.assess.price, bundle: BUYABLE.bundle.price, hotel: BUYABLE.hotelbundle.price,
      std: CONFIG.tiers.std.map(t => t.price), prop: CONFIG.tiers.prop.map(t => t.price),
      sale: CONFIG.sale.pct, products: Object.fromEntries(PRODUCTS.map(p => [p.name, p.price]))})""")


def chat(pg, text, wait=900):
    pg.fill("#chatInput", text); pg.press("#chatInput", "Enter"); pg.wait_for_timeout(wait)
    return pg.locator(".cmsg.bot").last.inner_text()


def open_home(make_page, base_url, when=None, hash_="", **kw):
    w = make_page(**kw)
    if when:
        w.page.clock.set_fixed_time(when)
    w.page.goto(base_url + "index.html" + hash_)
    w.page.wait_for_timeout(300)
    w.page.evaluate("document.querySelectorAll('details.more-prod').forEach(d => d.open = true)")
    return w


# ---------------- content & brand rules ----------------
def is_title_case(text):
    words = [x for x in re.split(r"\s+", text) if re.search(r"[A-Za-z]", x)]
    for i, w in enumerate(words):
        for j, part in enumerate(w.split("-")):
            m = re.search(r"[A-Za-z]", part)
            if not m: continue
            core = re.sub(r"[^A-Za-z’']", "", part).lower()
            if part[m.start()].islower() and not (core in SMALL and (j > 0 or i not in (0, len(words) - 1))):
                return False
    return True


def test_R01_all_headings_title_case(make_page, base_url):
    w = make_page()
    bad = []
    for path in ["index.html", "products.html", "industries/index.html", "industries/apartments.html", "tools/audit-summary.html"]:
        w.page.goto(base_url + path); w.page.wait_for_timeout(200)
        heads = w.page.eval_on_selector_all("h1,h2,h3,h4,summary", "els => els.map(e => e.innerText.trim()).filter(Boolean)")
        bad += [f"{path}: {h}" for h in heads if not is_title_case(h.replace("\n", " "))]
    assert bad == []


def test_R02_no_former_employer_names():
    hits = [(f, e) for f in all_html() for e in EMPLOYERS if e in open(f, encoding="utf-8").read()]
    assert hits == []


def test_R03_profile_focus_and_former(home):
    prof = home.page.inner_text(".profile")
    assert "healthcare technology" not in prof.lower()
    assert re.search(r"Focus\s+AI", prof)
    assert re.search(r"Experience\s+17 years as an IT (software )?professional", prof) and "Former" not in prof
    assert "on-site" in prof.lower()


def test_R04_founding_program_terms(home):
    t = home.page.inner_text("#founding")
    assert "25% off" in t and "testimonial" in t.lower() and "30%" not in t


def test_R05_offer_amounts(home):
    t = home.page.inner_text(".offers"); P = site_prices(home.page)
    assert "$150 credit" in t and "paid for the assessment is credited" in t and dollars(P["bundle"]) in t and dollars(P["hotel"]) in t


# ---------------- holiday sale ----------------
def test_R06_sale_banner_during_and_after(make_page, base_url):
    w = open_home(make_page, base_url, when=SALE_DAY)
    assert w.page.is_visible("#saleBar") and "10% or more off" in w.page.inner_text("#saleBar")
    P = site_prices(w.page); reg, sale = dollars(P["assess"]), dollars(sale_price(P["assess"], P["sale"]))
    assert sale in w.page.inner_text("#pkgGrid")
    w2 = open_home(make_page, base_url, when=AFTER_SALE)
    assert not w2.page.is_visible("#saleBar")
    assert sale not in w2.page.inner_text("#pkgGrid") and reg in w2.page.inner_text("#pkgGrid")


def test_R07_sale_price_math_on_products(make_page, base_url):
    w = open_home(make_page, base_url, when=SALE_DAY)
    chat_card = w.page.locator(".prod", has_text="ChatDesk").first.inner_text(); P = site_prices(w.page)
    setup = int(re.search(r"Setup \$([\d,]+)", P["products"]["ChatDesk"]).group(1).replace(",", ""))
    assert dollars(sale_price(setup, P["sale"])) in chat_card and dollars(sale_price(P["std"][0], P["sale"])) + "/mo" in chat_card


# ---------------- purchasing ----------------
def test_R08_buy_flow_and_payment_plans(make_page, base_url):
    w = open_home(make_page, base_url, when=AFTER_SALE)
    pg = w.page
    ids = pg.eval_on_selector_all("[data-buy]", "els => [...new Set(els.map(e => e.dataset.buy))]")
    assert set(["assess", "bundle", "hotelbundle", "care", "pilot", "chat", "salon", "rewards", "housekeeping"]).issubset(ids)
    for i in ids:
        pg.locator(f"[data-buy='{i}']").first.click()
        assert pg.is_visible("#buyModal"), i
        assert pg.inner_text("#buyTitle").strip(), i
        pg.click("#buyClose")
    pg.locator("[data-buy='care']").first.click()
    assert not pg.is_visible("#planOpt")          # monthly care plan under $1,000: no installment option
    pg.click("#buyClose")
    pg.locator("[data-buy='chat']").first.click()
    assert pg.is_visible("#planOpt")              # $1,000 setup: installments offered
    assert pg.locator("input[name=tier]").count() == 3   # Essentials / Growth / Pro
    pg.check("input[name=tier][value='1']")
    assert dollars(site_prices(pg)["std"][1]) + "/mo" in pg.inner_text("#buyPrice")
    pg.click("#buyGo")
    assert "required" in pg.inner_text("#buyErr")
    pg.fill("#buy_name", "Pat Buyer"); pg.fill("#buy_biz", "Pat Co"); pg.fill("#buy_email", "pat@example.com")
    pg.click("#buyGo")
    assert "checkbox" in pg.inner_text("#buyErr")
    assert pg.locator("input[name=method]").count() == 2   # PayPal (default) + Square
    assert pg.is_checked("input[name=method][value='PayPal']")
    pg.check("#buy_ok"); pg.check("input[name=plan][value='3 monthly payments']"); pg.check("input[name=method][value='PayPal']")
    pg.evaluate("CONFIG.paypalMe=''; if (CONFIG.squareLinks) CONFIG.squareLinks={}")   # no hosted checkout: test the emailed-invoice path
    pg.click("#buyGo")
    wait_js(pg, "document.getElementById('buyResult').innerText.trim().length > 0", 10000)
    res = pg.inner_text("#buyResult")
    assert "Nothing has been charged" in res
    href = pg.get_attribute("#buyResult a", "href")
    assert href.startswith(f"mailto:{OWNER_EMAIL}") and "3%20monthly%20payments" in href and "PayPal" in href and "Growth" in href
    assert w.errors == []


def test_R09_payment_plan_messaging(home):
    assert "3 interest-free monthly payments" in home.page.inner_text(".pricenote")
    assert home.page.locator("summary", has_text="Can I Pay Over Time?").count() == 1


# ---------------- demos, industries, landing links ----------------
def test_R10_demo_lab_all_scenarios(home):
    pg = home.page
    for key in pg.eval_on_selector_all("#labPick button", "els => els.map(e => e.dataset.demo)"):
        pg.click(f"#labPick button[data-demo='{key}']")
        pg.click("#labRun"); pg.wait_for_timeout(2300)
        assert pg.is_visible("#labOut"), key
        assert pg.inner_text("#labDraft").startswith("Draft reply"), key
        pg.click("#labApprove")
        assert "Approved in this demo" in pg.inner_text("#labStatus"), key
    assert home.errors == []


def test_R11_industry_landing_links(make_page, base_url, home):
    keys = home.page.evaluate("Object.keys(LANDINGS)")
    assert len(keys) >= 23
    w = make_page()
    for k in keys:
        w.page.goto(base_url + "index.html#" + k); w.page.wait_for_timeout(150)
        L = w.page.evaluate(f"LANDINGS['{k}']")
        assert L["line"].split(". ")[0].rstrip(".") in w.page.inner_text(".hero h1"), k
        assert w.page.input_value("#a_ind") == L["opt"], k
        w.page.goto("about:blank")
    assert w.errors == []


def test_R12_industry_chips_and_try_buttons(home):
    pg = home.page
    names = pg.eval_on_selector_all("#indChips button", "els => els.map(e => e.dataset.ind)")
    assert len(names) >= 22
    for k in names:
        pg.click(f"#indChips button[data-ind='{k}']")
        assert pg.locator("#indPanel h3").inner_text().strip(), k
        assert pg.locator("#indPanel [data-open-demo],#indPanel [data-open-chat]").count() == 1, k
    assert home.errors == []


# ---------------- chat assistant ----------------
@pytest.mark.parametrize("q,expect", [
    ("how much does it cost?", ["Assessment", "Pilot", "Care &", "/mo"]),
    ("tell me about the founding client program", ["25% off", "testimonial"]),
    ("Do you meet in person?", ["on-site", "travel"]),
    ("do you offer payment plans?", ["3 interest-free"]),
    ("can I buy online?", ["PayPal", "Square"]),
    ("can you set up a loyalty rewards program?", ["RewardsDesk"]),
    ("do you build chatbots?", ["ChatDesk"]),
    ("is there a free trial?", ["14-day trial", "trial workspace" if "trial workspace" in open(site_file("index.html"), encoding="utf-8").read() else "license key"]),
    ("we need help with housekeeping room turns", ["HousekeepingDesk"]),
])
def test_R13_chat_intents(make_page, base_url, q, expect):
    w = open_home(make_page, base_url, when=AFTER_SALE)
    w.page.click("#chatFab")
    a = chat(w.page, q)
    for e in expect:
        assert e in a, (q, e, a)
    assert w.errors == []


def test_R13b_chat_sale_intent(make_page, base_url):
    w = open_home(make_page, base_url, when=SALE_DAY)
    w.page.click("#chatFab")
    assert "10% or more off" in chat(w.page, "is there a holiday sale?")


def test_R13c_chat_lead_capture(home):
    pg = home.page
    pg.click("#chatFab")
    chat(pg, "Book a free audit")
    chat(pg, "Jane Doe", 700); chat(pg, "Sunrise Apartments", 700)
    assert "doesn’t look like an email" in chat(pg, "nope", 700)
    chat(pg, "jane@example.com", 700); chat(pg, "Skip", 700)
    final = chat(pg, "Maintenance requests get lost", 1200)
    assert "open the email draft" in final
    href = pg.locator(".cmsg.bot a").last.get_attribute("href")
    assert href.startswith(f"mailto:{OWNER_EMAIL}")


# ---------------- calculators & forms ----------------
def _legacy_R14(pg):
    for k, v in {"r1": 10, "r2": 5, "r3": 30, "r4": 40, "r5": 4, "r6": 1000}.items():
        pg.eval_on_selector(f"#{k}", f"(el) => {{ el.value = {v}; el.dispatchEvent(new Event('input')); }}")
    hrs = 10 * 5 * 0.40 * 4.33
    labor = round(hrs * 12 * 30); leads = round(4 * 0.25 * 1000 * 12)
    assert pg.inner_text("#roiHours") == f"{round(hrs):,}"
    assert pg.inner_text("#roiLabor") == f"${labor:,}"
    assert pg.inner_text("#roiLeads") == f"${leads:,}"
    assert pg.inner_text("#roiTotal") == f"${labor + leads:,}"


def test_R14_roi_math(home):
    pg = home.page
    if not is_v15(pg):
        return _legacy_R14(pg)
    pg.select_option("#roiTool", "property")
    for k, v in {"r1": 10, "r2": 5, "r3": 30, "r4": 40, "r5": 4, "r6": 1000, "r7": 25, "r8": 50, "r9": 20}.items():
        pg.eval_on_selector(f"#{k}", f"(el) => {{ el.value = {v}; el.dispatchEvent(new Event('input')); }}")
    P = site_prices(pg)
    hrs = 10 * 5 * 0.40 * 4.33
    labor = hrs * 30; gp = 4 * 0.25 * 1000 * 0.5; setup = 3500; cost = P["prop"][0] + 20
    net = labor + gp - cost
    assert pg.inner_text("#roiHours") == f"{round(hrs):,}"
    assert pg.inner_text("#roiLabor") == dollars(labor)
    assert pg.inner_text("#roiLeads") == dollars(gp)
    assert pg.inner_text("#roiCost") == dollars(cost) + "/mo"
    assert pg.inner_text("#roiTotal") == dollars(net) + "/mo"
    assert pg.inner_text("#roiPayback") == f"{setup / net:.1f} months"
    assert pg.inner_text("#roiYear") in (dollars(round(net) * 12 - setup), dollars(net * 12 - setup))
    # ChatGPT's worked example: 200 requests x 5 min at $30/hr, $3,500 setup, $150/mo -> $350/mo net, 10-month payback
    r = pg.evaluate("roiCalc({people:1,hours:200*5/60/4.33,rate:30,auto:100,missed:0,winback:0,sale:0,margin:0,usage:0,plan:150,setup:3500})")
    assert round(r["net"]) == 350 and round(r["payback"]) == 10
    # Zero or negative benefit shows no payback period
    for k in ["r1", "r5"]:
        pg.eval_on_selector(f"#{k}", "(el) => { el.value = el.min; el.dispatchEvent(new Event('input')); }")
    pg.eval_on_selector("#r9", "(el) => { el.value = 200; el.dispatchEvent(new Event('input')); }")
    pg.eval_on_selector("#r4", "(el) => { el.value = 10; el.dispatchEvent(new Event('input')); }")
    pg.eval_on_selector("#r2", "(el) => { el.value = 1; el.dispatchEvent(new Event('input')); }")
    assert pg.inner_text("#roiPayback") == "No payback at these inputs"
    assert pg.inner_text("#roiTotal").startswith("−")


def test_R15_roi_email_capture(home):
    pg = home.page
    pg.fill("#roiEmail", "bad"); pg.click("#roiMail button")
    assert "valid email" in pg.inner_text("#roiMsg")
    pg.fill("#roiEmail", "owner@example.com"); pg.click("#roiMail button"); pg.wait_for_timeout(300)
    assert pg.get_attribute("#roiMsg a", "href").startswith(f"mailto:{OWNER_EMAIL}")


def test_R16_project_builder_flow(home):
    pg = home.page
    if pg.locator("#startMore").count(): pg.click("#startMore > summary")
    pg.click("#bNext")
    pg.click("#bNext"); assert "required" in pg.inner_text("#bErr")
    pg.fill("#b_name", "A B"); pg.fill("#b_biz", "AB Co"); pg.fill("#b_email", "ab@example.com"); pg.fill("#b_goal", "Faster replies")
    pg.click("#bNext"); pg.click("#bNext")
    assert "AB Co" in pg.inner_text("#bSummary")
    pg.click("#bNext"); pg.wait_for_timeout(300)
    assert pg.is_visible("#bResult")
    assert pg.get_attribute("#bMail", "href").startswith(f"mailto:{OWNER_EMAIL}")


def test_R17_owner_email_configuration(home):
    assert home.page.evaluate("CONFIG.email") == OWNER_EMAIL
    assert home.page.get_attribute("#vEmail", "href") == f"mailto:{OWNER_EMAIL}"


# ---------------- links, QR, meta ----------------
def test_R18_internal_links_resolve():
    broken = []
    files = all_html()
    for f in files:
        s = open(f, encoding="utf-8").read()
        ids_cache = {}
        for href in re.findall(r'\shref="([^"#?][^"]*|#[^"]*)"', s):
            if href.startswith(("http", "mailto:", "tel:", "data:", "$", "javascript")) or "${" in href:
                continue
            if "?" in href:
                base, _, rest = href.partition("?")
                href = base + ("#" + rest.split("#", 1)[1] if "#" in rest else "")
            path, _, frag = href.partition("#")
            target = os.path.normpath(os.path.join(os.path.dirname(f), path)) if path else f
            if os.path.isdir(target): target = os.path.join(target, "index.html")
            if not os.path.exists(target):
                broken.append((os.path.relpath(f, ROOT), href)); continue
            if frag and target.endswith(".html"):
                ids = ids_cache.setdefault(target, set(re.findall(r'id="([^"]+)"', open(target, encoding="utf-8").read())))
                js_hashes = set(re.findall(r'"(for-[\w-]+)":', open(target, encoding="utf-8").read()))
                if frag not in ids and frag not in js_hashes and frag != "top":
                    broken.append((os.path.relpath(f, ROOT), href))
    assert broken == []


def test_R19_qr_defaults_to_website(home):
    pg = home.page
    assert pg.get_attribute("#qrTabs [data-qr='site']", "aria-pressed") == "true"
    assert "save this website" in pg.inner_text("#qrNote")
    assert pg.locator("#qr svg").count() == 1          # static QR, no CDN needed
    for k in ["vcard", "linkedin", "site"]:
        pg.click(f"#qrTabs [data-qr='{k}']")
        assert pg.locator("#qr svg").count() == 1, k
    assert "Loading QR" not in pg.content() and "cdnjs" not in pg.content()


def test_R20_save_site_button(home):
    home.page.click("#saveSite"); home.page.wait_for_timeout(300)
    assert home.errors == []


def test_R21_meta_tags_per_environment():
    for f in all_html():
        s = open(f, encoding="utf-8").read()
        rel = os.path.relpath(f, ROOT)
        assert '<link rel="canonical"' in s or "noindex" in s, rel
        if rel.startswith("staging" + os.sep):
            assert "noindex" in s and "STAGING" in s, rel
        elif not rel.startswith("tools"):
            assert "noindex" not in s, rel


def test_R22_robots_txt():
    r = open(os.path.join(ROOT, "robots.txt")).read()
    assert "Disallow: /staging/" in r and "Disallow: /tools/" in r and "Sitemap:" in r


def test_R23_product_guide_sections(make_page, base_url):
    w = make_page(); w.page.goto(base_url + "products.html")
    for art in w.page.locator("article.prod").all():
        t = art.inner_text()
        for k in ["HOW IT WORKS", "SAVES MONEY", "WINS MORE BUSINESS", "BOOSTS PRODUCTIVITY", "HUMAN IN THE LOOP", "Setup $", "plans from"]:
            assert k.lower() in t.lower(), (k, t[:40])


def test_R24_form_fields_are_labelled(home):
    unlabelled = home.page.evaluate("""() => [...document.querySelectorAll('input,select,textarea')]
      .filter(el => !el.classList.contains('hp') && el.type !== 'hidden' && el.type !== 'radio' && el.type !== 'checkbox')
      .filter(el => !(el.labels && el.labels.length) && !el.getAttribute('aria-label'))
      .map(el => el.id || el.name)""")
    assert unlabelled == []


def test_R25_prices_consistent_between_home_and_guide(make_page, base_url, home):
    home_prices = home.page.evaluate("Object.fromEntries(PRODUCTS.map(p => [p.name, p.price]))")
    w = make_page(); w.page.goto(base_url + "products.html")
    for art in w.page.locator("article.prod").all():
        name = art.locator("h2").inner_text().strip()
        assert art.locator(".price").inner_text().strip() == home_prices[name], name


def test_R26_audit_tool_pricing(make_page, base_url):
    w = make_page(width=1400, height=1000); w.page.goto(base_url + "tools/audit-summary.html")
    w.page.click("#sample"); w.page.wait_for_timeout(200)
    t = w.page.inner_text("#page")
    hp = make_page(); hp.page.goto(base_url + "index.html"); hp.page.wait_for_timeout(200)
    wo = int(re.search(r"Setup \$([\d,]+)", site_prices(hp.page)["products"]["WorkOrderDesk"]).group(1).replace(",", ""))
    assert dollars(wo * 0.75) + " setup" in t and "25% off" in t   # WorkOrderDesk with founding discount matches the site


@pytest.mark.skipif(not os.environ.get("REQUIRE_SYNC"), reason="only after a promote (REQUIRE_SYNC=1)")
def test_R27_staging_matches_production():
    import subprocess, sys
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "release.py"), "check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


# ---------------- v6: trials, plans, housekeeping, sale note ----------------
def test_R28_free_trial_flow(make_page, base_url):
    w = open_home(make_page, base_url, when=AFTER_SALE)
    pg = w.page
    trial_ids = pg.eval_on_selector_all("[data-trial]", "els => els.map(e => e.dataset.trial)")
    assert len(trial_ids) == 15
    pg.locator("[data-trial='housekeeping']").click()
    assert "14-Day Trial" in pg.inner_text("#buyTitle")
    assert not pg.is_visible("#methodOpts") and not pg.is_visible("#buyTerms") and pg.is_visible("#trialNote")
    assert "Free for 14 days, then" in pg.inner_text("#buyPrice") and dollars(site_prices(pg)["prop"][0]) + "/mo" in pg.inner_text("#buyPrice")
    pg.fill("#buy_name", "Tia Trial"); pg.fill("#buy_biz", "Seaside Resort"); pg.fill("#buy_email", "tia@example.com")
    pg.click("#buyGo")
    wait_js(pg, "document.getElementById('buyResult').innerText.trim().length > 0", 10000)
    assert "press Send" in pg.inner_text("#buyResult")
    href = pg.get_attribute("#buyResult a", "href")
    assert href.startswith(f"mailto:{OWNER_EMAIL}") and "free%20trial" in href.lower()
    assert w.errors == []


def test_R29_monthly_plan_tiers(make_page, base_url):
    w = open_home(make_page, base_url, when=AFTER_SALE)
    t = w.page.inner_text("#tiers"); P = site_prices(w.page)
    for x in ["Essentials", "Growth", "Pro", "14-day trial"] + [dollars(v) + "/mo" for v in P["std"] + P["prop"]]:
        assert x in t, x
    assert re.search(r"any 3 standard tools on Essentials for \$[\d,]+/mo", t)


def test_R30_sale_fine_print_on_its_own_line(make_page, base_url):
    w = open_home(make_page, base_url, when=SALE_DAY)
    assert "founding-client discount" not in w.page.inner_text("#saleText")
    fine = w.page.locator("#saleFine")
    assert "founding-client discount" in fine.inner_text()
    assert w.page.evaluate("getComputedStyle(document.getElementById('saleFine').closest('.sale-fine')).display") == "block"


def test_R31_hotel_tools(home):
    pg = home.page
    for name, needle in [("WorkOrderDesk", "hotels & resorts"), ("IntakeDesk", "Hotels & resorts"), ("HousekeepingDesk", "Hotels")]:
        assert needle in pg.locator(".prod", has_text=name).first.inner_text(), name
    pg.click("#labPick button[data-demo='housekeeping']")
    pg.fill("#labInput", "Room 512 checked out early and the VIP guests arrive at 2pm")
    pg.click("#labRun"); pg.wait_for_timeout(2300)
    out = pg.inner_text("#labOut")
    assert "Checkout clean" in out and "High" in out and "512" in out


def test_R32_product_prices(home):
    P = site_prices(home.page)
    tiers = home.page.evaluate("Object.fromEntries(PRODUCTS.map(p => [p.name, p.tier]))")
    for name, price in P["products"].items():
        if name == "ChatDesk" and "Setup" not in price: continue
        m = re.fullmatch(r"Setup \$([\d,]+) · plans from \$(\d+)/mo", price)
        assert m, (name, price)
        assert int(m.group(2)) == min(P["std"] if tiers[name] == "std" else P["prop"]), (name, price)


# ---------------- v7: navigation ----------------
def test_R33_back_to_top_and_home(home):
    pg = home.page
    assert not pg.is_visible("#toTop")
    pg.evaluate("window.scrollTo(0, 3000)"); pg.wait_for_timeout(200)
    assert pg.is_visible("#toTop")
    pg.click("#toTop"); wait_js(pg, "window.scrollY < 5", 5000)
    pg.evaluate("window.scrollTo(0, 3000)"); pg.wait_for_timeout(200)
    pg.click("#nav a[data-home]"); wait_js(pg, "window.scrollY < 5", 5000)
    assert pg.locator("#nav a").first.inner_text() == "Home"
    assert home.errors == []


@pytest.mark.parametrize("path", ["products.html", "industries/hotels.html"])
def test_R34_subpage_home_and_top(make_page, base_url, path):
    w = make_page(); pg = w.page
    pg.goto(base_url + path)
    assert pg.locator("header a", has_text="Home").count() == 1
    pg.evaluate("window.scrollTo(0, 2500)"); pg.wait_for_timeout(200)
    assert pg.is_visible("#toTop")
    pg.click("#toTop"); wait_js(pg, "window.scrollY < 5", 5000)
    assert w.errors == []


# ---------------- v8: email review fixes, booking, delivery ----------------
def test_R35_meaningful_defaults_without_interaction(make_page, base_url):
    w = make_page(); pg = w.page
    pg.route("**/*.js", lambda r: r.abort())       # simulate crawlers / link previews (no scripts)
    pg.goto(base_url + "index.html")
    html = pg.content()
    assert "requests handled" not in html and ">0 hrs<" not in html
    assert ("$1,402/mo" in pg.inner_text("#roiTotal") and "1.1 months" in pg.inner_text("#roiPayback")) if is_v15(pg) else "$21,868" in pg.inner_text("#roiTotal")
    assert "47" == pg.inner_text("#roiHours").strip()
    assert "Loading QR" not in html and pg.locator("#qr svg").count() == 1
    foot = pg.inner_text(".board-foot")
    for x in ["<2 min", "100%", "3–8 wk" if is_v15(pg) else "2–6 wk"]:
        assert x in foot, x


def test_R36_booking_links(home):
    pg = home.page
    assert pg.evaluate("CONFIG.calendarUrl") == "https://calendly.com/rashadfambro/free-workflow-audit"
    links = pg.eval_on_selector_all("a[data-cfg-href='calendarUrl']", "els => els.map(e => e.href)")
    assert len(links) >= 2 and all(l == "https://calendly.com/rashadfambro/free-workflow-audit" for l in links)
    pg.click("#chatFab")
    assert "pick a time" in chat(pg, "can I talk to Rashad?")
    assert pg.locator(".cmsg.bot").last.locator("a").first.get_attribute("href") == "https://calendly.com/rashadfambro/free-workflow-audit"


def test_R37_how_i_deliver_section(home):
    t = home.page.inner_text("#delivery")
    for x in ["Single Point of Contact", "AI-Assisted", "Tested Before It Ships", "reviewed by me"]:
        assert x.lower() in t.lower(), x
    assert "agent" not in t.lower()


def test_R38_faq_no_seasonal_copy(home):
    faq = home.page.inner_text("#faq")
    assert "Holiday" not in faq


# ---------------- v9: direct form sending, multi-industry, PackageDesk ----------------
def _fake_formsubmit(pg, success=True, seen=None):
    def handle(route):
        if seen is not None:
            seen.append((route.request.url, route.request.post_data_json))
        route.fulfill(status=200, content_type="application/json",
                      body='{"success":"true","message":"The form was submitted successfully."}' if success
                      else '{"success":"false","message":"This form needs Activation."}')
    pg.route(re.compile(r"https://formsubmit\.co/.*"), handle)


def test_R39_forms_send_directly_to_owner(make_page, base_url):
    w = make_page(); pg = w.page
    seen = []
    _fake_formsubmit(pg, True, seen)
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    assert pg.evaluate("CONFIG.formEndpoint") == f"https://formsubmit.co/ajax/{OWNER_EMAIL}"
    pg.fill("#a_name", "Test Person"); pg.fill("#a_biz", "Test Co"); pg.fill("#a_email", "test@example.com"); pg.fill("#a_flow", "Testing direct send"); pg.fill("#a_notes", "Two properties, launch before spring")
    pg.click("#auditForm button[type=submit]")
    wait_js(pg, "document.querySelector('#auditResult h4').innerText.includes('received')", 10000)
    assert not pg.is_visible("#auditMail")
    url, body = seen[-1]
    assert url == f"https://formsubmit.co/ajax/{OWNER_EMAIL}"
    assert body["email"] == "test@example.com" and "Email" not in body
    assert body["_subject"].startswith("New website lead (audit)") and "Test Co" in body["_subject"]
    assert body["_template"] == "table" and "_autoresponse" in body
    assert body["Notes"] == "Two properties, launch before spring"
    assert w.errors == []


def test_R40_unactivated_form_falls_back_to_email(make_page, base_url):
    w = make_page(); pg = w.page
    _fake_formsubmit(pg, False)
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    pg.fill("#a_name", "Test Person"); pg.fill("#a_biz", "Test Co"); pg.fill("#a_email", "test@example.com"); pg.fill("#a_flow", "Testing fallback")
    pg.click("#auditForm button[type=submit]")
    pg.wait_for_selector("#auditResult:not([hidden])", timeout=10000)
    assert pg.is_visible("#auditMail") and pg.get_attribute("#auditMail", "href").startswith(f"mailto:{OWNER_EMAIL}")
    assert "One Last Step" in pg.inner_text("#auditResult h4")


def test_R41_order_and_trial_send_directly(make_page, base_url):
    w = open_home(make_page, base_url, when=AFTER_SALE)
    pg = w.page
    seen = []
    _fake_formsubmit(pg, True, seen)
    pg.locator("[data-trial='package']").click()
    pg.wait_for_selector("#buy_name", state="visible")
    pg.fill("#buy_name", "Pat Package"); pg.fill("#buy_biz", "Lakeside Apartments"); pg.fill("#buy_email", "pat@example.com")
    pg.click("#buyGo")
    wait_js(pg, "document.getElementById('buyResult').innerText.trim().length > 0", 15000)
    assert "on its way" in pg.inner_text("#buyResult")
    assert seen[-1][1]["_subject"].startswith("Trial request") and "PackageDesk" in seen[-1][1]["Workflow"]


def test_R42_multi_industry_wording_and_packagedesk(home):
    pg = home.page
    ind = pg.inner_text("#industries")
    assert "Multi-industry solutions with workflow customizations" in ind
    assert "Current focus" not in ind and "first focus" not in ind.lower()
    assert "PackageDesk" in pg.inner_text("#products")
    assert "PackageDesk" in pg.inner_text(".tier-foot")
    pg.click("#labPick button[data-demo='package']")
    pg.fill("#labInput", "Refrigerated grocery delivery for apt 12C, resident isn't answering")
    pg.click("#labRun"); pg.wait_for_timeout(2300)
    out = pg.inner_text("#labOut")
    assert "Perishable" in out and "12C" in out
    pg.click("#chatFab")
    assert "PackageDesk" in chat(pg, "do you have a package room system for our mail room?")
    assert home.errors == []


# ---------------- v10: prototypes for every former "Ready to build" product ----------------
PROTOS = {"rewards": "rewards.html", "review": "reviews.html", "social": "social.html",
          "staff": "staff.html", "invoice": "invoices.html", "insight": "insights.html"}
MORE_PROTOS = {"chat": "chat.html", "property": "workorders.html", "resort": "guests.html", "salon": "bookings.html", "housekeeping": "housekeeping.html",
               "package": "packages.html", "service": "leads.html", "intake": "intake.html", "compliance": "compliance.html"}


def _proto(make_page, base_url, file):
    w = make_page(); w.page.goto(base_url + "prototypes/" + file); w.page.wait_for_timeout(300)
    return w


def test_R43_every_product_has_a_demo_or_prototype(home, base_url):
    pg = home.page
    assert pg.evaluate("PRODUCTS.every(p => ['Prototype', 'Starter ready'].includes(p.status) || p.status.startsWith('Live'))")
    for pid, file in PROTOS.items():
        href = pg.get_attribute(f"[data-proto-link='{pid}']", "href")
        assert href == f"prototypes/{file}"
    assert "Ready to build" not in pg.inner_text("#products")


def test_R44_prototypes_load_branded_without_errors(make_page, base_url):
    for file in list(PROTOS.values()) + ["index.html"]:
        w = _proto(make_page, base_url, file)
        assert w.errors == [], (file, w.errors)
        assert "Rashad Fambro Consulting" in w.page.inner_text("body")
        if file != "index.html":
            w.page.fill("#bizName", "Sunset Barbers")
            assert "Sunset Barbers" in w.page.inner_text("header")
            assert "nothing is sent" in w.page.inner_text(".banner")



def test_R45_prototype_core_flows(make_page, base_url):
    # RewardsDesk: look up, add points, approve an offer
    pg = _proto(make_page, base_url, "rewards.html").page
    pg.fill("#phone", "555-0142"); pg.click("#lookup"); pg.fill("#amt", "30"); pg.click("#addPts")
    assert "Reward ready" in pg.inner_text("#rewardBox")
    pg.click("[data-tab=offers]"); n = pg.locator("[data-ok]").count(); pg.locator("[data-ok]").first.click()
    assert pg.locator("[data-ok]").count() == n - 1
    # ReviewDesk: draft a reply to a 2-star review and post it
    pg = _proto(make_page, base_url, "reviews.html").page
    pg.click("[data-r='2']"); assert "sorry" in pg.input_value("#reply").lower()
    pg.click("#post"); assert pg.locator("[data-r='2']").count() == 0
    pg.click("[data-tab=ask]"); pg.click("[data-star='2']"); assert "Leave a Google review" in pg.inner_text("#askResult")
    # SocialDesk: draft a month, approve, schedule; DM keyword
    pg = _proto(make_page, base_url, "social.html").page
    pg.click("#gen"); assert pg.locator("[data-post]").count() == 12
    pg.locator("[data-app]").first.click(); pg.click("#sched"); assert "Scheduled" in pg.inner_text("#posts")
    pg.click("[data-tab=dms]"); pg.click("#testDm"); assert "PRICE" in pg.inner_text("#dmOut")
    # StaffDesk: answer from the handbook, unknown goes to a manager
    pg = _proto(make_page, base_url, "staff.html").page
    pg.click("#askBtn"); assert "Closing the register" in pg.inner_text("#ans")
    pg.fill("#q", "Is parking reimbursed?"); pg.click("#askBtn"); assert "manager" in pg.inner_text("#ans")
    # InvoiceDesk: quote -> invoice -> send; reminders exist
    pg = _proto(make_page, base_url, "invoices.html").page
    pg.locator("[data-conv]").first.click(); pg.click("[data-tab=invoices]"); pg.click("#sendInv")
    assert "Invoice #1043" in pg.inner_text("#preview")
    pg.click("[data-tab=remind]"); assert pg.locator("[data-rs]").count() >= 2
    # InsightDesk: summary and before/after
    pg = _proto(make_page, base_url, "insights.html").page
    pg.click("#nextWk"); pg.click("[data-tab=summary]"); assert "Good morning" in pg.inner_text("#sumTxt")
    pg.click("[data-tab=impact]"); assert "%" in pg.inner_text("#baRows")


# ---------------- v11: fixes from the external site review ----------------
def test_R46_static_html_reads_clean_for_crawlers():
    from urllib.parse import unquote
    s = open(site_file("index.html"), encoding="utf-8").read()
    assert "couldn’t be sent automatically" not in s.split("<script")[0]
    assert 'id="vPhoneRow"' not in s.split("<script")[0]
    assert '© <span id="yr">2026</span>' in s
    assert "Continue to secure checkout" not in s.split("<script")[0]


def test_R47_order_button_matches_payment_setup(home):
    pg = home.page
    if "squareLinks" in pg.content():
        pg.locator("[data-buy='assess']").first.click()
        assert pg.inner_text("#buyGo") == "Continue to secure checkout →"   # PayPal.me covers any amount
        pg.click("#buyClose")
        pg.evaluate("CONFIG.paypalMe=''; CONFIG.squareLinks={}")   # no hosted checkout configured: falls back to an emailed invoice
        pg.locator("[data-buy='assess']").first.click()
        assert pg.inner_text("#buyGo") == "Send my order request →"
        return
    pg.locator("[data-buy='assess']").first.click()
    assert pg.inner_text("#buyGo") == ("Send my order request →" if is_v15(pg) else "Place my order →")
    pg.click("#buyClose")
    pg.evaluate("CONFIG.payLinks.assess.paypal='https://example.com/pay'")
    pg.locator("[data-buy='assess']").first.click()
    assert pg.inner_text("#buyGo") == "Continue to secure checkout →"


def test_R48_email_draft_fallback_is_clean(make_page, base_url):
    from urllib.parse import unquote, urlparse, parse_qs
    w = make_page(); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    pg.fill("#a_name", "José Núñez"); pg.fill("#a_biz", "Café & Co — Downtown"); pg.fill("#a_email", "jose@example.com")
    pg.fill("#a_flow", "Bookings by DM; 40% no-shows"); pg.fill("#a_notes", "Two locations, it’s urgent")
    pg.click("#auditForm button[type=submit]")
    pg.wait_for_selector("#auditResult:not([hidden])", timeout=10000)
    assert "One Last Step" in pg.inner_text("#auditResult h4")
    assert "couldn’t be sent automatically" in pg.inner_text("#auditResultNote")
    href = pg.get_attribute("#auditMail", "href")
    q = parse_qs(urlparse(href).query)
    assert q["subject"][0] == "Free workflow audit request — Café & Co — Downtown"
    body = q["body"][0]
    for part in ["José Núñez", "Café & Co — Downtown", "40% no-shows", "Two locations, it’s urgent"]:
        assert part in body
    assert "�" not in body and "%" not in body.replace("40%", "")
    assert w.errors == []


def test_R49_plan_prices_are_consistent(home):
    P = site_prices(home.page)
    assert P["std"] == sorted(P["std"]) and P["prop"] == sorted(P["prop"]) and len(P["std"]) == len(P["prop"]) == 3
    assert P["prop"][0] >= P["std"][0]   # per-property plans never cheaper than standard ones


def test_R50_privacy_policy_page(make_page, base_url, home):
    assert home.page.get_attribute("footer a[href='privacy.html']", "href") == "privacy.html"
    assert home.page.locator("#auditForm a[href='privacy.html']").count() == 1
    w = make_page(); w.page.goto(base_url + "privacy.html"); w.page.wait_for_timeout(200)
    t = w.page.inner_text("body")
    for x in ["Privacy Policy", "What I Collect", "FormSubmit", "PayPal and Square", "delete", "Effective November 13, 2026"]:
        assert x in t, x
    assert w.errors == []


def test_R51_paypal_me_checkout_link(make_page, base_url):
    w = open_home(make_page, base_url, when=AFTER_SALE); pg = w.page
    pg.evaluate("CONFIG.paypalMe='TestHandle'")
    a = site_prices(pg)["assess"]
    assert pg.evaluate("payLinkFor('assess','PayPal')") == f"https://paypal.me/TestHandle/{a}USD"
    assert pg.evaluate("payLinkFor('assess','Square')").startswith("https://square.link/u/")   # one Square link per amount
    pg.locator("[data-buy='assess']").first.click()
    assert pg.inner_text("#buyGo") == "Continue to secure checkout →"
    w2 = open_home(make_page, base_url, when=SALE_DAY)
    w2.page.evaluate("CONFIG.paypalMe='TestHandle'")
    assert w2.page.evaluate("payLinkFor('assess','PayPal')") == f"https://paypal.me/TestHandle/{sale_price(a)}USD"


def test_R52_checkout_prices_match_listed_prices(home):
    pg = home.page
    pairs = pg.evaluate("""() => { const num = s => +((s.match(/\\$([\\d,]+)/) || [0, "0"])[1].replace(/,/g, ""));
      const pk = Object.fromEntries(CONFIG.packages.map(p => [p.id, num(p.price)]));
      return [[BUYABLE.assess.price, pk.assess], [BUYABLE.pilot.price, pk.pilot], [BUYABLE.care.monthly, pk.care]]; }""")
    for got, listed in pairs:
        assert got == listed, (got, listed)


def test_R53_all_prices_are_round_numbers(home, make_page, base_url):
    P = site_prices(home.page)
    nums = P["std"] + P["prop"] + [P["assess"], P["bundle"], P["hotel"]]
    nums += [int(x.replace(",", "")) for v in P["products"].values() for x in re.findall(r"\$([\d,]+)", v)]
    nums += [int(x.replace(",", "")) for x in re.findall(r"\$([\d,]+)", home.page.inner_text("#pricing"))]
    assert all(n % 10 == 0 for n in nums), [n for n in nums if n % 10]
    w = open_home(make_page, base_url, when=SALE_DAY)   # sale prices stay round too
    sale_nums = [int(x.replace(",", "")) for x in re.findall(r"\$([\d,]+)", w.page.inner_text("#products"))]
    assert sale_nums and all(n % 10 == 0 for n in sale_nums)


def test_R54_hero_profile_copy_and_bundles(home):
    pg = home.page
    hero = pg.inner_text(".hero")
    v21 = "Any industry" in hero
    lead = "17 years building software products and solutions" if v21 else "17 years building software products and solutions with customers"
    for x in [lead, "Human-Approved AI", "Virtual or On-site", "Pilots within weeks", "Integration with existing systems"] + (["Any industry", "Free 14-day trial", "You own your data"] if v21 else []):
        assert x in hero, x
    prof = pg.inner_text(".profile")
    if "MORE_ORDER" not in pg.content():
        assert "engineering & testing software products and solutions" in prof and "Available virtually worldwide, or on-site at your business" in prof
        assert "deliver software products that solve them" in pg.inner_text("#about")
    assert "Meets" not in prof
    offers = pg.inner_text(".offers")
    assert "Property Management Bundle" in offers and "ComplianceDesk" not in offers
    pg.locator("[data-buy='propbundle']").click()
    assert "Property Management Bundle" in pg.inner_text("#buyTitle")
    assert "30 days" not in pg.inner_text("#buyModal")


def test_R55_old_solutions_link_and_readable_also_line(make_page, base_url):
    w = make_page(width=390, height=844); pg = w.page
    pg.goto(base_url + "index.html#solutions"); pg.wait_for_timeout(1800)
    assert pg.locator("#solutions").count() == 1
    y = pg.evaluate("document.getElementById('solutions').getBoundingClientRect().top")
    assert abs(y) < 200      # lands at the products section, not the top of the page
    col = pg.evaluate("getComputedStyle(document.querySelector('#products .also b')).color")
    assert col == "rgb(255, 255, 255)"


def test_R56_tool_one_liners_and_clean_text(home):
    pg = home.page
    pg.click("#toolLines > summary")
    t = pg.inner_text("#toolLines")
    for x in ["ChatDesk — answers customer questions 24/7", "PackageDesk — package intake with pickup codes", "ComplianceDesk"]:
        assert x in t, x
    assert pg.locator(".tier-foot abbr").count() == 15
    tc = pg.evaluate("document.body.textContent")
    for bad in ["LocationAvailable", "Branded for Your BusinessYour", "wkpilot", "47staff", "0.3full"]:
        assert bad not in tc, bad


def test_R57_prices_match_everywhere_and_security(make_page, base_url):
    w = make_page(); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(400)
    sale = pg.evaluate("saleActive()")
    p = site_prices(pg)
    # The plan picker in checkout shows the same sale price as the header
    pg.locator("[data-buy='chat']").first.scroll_into_view_if_needed() if pg.locator("[data-buy='chat']").count() else None
    pg.evaluate("openBuy('chat','buy')"); pg.wait_for_timeout(200)
    first = pg.inner_text("#tierRadios label:first-child")
    std0 = p["std"][0]
    exp = dollars(sale_price(std0)) if sale else dollars(std0)
    assert exp + "/mo" in first.replace(".00", ""), first
    assert exp in pg.inner_text("#buyPrice").replace(".00", "")
    due = pg.inner_text("#dueNote")
    assert "Due at kickoff" in due and "Monthly" in due, due
    pg.click("#buyClose")
    # The proposal request shows the same assessment price as the package card
    pg.evaluate("openStart()"); pg.wait_for_timeout(200)
    a = p["assess"]; shown = dollars(sale_price(a)) if sale else dollars(a)
    assert shown in pg.inner_text("#bPkgs"), pg.inner_text("#bPkgs")
    if sale:
        assert "or more off" in pg.inner_text("#saleText")
    # Security: CSP + referrer policy on every page; honeypot field on every form
    for rel in ["index.html", "products.html", "privacy.html", "industries/hotels.html", "prototypes/reviews.html", "tools/audit-summary.html"]:
        html = open(site_file(rel), encoding="utf-8").read()
        assert 'http-equiv="Content-Security-Policy"' in html and "object-src 'none'" in html, rel
        assert 'name="referrer"' in html, rel
    assert pg.locator("#auditForm input[name=company_website], #builder input[name=company_website], #buyForm input[name=company_website]").count() == 3
    assert not w.errors, w.errors


def test_R58_reviewdesk_invites_everyone_the_same(make_page, base_url):
    w = make_page(); pg = w.page
    pg.goto(base_url + "prototypes/reviews.html"); pg.wait_for_timeout(400)
    pg.click("text=Ask for Reviews")
    shown = []
    for n in (1, 5):
        pg.click(f"[data-star='{n}']"); pg.wait_for_timeout(150)
        t = pg.inner_text("#askResult")
        assert "Leave a Google review" in t and "Send private feedback" in t, t
        shown.append(t.split("We'd love")[1])
    assert shown[0] == shown[1]
    for rel in ["index.html", "products.html", "prototypes/reviews.html", "prototypes/index.html"]:
        html = open(site_file(rel), encoding="utf-8").read().lower()
        assert "happy customers" not in html and "unhappy" not in html, rel
    assert not w.errors, w.errors


def test_R59_client_owned_model_and_allowances(home):
    pg = home.page
    if "Who Owns My Data" not in pg.content():
        pytest.skip("client-owned pricing is staged, not yet promoted")
    pr = pg.text_content("#pricing")
    for x in ["You own the accounts and the data", "$150/hour in 30-minute blocks", "Defect fixes are always free",
              "Fully Hosted (by request)", "1,000 AI conversations", "$10 per extra 500 texts"]:
        assert x in pr, x
    notes = pg.evaluate("CONFIG.tiers.std.map(t=>t.note).join(' | ')")
    assert "1 small change/mo" in notes and "3 small changes/mo" in notes and "6 small changes/mo" in notes
    pg.click("text=Who Owns My Data and Accounts?")
    assert "invited admin" in pg.inner_text("#faq")
    assert not home.errors, home.errors


def test_R60_featured_products_ctas_sample_audit_and_scope(make_page, base_url):
    w = make_page(); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    if not is_v15(pg):
        pytest.skip("staged, not yet promoted")
    # One main hero button; the demo is a secondary text link
    assert pg.locator(".hero .btn").count() == 1 and "free workflow audit" in pg.inner_text(".hero .btn-primary").lower()
    # Three featured tools; the other 12 are collapsed, with the full catalog in the Product Guide
    names = pg.eval_on_selector_all("#prodGrid .prod h3", "els => els.map(e => e.textContent)")
    assert names in (["WorkOrderDesk", "ChatDesk", "BookDesk"], ["WorkOrderDesk", "LeadDesk", "ChatDesk"]), names
    assert not pg.is_visible("#prodGridMore") and pg.locator("#prodGridMore .prod").count() == 12
    pg.click("#moreProducts > summary")
    assert pg.is_visible("#prodGridMore") and pg.locator("#moreProducts a[href='products.html']").count() == 1
    # Button labels describe what happens next
    v17 = _v17()
    assert pg.inner_text("[data-buy='chat']") == ("Order now" if v17 else "Request order")
    assert pg.inner_text("[data-buy='property']") == ("Order now" if v17 else "Request a pilot")
    assert pg.locator("text=Try demo").count() >= 1 and pg.locator("text=Try prototype ↗").count() >= 1
    assert pg.locator("button:text('Buy')").count() == 0 and pg.locator("text=Buy the bundle").count() == 0
    pg.locator(f"[data-buy='{'pilot' if v17 else 'property'}']").first.click()
    assert pg.text_content("#buyEyebrow") == "Request a Pilot" and pg.inner_text("#buyGo") == "Request my pilot →"
    pg.click("#buyClose")
    # Fictional sample audit with the four parts a real one has
    pg.click("#sampleAudit > summary")
    sa = pg.inner_text("#sampleAudit")
    for x in ["Fictional example", "Biggest bottleneck", "Recommended first change", "Baseline to measure"]:
        assert x in sa, x
    # Pilot scope and timing agree across pricing, FAQ and chat
    assert "Workflow & Automation Assessment" in pg.inner_text("#pricing") and "AI Readiness" not in pg.content()
    pr = pg.text_content("#pricing")
    assert "1 location, up to 2 workflows" in pr and "1–2 weeks of team testing" in pr
    assert pg.evaluate("CONFIG.packages.find(p => p.id === 'pilot').note") == "3–8 weeks to launch"
    assert "3–8 weeks: 2–6 weeks to build, then 1–2 weeks of testing" in pg.text_content("#faq")
    pg.click("#chatFab"); assert "3–8 weeks" in chat(pg, "how long does it take?")
    assert not w.errors, w.errors


def _v17():
    return "Starter edition" in open(site_file("index.html"), encoding="utf-8").read()


def _v16(base_url_page):
    return "MORE_ORDER" in open(site_file("index.html"), encoding="utf-8").read()


def test_R61_every_tool_has_a_working_trial_app(make_page, base_url):
    if not _v16(None):
        pytest.skip("staged, not yet promoted")
    checks = [("workorders.html", "#submit", "#triage", "Plumbing"), ("bookings.html", "[data-slot='9:00']", "#rows", "9:00"),
              ("packages.html", "#add", "#rows", "Dana"), ("leads.html", "#add", "#apList", "First reply"),
              ("guests.html", "#route", "#apList", "Housekeeping"), ("compliance.html", "[data-t='0']", "#tasks", "Done")]
    for f, btn, out, exp in checks:
        w = make_page(); pg = w.page
        pg.goto(base_url + "prototypes/" + f); pg.wait_for_timeout(300)
        pg.click(btn); pg.wait_for_timeout(200)
        assert exp in pg.text_content(out), f
        assert not w.errors, (f, w.errors)
    w = make_page(); pg = w.page
    pg.goto(base_url + "prototypes/chat.html"); pg.wait_for_timeout(300)
    pg.fill("#q", "what are your hours?"); pg.press("#q", "Enter"); pg.wait_for_timeout(200)
    assert "9 AM" in pg.inner_text("#log")
    pg.fill("#q", "do you fix boats?"); pg.press("#q", "Enter"); pg.wait_for_timeout(200)
    assert "do you fix boats?" in pg.text_content("#hoList")
    w = make_page(); pg = w.page
    pg.goto(base_url + "prototypes/housekeeping.html"); pg.wait_for_timeout(300)
    pg.click("[data-tab='assign']"); pg.click("#auto"); pg.wait_for_timeout(200)
    assert "Room" in pg.text_content("#att") and not w.errors
    w = make_page(); pg = w.page
    pg.goto(base_url + "prototypes/intake.html"); pg.wait_for_timeout(300)
    assert "Missing" in pg.text_content("#subList") and not w.errors


def test_R62_trial_links_count_down_expire_and_reject_tampering(make_page, base_url):
    if not _v16(None):
        pytest.skip("staged, not yet promoted")
    import datetime
    w = make_page(); pg = w.page
    pg.goto(base_url + "prototypes/workorders.html"); pg.wait_for_timeout(200)
    today = datetime.date.today()
    def link(start, biz="Lakeview Apartments", tools="property"):
        key = pg.evaluate(f"trialKey('{tools}', '{biz}', '{start}')")
        return f"?trial={key}&biz={biz.replace(' ', '%20')}&color=%23aa3355&start={start}&tools={tools}"
    pg.goto(base_url + "prototypes/workorders.html" + link(today.isoformat())); pg.wait_for_timeout(300)
    b = pg.inner_text(".banner")
    assert "Free 14-day trial for Lakeview Apartments" in b and "14 days left" in b and "Download my data" in b
    assert pg.inner_text("h1 [data-biz]") == "Lakeview Apartments"
    old = (today - datetime.timedelta(days=20)).isoformat()
    pg.goto(base_url + "prototypes/workorders.html" + link(old)); pg.wait_for_timeout(300)
    assert pg.is_visible("#trialEnd") and "has ended" in pg.inner_text(".banner")
    bad = link(today.isoformat()).replace("Lakeview", "Hackview", 1)
    pg.evaluate("localStorage.clear()")
    pg.goto(base_url + "prototypes/workorders.html" + bad); pg.wait_for_timeout(300)
    assert "isn't valid" in pg.inner_text(".banner")
    # A package opens as one product: the Desk Suite with every included tool
    pg.evaluate("localStorage.clear()")
    pg.goto(base_url + "prototypes/suite.html" + link(today.isoformat(), tools="property,package,chat")); pg.wait_for_timeout(600)
    assert pg.eval_on_selector_all("#nav button", "e => e.map(x => x.textContent)") == ["WorkOrderDesk", "PackageDesk", "ChatDesk"]
    assert "workorders.html?embed=1" in pg.get_attribute("#app", "src")
    pg.click("#nav button:nth-child(2)"); pg.wait_for_timeout(300)
    assert "packages.html" in pg.get_attribute("#app", "src")
    assert "14 days left" in pg.inner_text(".banner")
    assert not w.errors, w.errors


def test_R63_payments_profile_banner_and_product_order(make_page, base_url):
    if not _v16(None):
        pytest.skip("staged, not yet promoted")
    w = make_page(); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(400)
    names = pg.eval_on_selector_all("#prodGrid .prod h3, #prodGridMore .prod h3", "e => e.map(x => x.textContent)")
    assert names == ["WorkOrderDesk", "ChatDesk", "BookDesk", "GuestDesk", "HousekeepingDesk", "RewardsDesk", "InvoiceDesk", "LeadDesk",
                     "PackageDesk", "SocialDesk", "ReviewDesk", "StaffDesk", "InsightDesk", "IntakeDesk", "ComplianceDesk"], names
    # Ready product: pay the amount due now; built-to-order product: request without payment
    sale = pg.evaluate("saleActive()")
    full = sale_price(1500) if sale else 1500
    assert pg.evaluate("payLinkFor('chat','PayPal','Pay in full')") == f"https://paypal.me/RFambro/{int(full)}USD"
    v17 = _v17(); held = "pilot" if v17 else "property"
    if v17:
        assert pg.evaluate("payLinkFor('property','PayPal','Pay in full')") == f"https://paypal.me/RFambro/{int(sale_price(3500) if sale else 3500)}USD"
    assert pg.evaluate(f"payLinkFor('{held}','PayPal','Pay in full')") == ""
    pg.evaluate(f"openBuy('{held}','buy')"); pg.wait_for_timeout(200)
    assert not pg.is_visible("#methodOpts") and pg.is_visible("#pilotNote") and "No payment now" in pg.inner_text("#pilotNote")
    pg.click("#buyClose"); pg.evaluate("openBuy('chat','buy')"); pg.wait_for_timeout(200)
    assert pg.is_visible("#methodOpts") and pg.inner_text("#buyGo") == "Continue to secure checkout →"
    pg.click("#buyClose")
    # Profile, photo, banner
    prof = pg.inner_text(".profile")
    for x in ["17 years as an IT software professional", "Available virtually worldwide, or on-site", "AI Solutions, Workflow Automation, Custom Applications"]:
        assert x in prof, x
    assert "engineered and tested the software products and solutions" in pg.inner_text("#about")
    assert pg.evaluate("document.querySelector('.profile img.photo').naturalWidth") > 0
    if sale:
        assert pg.is_visible("#saleRound") and "rounded down" in pg.inner_text("#saleRound") and "rounded" not in pg.inner_text("#saleText")
    # Google polish: one back-to-top control; honeypot text not in the page
    assert "Back to top ↑" not in pg.inner_text("footer") and "Leave this field empty" not in pg.content()
    assert pg.inner_text("#roiYear") == "$15,324" and pg.inner_text("#roiCash") == "$280/mo"
    assert not w.errors, w.errors


def test_R64_starter_edition_orders_and_license_links(make_page, base_url):
    if not _v17():
        pytest.skip("staged, not yet promoted")
    import datetime
    w = make_page(); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    # Every tool and bundle can be ordered and paid now; only custom pilots wait for a quote
    for pid in ["property", "resort", "salon", "service", "package", "bundle", "propbundle", "hotelbundle", "assess"]:
        assert pg.evaluate(f"payLinkFor('{pid}','PayPal','Pay in full')").startswith("https://paypal.me/RFambro/"), pid
    pg.evaluate("openBuy('propbundle','buy')"); pg.wait_for_timeout(200)
    note = pg.inner_text("#deliveryNote")
    assert "Starter edition" in note and "1–3 business days" in note and "Desk Suite" in note and "acceptance checklist" in note
    assert pg.is_visible("#methodOpts") and pg.text_content("#buyEyebrow") == "Order Online"
    pg.click("#buyClose")
    assert "Starter edition in 1–3 business days" in pg.inner_text("#prodGrid")
    assert "What Exactly Am I Buying?" in pg.text_content("#faq")
    # A paid license link opens the branded Starter edition with backup and restore
    pg.goto(base_url + "prototypes/workorders.html"); pg.wait_for_timeout(200)
    until = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    key = pg.evaluate(f"licenseKey('property,package,chat','Lakeview Apartments','{until}')")
    pg.goto(base_url + f"prototypes/suite.html?license={key}&biz=Lakeview%20Apartments&color=%23225588&until={until}&tools=property,package,chat"); pg.wait_for_timeout(600)
    b = pg.inner_text(".banner")
    assert "Starter edition · licensed to Lakeview Apartments" in b and "Download backup" in b and "Restore backup" in b
    pg.goto(base_url + "prototypes/packages.html"); pg.wait_for_timeout(300)
    assert "licensed to Lakeview Apartments" in pg.inner_text(".banner") and not pg.is_visible("#reset")
    # Overdue more than 30 days: paused, data kept
    pg.evaluate("localStorage.clear()")
    old = (datetime.date.today() - datetime.timedelta(days=40)).isoformat()
    key = pg.evaluate(f"licenseKey('package','Lakeview Apartments','{old}')")
    pg.goto(base_url + f"prototypes/packages.html?license={key}&biz=Lakeview%20Apartments&until={old}&tools=package"); pg.wait_for_timeout(300)
    assert pg.is_visible("#trialEnd") and "Renew" in pg.inner_text("#trialEnd")
    # Tampered license rejected
    pg.goto(base_url + f"prototypes/packages.html?license={key}&biz=Other%20Co&until={old}&tools=package"); pg.wait_for_timeout(300)
    assert "isn't valid" in pg.inner_text(".banner")
    assert not w.errors, w.errors


def test_R65_square_checkout_covers_every_amount_due(make_page, base_url):
    """Every orderable item has a Square link for each amount due now: full, sale and first of 3 payments."""
    w = make_page(); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    missing = pg.evaluate("""(() => { const out = [];
      for (const [id, it] of Object.entries(BUYABLE)) { if (!it.price || isPilot(id) || it.quote) continue;
        const plans = it.price >= CONFIG.paymentPlan.minimum ? ["Pay in full", "3 monthly payments"] : ["Pay in full"];
        for (const plan of plans) { const amt = dueNow(id, plan);
          if (!amt) continue;
          const link = payLinkFor(id, "Square", plan);
          if (!/^https:\\/\\/square\\.link\\/u\\/[A-Za-z0-9]+$/.test(link)) out.push(`${id} ${plan} $${amt}`); } }
      return out; })()""")
    assert not missing, missing
    assert len(pg.evaluate("Object.keys(CONFIG.squareLinks)")) >= 28
    assert not w.errors, w.errors


def test_R66_bundle_sale_prices_checkout_opens_at_top_and_narrow_screens(make_page, base_url):
    w = make_page(width=390, height=700); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(400)
    sale = pg.evaluate("saleActive()")
    for bid, price, parts in [("bundle", 2500, [1500, 1500]), ("hotelbundle", 8000, [3500, 3500, 3500]), ("propbundle", 5500, [3500, 2000, 1500])]:
        card = pg.locator(f"[data-buy='{bid}']").first.locator("xpath=ancestor::article[1]").inner_text()
        if sale:
            s = sale_price(price)
            assert dollars(s) in card and f"save {dollars(sum(sale_price(x) for x in parts) - s)}" in card, card
        # Checkout opens at the top: title and close button visible, focus on the title
        pg.locator(f"[data-buy='{bid}']").first.scroll_into_view_if_needed(); pg.locator(f"[data-buy='{bid}']").first.click(); pg.wait_for_timeout(200)
        assert pg.evaluate("document.activeElement.id") == "buyTitle"
        assert pg.evaluate("document.getElementById('buyClose').getBoundingClientRect().top >= 0 && document.getElementById('buyTitle').getBoundingClientRect().top >= 0")
        pg.click("#buyClose")
    if sale:
        assert pg.evaluate("document.querySelector('.salebar .sale-l2 a').getClientRects().length") == 1   # arrow stays with its words
    # Estimator: setup and monthly follow the tool; bundles count usage for every tool
    pg.select_option("#roiTool", "propbundle")
    assert pg.inner_text("#roiSetup") == "$5,500" and pg.inner_text("#roiCost") == dollars(pg.evaluate("BUYABLE.propbundle.monthly") + 60) + "/mo"
    for width in (320, 375, 390, 414, 430):
        w2 = make_page(width=width, height=800); p2 = w2.page
        p2.goto(base_url + "index.html"); p2.wait_for_timeout(300)
        assert p2.evaluate("document.documentElement.scrollWidth") <= width, width
    assert not w.errors, w.errors


def test_R67_after_sale_rates_paybacks_lead_path_and_banner(make_page, base_url):
    w = make_page(); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(400)
    sale = pg.evaluate("saleActive()")
    P = site_prices(pg)
    # Checkout states the monthly rate after the sale and the Fully Hosted alternative
    pg.evaluate("openBuy('property','buy')"); pg.wait_for_timeout(150)
    note = pg.inner_text("#dueNote"); reg = P["prop"][0]
    if sale:
        assert f"then {dollars(reg)}/mo" in note, note
    assert f"Fully Hosted: {dollars(reg + 150)}/mo" in note, note
    pg.click("#buyClose")
    # Estimator: payback with staff time and cash-only payback, both labeled
    assert pg.inner_text("#roiPayback") == "1.1 months" and pg.inner_text("#roiCashPayback") == "5.4 months"
    assert "counting staff time" in pg.inner_text("#roi") and "cash-only payback" in pg.inner_text("#roi")
    pg.eval_on_selector("#r5", "(el) => { el.value = 0; el.dispatchEvent(new Event('input')); }")
    assert pg.inner_text("#roiCashPayback") == "No cash payback at these inputs"
    # Trial buttons set expectations; quote-driven visitors get a direct path to LeadDesk
    assert pg.locator("[data-trial]").first.inner_text() == "Request a branded trial"
    pg.click("[data-goto='service']"); pg.wait_for_timeout(900)
    assert pg.evaluate("document.getElementById('moreProducts').open") and pg.is_visible("#p-service")
    assert "path:service" in pg.evaluate("sessionStorage.getItem('rf-interest')")
    # Packages: simple comparison first, billing rules tucked into a panel
    assert "Client-Owned" in pg.inner_text(".host-compare") and "Fully Hosted" in pg.inner_text(".host-compare")
    assert not pg.is_visible("#billingDetails p")
    # Banner leads with the offer; rounding note is fine print
    if sale:
        l2 = pg.inner_text(".salebar .sale-l2")
        assert (l2.startswith("Founding clients (first 5)") or l2.startswith("Founding clients (first 5, ")) and "rounded" not in l2
    # Hero steps: number and text don't run together
    assert "1 Request captured" in pg.text_content("#heroPipe").replace("\n", " ")
    assert not w.errors, w.errors


def test_R68_leads_carry_site_activity(make_page, base_url):
    w = make_page(); pg = w.page
    sent = []
    pg.context.route(re.compile(r"https://formsubmit\.co/.*"), lambda r: (sent.append(r.request.post_data or ""), r.fulfill(status=200, body='{"success":"true"}', content_type="application/json")))
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    pg.evaluate("noteInterest('demo:property'); noteInterest('order:service')")
    pg.evaluate("sendLead('audit', {Name:'Test', Email:'t@example.com'})"); pg.wait_for_timeout(400)
    assert sent and "demo:property" in sent[0] and "order:service" in sent[0], sent


def _is_v21(pg):
    return pg.locator("#svcGrid").count() == 1


def test_R69_website_and_growth_services_orderable(make_page, base_url):
    w = make_page(); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    if not _is_v21(pg):
        pytest.skip("before v21")
    names = pg.locator("#svcGrid h3").all_inner_texts()
    assert names == ["Launch Website", "Booking Website", "30-Day Customer Comeback", "Site Care"], names
    for sid, regular in [("site1", 500), ("site5", 1500), ("comeback", 750)]:
        assert pg.evaluate(f"BUYABLE['{sid}'].price") == regular
        for plan in (["Pay in full", "3 monthly payments"] if regular >= 1000 else ["Pay in full"]):
            due = pg.evaluate(f"dueNow('{sid}', '{plan}')")
            assert due % 10 == 0 and pg.evaluate(f"payLinkFor('{sid}', 'Square', '{plan}')").startswith("https://square.link/u/"), (sid, plan, due)
        pg.click(f'#svcGrid [data-buy="{sid}"]')
        assert not pg.locator("#buyModal").is_hidden()
        pg.click("#buyClose")
    assert "own hosting account" in pg.inner_text("#svcGrid") and "your domain and hosting" in pg.inner_text("#services")
    assert not w.errors, w.errors


def test_R70_cross_industry_positioning(make_page, base_url):
    w = make_page(); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    if not _is_v21(pg):
        pytest.skip("before v21")
    assert "Any industry" in pg.inner_text(".hero-points")
    desc = pg.get_attribute('meta[name="description"]', "content") or ""
    og = pg.get_attribute('meta[property="og:description"]', "content") or ""
    assert "property" not in (desc + og).lower(), (desc, og)
    chips = pg.locator(".card.focus h3").all_inner_texts()
    assert len(chips) >= 4 and any("Salons" in c for c in chips) and any("Contractors" in c for c in chips), chips
    outcomes = pg.locator(".prod .outcome").count()
    assert outcomes == pg.locator(".prod").count() and outcomes >= 15, outcomes
    assert "Annual prepay" in pg.inner_text("#pricing")


def test_R71_founding_counter_follows_backend(make_page, base_url):
    w = make_page(); pg = w.page
    pg.context.route(re.compile(r"https://script\.google\.com/.*stats=founding.*"),
                     lambda r: r.fulfill(status=200, body='{"ok":true,"foundingLeft":3}', content_type="application/json"))
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    if not _is_v21(pg) or not pg.evaluate("CONFIG.backendUrl"):
        pytest.skip("before v21 or no backend")
    wait_js(pg, "document.getElementById('spots').textContent === '3'")
    assert pg.locator(".fLeft").first.inner_text() == "3"
    pg.evaluate("showFounding(0)")
    assert pg.is_hidden("#founding")
