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
    assert "on-site" in prof.lower()


def test_R04_founding_program_terms(home):
    t = home.page.inner_text("#founding")
    assert "25% off" in t and "testimonial" in t.lower() and "30%" not in t


def test_R05_offer_amounts(home):
    t = home.page.inner_text(".offers")
    assert "$150 credit" in t and "$750 assessment" in t and "$1,699" in t and "$5,999" in t


# ---------------- holiday sale ----------------
def test_R06_sale_banner_during_and_after(make_page, base_url):
    w = open_home(make_page, base_url, when=SALE_DAY)
    assert w.page.is_visible("#saleBar") and "10% off" in w.page.inner_text("#saleBar")
    assert "$675" in w.page.inner_text("#pkgGrid")  # $750 -> $675
    w2 = open_home(make_page, base_url, when=AFTER_SALE)
    assert not w2.page.is_visible("#saleBar")
    assert "$675" not in w2.page.inner_text("#pkgGrid") and "$750" in w2.page.inner_text("#pkgGrid")


def test_R07_sale_price_math_on_products(make_page, base_url):
    w = open_home(make_page, base_url, when=SALE_DAY)
    chat_card = w.page.locator(".prod", has_text="ChatDesk").first.inner_text()
    assert "$900" in chat_card and "$26/mo" in chat_card


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
    assert not pg.is_visible("#planOpt")          # $150/mo plan: no installment option
    pg.click("#buyClose")
    pg.locator("[data-buy='chat']").first.click()
    assert pg.is_visible("#planOpt")              # $1,000 setup: installments offered
    assert pg.locator("input[name=tier]").count() == 3   # Essentials / Growth / Pro
    pg.check("input[name=tier][value='1']")
    assert "$59/mo" in pg.inner_text("#buyPrice")
    pg.click("#buyGo")
    assert "required" in pg.inner_text("#buyErr")
    pg.fill("#buy_name", "Pat Buyer"); pg.fill("#buy_biz", "Pat Co"); pg.fill("#buy_email", "pat@example.com")
    pg.click("#buyGo")
    assert "checkbox" in pg.inner_text("#buyErr")
    pg.check("#buy_ok"); pg.check("input[name=plan][value='3 monthly payments']"); pg.check("input[name=method][value='PayPal']")
    pg.click("#buyGo"); pg.wait_for_timeout(400)
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
    ("how much does it cost?", ["$750", "$2,500", "$150/mo"]),
    ("tell me about the founding client program", ["25% off", "testimonial"]),
    ("Do you meet in person?", ["on-site", "travel"]),
    ("do you offer payment plans?", ["3 interest-free"]),
    ("can I buy online?", ["Square", "PayPal"]),
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
    # the QR library loads from a CDN; offline it falls back to a message after a few seconds
    pg.wait_for_function("() => document.querySelector('#qr svg') || /unavailable/.test(document.getElementById('qr').innerText)", timeout=15000)
    assert "save this website" in pg.inner_text("#qrNote")
    if ONLINE:
        assert pg.locator("#qr svg").count() == 1
    else:
        assert pg.locator("#qr svg").count() == 1 or "unavailable" in pg.inner_text("#qr")


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
    assert "$1,875 setup" in t and "25% off" in t   # WorkOrderDesk $2,500 with founding discount


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
    assert len(trial_ids) == 14
    pg.locator("[data-trial='housekeeping']").click()
    assert "14-Day Trial" in pg.inner_text("#buyTitle")
    assert not pg.is_visible("#methodOpts") and not pg.is_visible("#buyTerms") and pg.is_visible("#trialNote")
    assert "Free for 14 days, then" in pg.inner_text("#buyPrice") and "$49/mo" in pg.inner_text("#buyPrice")
    pg.fill("#buy_name", "Tia Trial"); pg.fill("#buy_biz", "Seaside Resort"); pg.fill("#buy_email", "tia@example.com")
    pg.click("#buyGo"); pg.wait_for_timeout(400)
    assert "press Send" in pg.inner_text("#buyResult")
    href = pg.get_attribute("#buyResult a", "href")
    assert href.startswith(f"mailto:{OWNER_EMAIL}") and "free%20trial" in href.lower()
    assert w.errors == []


def test_R29_monthly_plan_tiers(make_page, base_url):
    w = open_home(make_page, base_url, when=AFTER_SALE)
    t = w.page.inner_text("#tiers")
    for x in ["Essentials", "Growth", "Pro", "$29/mo", "$59/mo", "$99/mo", "$49/mo", "$179/mo", "$69/mo", "14-day trial"]:
        assert x in t, x


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
    prices = home.page.evaluate("Object.fromEntries(PRODUCTS.map(p => [p.name, p.price]))")
    expect = {"RewardsDesk": "$750", "ReviewDesk": "$150", "SocialDesk": "$750", "LeadDesk": "$1,000", "IntakeDesk": "$1,250", "ComplianceDesk": "$2,500"}
    for k, v in expect.items():
        assert prices[k].startswith(f"Setup {v} "), (k, prices[k])
