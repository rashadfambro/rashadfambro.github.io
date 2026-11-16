/**
 * Rashad Fambro Consulting — Lead Engine (Google Apps Script)
 * ------------------------------------------------------------
 * One free backend for the website:
 *   • Saves every lead (audit form, project request, chatbot) to a Google Sheet
 *   • Scores each lead so the best ones rise to the top
 *   • Emails the prospect an instant, personal-sounding acknowledgment + booking link
 *   • Emails you an alert with the lead summary
 *   • Writes a personalized reply as a Gmail DRAFT for you to review and send
 *   • Sends polite follow-ups (day 2, 5, 10) until they reply, book, or opt out
 *   • Sends you a Monday pipeline digest
 *   • Powers the website's AI chat assistant (Claude API key stays here, never in the site)
 *   • Trials & licenses: emails branded trial links, trial-ending reminders, Starter edition license links and renewals;
 *     marks past due and pauses unpaid licenses; matches Square/PayPal payment emails; apps check their key here
 *
 * Setup: see SETUP.md. Short version: paste into Extensions → Apps Script of a new
 * Google Sheet, edit CFG, run setup(), then Deploy → New deployment → Web app.
 */

const CFG = {
  OWNER_NAME: 'Rashad Fambro',
  OWNER_EMAIL: 'rashadfambro@gmail.com',
  BUSINESS: 'Rashad Fambro Consulting',
  TITLE: 'IT Software Consultant',
  SITE_URL: 'https://rashadfambro.github.io/',
  BOOKING_URL: '',           // Free Workflow Audit booking link (Calendly) — paste it here
  LINKEDIN: 'https://www.linkedin.com/in/rashadfambro/',
  PHONE: '',

  SEND_PROSPECT_ACK: true,   // instant "got it" email to the prospect
  CREATE_REPLY_DRAFT: true,  // personalized reply saved to Gmail Drafts for you to send
  FOLLOW_UP_DAYS: [2, 5, 10],
  FOUNDING_SPOTS: 5,         // founding-client spots shown on the website; each Licenses row whose Plan includes "Founding" fills one
  TRIAL_DAYS: 14,// days after the lead arrives; stops when they reply or you change Status

  // AI (optional). Add your key in Project Settings → Script properties as ANTHROPIC_API_KEY.
  AI_MODEL: 'claude-haiku-5-5',
  CHAT_MAX_TURNS: 14,        // messages kept per conversation
  CHAT_DAILY_LIMIT: 40,      // replies per visitor session per day (cost guard)
  CHAT_GLOBAL_DAILY_LIMIT: 600,

  // Automation switches (Rashad approved automatic trial, license and reminder emails on Nov 15, 2026)
  AUTO_SEND_TRIAL_LINKS: true,     // email the branded trial link as soon as a trial request arrives
  AUTO_SEND_LICENSE_LINKS: true,   // email the Starter license link when a row's Status becomes Active or a payment is recorded
  AUTO_MATCH_PAYMENTS: true,       // read Square/PayPal payment emails and record matching payments automatically
  TRIAL_REMINDER_DAYS: [3, 1],     // trial reminder emails (days before the end)
  RENEWAL_REMINDER_DAYS: 5,        // renewal reminder before a paid-through date
  PAUSE_AFTER_DAYS_PAST_DUE: 30,   // paid licenses pause automatically this long after the paid-through date
  PROTOTYPES_URL: 'https://rashadfambro.github.io/prototypes/',
  PACKAGES: [
    'Free Workflow Audit — $0, 30-minute video call plus a one-page summary in 3 business days',
    'Workflow & Automation Assessment — $750 virtual or $1,500 on-site plus travel at cost; whatever was paid is credited toward a build started within 60 days',
    'Pilot / Custom Build — from $3,500, 3–8 weeks to launch (2–6 weeks to build plus 1–2 weeks of team testing); 1 location, up to 2 workflows, 1 connection to an existing system',
    'Customizations to a Desk tool from $500; new custom applications from $5,000; larger change requests quoted by scope (fixed-price quotes)',
    'Care & Growth Plan — from $150/month for custom applications',
    'Holiday & New Year Sale: 10% or more off all listed products and services through January 31, 2027, rounded down to the nearest $10 (does not combine with the founding discount)',
    'Payment plans: setups of $1,000+ can be split into 3 interest-free monthly payments; pay online with Square or PayPal (Order now buttons on the site)',
    'Monthly license & support plans: standard tools Essentials $50 / Growth $90 / Pro $150 per tool; property & hospitality tools $90 / $150 / $250 per property; any 3 standard tools on Essentials $120/mo. Plans include 1 / 3 / 6 small changes a month; extra work $150/hour',
    'Client-owned accounts: tools run in accounts the client owns; usage (texts, AI, storage) is billed by their providers, usually under $40/mo per tool. Fully Hosted by request: +$100/mo per tool (+$150 per property tool) with usage allowances',
    'Every tool: free 14-day branded trial workspace; Starter edition delivered 1–3 business days after payment; Connected edition (live texting, email, calendar in the client\'s accounts) in 3–8 weeks',
    'Advisory hours — $150/hour',
    'Founding clients (first 5): 25% off first setup or project, first month free, monthly price locked 12 months, priority scheduling; a testimonial after launch is required',
    'Bundles: Launch (ChatDesk + BookDesk) $2,500 setup; Property Management (WorkOrderDesk + PackageDesk + ChatDesk) $5,500; Hotel Operations (GuestDesk + HousekeepingDesk + WorkOrderDesk) $8,000. Referral reward: $150',
    'Meetings: virtual worldwide by default; on-site visits available'
  ],
  PRODUCTS: [
    'WorkOrderDesk — maintenance requests sorted, assigned and tracked, with resident updates staff approve (setup $3,500)',
    'ChatDesk — website chat that answers questions 24/7 from approved answers and hands the rest to staff (setup $1,500)',
    'BookDesk — online booking, reminders and a waitlist that fills cancellations (setup $1,500)',
    'GuestDesk — guest and owner requests routed to the right department (setup $3,500)',
    'HousekeepingDesk — room status board and fair housekeeping assignments (setup $3,500)',
    'RewardsDesk — phone-number rewards program (setup $1,000)',
    'InvoiceDesk — invoices and payment reminders (setup $1,000)',
    'LeadDesk — every inquiry in one place with fast first replies and follow-ups (setup $1,500)',
    'PackageDesk — package logging with pickup codes by text (setup $2,000)',
    'SocialDesk — social posts and DM replies the owner approves (setup $1,000)',
    'ReviewDesk — the same review invitation for every customer, plus drafted review replies (setup $500)',
    'StaffDesk — handbook answers and shift swaps (setup $2,000)',
    'InsightDesk — owner dashboard and weekly summary (setup $2,000)',
    'IntakeDesk — secure intake forms that flag missing items (setup $2,000)',
    'ComplianceDesk — recurring checklists, deadlines and an audit log (setup $3,500)'
  ]
};

const LEAD_HEADERS = ['Received','Lead ID','Status','Score','Form','Name','Business','Email','Phone','Industry','Team size',
  'Need / goal','Package','Timeline','Budget','Current tools','Availability','Founding client','Source','Landing page',
  'Follow-ups sent','Last contact','Notes'];
const STOP_STATUSES = ['Replied','Booked','Trial','Proposal sent','Ordered','Won','Lost','Do not contact','Spam'];
// Pipeline order: statuses only move forward automatically. Lost / Do not contact / Spam are never changed by the script.
const STATUS_RANK = { 'New': 0, 'Not contacted': 0, 'Draft ready': 0, 'Contacted': 1, 'Replied': 2, 'Booked': 3, 'Trial': 4, 'Proposal sent': 5, 'Ordered': 5.5, 'Won': 6 };
const PROSPECT_HEADERS = ['Added','Business','Contact','Email','Phone','City','Industry','Tools to pitch','Source','Status','Last activity','Next step','Notes'];

