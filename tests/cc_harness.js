// Runs command-center/Code.gs against an in-memory Sheet, Gmail, Calendar and lead engine, as the owner
// and as a stranger, and prints what happened as JSON for tests/test_command_center.py.
const fs = require('fs'), vm = require('vm');
const src = fs.readFileSync(process.argv[2], 'utf8');
const out = { fetches: [], mails: [], errors: {} };
class Sheet {
  constructor(n) { this.name = n; this.rows = []; }
  appendRow(a) { this.rows.push(a.slice()); } setFrozenRows() {} getLastRow() { return this.rows.length; } getLastColumn() { return Math.max(0, ...this.rows.map(r => r.length)); }
  getRange(r, c, nr, nc) { const sh = this; return { setFontWeight() { return this; }, getValue: () => (sh.rows[r - 1] || [])[c - 1] ?? '', setValue: (v) => { sh.rows[r - 1][c - 1] = v; },
    getValues: () => Array.from({ length: nr || 1 }, (_, i) => Array.from({ length: nc || 1 }, (_, j) => (sh.rows[r - 1 + i] || [])[c - 1 + j] ?? '')) }; }
  getDataRange() { const sh = this; return { getValues: () => sh.rows.map(r => r.slice()) }; }
}
const sheets = {};
const book = { getSheetByName: (n) => sheets[n] || null, insertSheet: (n) => (sheets[n] = new Sheet(n)) };
let USER = 'rashadfambro@gmail.com';
const props = { LEADS_SHEET_ID: 'SHEET1', LEAD_ENGINE_URL: 'https://script.google.com/macros/s/TEST/exec', ADMIN_TOKEN: 'x'.repeat(32) };
const userProps = {};
const triggers = [];
const INBOX = [['Family <family@example.com>', 'Dinner Sunday?'], ['Bank <alerts@example.com>', 'Your statement is ready'], ['Calendly <no-reply@example.com>', 'New Event: Glow Studio'],
  ['Ana Ruiz <ana@example.com>', 'Re: Quick idea'], ['Lead Engine <rashadfambro@gmail.com>', '[Lead] Glow Studio (score 72)'], ['Shop <deals@example.com>', 'Your order has shipped'], ['Square <noreply@messaging.squareup.com>', 'You received $250.00'], ['Square <noreply@messaging.squareup.com>', 'Your point of sale is waiting'], ['PayPal <service@paypal.com>', 'Your October account statement is available']];
function xfo(m) { if (m == null) throw new Error('Argument cannot be null: mode'); return this; }   // same check as Google
const ctx = {
  console, JSON, Math, Number, String, Object, Array, RegExp, Error, Date,
  Session: { getActiveUser: () => ({ getEmail: () => USER }) },
  PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => props[k] || null }), getUserProperties: () => ({ getProperty: (k) => userProps[k] || null, setProperty: (k, v) => { userProps[k] = v; } }) },
  SpreadsheetApp: { openById: (id) => { if (id !== 'SHEET1') throw new Error('bad id'); return book; } },
  HtmlService: { createHtmlOutput: (h) => ({ html: h, setXFrameOptionsMode: xfo }), createTemplateFromFile: () => ({ evaluate: () => ({ html: 'INDEX', setTitle() { return this; }, addMetaTag() { return this; }, setXFrameOptionsMode: xfo }) }), XFrameOptionsMode: { ALLOWALL: 'ALLOWALL', DEFAULT: 'DEFAULT' } },   // the only two modes Google provides
  UrlFetchApp: { fetch: (url, opts) => { out.fetches.push({ url, payload: JSON.parse(opts.payload) }); return { getContentText: () => '{"ok":true,"key":"RFL-20261220-AAAAAA"}', getResponseCode: () => 200 }; } },
  CalendarApp: { getDefaultCalendar: () => ({ getEvents: () => [{ getTitle: () => 'Free audit: Glow Studio', getStartTime: () => new Date('2026-11-20T18:00:00Z'), getEndTime: () => new Date('2026-11-20T18:30:00Z'), getLocation: () => 'Meet' }] }) },
  GmailApp: { search: () => INBOX.map(([from, subject], i) => ({ getId: () => 'T' + i, getMessageCount: () => 1, getMessages: () => [{ getFrom: () => from, getSubject: () => subject, getDate: () => new Date('2026-11-16T15:00:00Z') }] })),
    getMessagesForThreads: (ts) => { out.batchCalls = (out.batchCalls || 0) + 1; return ts.map(t => t.getMessages()); }, sendEmail: (to, subject, body) => out.mails.push({ to, subject, body, kind: 'sent' }), createDraft: (to, subject, body) => out.mails.push({ to, subject, body, kind: 'draft' }) },
  Utilities: { formatDate: (d) => new Date(d).toISOString().slice(0, 16).replace('T', ' ') },
  ScriptApp: { getProjectTriggers: () => [], deleteTrigger() {}, newTrigger: (fn) => { const t = { timeBased() { return t; }, everyDays() { return t; }, atHour() { return t; }, inTimezone() { return t; }, create() { triggers.push(fn); } }; return t; }, getService: () => ({ getUrl: () => 'https://script.google.com/macros/s/CC/exec' }) },
};
vm.createContext(ctx);
vm.runInContext(src + '\n;globalThis.__api = { doGet, getDashboard, getExtras, licenseAction, setLeadStatus, addRequest, addFinance, setTheme, dailyBrief, setupCommandCenter, saveContact, addNote, addProspect, emailContact, startTrial };', ctx);
const A = ctx.__api;
const tryIt = (name, f) => { try { return f(); } catch (e) { out.errors[name] = e.message; return null; } };

