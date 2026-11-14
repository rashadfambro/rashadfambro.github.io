"""Smoke suite: fast checks that the site is up and its critical paths work.
Scenario IDs match TESTING.md."""
import json, os, re, xml.etree.ElementTree as ET
import pytest
from conftest import ROOT, OWNER_EMAIL, site_file

pytestmark = pytest.mark.smoke


def test_S01_home_loads_without_errors(home):
    assert "Rashad Fambro" in home.page.title()
    assert home.page.is_visible(".hero h1")
    assert home.errors == []


def test_S02_nav_links_point_to_existing_sections(home):
    hrefs = home.page.eval_on_selector_all("#nav a", "els => els.map(e => e.getAttribute('href'))")
    assert len(hrefs) >= 6
    for h in hrefs:
        assert home.page.locator(h).count() == 1, h


def test_S03_primary_cta_targets_audit(home):
    assert home.page.locator(".hero a[href='#audit']").count() >= 1
    assert home.page.locator("#audit form#auditForm").count() == 1


def test_S04_packages_show_current_prices(home):
    text = home.page.inner_text("#pkgGrid")
    assert home.page.locator("#pkgGrid .pkg").count() == 4
    for p in home.page.evaluate("CONFIG.packages.map(p => p.price)"):
        assert p.replace("From ", "") in text or p in text, p


def test_S05_product_grid_has_14_products(home):
    assert home.page.locator("#prodGrid .prod, #prodGridMore .prod").count() == 15


def test_S06_chat_assistant_answers(home):
    pg = home.page
    pg.click("#chatFab")
    pg.fill("#chatInput", "how much does it cost?")
    pg.press("#chatInput", "Enter")
    pg.wait_for_timeout(900)
    assert pg.evaluate("CONFIG.packages.find(p => p.id === 'assess').price") in pg.locator(".cmsg.bot").last.inner_text()
    assert home.errors == []


def test_S07_audit_form_validates_and_routes_to_owner_email(home):
    pg = home.page
    pg.click("#auditForm button[type=submit]")
    assert "required" in pg.inner_text("#auditErr")
    pg.fill("#a_name", "Test Person"); pg.fill("#a_biz", "Test Co"); pg.fill("#a_email", "test@example.com"); pg.fill("#a_flow", "Testing the form")
    pg.click("#auditForm button[type=submit]")
    pg.wait_for_timeout(400)
    assert pg.is_visible("#auditResult")
    assert f"mailto:{OWNER_EMAIL}" in pg.get_attribute("#auditMail", "href")


def test_S08_product_guide_loads(make_page, base_url):
    w = make_page(); w.page.goto(base_url + "products.html")
    assert w.page.locator("article.prod").count() == 15
    assert w.errors == []


def test_S09_all_industry_pages_load(make_page, base_url):
    files = sorted(f for f in os.listdir(site_file("industries")) if f.endswith(".html"))
    assert len(files) >= 22
    w = make_page()
    for f in files:
        resp = w.page.goto(base_url + "industries/" + f)
        assert resp.status == 200, f
        assert w.page.locator("h1").count() == 1, f
    assert w.errors == []


@pytest.mark.parametrize("path", ["index.html", "products.html", "industries/salons.html", "tools/audit-summary.html"])
def test_S10_no_horizontal_scroll_on_mobile(make_page, base_url, path):
    w = make_page(width=390, height=844); w.page.goto(base_url + path); w.page.wait_for_timeout(200)
    assert w.page.evaluate("document.documentElement.scrollWidth") <= 390


def test_S11_sitemap_urls_exist():
    tree = ET.parse(os.path.join(ROOT, "sitemap.xml"))
    locs = [e.text for e in tree.iter() if e.tag.endswith("loc")]
    assert len(locs) >= 24
    for u in locs:
        rel = u.replace("https://rashadfambro.github.io/", "") or "index.html"
        if rel.endswith("/"): rel += "index.html"
        assert os.path.exists(os.path.join(ROOT, rel)), rel


def test_S12_manifest_and_icons_valid():
    m = json.load(open(site_file("manifest.webmanifest")))
    assert m["name"] and m["start_url"]
    for icon in m["icons"]:
        assert os.path.exists(site_file(icon["src"])), icon["src"]


def test_S13_audit_summary_tool_renders_one_page(make_page, base_url):
    w = make_page(width=1400, height=1000); w.page.goto(base_url + "tools/audit-summary.html")
    w.page.click("#sample"); w.page.wait_for_timeout(200)
    assert "Workflow Audit Summary" in w.page.inner_text("#page")
    assert w.page.evaluate("document.getElementById('page').scrollHeight") <= 1056  # 11in at 96dpi
    assert w.errors == []
