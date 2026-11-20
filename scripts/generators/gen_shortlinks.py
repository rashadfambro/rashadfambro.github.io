#!/usr/bin/env python3
"""Short links for emails, e.g. rashadfambro.github.io/cleaning and rashadfambro.github.io/a/?RF-20261120-ABC123.

  python3 scripts/generators/gen_shortlinks.py [site root, default staging/]

Writes <root>/<slug>/index.html for every industry page (plus a few friendly aliases) and <root>/a/index.html,
which looks up a trial or license key with the lead engine and opens the full branded app link.
The list of folders is also used by scripts/release.py (SHORT_ITEMS)."""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALIASES = {"electricians": "contractors", "hvac": "contractors", "plumbers": "contractors", "trades": "contractors",
           "nails": "salons", "property": "apartments", "rentals": "short-term-rentals", "storage": "self-storage", "lawyers": "law-firms"}


def industries(root=ROOT):
    d = os.path.join(root, "industries")
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".html") and f != "index.html")


def short_items(root=ROOT):
    return industries(root) + sorted(ALIASES) + ["a"]


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://script.google.com https://script.googleusercontent.com; object-src 'none'; base-uri 'self'; form-action 'self'">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{title}</title>
<link rel="canonical" href="https://rashadfambro.github.io/industries/{slug}.html">
<meta http-equiv="refresh" content="0; url=../industries/{slug}.html">
<script>location.replace("../industries/{slug}.html" + location.search + location.hash);</script>
<style>body{{font:16px/1.5 system-ui,sans-serif;background:#0d1a2d;color:#e8eef7;display:grid;place-items:center;min-height:90vh;margin:0}}a{{color:#7cc4ff}}</style>
</head>
<body>
<p>Opening <a href="../industries/{slug}.html">{title}</a>&hellip;</p>
</body>
</html>
"""

KEY_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://script.google.com https://script.googleusercontent.com; object-src 'none'; base-uri 'self'; form-action 'self'">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>Opening Your App | Rashad Fambro Consulting</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;background:#0d1a2d;color:#e8eef7;display:grid;place-items:center;min-height:90vh;margin:0;padding:0 20px;text-align:center}}a{{color:#7cc4ff}}</style>
</head>
<body>
<main>
<h1 style="font:600 22px Georgia,serif">Opening Your App</h1>
<p id="msg">One moment&hellip;</p>
</main>
<script>
(function () {{
  var API = {api};
  var key = decodeURIComponent(location.search.slice(1).split("&")[0]).trim().toUpperCase();
  var env = /\\/staging\\//.test(location.pathname) ? "staging" : "production";
  var msg = document.getElementById("msg");
  function fail(t) {{ msg.innerHTML = t + ' Reply to the email you received, or contact <a href="../#contact">Rashad Fambro Consulting</a>, and a new link will be sent.'; }}
  if (!/^RFL?-\\d{{8}}-[A-Z0-9]{{6}}$/.test(key)) {{ fail("This link looks incomplete."); return; }}
  fetch(API + "?resolve=" + encodeURIComponent(key) + "&env=" + env, {{ cache: "no-store" }})
    .then(function (r) {{ return r.json(); }})
    .then(function (j) {{
      if (j && j.ok && /^https:\\/\\/rashadfambro\\.github\\.io\\/prototypes\\//.test(j.url)) location.replace(j.url);
      else fail("This link is no longer active.");
    }})
    .catch(function () {{ fail("The app could not be opened right now. Please try again in a minute."); }});
}})();
</script>
</body>
</html>
"""


def main(root):
    src = open(os.path.join(root, "index.html"), encoding="utf-8").read()
    api = re.search(r'backendUrl:\s*"([^"]+)"', src).group(1)
    targets = {s: s for s in industries(root)}
    targets.update(ALIASES)
    for slug, target in targets.items():
        page = open(os.path.join(root, "industries", target + ".html"), encoding="utf-8").read()
        title = html.unescape(re.search(r"<title>(.*?)</title>", page, re.S).group(1)).strip()
        os.makedirs(os.path.join(root, slug), exist_ok=True)
        with open(os.path.join(root, slug, "index.html"), "w", encoding="utf-8") as f:
            f.write(PAGE.format(title=html.escape(title), slug=target))
    os.makedirs(os.path.join(root, "a"), exist_ok=True)
    with open(os.path.join(root, "a", "index.html"), "w", encoding="utf-8") as f:
        f.write(KEY_PAGE.format(api=json.dumps(api)))
    print("short links written:", len(targets) + 1)


if __name__ == "__main__":
    main(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "staging"))
