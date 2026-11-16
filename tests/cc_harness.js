// Runs command-center/Code.gs against an in-memory Sheet, Gmail, Calendar and lead engine, as the owner
// and as a stranger, and prints what happened as JSON for tests/test_command_center.py.
const fs = require('fs'), vm = require('vm');
const src = fs.readFileSync(process.argv[2], 'utf8');
const out = { fetches: [], mails: [], errors: {} };
class Sheet {
  constructor(n) { this.name = n; this.rows = []; }
  appendRow(a) { this.rows.push(a.slice()); } setFrozenRows() {} getLastRow() { return this.rows.length; }
  getRange(r, c, nr, nc) { const sh = this; return { setFontWeight() { return this; }, getValue: () => (sh.rows[r - 1] || [])[c - 1] ?? '', setValue: (v) => { sh.rows[r - 1][c - 1] = v; } }; }
  getDataRange() { const sh = this; return { getValues: () => sh.rows.map(r => r.slice()) }; }
}
const sheets = {};
const book = { getSheetByName: (n) => sheets[n] || null, insertSheet: (n) => (sheets[n] = new Sheet(n)) };
let USER = 'rashadfambro@gmail.com';
const props = { LEADS_SHEET_ID: 'SHEET1', LEAD_ENGINE_URL: 'https://script.google.com/macros/s/TEST/exec', ADMIN_TOKEN: 'x'.repeat(32) };
const userProps = {};
const triggers = [];
const ctx = {
  console, JSON, Math, Number, String, Object, Array, RegExp, Error, Date,
  Session: { getActiveUser: () => ({ getEmail: () => USER }) },
  PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => props[k] || null }), getUserProperties: () => ({ getProperty: (k) => userProps[k] || null, setProperty: (k, v) => { userProps[k] = v; } }) },
  SpreadsheetApp: { openById: (id) => { if (id !== 'SHEET1') throw new Error('bad id'); return book; } },
  HtmlService: { createHtmlOutput: (h) => ({ html: h, setXFrameOptionsMode() { return this; } }), createTemplateFromFile: () => ({ evaluate: () => ({ html: 'INDEX', setTitle() { return this; }, addMetaTag() { return this; }, setXFrameOptionsMode() { return this; } }) }), XFrameOptionsMode: { DENY: 'DENY' } },
  UrlFetchApp: { fetch: (url, opts) => { out.fetches.push({ url, payload: JSON.parse(opts.payload) }); return { getContentText: () => '{"ok":true,"key":"RFL-20261220-AAAAAA"}', getResponseCode: () => 200 }; } },
  CalendarApp: { getDefaultCalendar: () => ({ getEvents: () => [{ getTitle: () => 'Free audit: Glow Studio', getStartTime: () => new Date('2026-11-20T18:00:00Z'), getEndTime: () => new Date('2026-11-20T18:30:00Z'), getLocation: () => 'Meet' }] }) },
  GmailApp: { search: () => [], sendEmail: (to, subject, body) => out.mails.push({ to, subject, body }) },
  Utilities: { formatDate: (d) => new Date(d).toISOString().slice(0, 16).replace('T', ' ') },
  ScriptApp: { getProjectTriggers: () => [], deleteTrigger() {}, newTrigger: (fn) => { const t = { timeBased() { return t; }, everyDays() { return t; }, atHour() { return t; }, inTimezone() { return t; }, create() { triggers.push(fn); } }; return t; }, getService: () => ({ getUrl: () => 'https://script.google.com/macros/s/CC/exec' }) },
};
vm.createContext(ctx);
vm.runInContext(src + '\n;globalThis.__api = { doGet, getDashboard, licenseAction, setLeadStatus, addRequest, addFinance, setTheme, dailyBrief, setupCommandCenter };', ctx);
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

// Stranger
USER = 'someone@example.com';
out.strangerPage = A.doGet().html;
for (const [n, f] of Object.entries({ getDashboard: () => A.getDashboard(), licenseAction: () => A.licenseAction('pause', 'RFL-20261220-AAAAAA'), setLeadStatus: () => A.setLeadStatus(2, 'Won'), addRequest: () => A.addRequest('qa-engineer', 'Normal', '', 'x'), addFinance: () => A.addFinance({ amount: 5 }), setTheme: () => A.setTheme('dark') }))
  tryIt('stranger:' + n, f);
out.fetchesAfterStranger = out.fetches.length;
console.log(JSON.stringify(out));
