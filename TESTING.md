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
| S05 | Products | 13 product cards |
| S06 | Chat assistant | Opens and answers a pricing question with $750 |
| S07 | Audit request form | Required-field validation; valid submit shows send panel addressed to rashadfambro@gmail.com |
| S08 | Product guide | 13 product sections, no errors |
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
| R05 | Offers | $150 referral, $750 assessment credit, $1,999 bundle |
| R06 | Holiday sale | Banner and 10% prices ($675) during the sale; hidden and regular prices after Jan 31, 2027 |
| R07 | Sale math | ChatDesk $1,200 → $1,080 and $149 → $134/mo during sale |
| R08 | Buy flow | Every Buy button opens checkout; plan option only for $1,000+; validation; order fallback to owner email with plan and method; nothing charged |
| R09 | Payment plans | Shown in pricing note and FAQ |
| R10 | Demo lab | All 6 demos triage and approve |
| R11 | Industry links | All 23 `#for-…` links personalize headline and preselect industry |
| R12 | Industry chips | All 22 chips show a panel with a working Try button |
| R13 | Chat intents | Pricing, founding, in-person, payment plans, buying, rewards, chatbots, holiday sale, full lead capture |
| R14 | Savings calculator | Matches the formula for known inputs |
| R15 | Estimate email capture | Rejects bad email; valid email produces send link to owner |
| R16 | Project request builder | 4 steps, validation, summary, send panel to owner |
| R17 | Owner email | CONFIG and contact card use rashadfambro@gmail.com |
| R18 | Internal links | Every relative link and #anchor resolves on every page |
| R19 | Website QR | Website tab selected by default with save message; QR renders (online) or falls back (offline) |
| R20 | Save this site | Button works without errors |
| R21 | Meta tags | Canonical on public pages; staging pages noindex with ribbon; production pages indexable |
| R22 | robots.txt | Blocks /staging/ and /tools/, lists sitemap |
| R23 | Product guide content | Each product has workflow, 4 benefit boxes, price |
| R24 | Accessibility | Every visible form field has a label |
| R25 | Price consistency | Product prices match between home page and guide |
| R26 | Audit tool pricing | Founding discount applied correctly ($2,500 → $1,875) |
| R27 | Staging parity | After a promote, staging and production are identical (run with REQUIRE_SYNC=1) |

## Latest runs (Nov 13, 2026)
GitHub Actions: all 4 jobs passed (smoke + regression × production + staging), including the online QR check.
Production: 51 passed, 1 skipped (R27, by design) · Staging: 51 passed, 1 skipped · R27 with REQUIRE_SYNC=1: passed.
Defects found and fixed during this run: two industry-page headings not in Title Case (price text inside the heading); QR caption showed the contact message while the QR library was loading; test harness link parser counted a `data-cfg-href` attribute as a link.
