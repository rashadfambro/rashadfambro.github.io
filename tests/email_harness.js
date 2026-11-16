// Runs the real lead-engine code (lead-engine/Code.gs) against an in-memory Google Sheet, Gmail and
// clock, triggers every kind of email it can send, and prints them as JSON for tests/test_lead_engine.py.
const fs = require('fs'), vm = require('vm');
const src = fs.readFileSync(process.argv[2], 'utf8');
const sent = [];
let NOW = new Date('2026-11-20T17:00:00Z');

class Range {
  constructor(sh, r, c, nr, nc) { Object.assign(this, { sh, r, c, nr: nr || 1, nc: nc || 1 }); }
  getValue() { return (this.sh.rows[this.r - 1] || [])[this.c - 1] ?? ''; }
  setValue(v) { while (this.sh.rows.length < this.r) this.sh.rows.push([]); this.sh.rows[this.r - 1][this.c - 1] = v; return this; }
  getValues() { const out = []; for (let i = 0; i < this.nr; i++) { const row = this.sh.rows[this.r - 1 + i] || []; out.push(Array.from({ length: this.nc }, (_, j) => row[this.c - 1 + j] ?? '')); } return out; }
  setFontWeight() { return this; } setDataValidation() { return this; } getSheet() { return this.sh; }
  getRow() { return this.r; } getColumn() { return this.c; }
}
class Sheet {
  constructor(name) { this.name = name; this.rows = []; }
  getName() { return this.name; }
  appendRow(a) { this.rows.push(a.slice()); return this; }
  getLastRow() { return this.rows.length; }
  getRange(r, c, nr, nc) { if (typeof r === 'string') return new Range(this, 1, 1); return new Range(this, r, c, nr, nc); }
  getDataRange() { const w = Math.max(1, ...this.rows.map(r => r.length)); return new Range(this, 1, 1, this.rows.length, w); }
  setFrozenRows() { return this; } getActiveRange() { return new Range(this, 2, 1); }
}
const book = { sheets: {}, getSheetByName(n) { return this.sheets[n] || null; }, insertSheet(n) { return (this.sheets[n] = new Sheet(n)); }, getUrl() { return 'https://docs.google.com/spreadsheets/d/TEST/edit'; } };
const cache = {};
const RealDate = Date;
class FakeDate extends RealDate { constructor(...a) { if (a.length === 0) super(NOW.getTime()); else super(...a); } static now() { return NOW.getTime(); } }
const ctx = {
  console, JSON, Math, Number, String, Object, Array, RegExp, Error, encodeURIComponent, isNaN, parseInt, parseFloat,
  Date: FakeDate,
  SpreadsheetApp: { getActiveSpreadsheet: () => book, getActive: () => book, getActiveSheet: () => book.sheets.Licenses, getUi: () => ({ alert() {}, createMenu() { const m = { addItem() { return m; }, addToUi() {} }; return m; } }),
    newDataValidation: () => { const b = { requireValueInList() { return b; }, build() { return {}; } }; return b; }, flush() {} },
  GmailApp: {
    sendEmail(to, subject, body, opts) { sent.push({ kind: 'email', to, subject, body, name: (opts || {}).name || '' }); },
    createDraft(to, subject, body) { sent.push({ kind: 'draft', to, subject, body, name: '' }); return {}; },
    search() { return []; }, getUserLabelByName() { return { }; }, createLabel() { return {}; }
  },
  Utilities: { formatDate(d, tz, f) { d = new RealDate(d); const p = (n) => String(n).padStart(2, '0');
      const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
      return f.replace('yyyy', d.getUTCFullYear()).replace('yy', String(d.getUTCFullYear()).slice(2)).replace('MMMM', months[d.getUTCMonth()]).replace('MM', p(d.getUTCMonth() + 1))
        .replace(/\bd\b/, d.getUTCDate()).replace('dd', p(d.getUTCDate())).replace('HH', p(d.getUTCHours())).replace('mm', p(d.getUTCMinutes())).replace('ss', p(d.getUTCSeconds())); } },
  Session: { getScriptTimeZone: () => 'UTC', getActiveUser: () => ({ getEmail: () => '' }) },
  CacheService: { getScriptCache: () => ({ get: (k) => (k in cache ? cache[k] : null), put: (k, v) => { cache[k] = v; }, remove: (k) => { delete cache[k]; } }) },
  PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => (k === 'ADMIN_TOKEN' ? 'T'.repeat(32) : null) }) },
  LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
  ScriptApp: { getProjectTriggers: () => [], newTrigger: () => { const t = { timeBased() { return t; }, atHour() { return t; }, everyDays() { return t; }, everyHours() { return t; }, onWeekDay() { return t; }, forSpreadsheet() { return t; }, onEdit() { return t; }, create() {} }; return t; }, WeekDay: {} },
  ContentService: { createTextOutput: (s) => ({ setMimeType: () => s }), MimeType: {} },
  UrlFetchApp: { fetch: () => ({ getContentText: () => '{}', getResponseCode: () => 200 }) },
};
vm.createContext(ctx);
vm.runInContext(src + '\n;globalThis.__api = { handleLead_, issueTrial_, activateRow_, onLicenseEdit, runLicenses, runFollowUps, weeklyDigest, adminAction_, sheet_, CFG, LICENSE_HEADERS, LEAD_HEADERS };', ctx);
const A = ctx.__api;
A.CFG.BOOKING_URL = 'https://calendly.com/example/free-workflow-audit';
A.CFG.CREATE_REPLY_DRAFT = true;
const tag = (label) => { sent.forEach(m => { if (!m.label) m.label = label; }); };

