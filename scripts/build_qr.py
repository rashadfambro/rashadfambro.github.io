#!/usr/bin/env python3
"""Regenerate the static QR codes embedded in index.html (website, contact card, LinkedIn).
Run after changing CONFIG (email, phone, siteUrl, linkedin, title):
    python3 scripts/build_qr.py [path/to/index.html]
Needs Playwright + Chromium (uses the page's own vcardText() so the QR always matches the site)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qr
from playwright.sync_api import sync_playwright

path = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "index.html"))
with sync_playwright() as p:
    kw = {"executable_path": os.environ["CHROME_PATH"]} if os.environ.get("CHROME_PATH") else {}
    b = p.chromium.launch(**kw); pg = b.new_page()
    pg.goto("file://" + path)
    data = pg.evaluate("({site: CONFIG.siteUrl, vcard: vcardText(), linkedin: CONFIG.linkedin})")
    b.close()
svgs = {k: qr.svg(v) for k, v in data.items() if v}
s = open(path, encoding="utf-8").read()
block = "/*QR-START*/const QR_SVGS = " + "{" + ",".join(f'{k}:{repr(v)}' for k, v in svgs.items()) + "};/*QR-END*/"
s = re.sub(r"/\*QR-START\*/.*?/\*QR-END\*/", lambda m: block, s, flags=re.S)
first = svgs.get("site") or svgs.get("vcard")
s = re.sub(r'(<div class="qr" id="qr" role="img" aria-label="[^"]*">).*?(</div>)', lambda m: m.group(1) + first + m.group(2), s, count=1, flags=re.S)
open(path, "w", encoding="utf-8").write(s)
print("QR codes embedded:", ", ".join(svgs))
