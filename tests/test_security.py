"""Security suite: content security policy, safe links, no secrets in the repo, no script injection,
spam protection, and search-engine guards. Scenario IDs match TESTING.md (SEC01–SEC10)."""
import os, re, subprocess
import pytest
from conftest import ROOT, SITE_PATH, OWNER_EMAIL, site_file

pytestmark = pytest.mark.security

PAYLOAD = '<img src=x onerror="window.__pwned=1"><script>window.__pwned=1</script>'


def site_html():
    base = site_file("")
    out = []
    for dp, dirs, fs in os.walk(base):
        rel = os.path.relpath(dp, ROOT).split(os.sep)[0]
        if SITE_PATH == "/" and rel in ("staging", "tests", ".git", ".github", "scripts"):
            continue
        out += [os.path.join(dp, f) for f in fs if f.endswith(".html")]
    return out


def test_SEC01_every_page_has_a_strict_content_security_policy():
    for f in site_html():
        s = open(f, encoding="utf-8").read()
        m = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', s)
        assert m, f
        csp = m.group(1)
        assert "object-src 'none'" in csp and "base-uri 'self'" in csp, f
        assert "unsafe-eval" not in csp, f
        script_src = re.search(r"script-src ([^;]+)", csp).group(1)
        assert "http" not in script_src and "*" not in script_src, (f, script_src)   # no third-party scripts
        assert 'name="referrer" content="strict-origin-when-cross-origin"' in s, f


def test_SEC02_new_tab_links_cannot_control_the_opener():
    for f in site_html():
        s = open(f, encoding="utf-8").read()
        for tag in re.findall(r"<a\b[^>]*target=\"_blank\"[^>]*>", s):
            assert "noopener" in tag, (os.path.relpath(f, ROOT), tag[:120])


def test_SEC03_no_insecure_http_resources():
    for f in site_html():
        s = open(f, encoding="utf-8").read()
        bad = [u for u in re.findall(r'(?:src|href|action)="(http://[^"]+)"', s) if not u.startswith(("http://127.0.0.1", "http://localhost"))]
        assert not bad, (os.path.relpath(f, ROOT), bad[:3])


def test_SEC04_no_secrets_or_private_data_committed():
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    secret = re.compile(r"AKIA[0-9A-Z]{16}|sk_live_[0-9a-zA-Z]{10,}|sk-ant-[0-9a-zA-Z-]{10,}|ghp_[0-9A-Za-z]{30,}|xox[baprs]-[0-9A-Za-z-]{10,}"
                        r"|-----BEGIN [A-Z ]*PRIVATE KEY-----|EAAG[0-9A-Za-z]{20,}|sq0atp-[0-9A-Za-z_-]{10,}|EAAA[0-9A-Za-z_-]{40,}")
    email = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z]{2,})+")
    allowed = {OWNER_EMAIL, "noreply@anthropic.com", "you@business.com", "you@company.com", "name@business.com",
               "noreply@messaging.squareup.com", "service@paypal.com"}   # public payment-provider senders used in test fixtures
    problems = []
    for rel in files:
        if not rel.endswith((".html", ".js", ".py", ".md", ".json", ".yml", ".txt", ".webmanifest", ".gs", ".ini")):
            continue
        s = open(os.path.join(ROOT, rel), encoding="utf-8", errors="ignore").read()
        if secret.search(s):
            problems.append((rel, "secret-like token"))
        for e in set(email.findall(s)):
            e = e.rstrip(".")
            if e in allowed or e.endswith(("@example.com", "@users.noreply.github.com", ".png", ".svg", ".jpg")) or "@" not in e:
                continue
            if re.match(r".*@(2x|3x)\b", e):
                continue
            problems.append((rel, e))
    assert not problems, problems[:10]


def test_SEC05_no_eval_or_document_write_in_site_code():
    for f in site_html():
        s = open(f, encoding="utf-8").read()
        for pat in (r"\beval\(", r"new Function\(", r"document\.write\("):
            assert not re.search(pat, s), (os.path.relpath(f, ROOT), pat)


def test_SEC06_chat_does_not_run_injected_code(make_page, base_url):
    w = make_page(); pg = w.page
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    pg.click("#chatFab")
    pg.fill("#chatInput", PAYLOAD); pg.press("#chatInput", "Enter"); pg.wait_for_timeout(900)
    assert pg.evaluate("window.__pwned") is None
    assert "<img" in pg.inner_text("#chatLog") or "onerror" in pg.inner_text("#chatLog")


@pytest.mark.parametrize("page,field,button", [
    ("prototypes/chat.html", "#q", None),
    ("prototypes/workorders.html", "#desc", "#submit"),
    ("prototypes/leads.html", "#nm", "#add"),
    ("prototypes/guests.html", "#gname", "#route"),
    ("prototypes/intake.html", "#nf", "#addF"),
])
def test_SEC07_tool_apps_do_not_run_injected_code(make_page, base_url, page, field, button):
    w = make_page(); pg = w.page
    pg.goto(base_url + page); pg.wait_for_timeout(300)
    pg.fill(field, PAYLOAD)
    if button:
        pg.click(button)
    else:
        pg.press(field, "Enter")
    pg.wait_for_timeout(300)
    for tab in pg.locator(".tabs button").all():
        tab.click(); pg.wait_for_timeout(80)
    assert pg.evaluate("window.__pwned") is None, page
    # Injected brand names are shown as text, not markup
    pg.fill("#bizName", PAYLOAD); pg.wait_for_timeout(200)
    assert pg.evaluate("window.__pwned") is None, page


def test_SEC08_spam_trap_drops_bot_submissions_without_sending(make_page, base_url):
    w = make_page(); pg = w.page
    sent = []
    pg.context.route(re.compile(r"https://formsubmit\.co/.*"), lambda r: (sent.append(r.request.url), r.abort()))
    pg.goto(base_url + "index.html"); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#auditForm input[name=company_website]').value='http://spam.example'")
    ok = pg.evaluate("sendLead('audit', {Name:'Bot', Email:'bot@example.com'})")
    assert ok is True and sent == []


def test_SEC09_trial_links_reject_tampering(make_page, base_url):
    w = make_page(); pg = w.page
    pg.goto(base_url + "prototypes/workorders.html"); pg.wait_for_timeout(200)
    key = pg.evaluate("trialKey('property','Acme','2030-01-01')")
    pg.goto(base_url + f"prototypes/workorders.html?trial={key}&biz=Acme&start=2030-01-01&tools=property,service"); pg.wait_for_timeout(300)
    assert "isn't valid" in pg.inner_text(".banner")


def test_SEC10_private_pages_are_hidden_from_search():
    s = open(site_file("tools/trial-link.html"), encoding="utf-8").read()
    assert 'name="robots" content="noindex, nofollow"' in s
    if SITE_PATH.startswith("/staging"):
        assert 'name="robots" content="noindex, nofollow"' in open(site_file("index.html"), encoding="utf-8").read()
