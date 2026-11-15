# Website Test Plan

Automated with **pytest + Playwright** (headless Chromium). Runs on every push and pull request in GitHub Actions (`.github/workflows/tests.yml`), against **production** (`/`) and **staging** (`/staging/`).

## Run locally
```bash
pip install pytest playwright && python -m playwright install chromium
python -m pytest -m smoke                         # production, smoke
SITE_PATH=/staging/ python -m pytest              # staging, everything
REQUIRE_SYNC=1 python -m pytest -k R27            # after a promote: staging == production
```

## Environments & release flow
| Environment | URL | Purpose |
|---|---|---|
| Production | https://rashadfambro.github.io/ | Live site |
| Staging | https://rashadfambro.github.io/staging/ | Exact replica (noindex, red STAGING ribbon). Changes land here first |
| Backups | branches `backup/prod-YYYYMMDD-HHMMSS` | Snapshot of production taken automatically before every promote (first one: `backup/prod-20261113`) |

1. Edit files under `staging/` → run `SITE_PATH=/staging/ python -m pytest` → push → check the staging URL.
2. `python3 scripts/release.py promote` (creates the backup branch, copies staging → production) → run the tests against production → push `main` and the backup branch.
3. To roll back: `python3 scripts/release.py rollback backup/prod-…` → push.

## Smoke suite (critical paths)
| ID | Scenario | Expected |
|---|---|---|
| S01 | Home page loads | Title present, hero visible, no JS errors |
| S02 | Navigation | Every nav link points to an existing section |
| S03 | Primary call to action | Hero CTA targets the audit form |
| S04 | Packages | 4 packages; $750 assessment, $2,500 pilot, $150/mo care plan |
| S05 | Products | 14 product cards |
| S06 | Chat assistant | Opens and answers a pricing question with $750 |
| S07 | Audit request form | Required-field validation; valid submit shows send panel addressed to rashadfambro@gmail.com |
| S08 | Product guide | 14 product sections, no errors |
| S09 | Industry pages | All 22 pages return 200 with one H1 |
| S10 | Mobile layout | No horizontal scroll at 390px (home, guide, industry, audit tool) |
| S11 | Sitemap | Valid XML; every URL maps to a real file |
| S12 | Save-to-home-screen | Manifest valid; icons exist |
| S13 | Audit summary tool | Sample renders on one letter page, no errors |

