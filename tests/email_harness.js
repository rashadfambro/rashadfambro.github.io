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
const drive = { folders: [], files: [] };
const book = { getId: () => 'SHEET1', getName: () => 'Leads - Rashad Fambro Consulting', sheets: {}, getSheetByName(n) { return this.sheets[n] || null; }, insertSheet(n) { return (this.sheets[n] = new Sheet(n)); }, getUrl() { return 'https://docs.google.com/spreadsheets/d/TEST/edit'; }, getSheets() { return Object.values(this.sheets); }, deleteSheet(sh) { delete this.sheets[sh.name]; } };
const cache = {};
const RealDate = Date;
class FakeDate extends RealDate { constructor(...a) { if (a.length === 0) super(NOW.getTime()); else super(...a); } static now() { return NOW.getTime(); } }
const ctx = {
  console, JSON, Math, Number, String, Object, Array, RegExp, Error, encodeURIComponent, isNaN, parseInt, parseFloat,
  Date: FakeDate,
  SpreadsheetApp: { getActiveSpreadsheet: () => book, getActive: () => book, getActiveSheet: () => book.sheets.Licenses, getUi: () => ({ alert() {}, createMenu() { const m = { addItem() { return m; }, addSeparator() { return m; }, addToUi() {} }; return m; } }),
    newDataValidation: () => { const b = { requireValueInList() { return b; }, build() { return {}; } }; return b; }, flush() {} },
  GmailApp: {
    sendEmail(to, subject, body, opts) { sent.push({ kind: 'email', to, subject, body, name: (opts || {}).name || '' }); },
    createDraft(to, subject, body) { sent.push({ kind: 'draft', to, subject, body, name: '' }); return {}; },
    search(q) { return (ctx.__gmail || []).filter(t => t.match(q)).map(t => t.thread); }, getUserLabelByName() { return {}; }, createLabel() { return {}; }
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
  DriveApp: {
    getFoldersByName: (n) => { const f = drive.folders.filter(x => x.name === n); let i = 0; return { hasNext: () => i < f.length, next: () => f[i++] }; },
    createFolder: (n) => { const f = { name: n, files: [], getFiles() { const a = this.files.filter(x => !x.trashed); let i = 0; return { hasNext: () => i < a.length, next: () => a[i++] }; } }; drive.folders.push(f); return f; },
    getFileById: () => ({ makeCopy: (name, folder) => { const f = { name, created: new RealDate(NOW.getTime() + folder.files.length * 1000), trashed: false, getDateCreated() { return this.created; }, setTrashed(v) { this.trashed = v; } }; folder.files.push(f); return f; } })
  },
  UrlFetchApp: { fetch: () => ({ getContentText: () => '{}', getResponseCode: () => 200 }) },
};
vm.createContext(ctx);
vm.runInContext(src + '\n;globalThis.__api = { doPost, doGet, clearTestData, runTestCycle, handleLead_, issueTrial_, activateRow_, onLicenseEdit, runLicenses, runFollowUps, weeklyDigest, adminAction_, sheet_, matchPayments, syncPipeline, backupSheet, checkLicense_, CFG, LICENSE_HEADERS, LEAD_HEADERS, ORDER_HEADERS, PROSPECT_HEADERS };', ctx);
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


// 4. Payment matching: one Square email that matches the open order, one PayPal email that matches nothing
const mkThread = (from, subject, body) => ({ thread: { getMessages: () => [{ getPlainBody: () => body, getSubject: () => subject, getFrom: () => from }], addLabel() {} } });
const ordersSh = A.sheet_('Orders', A.ORDER_HEADERS);
const orderRow = ordersSh.rows.findIndex(r => r[5] === 'ana@example.com') + 1;
ctx.__gmail = [
  { match: q => /squareup|paypal/.test(q), ...mkThread('Square <noreply@messaging.squareup.com>', 'You received $2,250.00 from Ana Ruiz', 'Payment received\n$2,250.00\nCustomer: Ana Ruiz\nana@example.com\nLaunch Bundle') },
  { match: q => /squareup|paypal/.test(q), ...mkThread('service@paypal.com', "You've got money", 'Bob Stone sent you $999.00 USD') },
];
A.matchPayments(); tag('payments');
const result = { orderStatus: ordersSh.getRange(orderRow, 3).getValue(), orderKey: ordersSh.getRange(orderRow, 12).getValue() };
const anaLic = lic.rows.filter(r => r[3] === 'ana@example.com' && r[1] === 'chat,salon' && r[4] === 'Active' && String(r[0]).startsWith('RFL-'));
result.licenseActive = anaLic.length > 0;
result.checkActive = A.checkLicense_({ key: result.orderKey });

// 5. Status sync: replies, bookings, proposals, STOP, sent outreach; Lost is never changed
const pros = A.sheet_('Prospects', A.PROSPECT_HEADERS);
const P = (biz, email, status) => pros.appendRow(['2026-11-15', biz, '', email, '', 'Las Vegas', 'x', 'x', 'test', status, '', '', '']);
P('Replied Co', 'reply@example.com', 'Not contacted'); P('Booked Co', 'book@example.com', 'Draft ready'); P('Proposal Co', 'prop@example.com', 'Booked');
P('Stop Co', 'stop@example.com', 'Contacted'); P('Sent Co', 'sent@example.com', 'Not contacted'); P('Lost Co', 'lost@example.com', 'Lost'); P('Quiet Co', 'quiet@example.com', 'Not contacted');
ctx.__gmail = [
  { match: q => q.startsWith('from:reply@example.com -from:me'), thread: {} },
  { match: q => q.startsWith('from:calendly.com "book@example.com"'), thread: {} },
  { match: q => q.startsWith('in:sent to:prop@example.com subject:proposal'), thread: {} },
  { match: q => q.startsWith('from:stop@example.com (STOP'), thread: {} },
  { match: q => q.startsWith('in:sent to:sent@example.com after'), thread: {} },
  { match: q => q.indexOf('lost@example.com') >= 0, thread: {} },
];
A.syncPipeline();
result.statuses = Object.fromEntries(pros.rows.slice(1).map(r => [r[1], r[9]]));

// 6. Admin endpoint refuses a bad token and logs it
result.adminBad = A.adminAction_({ token: 'wrong', action: 'pause', key: result.orderKey });
const logSh = A.sheet_('Log', ['Time', 'Source', 'Action', 'Target', 'Result']);
result.adminLogged = logSh.rows.some(r => r[1] === 'admin' && /refused/.test(r[4]));

// 7. Nightly backup keeps the newest 30 copies
for (let i = 0; i < 32; i++) A.backupSheet();
const bf = drive.folders.find(f => f.name === 'RF Lead Engine Backups');
result.backups = { kept: bf.files.filter(f => !f.trashed).length, trashed: bf.files.filter(f => f.trashed).length };

// 8. Test environment: staging traffic goes to TEST tabs and every email goes to the owner
const before = { leads: leads.rows.length, licenses: lic.rows.length, orders: ordersSh.rows.length, mails: sent.length };
const post = (b) => JSON.parse(A.doPost({ postData: { contents: JSON.stringify(b) } }));
result.testPost = post({ type: 'lead', env: 'staging', form: 'trial', Name: 'Real Person', Business: 'Staging Spa', Email: 'customer@example.com', Package: 'BookDesk (Essentials plan)' });
post({ type: 'lead', env: 'staging', form: 'order', Name: 'Real Person', Business: 'Staging Spa', Email: 'customer@example.com', Package: 'BookDesk setup', 'Amount due': '1350', Plan: 'Pay in full', Method: 'Square' });
const testLic = book.sheets['TEST Licenses'];
testLic.rows[1][7] = new Date(NOW.getTime() + 1 * day);
A.runLicenses();   // production run also checks TEST tabs, in test mode
const testMails = sent.slice(before.mails);
result.test = {
  tabs: Object.keys(book.sheets).filter(n => n.startsWith('TEST ')).sort(),
  prodUnchanged: leads.rows.length === before.leads && lic.rows.length === before.licenses && ordersSh.rows.length === before.orders,
  allToOwner: testMails.length > 0 && testMails.every(m => m.to === 'rashadfambro@gmail.com'),
  tagged: testMails.filter(m => /^\[TEST to customer@example\.com\]/.test(m.subject)).length,
  reminder: testMails.some(m => /^\[TEST to customer@example\.com\].*trial ends in 1 day/.test(m.subject)),
  check: JSON.parse(A.doGet({ parameter: { env: 'staging', check: 'trial', key: testLic.rows[1][0] } })).valid,
  checkInProd: JSON.parse(A.doGet({ parameter: { check: 'trial', key: testLic.rows[1][0] } })).status,
};
tag('test environment');
A.clearTestData();
result.test.cleared = !Object.keys(book.sheets).some(n => n.startsWith('TEST '));
console.log(JSON.stringify({ mails: sent, result }));