/* ======================= test environment ======================= */
// Staging, local and test traffic sends env:"staging". It is stored in separate "TEST ..." tabs, and every email it
// would send goes to the owner instead, marked [TEST to <address>]. Production tabs and real customers are never touched.
const TEST_PREFIX = 'TEST ';
let ENV_ = 'production';
function setEnv_(v) { ENV_ = v === 'staging' ? 'staging' : 'production'; return ENV_; }
function isTest_() { return ENV_ === 'staging'; }
function withTest_(fn) { const before = ENV_; ENV_ = 'staging'; try { fn(); } catch (e) { console.error(e); } finally { ENV_ = before; } }
function hasTestData_() { return !!SpreadsheetApp.getActiveSpreadsheet().getSheetByName(TEST_PREFIX + 'Licenses') || !!SpreadsheetApp.getActiveSpreadsheet().getSheetByName(TEST_PREFIX + 'Leads'); }
/** Menu: removes every TEST tab so the next test run starts clean. */
function clearTestData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.getSheets().filter(sh => sh.getName().indexOf(TEST_PREFIX) === 0).forEach(sh => ss.deleteSheet(sh));
}
/** Menu: runs the daily license checks and follow-ups on the TEST tabs right now (emails go to you). */
function runTestCycle() { withTest_(() => { runLicenses(); runFollowUps(); syncPipeline(); }); }

/* ======================= web endpoints ======================= */

function doPost(e) {
  try {
    const body = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    setEnv_(body.env);
    if (body.website) return json_({ ok: true });            // honeypot: bots fill hidden field
    if (body.type === 'lead') return json_(handleLead_(body));
    if (body.type === 'chat') return json_(handleChat_(body));
    if (body.type === 'license') return json_(checkLicense_(body));
    if (body.type === 'admin') return json_(adminAction_(body));
    return json_({ ok: false, error: 'unknown type' });
  } catch (err) {
    console.error(err);
    return json_({ ok: false, error: 'server error' });
  }
}

