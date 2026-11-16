"""Read-only checks against the live lead engine (Google Apps Script) named in CONFIG.backendUrl.

LIVE01  ?stats=founding answers with a founding-spots count (drives the website counter).
LIVE02  ?check=license with an unknown key answers ok (the tool apps' online license check).
Neither call creates rows or sends email. Skipped when this machine can't reach Google (some sandboxes);
GitHub Actions runs them on every push.
"""
import json, os, re, urllib.request, urllib.error, pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytestmark = [pytest.mark.smoke]


def backend_url():
    sub = os.environ.get("SITE_PATH", "/").strip("/")
    html = (ROOT / sub / "index.html" if sub else ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'backendUrl:\s*"([^"]*)"', html)
    return m.group(1) if m else ""


def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "site-tests"}), timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, OSError) as e:
        if os.environ.get("CI"):
            raise
        pytest.skip(f"live backend not reachable from here: {e}")


def test_LIVE01_founding_stats():
    url = backend_url()
    if not url:
        pytest.skip("no backend configured")
    d = get(url + "?stats=founding")
    assert d.get("ok") is True and isinstance(d.get("foundingLeft"), int) and 0 <= d["foundingLeft"] <= 5, d


def test_LIVE02_license_check_endpoint():
    url = backend_url()
    if not url:
        pytest.skip("no backend configured")
    d = get(url + "?check=license&key=RFL-20000101-TEST00")
    assert d.get("ok") is True and "valid" in d, d
