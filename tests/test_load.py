"""Load suite: many visitors at once. Requests go to the local test server (never to GitHub Pages),
so the numbers check the site's own weight and stability under concurrency. IDs match TESTING.md (LOAD01–LOAD03).
For a gentle check of the live site, see scripts/load_check.py."""
import concurrent.futures as cf, statistics, time, urllib.request
import pytest

pytestmark = pytest.mark.load

PAGES = ["index.html", "products.html", "privacy.html", "industries/apartments.html", "prototypes/index.html",
         "prototypes/workorders.html", "prototypes/chat.html", "prototypes/bookings.html", "prototypes/suite.html", "images/rashad-fambro.jpg"]


def _get(url):
    t = time.perf_counter()
    with urllib.request.urlopen(url, timeout=10) as r:
        body = r.read()
        return r.status, len(body), (time.perf_counter() - t) * 1000


def test_LOAD01_600_requests_from_30_concurrent_visitors(base_url):
    urls = [base_url + PAGES[i % len(PAGES)] for i in range(600)]
    with cf.ThreadPoolExecutor(max_workers=30) as ex:
        results = list(ex.map(_get, urls))
    errors = [r for r in results if r[0] != 200 or r[1] == 0]
    times = sorted(r[2] for r in results)
    p95 = times[int(len(times) * 0.95)]
    assert not errors, errors[:5]
    assert p95 < 1500, f"p95 {p95:.0f} ms"
    assert statistics.median(times) < 500, f"median {statistics.median(times):.0f} ms"


def test_LOAD02_ten_visitors_use_the_site_at_the_same_time(browser, base_url):
    """Ten browser sessions load the home page and run the estimator and checkout together."""
    ctxs = [browser.new_context(viewport={"width": 1100, "height": 800}) for _ in range(10)]
    try:
        pages = [c.new_page() for c in ctxs]
        errs = []
        for p in pages:
            p.on("pageerror", lambda e: errs.append(str(e)))
        t = time.perf_counter()
        for p in pages:
            p.goto(base_url + "index.html", wait_until="domcontentloaded")
        for p in pages:
            p.wait_for_timeout(50)
            p.evaluate("(() => { const r = document.getElementById('r1'); r.value = 12; r.dispatchEvent(new Event('input')); openBuy('chat','buy'); })()")
        elapsed = time.perf_counter() - t
        assert all(p.is_visible("#buyModal") for p in pages)
        assert not errs, errs
        assert elapsed < 30, f"10 sessions took {elapsed:.1f} s"
    finally:
        for c in ctxs:
            c.close()


def test_LOAD03_trial_apps_handle_parallel_users(browser, base_url):
    """Eight trial users work in different tool apps at once without errors or lost data."""
    apps = [("workorders.html", "#submit"), ("packages.html", "#add"), ("leads.html", "#add"), ("guests.html", "#route"),
            ("chat.html", None), ("bookings.html", "[data-slot]:not([disabled])"), ("housekeeping.html", "[data-room='101']"), ("compliance.html", "[data-t]:not([disabled])")]
    ctxs = [browser.new_context() for _ in apps]
    try:
        errs = []
        pages = []
        for c, (f, _) in zip(ctxs, apps):
            p = c.new_page(); p.on("pageerror", lambda e: errs.append(str(e)))
            p.goto(base_url + "prototypes/" + f); pages.append(p)
        for _ in range(3):
            for p, (f, btn) in zip(pages, apps):
                if btn:
                    p.locator(btn).first.click()
                else:
                    p.fill("#q", "hours?"); p.press("#q", "Enter")
        for p, (f, _) in zip(pages, apps):
            saved = p.evaluate("Object.keys(localStorage).filter(k => k.startsWith('proto-')).length")
            assert saved >= 1, f
        assert not errs, errs
    finally:
        for c in ctxs:
            c.close()