## Regression suite (full coverage)
| ID | Scenario | Expected |
|---|---|---|
| R01 | Title Case | All H1–H4 and FAQ headings in Title Case (home, guide, industry, tool) |
| R02 | Privacy of employers | No former employer names on any page |
| R03 | Profile | Focus includes AI; Former has no "healthcare technology"; on-site meetings mentioned |
| R04 | Founding program | 25% off, testimonial required, no 30% |
| R05 | Offers | $150 referral, $750 assessment credit, $1,699 Launch Bundle, $5,999 Hotel Operations Bundle |
| R06 | Holiday sale | Banner and 10% prices ($675) during the sale; hidden and regular prices after Jan 31, 2027 |
| R07 | Sale math | ChatDesk $1,000 → $900 and $25 → $23/mo during sale |
| R08 | Buy flow | Every Buy button opens checkout; PayPal (default) or Square; Essentials/Growth/Pro tier choice updates price; installments only for $1,000+; validation; order fallback to owner email with tier, plan and method; nothing charged |
| R09 | Payment plans | Shown in pricing note and FAQ |
| R10 | Demo lab | All 7 demos (incl. housekeeping) triage and approve |
| R11 | Industry links | All 23 `#for-…` links personalize headline and preselect industry |
| R12 | Industry chips | All 22 chips show a panel with a working Try button |
| R13 | Chat intents | Pricing, founding, in-person, payment plans, buying, rewards, chatbots, free trial, housekeeping, holiday sale, full lead capture |
| R14 | Savings estimator | Net monthly benefit after plan + usage, payback, year one; ChatGPT worked example ($350/mo, 10 months); no payback shown when benefit ≤ 0 |
| R15 | Estimate email capture | Rejects bad email; valid email produces send link to owner |
| R16 | Project request builder | 4 steps, validation, summary, send panel to owner |
| R17 | Owner email | CONFIG and contact card use rashadfambro@gmail.com |
| R18 | Internal links | Every relative link and #anchor resolves on every page |
| R19 | Website QR | Website tab selected by default; static QR codes (website, contact card, LinkedIn) render instantly with no CDN; verified to decode |
| R20 | Save this site | Button works without errors |
| R21 | Meta tags | Canonical on public pages; staging pages noindex with ribbon; production pages indexable |
| R22 | robots.txt | Blocks /staging/ and /tools/, lists sitemap |
| R23 | Product guide content | Each product has workflow, 4 benefit boxes, price |
| R24 | Accessibility | Every visible form field has a label |
| R25 | Price consistency | Product prices match between home page and guide |
| R26 | Audit tool pricing | Founding discount applied correctly ($2,500 → $1,875) |
| R28 | Free trials | 14 trial buttons; trial modal hides payment fields; price shows “Free for 14 days, then…”; request goes to owner email |
| R29 | Monthly plans | Essentials/Growth/Pro at $25/$49/$79 (standard) and $49/$99/$150 (property); $59 suite; trial mention |
| R30 | Sale fine print | “Doesn’t combine…” on its own smaller line, not in the main sale sentence |
| R31 | Hotel tools | WorkOrderDesk and IntakeDesk list hotels & resorts; HousekeepingDesk demo classifies a VIP checkout as high-priority Checkout clean |
| R32 | Product prices | RewardsDesk $750, ReviewDesk $150, SocialDesk $750, LeadDesk $1,000, IntakeDesk $1,250, ComplianceDesk $2,500 |
| R33 | Home & back to top | Home is the first nav item; floating Top button appears after scrolling and returns to the top; Home does the same |
| R34 | Subpage navigation | Product guide and industry pages have a Home link and a working Top button |
| R35 | No-script defaults | Without JavaScript (crawlers, link previews): no “0 requests”/“$0”, calculator shows real defaults, QR present, benchmark stats shown |
| R36 | Booking | Calendly audit link in CONFIG, audit section, contact section and chat |
| R37 | How I Deliver | Section explains single point of contact, AI-assisted delivery reviewed by Rashad, testing and support (no “agent” jargon) |
| R38 | FAQ copy | No seasonal sale sentence in the FAQ |
| R27 | Staging parity | After a promote, staging and production are identical (run with REQUIRE_SYNC=1) |

## Latest runs (Nov 13, 2026)
GitHub Actions: all 4 jobs passed (smoke + regression × production + staging), including the online QR check.
Release of Nov 13 (pricing/tiers/trials/housekeeping): production 57 passed + R27 parity passed; staging 57 passed. Defect found and fixed: the chat assistant treated “free trial” as a request for the free audit.
Earlier run: production 51 passed, 1 skipped (R27, by design) · Staging: 51 passed, 1 skipped · R27 with REQUIRE_SYNC=1: passed.
Defects found and fixed during this run: two industry-page headings not in Title Case (price text inside the heading); QR caption showed the contact message while the QR library was loading; test harness link parser counted a `data-cfg-href` attribute as a link.
| R39 | Forms send directly to Rashad's Gmail through FormSubmit (correct endpoint, subject, reply-to, auto-reply) |
| R40 | If the form service isn't activated or fails, the visitor gets the email-draft fallback |
| R41 | Trials and orders also send directly |
| R42 | Multi-industry wording, PackageDesk product, demo and chat answer |

