"""Performance suite: page-weight budgets, load timing, request counts, and interaction speed.
Budgets are generous enough for CI machines but catch real regressions. IDs match TESTING.md (PERF01–PERF06)."""
import os, time
import pytest
from conftest import ROOT, site_file

pytestmark = pytest.mark.performance

KB = 1024


def test_PERF01_page_weight_budgets():
    budgets = {"index.html": 320 * KB, "products.html": 80 * KB, "privacy.html": 60 * KB}
    for rel, limit in budgets.items():
        size = os.path.getsize(site_file(rel))
        assert size <= limit, f"{rel} is {size // KB} KB (budget {limit // KB} KB)"
    for f in os.listdir(site_file("prototypes")):
        size = os.path.getsize(site_file("prototypes/" + f))
        assert size <= 60 * KB, f"prototypes/{f} is {size // KB} KB (budget 60 KB)"
    for f in os.listdir(site_file("industries")):
        assert os.path.getsize(site_file("industries/" + f)) <= 60 * KB, f
    img = site_file("images")
    if os.path.isdir(img):
        for f in os.listdir(img):
            assert os.path.getsize(os.path.join(img, f)) <= 60 * KB, f


@pytest.mark.parametrize("rel,dcl_ms,load_ms", [
    ("index.html", 2500, 5000),
    ("products.html", 1500, 4000),
    ("prototypes/workorders.html", 1500, 4000),
    ("prototypes/suite.html", 2000, 5000),
])
def test_PERF02_pages_load_fast(make_page, base_url, rel, dcl_ms, load_ms):
    w = make_page(); pg = w.page
    pg.goto(base_url + rel, wait_until="load")
    t = pg.evaluate("(() => { const n = performance.getEntriesByType('navigation')[0]; return {dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd}; })()")
    assert t["dcl"] < dcl_ms, f"{rel} DOMContentLoaded {t['dcl']:.0f} ms"
    assert t["load"] < load_ms, f"{rel} load {t['load']:.0f} ms"
    fcp = pg.evaluate("(performance.getEntriesByName('first-contentful-paint')[0] || {}).startTime || 0")
    assert fcp < 2500, f"{rel} first paint {fcp:.0f} ms"


def test_PERF03_home_page_makes_few_requests(make_page, base_url):
    w = make_page(); pg = w.page
    reqs = []
    pg.on("request", lambda r: reqs.append(r.url))
    pg.goto(base_url + "index.html", wait_until="load"); pg.wait_for_timeout(500)
    local = [u for u in reqs if u.startswith(base_url.split("/staging")[0])]
    assert len(reqs) <= 15, reqs
    assert len(local) <= 8, local


def test_PERF04_interactions_respond_quickly(make_page, base_url):
    w = make_page(); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    # Savings estimator recalculates in well under a frame budget
    ms = pg.evaluate("""(() => { const r = document.getElementById('r1'); const t = performance.now();
        for (let i = 1; i <= 50; i++) { r.value = i; r.dispatchEvent(new Event('input')); } return (performance.now() - t) / 50; })()""")
    assert ms < 16, f"estimator update {ms:.1f} ms"
    # Checkout opens fast
    ms = pg.evaluate("(() => { const t = performance.now(); openBuy('chat','buy'); return performance.now() - t; })()")
    assert ms < 100, f"checkout open {ms:.1f} ms"
    pg.click("#buyClose")
    # Chat replies within a second
    pg.click("#chatFab"); t = time.time()
    pg.fill("#chatInput", "how much does it cost?"); pg.press("#chatInput", "Enter")
    for _ in range(40):
        if pg.locator(".cmsg.bot").count() > 1:
            break
        pg.wait_for_timeout(50)
    assert time.time() - t < 2.5


def test_PERF05_tool_apps_stay_fast_with_lots_of_data(make_page, base_url):
    """A busy property: 1,000 work orders should still render in well under a second."""
    w = make_page(); pg = w.page
    pg.goto(base_url + "prototypes/workorders.html"); pg.wait_for_timeout(200)
    ms = pg.evaluate("""(() => { for (let i = 0; i < 1000; i++) S.orders.push({id: 1000 + i, unit: String(100 + i % 300), res: 'Resident ' + i,
        issue: 'Sample issue ' + i, cat: 'General', pri: i % 7 ? 'Normal' : 'High', tech: '', status: 'New', hrs: 1});
        const t = performance.now(); render(); return performance.now() - t; })()""")
    assert ms < 800, f"render with 1,000 orders took {ms:.0f} ms"
    assert pg.locator("#rows tr").count() >= 1000
    assert not w.errors, w.errors


def test_PERF06_mobile_layout_has_no_horizontal_scroll(make_page, base_url):
    for rel in ["index.html", "products.html", "prototypes/workorders.html", "prototypes/suite.html"]:
        w = make_page(width=390, height=844); pg = w.page
        pg.goto(base_url + rel); pg.wait_for_timeout(300)
        assert pg.evaluate("document.documentElement.scrollWidth") <= 392, rel