function doGet(e) {
  const p = (e && e.parameter) || {};
  setEnv_(p.env);
  if (p.check && p.key) return json_(checkLicense_({ kind: p.check, key: p.key }));
  if (p.stats === 'founding') return json_(foundingStats_());
  return json_({ ok: true, service: CFG.BUSINESS + ' lead engine' });
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

/* ======================= leads ======================= */

function handleLead_(d) {
  const lead = normalize_(d);
  if (!lead.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(lead.email)) return { ok: false, error: 'email required' };

  // basic abuse guard: max 5 submissions per email per hour
  const cache = CacheService.getScriptCache();
  const k = 'lead:' + lead.email.toLowerCase();
  const n = Number(cache.get(k) || 0);
  if (n >= 5) return { ok: true, duplicate: true };
  cache.put(k, String(n + 1), 3600);

  const sh = sheet_('Leads', LEAD_HEADERS);
  const existing = findRowByEmail_(sh, lead.email);
  lead.score = score_(lead);
  lead.id = existing ? sh.getRange(existing, 2).getValue() : 'L' + Utilities.formatDate(new Date(), 'UTC', 'yyMMddHHmmss') + Math.floor(Math.random() * 90 + 10);

  if (existing) {
    // returning lead: append the new request to Notes, bump score, re-open if it had gone quiet
    const notes = sh.getRange(existing, 23).getValue();
    sh.getRange(existing, 23).setValue((notes ? notes + '\n' : '') + stamp_() + ' ' + lead.form + ': ' + (lead.need || lead.packageName || ''));
    sh.getRange(existing, 4).setValue(Math.max(lead.score, Number(sh.getRange(existing, 4).getValue()) || 0));
    if (lead.packageName) sh.getRange(existing, 13).setValue(lead.packageName);
  } else {
    sh.appendRow([new Date(), lead.id, 'New', lead.score, lead.form, lead.name, lead.business, lead.email, lead.phone,
      lead.industry, lead.teamSize, lead.need, lead.packageName, lead.timeline, lead.budget, lead.tools,
      lead.availability, lead.founding, lead.source, lead.page, 0, new Date(), '']);
  }

  const row = existing || sh.getLastRow();
  const isTrial = /trial/i.test(lead.form), isOrder = /order/i.test(lead.form);
  if (isTrial) { issueTrial_(lead); bumpStatus_(sh, row, 'Trial'); }                  // trial emails replace audit follow-ups
  else if (isOrder) { const id = logOrder_(lead); sendOrderAck_(lead, id); bumpStatus_(sh, row, 'Ordered'); }
  else if (CFG.SEND_PROSPECT_ACK && !existing) sendAck_(lead);
  notifyOwner_(lead, !!existing);
  if (CFG.CREATE_REPLY_DRAFT && !isTrial && !isOrder) createDraft_(lead);
  return { ok: true, id: lead.id };
}

function normalize_(d) {
  const g = (...keys) => { for (const key of keys) if (d[key]) return String(d[key]).trim().slice(0, 2000); return ''; };
  return {
    form: g('form') || 'website',
    name: g('Name', 'name'),
    business: g('Business', 'business'),
    email: g('Email', 'email'),
    phone: g('Phone', 'phone'),
    industry: g('Industry', 'industry'),
    teamSize: g('Team size', 'teamSize'),
    need: g('Workflow', 'Goal', 'need', 'goal'),
    packageName: g('Package', 'package'),
    timeline: g('Start', 'timeline'),
    budget: g('Budget', 'budget'),
    amountDue: g('Amount due', 'amountDue'),
    plan: g('Plan', 'plan'),
    method: g('Method', 'method'),
    tools: g('Current tools', 'tools'),
    availability: [g('Availability', 'availability'), g('Meeting preference', 'meeting')].filter(Boolean).join(' · '),
    founding: g('Founding client program', 'founding'),
    source: g('source'),
    page: g('page')
  };
}

/** 0–100. Tune the weights to match the clients you want most. */
function score_(l) {
  let s = 20;
  const ind = (l.industry || '').toLowerCase();
  if (/apartment|property|hotel|resort|timeshare|vacation/.test(ind)) s += 20;      // current focus markets
  else if (ind) s += 10;
  if (/pilot|mvp|assessment|care/i.test(l.packageName)) s += 15;
  if (/soon|asap|1–2|1-2/i.test(l.timeline)) s += 15;
  if (/\$7,500|\$20,000/.test(l.budget)) s += 15; else if (/\$2,500/.test(l.budget)) s += 8;
  if (/16|51|200/.test(l.teamSize)) s += 10; else if (/6–15|6-15/.test(l.teamSize)) s += 6;
  if (l.need && l.need.length > 60) s += 5;
  if (l.phone) s += 5;
  if (/yes/i.test(l.founding)) s += 5;
  return Math.min(100, s);
}

/* ======================= email ======================= */

/** Moves a lead forward (never backward, never out of Lost / Do not contact / Spam). */
function bumpStatus_(sh, row, status) {
  const cur = String(sh.getRange(row, 3).getValue() || 'New');
  if (cur in STATUS_RANK && STATUS_RANK[status] > STATUS_RANK[cur]) sh.getRange(row, 3).setValue(status);
}

/** Confirmation for an order placed on the site (payment happens on Square or PayPal; the license link follows automatically). */
function sendOrderAck_(l, orderId) {
  const amount = Number(String(l.amountDue || '').replace(/[^\d.]/g, ''));
  send_(l.email, 'Order received: ' + (l.packageName || 'your order') + ' for ' + (l.business || 'your business'),
    ['Hi ' + first_(l.name) + ',', '',
     'Thanks for your order' + (l.business ? ' for ' + l.business : '') + '. Here are the details:', '',
     '- Item: ' + (l.packageName || 'see your order'),
     amount ? '- Amount due now: $' + amount.toLocaleString('en-US') + (l.plan ? ' (' + l.plan + ')' : '') : null,
     l.method ? '- Payment method: ' + l.method : null,
     '- Order number: ' + orderId, '',
     'If the checkout page didn\'t finish, reply to this email and I\'ll send a secure payment link. As soon as payment arrives, your Starter edition link is emailed to you automatically, and I\'ll reach out to schedule a 30-minute setup call.', '',
     'Questions? Just reply.', '', 'Best,' + signature_()].filter(x => x !== null).join('\n'),
    { name: CFG.OWNER_NAME, replyTo: CFG.OWNER_EMAIL });
}
function first_(name) { return (name || '').split(/\s+/)[0] || 'there'; }
function signature_() {
  return '\n' + [CFG.OWNER_NAME, CFG.TITLE + ' · ' + CFG.BUSINESS, CFG.PHONE, CFG.SITE_URL, CFG.LINKEDIN].filter(Boolean).join('\n');
}
function bookingLine_() {
  return CFG.BOOKING_URL
    ? 'If it’s easier, you can grab a 30-minute time that works for you here: ' + CFG.BOOKING_URL
    : 'Reply with two or three times that work for you this week and I’ll send a calendar invite.';
}

function sendAck_(l) {
  const isProject = /project|proposal/i.test(l.form);
  const subject = isProject ? 'Got your project request — next steps' : 'Got your request — let’s find your quickest win';
  const body = [
    'Hi ' + first_(l.name) + ',', '',
    'Thanks for reaching out' + (l.business ? ' about ' + l.business : '') + '. I received your ' +
      (isProject ? 'project request' : 'request') + ' and I’ll personally review it within one business day.', '',
    l.need ? 'You mentioned: “' + l.need.slice(0, 300) + '”' : '',
    l.need ? '' : null,
    bookingLine_(), '',
    'To make our call as useful as possible, it helps to know roughly how often this task happens each week and which tools your team uses for it today. A quick reply is plenty.', '',
    'Talk soon,' + signature_(), '',
    '(Reply STOP if you’d rather not get follow-up emails.)'
  ].filter(x => x !== null).join('\n');
  send_(l.email, subject, body, { name: CFG.OWNER_NAME, replyTo: CFG.OWNER_EMAIL });
}

function notifyOwner_(l, returning) {
  // Plain text only: Gmail shows emoji in script-sent subjects as question marks.
  const subject = (/trial/i.test(l.form) ? '[Trial] New 14-day trial' : /order/i.test(l.form) ? '[Order] New order, awaiting payment' : returning ? '[Returning] Lead is back' : (l.score >= 60 ? '[Hot lead]' : '[Lead]')) +
    (/^\[(Hot lead|Lead)\]$/.test(returning ? '' : (l.score >= 60 ? '[Hot lead]' : '[Lead]')) && !/trial|order/i.test(l.form) ? ' ' : ': ') + (l.business || l.name || l.email) + ' (score ' + l.score + ', ' + l.form + ')';
  const lines = Object.entries({
    Name: l.name, Business: l.business, Email: l.email, Phone: l.phone, Industry: l.industry, 'Team size': l.teamSize,
    Need: l.need, Package: l.packageName, Timeline: l.timeline, Budget: l.budget, Tools: l.tools,
    Availability: l.availability, Founding: l.founding, Source: l.source, Page: l.page
  }).filter(([, v]) => v).map(([k, v]) => k + ': ' + v);
  const body = lines.join('\n') + '\n\n' +
    (CFG.CREATE_REPLY_DRAFT ? 'A personalized reply is waiting in your Gmail Drafts.\n' : '') +
    'Lead sheet: ' + SpreadsheetApp.getActiveSpreadsheet().getUrl();
  send_(CFG.OWNER_EMAIL, subject, body, { name: CFG.BUSINESS + ' Leads' });
}

function createDraft_(l) {
  let text = '';
  if (aiKey_()) {
    try {
      text = claude_([
        { role: 'user', content:
          'Write a short, warm, plain-English email reply from ' + CFG.OWNER_NAME + ' (' + CFG.TITLE + ') to this new inquiry. ' +
          'Goals: show you understood their specific problem, suggest 1–2 concrete ideas of what could help (no prices, no guarantees), ' +
          'and ask them to book the free 30-minute workflow audit. Under 170 words. No subject line. No placeholders. ' +
          'Do not include a sign-off or signature.\n\nInquiry details:\n' + JSON.stringify(l, null, 2) }
      ], 'You draft client emails for a small software consulting business. Be specific, friendly and honest; never invent facts about the prospect.', 500);
    } catch (err) { console.warn('AI draft failed, using template', err); }
  }
  if (!text) {
    text = 'Hi ' + first_(l.name) + ',\n\n' +
      'Thanks again for reaching out' + (l.business ? ' about ' + l.business : '') + '. ' +
      (l.need ? 'I read through what you shared about “' + l.need.slice(0, 160) + '”, and it’s a great fit for a quick workflow audit. ' : '') +
      'In 30 minutes we’ll map where the time goes, and I’ll send you a one-page summary with the first change I’d make — yours to keep either way.\n\n' +
      bookingLine_() + '\n\nBest,';
  }
  draft_(l.email, 'Re: your ' + (/project/i.test(l.form) ? 'project request' : 'workflow audit request'),
    text.replace(/\s+$/, '') + (/Best,$/.test(text) ? '' : '\n\nBest,') + signature_(), { name: CFG.OWNER_NAME });
}

/* ======================= email sending ======================= */

/** Every email goes through here. Subjects and bodies are converted to plain characters first:
 *  emoji and some symbols arrived as "??????" in script-sent subjects, and plain text reads the same everywhere. */
const ASCII_MAP_ = [[/[‘’‚′]/g, "'"], [/[“”„″]/g, '"'], [/[–—−]/g, '-'], [/…/g, '...'],
  [/[•·▸►‣]/g, '-'], [/→/g, '->'], [/ /g, ' '], [/™/g, '(TM)'], [/©/g, '(c)'], [/×/g, 'x']];
function plain_(s) {
  s = String(s == null ? '' : s);
  ASCII_MAP_.forEach(m => { s = s.replace(m[0], m[1]); });
  s = s.normalize ? s.normalize('NFKD').replace(/[̀-ͯ]/g, '') : s;   // café -> cafe
  return s.replace(/[^\x09\x0A\x0D\x20-\x7E]/g, '');                            // drop anything else (emoji)
}
function testRoute_(to, subject) { return isTest_() ? [CFG.OWNER_EMAIL, '[TEST to ' + to + '] ' + subject] : [to, subject]; }
function send_(to, subject, body, opts) { const r = testRoute_(to, subject); GmailApp.sendEmail(r[0], plain_(r[1]).replace(/\s+/g, ' ').trim(), plain_(body), opts || {}); }
function draft_(to, subject, body, opts) { const r = testRoute_(to, subject); return GmailApp.createDraft(r[0], plain_(r[1]).replace(/\s+/g, ' ').trim(), plain_(body), opts || {}); }

/* ======================= trials & licenses (v2, Nov 15 2026) =======================
 * Licenses tab, one row per client (a package is one row listing several tools):
 *   Key | Tools | Business | Email | Status | Plan | Created | Ends / paid through | Last check | Notes | Link | Color | Contact | Amount
 * Status: Trial → (Active) → Past due → Paused; or Expired / Canceled.
 * Everything below runs on its own once setup() has installed the triggers:
 *   • A trial request from the site → branded trial link emailed automatically (AUTO_SEND_TRIAL_LINKS).
 *   • Daily: trial reminders 3 and 1 days before the end, "trial ended" email, Expired status.
 *   • You change Status to Active (or use Desk ▸ Record payment) → paid-through date set, Starter license link emailed.
 *   • Daily: renewal reminder 5 days before paid-through; Past due the day after; Paused after 30 days past due.
 *   • Paused or Canceled → the tool apps lock on their next online check (the client's data stays on their device).
 *   • Every few hours: Square/PayPal payment emails are matched to orders and recorded automatically.
 */
const LICENSE_HEADERS = ['Key','Tools','Business','Email','Status','Plan','Created','Ends / paid through','Last check','Notes','Link','Color','Contact','Amount'];
const LICENSE_STATUSES = ['Trial','Active','Past due','Paused','Expired','Canceled'];
const ORDER_HEADERS = ['Received','Order ID','Status','Business','Name','Email','Item','Tools','Amount due','Plan','Method','License key','Notes'];
const TOOL_IDS = { WorkOrderDesk:'property', ChatDesk:'chat', BookDesk:'salon', GuestDesk:'resort', HousekeepingDesk:'housekeeping',
  RewardsDesk:'rewards', InvoiceDesk:'invoice', LeadDesk:'service', PackageDesk:'package', SocialDesk:'social', ReviewDesk:'review',
  StaffDesk:'staff', InsightDesk:'insight', IntakeDesk:'intake', ComplianceDesk:'compliance' };
const TOOL_PAGES = { property:'workorders.html', chat:'chat.html', salon:'bookings.html', resort:'guests.html', housekeeping:'housekeeping.html',
  rewards:'rewards.html', invoice:'invoices.html', service:'leads.html', package:'packages.html', social:'social.html', review:'reviews.html',
  staff:'staff.html', insight:'insights.html', intake:'intake.html', compliance:'compliance.html' };
const BUNDLE_TOOLS = { 'Launch Bundle':'chat,salon', 'Property Management Bundle':'property,package,chat', 'Hotel Operations Bundle':'resort,housekeeping,property' };

// Same keys as the tool apps (prototypes) and the internal link generator — keep these three in step.
function trialHash_(s) { let h = 2166136261; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return (h >>> 0).toString(36).toUpperCase().padStart(6, '0').slice(0, 6); }
function trialKey_(tools, biz, start) { return 'RF-' + start.replace(/-/g, '') + '-' + trialHash_(tools + '|' + biz.trim().toLowerCase() + '|' + start); }
function licenseKey_(tools, biz, until) { return 'RFL-' + until.replace(/-/g, '') + '-' + trialHash_('L|' + tools + '|' + biz.trim().toLowerCase() + '|' + until); }
function ymd_(d) { return Utilities.formatDate(new Date(d), Session.getScriptTimeZone(), 'yyyy-MM-dd'); }
function addDays_(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x; }
function addMonths_(d, n) { const x = new Date(d); x.setMonth(x.getMonth() + n); return x; }
function daysUntil_(d) { const a = new Date(ymd_(new Date()) + 'T00:00:00'), b = new Date(ymd_(d) + 'T00:00:00'); return Math.round((b - a) / 86400000); }
function prettyDate_(d) { return Utilities.formatDate(new Date(d), Session.getScriptTimeZone(), 'MMMM d, yyyy'); }

/** "WorkOrderDesk (Essentials plan)" / "Property Management Bundle: …" / "ChatDesk, BookDesk" → "property,package,chat" */
function toolsFrom_(text) {
  text = String(text || '');
  for (const name in BUNDLE_TOOLS) if (text.indexOf(name) >= 0) return BUNDLE_TOOLS[name];
  const ids = [];
  Object.keys(TOOL_IDS).forEach(n => { if (text.indexOf(n) >= 0 && ids.indexOf(TOOL_IDS[n]) < 0) ids.push(TOOL_IDS[n]); });
  return ids.join(',') || 'chat';
}
function toolNames_(tools) { const rev = {}; Object.keys(TOOL_IDS).forEach(n => rev[TOOL_IDS[n]] = n); return tools.split(',').map(t => rev[t] || t).join(', '); }
function appLink_(kind, tools, biz, date, color) {
  const page = tools.indexOf(',') >= 0 ? 'suite.html' : (TOOL_PAGES[tools] || 'suite.html');
  const key = kind === 'trial' ? trialKey_(tools, biz, date) : licenseKey_(tools, biz, date);
  const q = [kind + '=' + encodeURIComponent(key), 'biz=' + encodeURIComponent(biz), 'color=' + encodeURIComponent(color || '#2f7fe0'),
    (kind === 'trial' ? 'start=' : 'until=') + date, 'tools=' + encodeURIComponent(tools)].join('&');
  return { key: key, url: CFG.PROTOTYPES_URL + page + '?' + q };
}
function mail_(to, subject, body) {
  send_(to, subject, body, { name: CFG.OWNER_NAME, replyTo: CFG.OWNER_EMAIL });
}
function note_(sh, row, text, col) { const c = sh.getRange(row, col || 10); c.setValue((c.getValue() ? c.getValue() + ' · ' : '') + stamp_() + ' ' + text); }

/** A trial request from the site (form "trial"): issue the branded trial link and email it. */
function issueTrial_(l) {
  const sh = sheet_('Licenses', LICENSE_HEADERS);
  const tools = toolsFrom_(l.packageName || l.need), biz = l.business || l.name || 'Your Business', start = ymd_(new Date());
  const link = appLink_('trial', tools, biz, start, '#2f7fe0');
  const ends = addDays_(new Date(start + 'T00:00:00'), CFG.TRIAL_DAYS);
  sh.appendRow([link.key, tools, biz, l.email, 'Trial', 'Trial', new Date(), ends, '', 'trial requested', link.url, '#2f7fe0', l.name, '']);
  if (CFG.AUTO_SEND_TRIAL_LINKS) {
    mail_(l.email, 'Your 14-day ' + toolNames_(tools) + ' trial for ' + biz,
      'Hi ' + first_(l.name) + ',\n\nHere is your free ' + CFG.TRIAL_DAYS + '-day trial of ' + toolNames_(tools) + ', branded for ' + biz + ':\n' + link.url +
      '\n\nTry it with the sample data or enter your own. It runs in your browser and nothing is sent to your customers. ' +
      'Your trial ends ' + prettyDate_(ends) + ', and nothing is charged automatically. I\'ll send a reminder before it ends.\n\n' +
      'Want help loading your real services, hours and team? ' + (CFG.BOOKING_URL ? 'Book a free 30-minute setup call: ' + CFG.BOOKING_URL : 'Reply with a couple of times for a free 30-minute setup call.') +
      '\n\nBest,' + signature_());
    note_(sh, sh.getLastRow(), 'trial link emailed');
  }
  return link.key;
}

/** An order from the site (form "order"): log it so the payment can be matched and the license issued. */
function logOrder_(l) {
  const sh = sheet_('Orders', ORDER_HEADERS);
  const amount = Number(String(l.amountDue || '').replace(/[^\d.]/g, '')) || '';
  const id = 'O' + Utilities.formatDate(new Date(), 'UTC', 'yyMMddHHmmss');
  sh.appendRow([new Date(), id, 'Awaiting payment', l.business, l.name, l.email, l.packageName, toolsFrom_(l.packageName), amount, l.plan || 'Pay in full', l.method, '', l.founding ? 'founding' : '']);
  return id;
}

/** Answers the tool apps' online check: ?check=trial|license&key=… */
function checkLicense_(d) {
  const key = String(d.key || '').trim().toUpperCase();
  if (!key) return { ok: false, valid: false, error: 'key required' };
  const sh = sheet_('Licenses', LICENSE_HEADERS), rows = sh.getDataRange().getValues();
  for (let r = 1; r < rows.length; r++) {
    if (String(rows[r][0]).toUpperCase() !== key) continue;
    const status = rows[r][4], ends = rows[r][7], daysLeft = ends ? daysUntil_(ends) : null;
    sh.getRange(r + 1, 9).setValue(new Date());
    const valid = status === 'Active' || status === 'Past due' || (status === 'Trial' && daysLeft !== null && daysLeft >= 0);
    return { ok: true, valid: valid, status: status, tools: rows[r][1], plan: rows[r][5], ends: ends ? ymd_(ends) : null, daysLeft: daysLeft };
  }
  return { ok: true, valid: true, status: 'Unknown' };   // unknown keys keep working offline-style; the app's own date check still applies
}

/** Issue (or renew) the paid Starter license for a row: paid through +1 month, new link, email. */
function activateRow_(sh, row, opts) {
  opts = opts || {};
  const v = sh.getRange(row, 1, 1, LICENSE_HEADERS.length).getValues()[0];
  const tools = v[1], biz = v[2], email = v[3], color = v[11] || '#2f7fe0', contact = v[12];
  const prev = v[7] && v[4] !== 'Trial' && v[4] !== 'Expired' ? new Date(v[7]) : new Date();
  const base = prev > new Date() ? prev : new Date();
  const until = ymd_(addMonths_(base, opts.months || 1));
  const link = appLink_('license', tools, biz, until, color);
  sh.getRange(row, 1).setValue(link.key);
  sh.getRange(row, 5).setValue('Active');
  if (!v[5] || v[5] === 'Trial') sh.getRange(row, 6).setValue('Essentials');
  CacheService.getScriptCache().remove('foundingLeft');
  sh.getRange(row, 8).setValue(new Date(until + 'T00:00:00'));
  sh.getRange(row, 11).setValue(link.url);
  note_(sh, row, (opts.renewal ? 'renewed' : 'activated') + ' through ' + until);
  if (CFG.AUTO_SEND_LICENSE_LINKS && email) {
    mail_(email, (opts.renewal ? 'Your renewed ' : 'Your ') + toolNames_(tools) + ' link for ' + biz,
      'Hi ' + first_(contact) + ',\n\n' + (opts.renewal ? 'Thanks for your payment! ' : 'Welcome aboard! ') +
      'Here is your Starter edition of ' + toolNames_(tools) + ', branded for ' + biz + ':\n' + link.url +
      '\n\nBookmark it on the computer or tablet your team uses. Your plan is paid through ' + prettyDate_(until) + '.\n' +
      '- Your data is saved on that device. Use "Download backup" weekly; "Restore backup" brings it back on a new device.\n' +
      '- When you approve a message, it\'s copied so you can paste it into your text or email app. Live sending comes with the Connected edition.\n' +
      (opts.renewal ? '' : '\n' + (CFG.BOOKING_URL ? 'Book your 30-minute setup call: ' + CFG.BOOKING_URL : 'Reply with a couple of times for your 30-minute setup call.') + '\n') +
      '\nBest,' + signature_());
    note_(sh, row, 'license link emailed');
  }
  SpreadsheetApp.flush();
  return link;
}

/** Installable onEdit trigger: changing Status in the Licenses tab enables or disables a license. */
function onLicenseEdit(e) {
  try {
    const sh = e.range.getSheet();
    if (sh.getName() === TEST_PREFIX + 'Licenses') ENV_ = 'staging'; else if (sh.getName() !== 'Licenses') return;
    if (e.range.getColumn() !== 5 || e.range.getRow() < 2) return;
    const row = e.range.getRow(), status = e.value, email = sh.getRange(row, 4).getValue(), tools = sh.getRange(row, 2).getValue(), biz = sh.getRange(row, 3).getValue();
    if (status === 'Active') activateRow_(sh, row);
    if ((status === 'Paused' || status === 'Canceled') && email) {
      mail_(email, 'Your ' + toolNames_(tools) + ' license is ' + status.toLowerCase(),
        'Hi,\n\nYour ' + toolNames_(tools) + ' license for ' + biz + ' is now ' + status.toLowerCase() + '. Your data stays on your device, and you can download a backup from the app at any time.' +
        (status === 'Paused' ? ' Reply to this email and I\'ll turn it back on as soon as the plan is current.' : ' Thank you for working with me.') + '\n\nBest,' + signature_());
      note_(sh, row, status.toLowerCase() + ' (emailed)');
    }
  } catch (err) { console.error(err); }
}

/** Menu helper: record a payment for the selected Licenses row (renews one month). */
function recordPaymentForSelectedRow() {
  const sh = SpreadsheetApp.getActiveSheet();
  if (sh.getName() !== 'Licenses') { SpreadsheetApp.getUi().alert('Select a row on the Licenses tab first.'); return; }
  const row = sh.getActiveRange().getRow(); if (row < 2) return;
  const status = sh.getRange(row, 5).getValue();
  activateRow_(sh, row, { renewal: status === 'Active' || status === 'Past due' || status === 'Paused' });
}

/** Runs daily: trial reminders and expiry; renewal reminders, Past due, and automatic pause. */
function runLicenses() {
  if (!isTest_() && hasTestData_()) withTest_(runLicenses);   // test licenses get the same checks (emails go to you)
  const sh = sheet_('Licenses', LICENSE_HEADERS), rows = sh.getDataRange().getValues();
  for (let r = 1; r < rows.length; r++) {
    const [key, tools, biz, email, status, plan, , ends, , notes, link, , contact] = rows[r];
    if (!ends || !email) continue;
    const d = daysUntil_(ends), row = r + 1, n = String(notes || '');
    if (status === 'Trial') {
      if (CFG.TRIAL_REMINDER_DAYS.indexOf(d) >= 0 && n.indexOf('reminder ' + d + 'd') < 0) {
        mail_(email, 'Your ' + toolNames_(tools) + ' trial ends in ' + d + ' day' + (d === 1 ? '' : 's'),
          'Hi ' + first_(contact) + ',\n\nYour free trial for ' + biz + ' ends on ' + prettyDate_(ends) + '. To keep it running, choose a plan here:\n' + CFG.SITE_URL + '#pricing' +
          '\n\nOr reply with questions. If you let it end, nothing is charged and you can still download what you entered from the app.\n\nYour trial link: ' + link + '\n\nBest,' + signature_());
        note_(sh, row, 'reminder ' + d + 'd');
      }
      if (d < 0) {
        sh.getRange(row, 5).setValue('Expired');
        mail_(email, 'Your ' + toolNames_(tools) + ' trial has ended',
          'Hi ' + first_(contact) + ',\n\nYour free trial for ' + biz + ' has ended. Nothing was charged. Your entries are still in the app, and you can download them.\n\n' +
          'Ready to keep going? Choose a plan here: ' + CFG.SITE_URL + '#pricing, or reply and I\'ll help you pick the right one.\n\nBest,' + signature_());
        note_(sh, row, 'expired (emailed)');
      }
    }
    if (status === 'Active' && d === CFG.RENEWAL_REMINDER_DAYS && n.indexOf('renewal reminder ' + ymd_(ends)) < 0) {
      mail_(email, 'Your ' + toolNames_(tools) + ' plan renews ' + prettyDate_(ends),
        'Hi ' + first_(contact) + ',\n\nA quick heads-up: your ' + plan + ' plan for ' + biz + ' is paid through ' + prettyDate_(ends) + '. I\'ll send the next invoice shortly; once it\'s paid, you\'ll get your renewed link automatically.\n\nBest,' + signature_());
      note_(sh, row, 'renewal reminder ' + ymd_(ends));
    }
    if (status === 'Active' && d < 0) { sh.getRange(row, 5).setValue('Past due'); note_(sh, row, 'past due');
      mail_(CFG.OWNER_EMAIL, 'Past due: ' + biz, biz + ' (' + email + ') is past due since ' + prettyDate_(ends) + '. Tools: ' + toolNames_(tools) + '.'); }
    if (status === 'Past due' && d <= -CFG.PAUSE_AFTER_DAYS_PAST_DUE) { sh.getRange(row, 5).setValue('Paused');
      mail_(email, 'Your ' + toolNames_(tools) + ' license is paused',
        'Hi ' + first_(contact) + ',\n\nYour plan for ' + biz + ' is ' + (-d) + ' days past due, so the app is paused. Your data is safe on your device. Reply and I\'ll turn it back on as soon as the plan is current.\n\nBest,' + signature_());
      note_(sh, row, 'paused (emailed)'); }
  }
}

/** Runs every few hours: match Square/PayPal payment emails to orders or licenses, then issue/renew automatically. */
function matchPayments() {
  if (!CFG.AUTO_MATCH_PAYMENTS) return;
  const label = GmailApp.getUserLabelByName('Desk/payment-matched') || GmailApp.createLabel('Desk/payment-matched');
  const threads = GmailApp.search('newer_than:3d -label:Desk/payment-matched (from:(squareup.com) OR from:(paypal.com)) (payment OR paid OR received)', 0, 30);
  const orders = sheet_('Orders', ORDER_HEADERS), lic = sheet_('Licenses', LICENSE_HEADERS);
  threads.forEach(th => {
    const msg = th.getMessages()[th.getMessages().length - 1], body = msg.getPlainBody() + ' ' + msg.getSubject();
    const amt = (body.match(/\$\s?([\d,]+\.\d{2})/) || [])[1], payer = ((body.match(/[\w.+-]+@[\w-]+\.[\w.-]+/g) || []).filter(e => !/squareup|paypal|rashadfambro/i.test(e))[0] || '').toLowerCase();
    if (!amt) return;
    const amount = Number(amt.replace(/,/g, ''));
    const ov = orders.getDataRange().getValues(); let matched = false;
    for (let r = ov.length - 1; r >= 1 && !matched; r--) {
      if (ov[r][2] !== 'Awaiting payment' || Number(ov[r][8]) !== amount) continue;
      if (payer && String(ov[r][5]).toLowerCase() !== payer) continue;
      // find or create the license row, then activate
      const lv = lic.getDataRange().getValues(); let row = 0;
      for (let i = 1; i < lv.length; i++) if (String(lv[i][3]).toLowerCase() === String(ov[r][5]).toLowerCase() && lv[i][1] === ov[r][7]) row = i + 1;
      if (!row) { lic.appendRow(['', ov[r][7], ov[r][3] || ov[r][4], ov[r][5], 'Trial', /founding/i.test(ov[r][12]) ? 'Essentials (Founding)' : 'Essentials', new Date(), '', '', 'from order ' + ov[r][1], '', '#2f7fe0', ov[r][4], amount]); row = lic.getLastRow(); }
      else if (/founding/i.test(ov[r][12]) && !/founding/i.test(lic.getRange(row, 6).getValue())) lic.getRange(row, 6).setValue(String(lic.getRange(row, 6).getValue() || 'Essentials').replace(/^Trial$/, 'Essentials') + ' (Founding)');
      CacheService.getScriptCache().remove('foundingLeft');
      const link = activateRow_(lic, row);
      orders.getRange(r + 1, 3).setValue('Paid'); orders.getRange(r + 1, 12).setValue(link.key);
      orders.getRange(r + 1, 13).setValue('matched ' + stamp_() + ' from ' + msg.getFrom());
      matched = true;
    }
    if (!matched) mail_(CFG.OWNER_EMAIL, 'Payment received: match it by hand ($' + amt + ')',
      'A payment email arrived but didn\'t match exactly one open order.\nFrom: ' + msg.getFrom() + '\nSubject: ' + msg.getSubject() +
      '\n\nOpen the Licenses tab, select the client\'s row, and use Desk ▸ Record payment.');
    th.addLabel(label);
  });
}

/** Founding spots left for the website counter (cached 10 minutes). A Licenses row counts when its
 *  Plan includes "Founding" and it is Active, Past due or Paused. */
function foundingStats_() {
  const cache = CacheService.getScriptCache(), hit = cache.get('foundingLeft');
  if (hit !== null) return { ok: true, foundingLeft: Number(hit) };
  const rows = sheet_('Licenses', LICENSE_HEADERS).getDataRange().getValues().slice(1);
  const taken = rows.filter(r => /founding/i.test(String(r[5])) && ['Active', 'Past due', 'Paused'].indexOf(r[4]) >= 0).length;
  const left = Math.max(0, CFG.FOUNDING_SPOTS - taken);
  cache.put('foundingLeft', String(left), 600);
  return { ok: true, foundingLeft: left };
}
function markFoundingClient() {
  const sh = SpreadsheetApp.getActiveSheet();
  if (sh.getName() !== 'Licenses') { SpreadsheetApp.getUi().alert('Select a row on the Licenses tab first.'); return; }
  const row = sh.getActiveRange().getRow(); if (row < 2) return;
  const plan = String(sh.getRange(row, 6).getValue() || 'Essentials').replace(/\s*\(Founding\)/i, '');
  sh.getRange(row, 6).setValue(plan + ' (Founding)'); note_(sh, row, 'marked founding client');
  CacheService.getScriptCache().remove('foundingLeft');
  SpreadsheetApp.getUi().alert('Marked as a founding client. The website shows ' + foundingStats_().foundingLeft + ' spot(s) left within a few minutes.');
}

/* ======================= nightly backup ======================= */

/** Runs nightly: copies the whole Sheet (leads, prospects, licenses, orders, log) into the Drive folder
 *  "RF Lead Engine Backups" and keeps the newest 30 copies. Restore = open a copy and copy rows back. */
function backupSheet() {
  const name = 'RF Lead Engine Backups';
  const it = DriveApp.getFoldersByName(name);
  const folder = it.hasNext() ? it.next() : DriveApp.createFolder(name);
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  DriveApp.getFileById(ss.getId()).makeCopy(ss.getName() + ' backup ' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HHmm'), folder);
  const files = [], fi = folder.getFiles();
  while (fi.hasNext()) files.push(fi.next());
  files.sort((a, b) => b.getDateCreated() - a.getDateCreated()).slice(30).forEach(f => f.setTrashed(true));
  log_('backup', ss.getName(), 'ok, ' + Math.min(files.length, 30) + ' kept');
}

/* ======================= admin actions (Command Center) ======================= */

/** Called only by the private Command Center with the shared ADMIN_TOKEN (Script properties in both
 *  projects). Runs the same steps as the Sheet menu, so emails and links go out exactly as usual.
 *  Every call, allowed or refused, is written to the Log tab. */
function adminAction_(b) {
  const want = PropertiesService.getScriptProperties().getProperty('ADMIN_TOKEN') || '';
  const ok = want.length >= 24 && safeEqual_(String(b.token || ''), want);
  const act = String(b.action || ''), key = String(b.key || '').trim().toUpperCase();
  if (!ok) { log_('admin', act, key, 'refused: bad token'); return { ok: false, error: 'unauthorized' }; }
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const sh = sheet_('Licenses', LICENSE_HEADERS), rows = sh.getDataRange().getValues();
    let row = 0;
    for (let r = 1; r < rows.length; r++) if (String(rows[r][0]).toUpperCase() === key) row = r + 1;
    if (!row) { log_('admin', act, key, 'not found'); return { ok: false, error: 'license not found' }; }
    const email = rows[row - 1][3], tools = rows[row - 1][1], biz = rows[row - 1][2], status = rows[row - 1][4];
    let result;
    if (act === 'record_payment') { const link = activateRow_(sh, row, { renewal: ['Active', 'Past due', 'Paused'].indexOf(status) >= 0 }); result = { key: link.key }; }
    else if (act === 'pause' || act === 'cancel') {
      const s = act === 'pause' ? 'Paused' : 'Canceled';
      sh.getRange(row, 5).setValue(s);
      onLicenseEdit({ range: sh.getRange(row, 5), value: s });   // same notice email as editing the cell by hand
      result = { status: s };
    }
    else if (act === 'resend') {
      mail_(email, 'Your ' + toolNames_(tools) + ' link for ' + biz, 'Hi,\n\nHere is your link again:\n' + rows[row - 1][10] + '\n\nBest,' + signature_());
      note_(sh, row, 'link re-sent'); result = { sent: true };
    }
    else if (act === 'mark_founding') {
      const plan = String(rows[row - 1][5] || 'Essentials').replace(/\s*\(Founding\)/i, '');
      sh.getRange(row, 6).setValue(plan + ' (Founding)'); CacheService.getScriptCache().remove('foundingLeft'); result = foundingStats_();
    }
    else { log_('admin', act, key, 'unknown action'); return { ok: false, error: 'unknown action' }; }
    log_('admin', act, key, 'ok');
    return Object.assign({ ok: true }, result);
  } catch (err) { log_('admin', act, key, 'error: ' + err); return { ok: false, error: 'server error' }; }
  finally { lock.releaseLock(); }
}
function safeEqual_(a, b) { if (a.length !== b.length) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; }
function log_(source, action, target, result) {
  try { sheet_('Log', ['Time', 'Source', 'Action', 'Target', 'Result']).appendRow([new Date(), source, action, target, result]); } catch (e) { console.error(e); }
}

function onOpen() {
  SpreadsheetApp.getUi().createMenu('Desk')
    .addItem('Record payment for selected license row', 'recordPaymentForSelectedRow')
    .addItem('Mark selected license row as a founding client', 'markFoundingClient')
    .addItem('Run license checks now', 'runLicenses')
    .addItem('Match payment emails now', 'matchPayments')
    .addItem('Update lead and prospect statuses now', 'syncPipeline')
    .addItem('Back up this Sheet now', 'backupSheet')
    .addSeparator()
    .addItem('Test environment: run reminders and checks now', 'runTestCycle')
    .addItem('Test environment: clear all TEST tabs', 'clearTestData')
    .addToUi();
}

/* ======================= automatic pipeline updates ======================= */

/** Runs every 2 hours. Moves leads (and outbound prospects) forward on their own, from what already
 *  happened in Gmail, Calendly and the Licenses/Orders tabs, so the sheets never need hand updates:
 *  your outreach email sent → Contacted; they reply → Replied; Calendly booking → Booked;
 *  trial started → Trial; email with "proposal" in the subject sent to them → Proposal sent;
 *  paid order or Active license → Won; "STOP" or "unsubscribe" reply → Do not contact. */
function syncPipeline() {
  if (!isTest_() && hasTestData_()) withTest_(syncPipeline);
  const lic = sheet_('Licenses', LICENSE_HEADERS).getDataRange().getValues().slice(1);
  const ord = sheet_('Orders', ORDER_HEADERS).getDataRange().getValues().slice(1);
  const won = {}, trial = {};
  lic.forEach(r => { const e = String(r[3]).toLowerCase(); if (!e) return;
    if (['Active', 'Past due', 'Paused'].indexOf(r[4]) >= 0) won[e] = true; else if (r[4] === 'Trial') trial[e] = true; });
  ord.forEach(r => { if (r[2] === 'Paid') won[String(r[5]).toLowerCase()] = true; });
  syncSheet_(sheet_('Leads', LEAD_HEADERS), 3, 8, 1, 23, won, trial);
  syncSheet_(sheet_('Prospects', PROSPECT_HEADERS), 10, 4, 1, 13, won, trial, 11);
}

function syncSheet_(sh, statusCol, emailCol, sinceCol, notesCol, won, trial, activityCol) {
  const rows = sh.getDataRange().getValues(); let checked = 0;
  for (let r = 1; r < rows.length; r++) {
    const email = String(rows[r][emailCol - 1] || '').trim().toLowerCase();
    const status = String(rows[r][statusCol - 1] || 'New');
    if (!email || !(status in STATUS_RANK) && status !== '') continue;           // Lost, Do not contact, Spam: leave alone
    const since = rows[r][sinceCol - 1] ? new Date(rows[r][sinceCol - 1]) : addDays_(new Date(), -60);
    if (status === 'Won' || daysUntil_(since) < -120) continue;                      // done, or gone quiet for 4 months
    if (++checked > 120) break;                                                      // stays well inside Gmail's daily quota
    const next = detectStatus_(email, since, won, trial);
    if (!next) continue;
    if (next === 'Do not contact' || (STATUS_RANK[next] || 0) > (STATUS_RANK[status] || 0)) {
      sh.getRange(r + 1, statusCol).setValue(next);
      note_(sh, r + 1, 'auto: ' + next, notesCol);
      if (activityCol) sh.getRange(r + 1, activityCol).setValue(new Date());
    }
  }
}

function detectStatus_(email, since, won, trial) {
  if (won[email]) return 'Won';
  const after = ' after:' + Utilities.formatDate(new Date(since), Session.getScriptTimeZone(), 'yyyy/MM/dd');
  const q = (s) => GmailApp.search(s + after, 0, 1).length > 0;
  if (q('from:' + email + ' (STOP OR unsubscribe)')) return 'Do not contact';
  if (q('in:sent to:' + email + ' subject:proposal')) return 'Proposal sent';
  if (trial[email]) return 'Trial';
  if (q('from:calendly.com "' + email + '"')) return 'Booked';
  if (q('from:' + email + ' -from:me')) return 'Replied';
  if (q('in:sent to:' + email)) return 'Contacted';
  return '';
}

/* ======================= follow-ups & digest ======================= */

/** Runs daily (installed by setup). Sends the next follow-up unless the lead replied or you changed Status. */
function runFollowUps() {
  if (!isTest_() && hasTestData_()) withTest_(runFollowUps);
  const sh = sheet_('Leads', LEAD_HEADERS);
  const rows = sh.getDataRange().getValues();
  const now = new Date();
  for (let r = 1; r < rows.length; r++) {
    const row = rows[r];
    const [received, , status, , form, name, business, email] = row;
    const sent = Number(row[20]) || 0;
    if (!email || STOP_STATUSES.indexOf(status) >= 0 || sent >= CFG.FOLLOW_UP_DAYS.length) continue;
    if (hasReplied_(email, received)) { sh.getRange(r + 1, 3).setValue(hasStop_(email, received) ? 'Do not contact' : 'Replied'); continue; }
    const days = (now - new Date(received)) / 86400000;
    if (days < CFG.FOLLOW_UP_DAYS[sent]) continue;
    const msg = followUpText_(sent, name, business);
    send_(email, msg.subject, msg.body + '\nBest,' + signature_() + '\n\n(Reply STOP to opt out.)', { name: CFG.OWNER_NAME, replyTo: CFG.OWNER_EMAIL });
    sh.getRange(r + 1, 21).setValue(sent + 1);
    sh.getRange(r + 1, 22).setValue(now);
    if (status === 'New') sh.getRange(r + 1, 3).setValue('Contacted');
  }
}

function followUpText_(i, name, business) {
  const n = first_(name);
  const t = [
    { subject: 'Quick follow-up on your request',
      body: 'Hi ' + n + ',\n\nJust making sure my last note didn’t get buried. I’d still love to walk through the workflow you mentioned' + (business ? ' at ' + business : '') + '.\n\n' + bookingLine_() + '\n' },
    { subject: 'One idea for you',
      body: 'Hi ' + n + ',\n\nOne thing I see often: the biggest time savings usually come from fixing how requests get captured and handed off, before adding any new software. That’s exactly what the free audit maps out, and you keep the one-page summary either way.\n\n' + bookingLine_() + '\n' },
    { subject: 'Should I close your request?',
      body: 'Hi ' + n + ',\n\nI haven’t heard back, so I’ll assume the timing isn’t right and close out your request for now. If anything changes, just reply to this email and we’ll pick it right back up.\n' }
  ];
  return t[Math.min(i, t.length - 1)];
}

function hasReplied_(email, since) {
  const after = Utilities.formatDate(new Date(since), Session.getScriptTimeZone(), 'yyyy/MM/dd');
  return GmailApp.search('from:' + email + ' after:' + after, 0, 1).length > 0;
}
function hasStop_(email, since) {
  const after = Utilities.formatDate(new Date(since), Session.getScriptTimeZone(), 'yyyy/MM/dd');
  return GmailApp.search('from:' + email + ' after:' + after + ' (STOP OR unsubscribe)', 0, 1).length > 0;
}

/** Runs Monday mornings (installed by setup). */
function weeklyDigest() {
  const rows = sheet_('Leads', LEAD_HEADERS).getDataRange().getValues().slice(1);
  const weekAgo = Date.now() - 7 * 86400000;
  const fresh = rows.filter(r => new Date(r[0]).getTime() >= weekAgo);
  const open = rows.filter(r => ['New', 'Contacted', 'Replied', 'Booked', 'Proposal sent'].indexOf(r[2]) >= 0)
    .sort((a, b) => b[3] - a[3]).slice(0, 10);
  const bySource = {};
  fresh.forEach(r => { const s = r[18] || 'direct'; bySource[s] = (bySource[s] || 0) + 1; });
  const chats = sheet_('Chats', ['Time', 'Session', 'Role', 'Message', 'Page']).getLastRow() - 1;
  const body = 'Leads this week: ' + fresh.length + '\n' +
    'By source: ' + (Object.entries(bySource).map(([k, v]) => k + ' ' + v).join(', ') || 'none') + '\n' +
    'Chat messages logged (all time): ' + Math.max(0, chats) + '\n\nTop open leads:\n' +
    (open.map(r => '• [' + r[3] + '] ' + (r[6] || r[5]) + ' — ' + r[2] + ' — ' + (r[11] || '').slice(0, 80)).join('\n') || '• none yet') +
    '\n\nSheet: ' + SpreadsheetApp.getActiveSpreadsheet().getUrl();
  send_(CFG.OWNER_EMAIL, 'Weekly pipeline — ' + fresh.length + ' new lead(s)', body, { name: CFG.BUSINESS + ' Leads' });
}

/* ======================= AI chat ======================= */

function systemPrompt_() {
  return [
    'You are the website assistant for ' + CFG.BUSINESS + ', run by ' + CFG.OWNER_NAME + ', a ' + CFG.TITLE + '.',
    'You are an automated assistant. If asked, say so plainly; Rashad personally handles every project.',
    'About Rashad: 17 years working directly with customers and building the software that solves their problems; former Director of Quality Assurance who led 50+ engineers across 4 countries supporting 80+ client organizations; experience in healthcare technology, finance and payments, restaurant systems, retail and defense. Do not name his former employers.',
    'He works with clients worldwide, remotely or on-site. What he does: AI chat and booking assistants, workflow automation, smart intake and drafted replies (with staff approval), custom applications and tools, software selection and integration, dashboards, and testing/training/support. Primary focus: apartment communities, hotels, resorts and timeshares; also salons, barbers, massage and spa, smoke shops, restaurants, contractors, real estate, law firms, dental offices, HUD-assisted housing and other small businesses.',
    'Packages:\n- ' + CFG.PACKAGES.join('\n- '),
    'Products (working prototypes he adapts to each client):\n- ' + CFG.PRODUCTS.join('\n- '),
    'How it works: free audit with a one-page summary in 3 business days → order a tool or bundle (Starter edition in 1–3 business days) or a fixed-price proposal for custom work → Connected edition or pilot in 3–8 weeks including team testing → 30-day results review. Clients own their accounts and data, and decide what is automated and what needs approval.',
    'Founding client program: a small number of early clients get a founding rate on their first pilot in exchange for feedback and, if happy, a short case study.',
    'Mission: build AI solutions and tools that increase human productivity — helping businesses earn more and teams move faster, with humans in the loop approving what matters.',
    'Rules: Keep replies under 90 words, friendly and plain-English. Only quote prices written here and say every build gets a fixed written quote; never promise specific results. No legal, medical or financial advice. Do not ask for passwords, payment details, or private customer/patient information. If you do not know, say so and offer to connect them with Rashad.',
    'Goal: understand their business and biggest time-waster, recommend the most relevant product or package, and invite them to book the free audit' + (CFG.BOOKING_URL ? ' at ' + CFG.BOOKING_URL : '') + '.',
    'Ask for their name, business, email and what they want to improve, one or two items at a time, only after they show interest. When you have at least a name and a valid email they gave you, append exactly one line at the very end of your reply: <lead>{"name":"","business":"","email":"","phone":"","industry":"","need":""}</lead> with the values filled in. Only include it once per conversation, and never mention the tag.'
  ].join('\n\n');
}

function handleChat_(d) {
  if (!aiKey_()) return { ok: false, error: 'ai not configured' };
  const session = String(d.session || 'anon').slice(0, 64);
  const cache = CacheService.getScriptCache();
  const sKey = 'chat:' + session, gKey = 'chat:all:' + Utilities.formatDate(new Date(), 'UTC', 'yyyyMMdd');
  const sCount = Number(cache.get(sKey) || 0), gCount = Number(cache.get(gKey) || 0);
  if (sCount >= CFG.CHAT_DAILY_LIMIT || gCount >= CFG.CHAT_GLOBAL_DAILY_LIMIT) {
    return { ok: true, reply: 'I’ve hit my chat limit for today — the fastest way to reach Rashad is the free audit form on this page, and he’ll reply within one business day.' };
  }
  cache.put(sKey, String(sCount + 1), 21600); cache.put(gKey, String(gCount + 1), 21600);

  const msgs = (Array.isArray(d.messages) ? d.messages : [])
    .filter(m => m && (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string')
    .slice(-CFG.CHAT_MAX_TURNS)
    .map(m => ({ role: m.role, content: m.content.slice(0, 1500) }));
  while (msgs.length && msgs[0].role !== 'user') msgs.shift();
  if (!msgs.length) return { ok: false, error: 'empty' };

  let reply = claude_(msgs, systemPrompt_(), 400);
  let leadSaved = false;
  const m = reply.match(/<lead>([\s\S]*?)<\/lead>/);
  if (m) {
    reply = reply.replace(m[0], '').trim();
    try {
      const lead = JSON.parse(m[1]);
      if (lead.email && !cache.get('chatlead:' + session)) {
        handleLead_(Object.assign({ form: 'chatbot', source: d.source || '', page: d.page || '' }, lead));
        cache.put('chatlead:' + session, '1', 21600);
        leadSaved = true;
      }
    } catch (err) { console.warn('lead parse failed', err); }
  }
  const log = sheet_('Chats', ['Time', 'Session', 'Role', 'Message', 'Page']);
  const last = msgs[msgs.length - 1];
  log.appendRow([new Date(), session, 'user', last.content, d.page || '']);
  log.appendRow([new Date(), session, 'assistant', reply, d.page || '']);
  return { ok: true, reply: reply, leadSaved: leadSaved };
}

function aiKey_() { return PropertiesService.getScriptProperties().getProperty('ANTHROPIC_API_KEY'); }

function claude_(messages, system, maxTokens) {
  const res = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: { 'x-api-key': aiKey_(), 'anthropic-version': '2023-06-01' },
    payload: JSON.stringify({ model: CFG.AI_MODEL, max_tokens: maxTokens || 400, system: system, messages: messages })
  });
  const data = JSON.parse(res.getContentText() || '{}');
  if (res.getResponseCode() !== 200) throw new Error('Claude API ' + res.getResponseCode() + ': ' + res.getContentText().slice(0, 300));
  return (data.content || []).filter(c => c.type === 'text').map(c => c.text).join('\n').trim();
}

/* ======================= setup & utilities ======================= */

/** Run once from the editor. Creates the sheets and the daily/weekly schedules. */
function setup() {
  sheet_('Leads', LEAD_HEADERS);
  sheet_('Chats', ['Time', 'Session', 'Role', 'Message', 'Page']);
  const lic = sheet_('Licenses', LICENSE_HEADERS);
  lic.getRange('E2:E').setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(LICENSE_STATUSES, true).build());
  const sh = sheet_('Leads', LEAD_HEADERS);
  sh.setFrozenRows(1);
  const statusRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['New', 'Contacted'].concat(STOP_STATUSES), true).build();
  sh.getRange('C2:C').setDataValidation(statusRule);
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('runFollowUps').timeBased().everyDays(1).atHour(9).create();
  ScriptApp.newTrigger('runLicenses').timeBased().everyDays(1).atHour(8).create();
  ScriptApp.newTrigger('weeklyDigest').timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(7).create();
  ScriptApp.newTrigger('matchPayments').timeBased().everyHours(2).create();
  ScriptApp.newTrigger('syncPipeline').timeBased().everyHours(2).create();
  ScriptApp.newTrigger('backupSheet').timeBased().everyDays(1).atHour(2).create();
  const pros = sheet_('Prospects', PROSPECT_HEADERS); pros.setFrozenRows(1);
  ScriptApp.newTrigger('onLicenseEdit').forSpreadsheet(SpreadsheetApp.getActive()).onEdit().create();
  const ord = sheet_('Orders', ORDER_HEADERS); ord.setFrozenRows(1);
  ord.getRange('C2:C').setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(['Awaiting payment','Paid','Canceled'], true).build());
  lic.setFrozenRows(1);
  console.log('Setup complete. Now Deploy → New deployment → Web app (Execute as: Me, Access: Anyone).');
}

/** Sends a fake lead through the whole pipeline to your own inbox. */
function testLead() {
  handleLead_({ form: 'audit', Name: 'Test Prospect', Business: 'Sunrise Apartments', Email: CFG.OWNER_EMAIL,
    Industry: 'Apartment community / property management', 'Team size': '6–15',
    Workflow: 'Residents text maintenance requests to three different people and some get lost over the weekend.',
    source: 'test', page: 'setup' });
}

function sheet_(name, headers) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  if (isTest_() && name.indexOf(TEST_PREFIX) !== 0) name = TEST_PREFIX + name;
  let sh = ss.getSheetByName(name);
  if (!sh) { sh = ss.insertSheet(name); sh.appendRow(headers); sh.getRange(1, 1, 1, headers.length).setFontWeight('bold'); }
  return sh;
}
function findRowByEmail_(sh, email) {
  const last = sh.getLastRow(); if (last < 2) return 0;
  const vals = sh.getRange(2, 8, last - 1, 1).getValues();
  for (let i = 0; i < vals.length; i++) if (String(vals[i][0]).toLowerCase() === email.toLowerCase()) return i + 2;
  return 0;
}
function stamp_() { return Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd'); }
