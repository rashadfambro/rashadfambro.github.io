# Command Center

A private dashboard for running the business. It lives in your own Google account, and only you can open it.

| Tab | What it shows | What you can do |
|---|---|---|
| **Today** | Alerts (new and hot leads, trials ending, past-due clients, unpaid orders, agent replies), meetings for the next 7 days, unread **business** email only (clients, prospects, bookings, payments, orders, website forms; personal mail never shows) | Click through to any email |
| **Prospects & Pipeline** | A board (or sortable table) of every website lead and outbound prospect by stage, with filters for source, industry, location, suggested products, stage and contact info, plus sorting by any column. Cards show location, phone, email, the next step and a "Draft ready" tag | Drag a card to a new stage; open it to see and copy the email and phone, edit details and the **next step**, write long notes, email from a template with **Cc and Bcc** (send now or save as a Gmail draft), preview, edit and send the contact's Gmail drafts, start a 14-day trial, and add prospects. **New lead search** sends a search (industry, location, count, buying signal) to the lead researcher |
| **Emails** | Your Gmail drafts addressed to prospects, leads and clients (cold emails included), and unread business email | Preview, edit (To, Cc, Bcc, subject, body), send or discard a draft. Sending marks the prospect Contacted and adds a note |
| **Clients & Licenses** | Every trial and client, plan, paid-through date, last app check; orders | Record payment, resend link, pause, cancel, mark as founding client. Clients get the usual emails |
| **Finances** | Income, expenses, profit and monthly recurring revenue for any date range; a monthly income vs expenses chart; expenses by category, income by product and by client; itemized ledger | Filter by date range, type, category, product, client or text; sort any column; add income or an expense (one-time, monthly or yearly); delete an entry; download a CSV report or print |
| **Agent Team** | Your requests and the agent team's responses | Send a request to any agent (status reports, releases, proposals, research) |
| **Activity Log** | Every action from the Command Center and the lead engine's admin endpoint | Read only |
| **Settings** | Data (Live or Test), theme, start tab, auto-refresh, how many days of inbox to show, Bcc me on emails, email signature | Saved to your Google account |

You also get a **daily brief by email at 7 AM** with the same alerts, meetings and numbers.

**Live / Test data:** **Settings → Data** switches to the TEST tabs that the staging site and staging apps write to. In test data every email goes to you (Gmail drafts can't be sent from test data), marked `[TEST to ...]`, so you can try every step without reaching a customer.

## Security
- The web app is deployed with **Execute as: Me** and **Who has access: Only myself**. Google sign-in is the front door, and every server function also checks that the signed-in user is the owner.
- Settings (Sheet ID, lead engine URL, admin token) live in **Script properties**, never in the code or this repo.
- License actions go to the lead engine with a secret admin token of at least 24 characters. A wrong token is refused and logged.
- Every action is written to the **Log** tab. Page output is escaped, and the page can't be embedded in other sites.
- Tests: `tests/test_command_center.py` checks the numbers, the owner check on every function, and that every button calls the right action.

## Setup (About 15 Minutes)
1. **Update the lead engine first.** Paste the new `lead-engine/Code.gs` over the old code in the lead-engine Apps Script and save. Go to **Project Settings → Script properties** and add `ADMIN_TOKEN` with a long random value (e.g. 32+ letters and numbers). Then click **Deploy → Manage deployments → ✏️ Edit → Version: New version → Deploy**. This keeps the same web app URL. Finally, run **setup** once more to add the new 2-hour status sync and the Prospects tab.
2. Go to script.google.com and click **New project**. Name it "Command Center".
3. Replace `Code.gs` with `command-center/Code.gs`. Click **+ → HTML**, name it `Index`, and paste the contents of `command-center/Index.html.txt` (stored as .txt so the public website never serves it as a page).
4. **Project Settings → Script properties:**
   - `LEADS_SHEET_ID`: the long ID in your Leads sheet's address (between `/d/` and `/edit`)
   - `LEAD_ENGINE_URL`: the lead engine web app URL (ends in `/exec`)
   - `ADMIN_TOKEN`: the same value as in step 1
5. Run **setupCommandCenter** once and approve the permissions (Sheets, Gmail read, Calendar read, external requests, triggers).
6. **Deploy → New deployment → Web app**, with **Execute as: Me** and **Who has access: Only myself**. Bookmark the URL on your phone and computer.

## How The Agent Team Picks Up Requests
Requests land in the **Requests** tab with Status `New`. A scheduled Claude task checks the tab, routes each request through chief-of-staff to the right agent, does the work, and writes the response (and a link to any doc, draft or release) back to the row with Status `Done`. Customer-facing results come back as drafts for your approval, as always.