// Owner
A.setupCommandCenter();
out.triggers = triggers;
sheets.Leads = new Sheet('Leads'); sheets.Leads.appendRow(['Received', 'Lead ID', 'Status', 'Score', 'Form', 'Name', 'Business', 'Email']);
sheets.Leads.appendRow([new Date().toISOString(), 'L1', 'New', 72, 'audit', 'Ana', 'Glow Studio', 'ana@example.com']);
out.page = A.doGet().html;
out.dash = A.getDashboard();
out.status = A.setLeadStatus(2, 'Booked'); out.leadAfter = sheets.Leads.rows[1][2];
tryIt('badStatus', () => A.setLeadStatus(2, 'Hacked'));
tryIt('badRow', () => A.setLeadStatus(999, 'Won'));
out.req = A.addRequest('release-manager', 'High', 'BookDesk', 'Ship BookDesk 1.2 to staging');
tryIt('emptyReq', () => A.addRequest('qa-engineer', 'Normal', '', '   '));
A.addRequest('not-an-agent', 'Urgent!!', 'x', 'Routed to chief of staff'); out.requests = sheets.Requests.rows.slice(1).map(r => [r[2], r[3], r[6]]);
A.addFinance({ type: 'Expense', amount: '29', category: 'Software', description: 'Domain' });
tryIt('badAmount', () => A.addFinance({ type: 'Income', amount: '-' }));
out.finance = sheets.Finance.rows.slice(1).map(r => [r[1], r[4]]);
out.license = A.licenseAction('pause', 'RFL-20261220-AAAAAA');
tryIt('badKey', () => A.licenseAction('pause', "RFL-1'; DROP"));
tryIt('badAction', () => A.licenseAction('delete_everything', 'RFL-20261220-AAAAAA'));
out.theme = A.setTheme('contrast'); out.themeAfter = A.getDashboard().theme;
tryIt('badTheme', () => A.setTheme('neon'));
A.dailyBrief();
out.log = sheets.Log.rows.slice(1).map(r => r[2]);

