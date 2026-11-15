"""Gentle load check of the LIVE site (GitHub Pages). Run by hand, not in CI:

    python3 scripts/load_check.py                 # 60 requests, 6 at a time
    python3 scripts/load_check.py --requests 200 --concurrency 10

Keeps volume low on purpose: GitHub Pages is a shared CDN, and its usage limits apply.
Prints error count, median and p95 response time per page."""
import argparse, concurrent.futures as cf, statistics, time, urllib.request

SITE = "https://rashadfambro.github.io/"
PAGES = ["", "products.html", "privacy.html", "prototypes/", "prototypes/workorders.html", "industries/apartments.html"]


def get(url):
    t = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            r.read(); return url, r.status, (time.perf_counter() - t) * 1000
    except Exception as e:
        return url, str(e), (time.perf_counter() - t) * 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--requests", type=int, default=60)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--site", default=SITE)
    a = ap.parse_args()
    a.requests = min(a.requests, 500)
    urls = [a.site + PAGES[i % len(PAGES)] for i in range(a.requests)]
    with cf.ThreadPoolExecutor(max_workers=min(a.concurrency, 20)) as ex:
        res = list(ex.map(get, urls))
    errors = [r for r in res if r[1] != 200]
    print(f"{len(res)} requests, {len(errors)} errors")
    for p in PAGES:
        ts = sorted(r[2] for r in res if r[0] == a.site + p and r[1] == 200)
        if ts:
            print(f"  /{p:<32} median {statistics.median(ts):6.0f} ms   p95 {ts[int(len(ts) * .95) - 1 if len(ts) > 1 else 0]:6.0f} ms")
    for r in errors[:5]:
        print("  error:", r[0], r[1])


if __name__ == "__main__":
    main()
