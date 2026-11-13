# Rashad Fambro Consulting — Working Agreement for Claude

This repo is the public website (GitHub Pages) and the home of the agent team in `.claude/agents/`.

**Entry point:** chief-of-staff routes requests and turns scheduled agent tasks on or off. Keep usage low: only run the agents a request needs.

**Product team:** product-manager → mvp-builder → qa-engineer → release-manager → client-success
**Client delivery:** project-manager (kickoff → weekly status → launch → hand-off to client-success)
**Growth pipeline:** pipeline-coordinator → lead-researcher → outreach-writer → scheduler → (audit + client-proposal skill) → billing-coordinator → client-success; social-media-manager weekly

## Non-negotiables
- Human in the loop: anything customer-facing (emails, posts, invoices, prices, promises) is a draft until Rashad approves.
- Published prices only; the site's `CONFIG` in index.html is the price source of truth.
- Never name Rashad's former employers. Headings in Title Case. Global wording (not US-only).
- Changes go to `staging/` first; tests must be 100% before `scripts/release.py promote`. See TESTING.md.
- Public repo: never commit prospect lists, client data, API keys, or personal information. Business docs live in the Claude project "AI Consulting Business" and on EHD 2 (`/Volumes/EHD 2/AI Consulting Company`).
- Forms send directly to rashadfambro@gmail.com through FormSubmit (CONFIG.formEndpoint); if a send fails the visitor gets an email draft as a fallback. When the Apps Script lead engine is deployed, set CONFIG.backendUrl and it takes over first.
- Meetings: Rashad's general hours are weekdays 8 AM–8 PM Eastern (flexible). Meetings may be booked directly.
