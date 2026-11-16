# Command Center

A private dashboard for running the business. It lives in your own Google account, and only you can open it.

| Tab | What it shows | What you can do |
|---|---|---|
| **Today** | Alerts (new and hot leads, trials ending, past-due clients, unpaid orders, agent replies), meetings for the next 7 days, unread **business** email only (clients, prospects, bookings, payments, orders, website forms; personal mail never shows) | Click through to any email |
| **Prospects & Pipeline** | A board of every website lead and outbound prospect by stage (New, Contacted, Replied, Booked, Trial, Proposal sent, Client, Closed), with search, totals and win rate | Drag a card to a new stage; open it to edit names and details, call or copy the phone number, email from a template (send now or save as a Gmail draft), add dated notes, start a 14-day trial (the link is emailed automatically), mark as client or lost, and add new prospects. Every change is noted on the record and in the Activity Log; stages also move forward on their own every 2 hours |
| **Clients & Licenses** | Every trial and client, plan, paid-through date, last app check; orders | Record payment, resend link, pause, cancel, mark as founding client. Clients get the usual emails |
| **Finance** | Estimated monthly revenue from active plans, revenue this month and year, costs, profit; ledger | Add income or an expense (paid orders count automatically) |
| **Agent Team** | Your requests and the agent team's responses | Send a request to any agent (status reports, releases, proposals, research) |
| **Activity Log** | Every action from the Command Center and the lead engine's admin endpoint | Read only |

You also get a **daily brief by email at 7 AM** with the same alerts, meetings and numbers.

**Live / Test data:** the **Data** menu in the header switches to the TEST tabs that the staging site and staging apps write to. In test data every email goes to you, marked `[TEST to ...]`, so you can try every step without reaching a customer.

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
