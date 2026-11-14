#!/usr/bin/env python3
"""Release tool for rashadfambro.github.io

Environments (all served by GitHub Pages from branch `main`):
  Production  https://rashadfambro.github.io/
  Staging     https://rashadfambro.github.io/staging/   (noindex replica; changes land here first)
  Backups     branches `backup/prod-YYYYMMDD-HHMMSS` — a snapshot of production taken before every promote

Usage:
  python3 scripts/release.py sync-staging   # copy production -> staging (refresh staging to match prod)
  python3 scripts/release.py promote        # tag a prod backup, then copy staging -> production
  python3 scripts/release.py rollback REF   # restore production files from a backup branch
  python3 scripts/release.py check          # verify staging and production are identical (except markers)

Flow: edit files under staging/  ->  run tests against /staging/  ->  push  ->  check staging URL
      ->  promote  ->  run tests against /  ->  push.
"""
import os, re, shutil, subprocess, sys, datetime, filecmp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING = os.path.join(ROOT, "staging")
SITE_ITEMS = ["index.html", "products.html", "privacy.html", "industries", "tools", "manifest.webmanifest", "icon.svg", "icon-192.png", "icon-512.png", "prototypes"]
START, END = "<!--STAGING-START-->", "<!--STAGING-END-->"
MARKER = (START + '<meta name="robots" content="noindex, nofollow">'
          '<style>.stg-ribbon{position:fixed;right:0;top:50%;z-index:9999;transform:rotate(-90deg) translateY(-100%);transform-origin:right top;background:#ff5a5a;color:#fff;'
          'font:800 12px/1 system-ui,sans-serif;letter-spacing:.12em;padding:8px 12px;border-radius:8px 8px 0 0}</style>'
          + END)
RIBBON = START + '<div class="stg-ribbon" aria-hidden="true">STAGING</div>' + END


def html_files(base):
    for dp, _, fs in os.walk(base):
        for f in fs:
            if f.endswith(".html"):
                yield os.path.join(dp, f)


def add_markers(path):
    s = open(path, encoding="utf-8").read()
    if START in s:
        return
    s = s.replace("</head>", MARKER + "</head>", 1)
    s = re.sub(r"(<body[^>]*>)", r"\1" + RIBBON, s, count=1)
    open(path, "w", encoding="utf-8").write(s)


def strip_markers(s):
    return re.sub(re.escape(START) + r".*?" + re.escape(END), "", s, flags=re.S)


def copy_items(src, dst):
    for item in SITE_ITEMS:
        a, b = os.path.join(src, item), os.path.join(dst, item)
        if not os.path.exists(a):
            continue
        if os.path.isdir(a):
            if os.path.exists(b):
                shutil.rmtree(b)
            shutil.copytree(a, b)
        else:
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.copy2(a, b)


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], check=True, capture_output=True, text=True).stdout.strip()


def sync_staging():
    os.makedirs(STAGING, exist_ok=True)
    copy_items(ROOT, STAGING)
    for f in html_files(STAGING):
        add_markers(f)
    print("staging refreshed from production")


def promote():
    ref = "backup/prod-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    git("branch", ref)
    print("backup branch created:", ref, "(push with: git push origin", ref + ")")
    copy_items(STAGING, ROOT)
    for item in SITE_ITEMS:
        p = os.path.join(ROOT, item)
        files = list(html_files(p)) if os.path.isdir(p) else ([p] if p.endswith(".html") else [])
        for f in files:
            s = open(f, encoding="utf-8").read()
            open(f, "w", encoding="utf-8").write(strip_markers(s))
    print("staging promoted to production")


def rollback(ref):
    for item in SITE_ITEMS:
        git("checkout", ref, "--", item)
    print("production restored from", ref, "- commit and push to publish")


def check():
    diffs = []
    for item in SITE_ITEMS:
        a, b = os.path.join(ROOT, item), os.path.join(STAGING, item)
        pairs = []
        if os.path.isdir(a):
            for f in html_files(a):
                pairs.append((f, os.path.join(b, os.path.relpath(f, a))))
        elif os.path.exists(a):
            pairs.append((a, b))
        for x, y in pairs:
            if not os.path.exists(y):
                diffs.append(("missing in staging", y)); continue
            if x.endswith(".html"):
                if strip_markers(open(x, encoding="utf-8").read()) != strip_markers(open(y, encoding="utf-8").read()):
                    diffs.append(("differs", os.path.relpath(y, ROOT)))
            elif not filecmp.cmp(x, y, shallow=False):
                diffs.append(("differs", os.path.relpath(y, ROOT)))
    for d in diffs:
        print(*d)
    print("identical" if not diffs else f"{len(diffs)} difference(s)")
    return 0 if not diffs else 1


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "sync-staging": sync_staging()
    elif cmd == "promote": promote()
    elif cmd == "rollback" and len(sys.argv) > 2: rollback(sys.argv[2])
    elif cmd == "check": sys.exit(check())
    else: print(__doc__)