// 1. Website leads: audit, project, order, trial (owner alert, prospect reply, draft)
A.handleLead_({ form: 'audit', Name: 'Maria O’Connor', Business: 'Café Olé Salon', Email: 'maria@example.com', Industry: 'Salon', 'Team size': '6–15', Need: 'Clients text “are you open?” all day — we miss bookings…', Source: 'walk-in' }); tag('lead: audit');
A.handleLead_({ form: 'project', Name: 'Sam Lee', Business: 'Lee HVAC', Email: 'sam@example.com', Need: 'After-hours calls', Timeline: 'ASAP' }); tag('lead: project');
A.handleLead_({ form: 'order', Name: 'Ana Ruiz', Business: 'Glow Studio', Email: 'ana@example.com', Package: 'Launch Bundle: ChatDesk + BookDesk setup', Workflow: 'Order via Square', 'Amount due': '2250', Plan: 'Pay in full', Method: 'Square' }); tag('lead: order');
A.handleLead_({ form: 'trial', Name: 'Tom Park', Business: 'Park Auto', Email: 'tom@example.com', Package: 'LeadDesk (Essentials plan)' }); tag('lead: trial');

// 2. License lifecycle on the Licenses tab
const lic = A.sheet_('Licenses', A.LICENSE_HEADERS);
const day = 86400000;
const addLic = (key, status, endsInDays, plan) => lic.appendRow([key, 'chat,salon', 'Glow Studio', 'ana@example.com', status, plan || 'Essentials', new Date(NOW - 10 * day), new Date(NOW.getTime() + endsInDays * day), '', '', 'https://example.com/app', '#2f7fe0', 'Ana Ruiz', 2250]);
addLic('RF-20261108-AAAAAA', 'Trial', 3); addLic('RF-20261108-BBBBBB', 'Trial', 1); addLic('RF-20261101-CCCCCC', 'Trial', -1);
addLic('RFL-20261125-DDDDDD', 'Active', 5); addLic('RFL-20261119-EEEEEE', 'Active', -1); addLic('RFL-20261020-FFFFFF', 'Past due', -31);
A.runLicenses(); tag('licenses: daily run');
A.activateRow_(lic, 2); tag('license: activated');
A.activateRow_(lic, 3, { renewal: true }); tag('license: renewed');
A.onLicenseEdit({ range: lic.getRange(4, 5), value: 'Canceled' }); tag('license: canceled');
A.adminAction_({ token: 'T'.repeat(32), action: 'resend', key: lic.getRange(2, 1).getValue() }); tag('license: resend');

// 3. Follow-ups (day 2, 5, 10) and the weekly digest
const leads = A.sheet_('Leads', A.LEAD_HEADERS);
for (let r = 2; r <= leads.getLastRow(); r++) leads.getRange(r, 1).setValue(new Date(NOW - 20 * day));
for (let i = 0; i < 3; i++) { A.runFollowUps(); }
tag('follow-ups');
A.weeklyDigest(); tag('weekly digest');

console.log(JSON.stringify(sent));
