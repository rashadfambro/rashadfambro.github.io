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
    assert re.search(r"Experience\s+17 years as an IT professional", prof) and "Former" not in prof
    assert "on-site" in prof.lower()


def test_R04_founding_program_terms(home):
    t = home.page.inner_text("#founding")
    assert "25% off" in t and "testimonial" in t.lower() and "30%" not in t


def test_R05_offer_amounts(home):
    t = home.page.inner_text(".offers"); P = site_prices(home.page)
    assert "$150 credit" in t and dollars(P["assess"]) + " assessment" in t and dollars(P["bundle"]) in t and dollars(P["hotel"]) in t


# ---------------- holiday sale ----------------
def test_R06_sale_banner_during_and_after(make_page, base_url):
    w = open_home(make_page, base_url, when=SALE_DAY)
    assert w.page.is_visible("#saleBar") and "10% off" in w.page.inner_text("#saleBar")
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
    pg.click("#buyGo")
    pg.wait_for_function("document.getElementById('buyResult').innerText.trim().length > 0", timeout=10000)
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
    ("is there a free trial?", ["14-day trial", "license key"]),
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
    assert "10% off" in chat(w.page, "is there a holiday sale?")


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
def test_R14_roi_math(home):
    pg = home.page
    for k, v in {"r1": 10, "r2": 5, "r3": 30, "r4": 40, "r5": 4, "r6": 1000}.items():
        pg.eval_on_selector(f"#{k}", f"(el) => {{ el.value = {v}; el.dispatchEvent(new Event('input')); }}")
    hrs = 10 * 5 * 0.40 * 4.33
    labor = round(hrs * 12 * 30); leads = round(4 * 0.25 * 1000 * 12)
    assert pg.inner_text("#roiHours") == f"{round(hrs):,}"
    assert pg.inner_text("#roiLabor") == f"${labor:,}"
    assert pg.inner_text("#roiLeads") == f"${leads:,}"
    assert pg.inner_text("#roiTotal") == f"${labor + leads:,}"


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
    pg.wait_for_function("document.getElementById('buyResult').innerText.trim().length > 0", timeout=10000)
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
    assert w.page.evaluate("getComputedStyle(document.getElementById('saleFine')).display") == "block"


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
    pg.click("#toTop"); pg.wait_for_function("window.scrollY < 5", timeout=5000)
    pg.evaluate("window.scrollTo(0, 3000)"); pg.wait_for_timeout(200)
    pg.click("#nav a[data-home]"); pg.wait_for_function("window.scrollY < 5", timeout=5000)
    assert pg.locator("#nav a").first.inner_text() == "Home"
    assert home.errors == []


@pytest.mark.parametrize("path", ["products.html", "industries/hotels.html"])
def test_R34_subpage_home_and_top(make_page, base_url, path):
    w = make_page(); pg = w.page
    pg.goto(base_url + path)
    assert pg.locator("header a", has_text="Home").count() == 1
    pg.evaluate("window.scrollTo(0, 2500)"); pg.wait_for_timeout(200)
    assert pg.is_visible("#toTop")
    pg.click("#toTop"); pg.wait_for_function("window.scrollY < 5", timeout=5000)
    assert w.errors == []


# ---------------- v8: email review fixes, booking, delivery ----------------
def test_R35_meaningful_defaults_without_interaction(make_page, base_url):
    w = make_page(); pg = w.page
    pg.route("**/*.js", lambda r: r.abort())       # simulate crawlers / link previews (no scripts)
    pg.goto(base_url + "index.html")
    html = pg.content()
    assert "requests handled" not in html and ">0 hrs<" not in html
    assert "$21,868" in pg.inner_text("#roiTotal") and "47" == pg.inner_text("#roiHours").strip()
    assert "Loading QR" not in html and pg.locator("#qr svg").count() == 1
    foot = pg.inner_text(".board-foot")
    for x in ["<2 min", "100%", "2–6 wk"]:
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
    pg.wait_for_function("document.querySelector('#auditResult h4').innerText.includes('received')", timeout=10000)
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
    pg.wait_for_function("document.getElementById('buyResult').innerText.trim().length > 0", timeout=15000)
    assert "on its way" in pg.inner_text("#buyResult")
    assert seen[-1][1]["_subject"].startswith("Trial request") and "PackageDesk" in seen[-1][1]["Workflow"]


def test_R42_multi_industry_wording_and_packagedesk(home):
    pg = home.page
    ind = pg.inner_text("#industries")
    assert "Multi-industry solutions with workflow customizations" in ind
    assert "Current focus" not in ind and "first focus" not in ind.lower()
    assert "PackageDesk" in pg.inner_text("#prodGrid")
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


def _proto(make_page, base_url, file):
    w = make_page(); w.page.goto(base_url + "prototypes/" + file); w.page.wait_for_timeout(300)
    return w


def test_R43_every_product_has_a_demo_or_prototype(home, base_url):
    pg = home.page
    assert pg.evaluate("PRODUCTS.every(p => p.status === 'Prototype' || p.status.startsWith('Live'))")
    for pid, file in PROTOS.items():
        href = pg.get_attribute(f"[data-proto-link='{pid}']", "href")
        assert href == f"prototypes/{file}"
    assert "Ready to build" not in pg.inner_text("#prodGrid")


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
    pg.click("[data-tab=ask]"); pg.click("[data-star='2']"); assert "privately" in pg.inner_text("#askResult")
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
    pg.locator("[data-buy='assess']").first.click()
    assert pg.inner_text("#buyGo") == "Place my order →"
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
    assert pg.evaluate("payLinkFor('assess','Square')") == ""
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
    for x in ["17 years building software products and solutions with customers", "Human-Approved AI", "Virtual or On-site", "Pilots within weeks", "Integration with existing systems"]:
        assert x in hero, x
    prof = pg.inner_text(".profile")
    assert "engineering & testing software products and solutions" in prof and "Available virtually worldwide, or on-site at your business" in prof
    assert "Meets" not in prof
    assert "deliver software products that solve them" in pg.inner_text("#about")
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
