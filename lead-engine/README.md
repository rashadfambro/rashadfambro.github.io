# Lead Engine: Trial, License And Payment Automation

`Code.gs` is the free Google Apps Script backend for the website and the Desk tools. It runs in Rashad's own Google account: one Google Sheet plus Gmail. No client keys or customer data are stored here. The Sheet only holds business name, contact, tools and license status.

## What Runs On Its Own

| When | What happens |
|---|---|
| A visitor requests a free trial | Row added to **Licenses** (Status Trial). The branded 14-day trial link is emailed right away |
| 3 days and 1 day before a trial ends | Reminder email with the plan link. The app also shows an amber banner and a once-a-day reminder |
| The day after a trial ends | Status becomes Expired and a "trial ended, nothing charged" email goes out |
| A visitor places an order | Row added to **Orders** (Awaiting payment) with the exact amount due |
| Every 2 hours | Square/PayPal payment emails are matched to open orders by amount and payer email. On a match the license is issued and the Starter link is emailed. Anything unmatched is emailed to Rashad to record by hand |
| You set Status to **Active** (or use Desk ▸ Record payment) | Paid through set to one month ahead, new license link saved in the row and emailed |
| 5 days before paid through | Renewal reminder email |
| The day after paid through | Status becomes Past due and Rashad gets an alert. The app shows "renewal past due" |
| 30 days past due | Status becomes Paused and the client is emailed. The app locks on its next online check, and data stays on the client's device |
| You set Status to **Paused** or **Canceled** | Notice emailed. The app locks on its next online check |

Each automatic email can be turned off in `CFG`: `AUTO_SEND_TRIAL_LINKS`, `AUTO_SEND_LICENSE_LINKS`, `AUTO_MATCH_PAYMENTS`. Timing is set by `TRIAL_REMINDER_DAYS`, `RENEWAL_REMINDER_DAYS` and `PAUSE_AFTER_DAYS_PAST_DUE`.

## One-Time Setup (About 20 Minutes)

1. Create a Google Sheet named "RF Lead Engine". Open **Extensions ▸ Apps Script**, paste `Code.gs`, then save.
2. Fill in `BOOKING_URL` (and optionally `PHONE`) in `CFG`.
3. Run **setup** once and approve the permissions it asks for (Sheets, Gmail, triggers). This creates the Leads, Chats, Licenses and Orders tabs plus all schedules.
4. **Deploy ▸ New deployment ▸ Web app**, with Execute as: Me and Who has access: Anyone. Copy the `/exec` URL.
5. Paste the URL into `CONFIG.backendUrl` in index.html and into `DESK_BACKEND` in `scripts/generators/gen_prototypes.py`. Regenerate the prototypes, then release through staging.
6. Optional: add `ANTHROPIC_API_KEY` under Project Settings ▸ Script properties for the AI chat.
7. Run **testLead** to see the whole flow arrive in your own inbox.

The links this script emails are tested against the real tool apps in `tests/test_lead_engine.py`.