// Prospects: add, edit, note, email (send and draft), trial, safety checks, and the test-data switch
const PH = ['Added', 'Business', 'Contact', 'Email', 'Phone', 'City', 'Industry', 'Tools to pitch', 'Source', 'Status', 'Last activity', 'Next step', 'Notes'];
out.inbox = A.getExtras().inbox.map(m => m.subject); out.dashHasNoInbox = !('inbox' in A.getDashboard());
out.addP = A.addProspect({ Business: 'Sunrise Apartments', Contact: 'Lee Park', Email: 'lee@example.com', Phone: '702-555-0100', City: 'Henderson', 'Tools to pitch': 'WorkOrderDesk', Notes: 'Met at the leasing office' });
tryIt('addNoBiz', () => A.addProspect({ Email: 'x@example.com' }));
tryIt('addBadEmail', () => A.addProspect({ Business: 'X', Email: 'not-an-email' }));
const pr = sheets.Prospects; const P = (k) => pr.rows[1][PH.indexOf(k)];
out.saved = A.saveContact('prospect', { row: 2, email: 'lee@example.com' }, { Contact: 'Lee Park-Jones', Status: 'Booked', 'Next step': 'Demo Thursday', Source: 'hacked', Notes: 'overwrite' });
out.afterSave = { contact: P('Contact'), status: P('Status'), next: P('Next step'), source: P('Source'), notesHasEdit: /edited:/.test(P('Notes')) && /Met at the leasing office/.test(P('Notes')) };
tryIt('badStage', () => A.saveContact('prospect', { row: 2, email: 'lee@example.com' }, { Status: 'Owned' }));
tryIt('wrongPerson', () => A.saveContact('prospect', { row: 2, email: 'someone-else@example.com' }, { Status: 'Won' }));
A.addNote('prospect', { row: 2, email: 'lee@example.com' }, 'Owner wants pricing for 3 properties');
out.noteSaved = /Owner wants pricing/.test(P('Notes'));
pr.rows[1][PH.indexOf('Status')] = 'Not contacted';
A.emailContact('prospect', { row: 2, email: 'lee@example.com' }, 'Quick idea for Sunrise — café', 'Hi Lee \u{1F600}\n\nThanks.', 'send');
out.afterEmail = { status: P('Status'), mail: out.mails[out.mails.length - 1] };
A.emailContact('prospect', { row: 2, email: 'lee@example.com' }, 'Draft only', 'Body', 'draft');
out.draft = out.mails[out.mails.length - 1];
pr.rows[1][PH.indexOf('Status')] = 'Do not contact';
tryIt('dnc', () => A.emailContact('prospect', { row: 2, email: 'lee@example.com' }, 'Hi', 'x', 'send'));
pr.rows[1][PH.indexOf('Status')] = 'Contacted';
out.trial = A.startTrial('prospect', { row: 2, email: 'lee@example.com' }, 'WorkOrderDesk');
out.trialFetch = out.fetches[out.fetches.length - 1].payload; out.afterTrial = P('Status');
A.saveContact('lead', { row: 2, email: 'ana@example.com' }, { Status: 'Won' }); out.leadWon = sheets.Leads.rows[1][2];
// test data: TEST tabs only, email goes to the owner
sheets['TEST Prospects'] = new Sheet('TEST Prospects'); sheets['TEST Prospects'].appendRow(PH);
A.addProspect({ Business: 'Staging Spa', Email: 'customer@example.com' }, 'test');
A.emailContact('prospect', { row: 2, email: 'customer@example.com' }, 'Hello', 'Test body', 'send', 'test');
out.testMail = out.mails[out.mails.length - 1];
A.startTrial('prospect', { row: 2, email: 'customer@example.com' }, 'BookDesk', 'test'); out.testTrialEnv = out.fetches[out.fetches.length - 1].payload.env;
out.testDash = A.getDashboard('test'); out.testDash = { env: out.testDash.env, prospects: out.testDash.prospects.map(p => p.Business) };
out.liveProspects = sheets.Prospects.rows.slice(1).map(r => r[1]);

// Stranger
USER = 'someone@example.com';
out.strangerPage = A.doGet().html;
for (const [n, f] of Object.entries({ getExtras: () => A.getExtras(), saveContact: () => A.saveContact('prospect', { row: 2, email: 'lee@example.com' }, { Status: 'Won' }), addNote: () => A.addNote('prospect', { row: 2 }, 'x'), addProspect: () => A.addProspect({ Business: 'X' }), emailContact: () => A.emailContact('prospect', { row: 2 }, 'a', 'b', 'send'), startTrial: () => A.startTrial('prospect', { row: 2 }, 'x'), getDashboard: () => A.getDashboard(), licenseAction: () => A.licenseAction('pause', 'RFL-20261220-AAAAAA'), setLeadStatus: () => A.setLeadStatus(2, 'Won'), addRequest: () => A.addRequest('qa-engineer', 'Normal', '', 'x'), addFinance: () => A.addFinance({ amount: 5 }), setTheme: () => A.setTheme('dark') }))
  tryIt('stranger:' + n, f);
out.fetchesAfterStranger = out.fetches.length;
console.log(JSON.stringify(out));
