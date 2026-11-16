"""Shared fixtures: serves the repo over HTTP and provides a browser.

Environment variables:
  SITE_PATH    "/" (production, default) or "/staging/"
  CHROME_PATH  optional path to a local Chrome/Chromium executable
  CI           set by GitHub Actions; enables checks that need internet (CDN QR library)
"""
import functools, http.server, os, socketserver, threading, re
import pytest
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_PATH = os.environ.get("SITE_PATH", "/")
if not SITE_PATH.endswith("/"):
    SITE_PATH += "/"
ONLINE = bool(os.environ.get("CI"))
OWNER_EMAIL = "rashadfambro@gmail.com"


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@pytest.fixture(scope="session")
def base_url():
    handler = functools.partial(_Quiet, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}{SITE_PATH}"
    httpd.shutdown()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        kw = {}
        if os.environ.get("CHROME_PATH"):
            kw["executable_path"] = os.environ["CHROME_PATH"]
        engine = os.environ.get("BROWSER", "chromium")      # chromium | webkit (Safari engine) | firefox
        b = getattr(p, engine).launch(**(kw if engine == "chromium" else {}))
        # Never reach the real lead engine (Google Apps Script) from tests: every context gets it blocked.
        # Tests that need a backend answer add their own route, which takes priority over this one.
        _new_context = b.new_context
        def guarded_context(*a, **k):
            c = _new_context(*a, **k)
            c.route(LIVE_BACKEND, lambda r: r.abort())
            return c
        b.new_context = guarded_context
        yield b
        b.close()


LIVE_BACKEND = re.compile(r"https://script\.(google|googleusercontent)\.com/.*")

IGNORED_CONSOLE = re.compile(r"Failed to load resource|net::ERR_|fonts\.(googleapis|gstatic)|cdnjs", re.I)


class PageWithErrors:
    """A page that records uncaught JS errors and console errors."""
    def __init__(self, page):
        self.page = page
        self.errors = []
        page.on("pageerror", lambda e: self.errors.append(f"pageerror: {e}"))
        page.on("console", lambda m: (m.type == "error" and not IGNORED_CONSOLE.search(m.text)) and self.errors.append(f"console: {m.text}"))


@pytest.fixture
def make_page(browser):
    pages = []
    def _make(width=1300, height=900, **ctx):
        context = browser.new_context(viewport={"width": width, "height": height}, **ctx)
        # Never send real form emails from tests: the form service is unreachable unless a test overrides it.
        context.route(re.compile(r"https://formsubmit\.co/.*"), lambda r: r.abort())
        pg = context.new_page()
        w = PageWithErrors(pg)
        pages.append((context, w))
        return w
    yield _make
    for context, w in pages:
        context.close()


@pytest.fixture
def home(make_page, base_url):
    w = make_page()
    w.page.goto(base_url + "index.html")
    w.page.wait_for_timeout(300)
    w.page.evaluate("document.querySelectorAll('details.more-prod').forEach(d => d.open = true)")  # most tests reach every product; R60 covers the collapsed default
    return w


def site_file(rel):
    """Path of a site file within the environment under test."""
    return os.path.join(ROOT, SITE_PATH.strip("/"), rel)