Tests never send real emails: `tests/conftest.py` blocks formsubmit.co unless a test fakes the response.
| R43 | Every product has a demo or a prototype; prototype buttons link to the right page |
| R44 | All six prototypes and the prototype index load without errors and take the visitor's brand name |
| R45 | Core flow in each prototype works (points and offers, review replies, post drafting, handbook answers, invoices and reminders, weekly summary) |
| R46 | Page source reads cleanly for crawlers: no fallback message, no empty phone row, footer year, no checkout promise in static HTML |
| R47 | Order button says "Place my order" unless a payment link is set, then "Continue to secure checkout" |
| R48 | Email-draft fallback keeps accents, symbols and dashes intact in subject and body |
| R49 | Plan prices are consistent: ascending tiers, per-property plans never below standard |
| R50 | Privacy Policy page exists, is linked from the footer and the audit form |
| R51 | With a PayPal.me handle set, "Pay in full" with PayPal links to paypal.me/<handle>/<amount> (sale price during the sale) |
| R52 | Checkout prices for the assessment, pilot and care plan match the listed prices |
| R53 | Every price, including sale prices, is a round number ending in 0 |
| R54 | Hero, profile and About copy; Property Management Bundle (no ComplianceDesk); one cancellation policy |
| R55 | Old #solutions links land on Products; the products note is readable on mobile |
| R56 | Pricing lists a one-line description for all 15 tools; page text has no run-together words |
| R57 | Checkout plan picker, proposal request and header show the same (sale) prices; due-at-kickoff summary; CSP, referrer policy and spam honeypot on every page/form |
| R58 | ReviewDesk shows every customer the same review and private-feedback options, whatever their rating |
| R59 | Client-owned model: ownership FAQ, support allowances per plan, extra-support rate, Fully Hosted allowances and overages (skips until promoted) |
| R60 | One main hero button; 3 featured tools with the rest collapsed; Request order / Request a pilot / Try demo labels; fictional sample audit; pilot scope and 3–8 week timing agree in pricing, FAQ and chat |
| R61 | All 9 new trial apps (WorkOrderDesk, ChatDesk, BookDesk, GuestDesk, HousekeepingDesk, PackageDesk, LeadDesk, IntakeDesk, ComplianceDesk) load and their main action works |
| R62 | Trial links: branded countdown, end-of-trial screen after 14 days, tampered links rejected; a package opens as one Desk Suite |
| R63 | Product order; PayPal pays the amount due now for ready products; pilot requests ask for no payment; profile, photo, sale banner second line; one back-to-top; ROI rounding and cash view |
| R64 | Starter edition: every tool and bundle can be ordered and paid now, delivery note in checkout, paid license links open the branded Starter edition (or Desk Suite) with backup/restore, overdue licenses pause, tampered links rejected |
| R65 | Square checkout has a link for every amount due now (full, sale, first of 3) on every orderable item |

Price tests read prices from the site's CONFIG, so they keep passing when prices change.

## Security, Performance and Load Suites
Run any suite on its own: `python -m pytest -m security` (or `performance`, `load`). CI runs all five suites against production and staging on every push.

| ID | Security check |
|---|---|
| SEC01 | Every page has a strict Content Security Policy (no third-party scripts, no eval, object-src none) and a strict referrer policy |
| SEC02 | Every link that opens a new tab uses rel="noopener" |
| SEC03 | No insecure http:// resources |
| SEC04 | No secrets (API keys, tokens, private keys) or unexpected email addresses in any committed file |
| SEC05 | No eval, new Function or document.write in site code |
| SEC06 | The chat shows injected HTML as text and never runs it |
| SEC07 | Five tool apps (and the brand-name field) never run injected HTML |
| SEC08 | The hidden spam trap drops bot submissions without sending anything |
| SEC09 | Tampered trial links are rejected |
| SEC10 | Internal pages (trial-link generator) and staging are hidden from search engines |

| ID | Performance budget |
|---|---|
| PERF01 | Page weight: home ≤ 320 KB, Product Guide ≤ 80 KB, each tool app, industry page and image ≤ 60 KB |
| PERF02 | Home, Product Guide, WorkOrderDesk and Desk Suite: DOMContentLoaded, load and first paint within budget |
| PERF03 | Home page loads with ≤ 15 requests (≤ 8 from the site itself) |
| PERF04 | Estimator updates in < 16 ms, checkout opens in < 100 ms, chat replies in < 2.5 s |
| PERF05 | WorkOrderDesk renders 1,000 work orders in < 800 ms |
| PERF06 | No sideways scrolling at phone width on key pages |

| ID | Load check (local test server, never GitHub Pages) |
|---|---|
| LOAD01 | 600 requests from 30 concurrent visitors: no errors, median < 500 ms, p95 < 1.5 s |
| LOAD02 | 10 browser sessions use the home page, estimator and checkout at the same time |
| LOAD03 | 8 trial users work in different tool apps at once with no errors and their data saved |

For a gentle check of the live site, run `python3 scripts/load_check.py` by hand (capped at 500 requests).
