/**
 * Rashad Fambro Consulting — Command Center (Google Apps Script web app)
 * -----------------------------------------------------------------------
 * A private dashboard for running the business: today's alerts, pipeline, clients and licenses,
 * finances, requests to the agent team, and an activity log.
 *
 * Security
 *   • Deploy as a web app with Execute as: Me and Who has access: Only myself. Google sign-in is the
 *     front door; every server call also checks that the signed-in user is the owner.
 *   • It reads the lead-engine Sheet by ID. License actions go to the lead engine's admin endpoint
 *     with a shared token, so the usual client emails are sent by the same code as always.
 *   • Settings live in Script properties, never in this file: LEADS_SHEET_ID, LEAD_ENGINE_URL, ADMIN_TOKEN.
 *   • Every action is written to the Log tab. Page output is escaped in the browser.
 *
 * Setup: see command-center/README.md.
 */

const CC = {
  OWNER_EMAIL: 'rashadfambro@gmail.com',
  TIMEZONE: 'America/Los_Angeles',
  // Plan prices for the monthly-revenue estimate. Keep in step with the website CONFIG.
  PLAN_PRICES: { std: { Essentials: 50, Growth: 90, Pro: 150 }, prop: { Essentials: 90, Growth: 150, Pro: 250 } },
  PROPERTY_TOOLS: ['property', 'resort', 'housekeeping', 'package'],
  ALERT_QUERY: 'is:unread in:inbox -category:promotions -category:social -category:forums newer_than:3d',
  // The inbox panel shows business mail only: these senders, anyone in your Leads/Prospects/Licenses/Orders tabs,
  // and the business's own alert subjects. Everything else in the mailbox is left out.
  BUSINESS_SENDERS: ['calendly.com', 'squareup.com', 'messaging.squareup.com', 'paypal.com', 'formsubmit.co', 'upwork.com', 'contra.com', 'clutch.co'],
  BUSINESS_SUBJECT: /^\s*\[(lead|trial|order|alert|test|daily brief|payment)|free workflow audit|trial request|order request|new website lead|proposal request|new event:|canceled event:|invitation from an invitee/i,
  STAGES: ['New', 'Not contacted', 'Draft ready', 'Contacted', 'Replied', 'Booked', 'Trial', 'Proposal sent', 'Ordered', 'Won', 'Lost', 'Do not contact', 'Spam'],
  RANK: { 'New': 0, 'Not contacted': 0, 'Draft ready': 0, 'Contacted': 1, 'Replied': 2, 'Booked': 3, 'Trial': 4, 'Proposal sent': 5, 'Ordered': 5.5, 'Won': 6 },
  AGENTS: ['chief-of-staff', 'pipeline-coordinator', 'lead-researcher', 'outreach-writer', 'scheduler', 'billing-coordinator',
    'client-success', 'project-manager', 'product-manager', 'mvp-builder', 'qa-engineer', 'release-manager', 'social-media-manager']
};
const REQUEST_HEADERS = ['Time', 'Request ID', 'Agent', 'Priority', 'Client / topic', 'Request', 'Status', 'Response', 'Link', 'Updated'];
const FINANCE_HEADERS = ['Date', 'Type', 'Category', 'Description', 'Amount', 'Client', 'Method', 'Reference'];
const PROSPECT_HEADERS = ['Added', 'Business', 'Contact', 'Email', 'Phone', 'City', 'Industry', 'Tools to pitch', 'Source', 'Status', 'Last activity', 'Next step', 'Notes'];
// Which tab and columns each kind of contact uses (columns are found by header name, so column order can change).
const KINDS = {
  lead: { tab: 'Leads', name: 'Name', activity: 'Last contact', fields: ['Name', 'Business', 'Email', 'Phone', 'Industry', 'Status'] },
  prospect: { tab: 'Prospects', name: 'Contact', activity: 'Last activity', fields: ['Contact', 'Business', 'Email', 'Phone', 'City', 'Industry', 'Tools to pitch', 'Status', 'Next step'] }
};
// Test data: the lead engine keeps staging traffic in "TEST ..." tabs. env 'test' points every read and action there.
let ENV_ = 'live';
function setEnv_(env) { ENV_ = env === 'test' ? 'test' : 'live'; }
function tname_(name) { return ENV_ === 'test' ? 'TEST ' + name : name; }

/* ======================= web app ======================= */

function doGet() {
  if (!isOwner_()) {
    const seen = Session.getActiveUser().getEmail() || 'no signed-in Google account was shared with this app';
    return HtmlService.createHtmlOutput('<div style="font:16px system-ui;max-width:560px;margin:40px auto;line-height:1.5">' +
      '<h2>Command Center: Not Authorized</h2><p>This page only opens for the owner account. Google reported: <b>' +
      String(seen).replace(/[<>&"]/g, '') + '</b>.</p><p>Fixes: open the link in a browser window signed in to only your business Google account ' +
      '(or a private window), and check the deployment is set to <b>Execute as: Me</b> and <b>Who has access: Only myself</b>.</p></div>')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DEFAULT);
  }
  return HtmlService.createTemplateFromFile('Index').evaluate()
    .setTitle('Command Center · Rashad Fambro Consulting')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DEFAULT);
}

function isOwner_() {
  const me = (Session.getActiveUser().getEmail() || '').toLowerCase();
  return me === CC.OWNER_EMAIL.toLowerCase();
}
function guard_() { if (!isOwner_()) throw new Error('Not authorized'); }
function prop_(k) { return PropertiesService.getScriptProperties().getProperty(k) || ''; }
function book_() {
  const id = prop_('LEADS_SHEET_ID');
  if (!id) throw new Error('Set LEADS_SHEET_ID in Project Settings → Script properties');
  return SpreadsheetApp.openById(id);
}
function tab_(name, headers) {
  name = tname_(name);
  const ss = book_(); let sh = ss.getSheetByName(name);
  if (!sh && headers) { sh = ss.insertSheet(name); sh.appendRow(headers); sh.setFrozenRows(1); sh.getRange(1, 1, 1, headers.length).setFontWeight('bold'); }
  return sh;
}
function values_(name) {
  const sh = tab_(name); if (!sh) return [];
  const v = sh.getDataRange().getValues(); const h = v.shift() || [];
  return v.filter(r => r.some(c => c !== '')).map((r, i) => { const o = { _row: i + 2 }; h.forEach((k, j) => o[k] = r[j] instanceof Date ? r[j].toISOString() : r[j]); return o; });
}
function log_(action, target, result) {
  tab_('Log', ['Time', 'Source', 'Action', 'Target', 'Result']).appendRow([new Date(), 'command-center', action, String(target).slice(0, 200), String(result).slice(0, 500)]);
}

/* ======================= data for the dashboard ======================= */

/** Everything the dashboard shows, in one call. */
function getDashboard(env) {
  guard_();
  setEnv_(env);
  const data = {
    leads: values_('Leads'), prospects: values_('Prospects'), licenses: values_('Licenses'), orders: values_('Orders'),
    finance: values_('Finance'), requests: values_('Requests'), log: values_('Log').slice(-60).reverse()
  };
  const summary = summarize_(data, new Date().toISOString(), CC);
  return {
    summary: summary,
    leads: data.leads.slice(-200).reverse(), prospects: data.prospects.slice(-200).reverse(),
    licenses: data.licenses, orders: data.orders.slice(-100).reverse(), finance: data.finance.slice(-200).reverse(),
    requests: data.requests.slice(-100).reverse(), log: data.log,
    calendar: calendar_(), inbox: inbox_(contacts_(data)), agents: CC.AGENTS, generated: new Date().toISOString(), env: ENV_, stages: CC.STAGES,
    theme: PropertiesService.getUserProperties().getProperty('theme') || 'dark'
  };
}

/** Pure function (no Google services), so it can be unit-tested. */
function summarize_(d, nowIso, cfg) {
  const now = new Date(nowIso), day = 86400000;
  const days = (iso) => iso ? Math.round((new Date(iso) - now) / day) : null;
  const sameMonth = (iso) => { const x = new Date(iso); return x.getFullYear() === now.getFullYear() && x.getMonth() === now.getMonth(); };
  const sameYear = (iso) => new Date(iso).getFullYear() === now.getFullYear();
  const money = (v) => Number(String(v).replace(/[^\d.-]/g, '')) || 0;
  const alerts = [];
  const pipeline = {};
  d.leads.forEach(l => { const s = l.Status || 'New'; pipeline[s] = (pipeline[s] || 0) + 1; });
  const newLeads = d.leads.filter(l => (l.Status || 'New') === 'New');
  newLeads.forEach(l => alerts.push({ level: Number(l.Score) >= 60 ? 'high' : 'info', kind: 'Lead', text: (l.Business || l.Name || l.Email) + ' (score ' + (l.Score || 0) + ', ' + (l.Form || 'website') + ')', ref: l.Email }));
  d.licenses.forEach(x => {
    const left = days(x['Ends / paid through']);
    if (x.Status === 'Trial' && left !== null && left >= 0 && left <= 3) alerts.push({ level: 'warn', kind: 'Trial ending', text: x.Business + ': ' + left + ' day(s) left', ref: x.Key });
    if (x.Status === 'Past due') alerts.push({ level: 'high', kind: 'Past due', text: x.Business + ' (' + x.Tools + ')', ref: x.Key });
    if (x.Status === 'Active' && left !== null && left >= 0 && left <= 5) alerts.push({ level: 'info', kind: 'Renewal', text: x.Business + ' renews in ' + left + ' day(s)', ref: x.Key });
  });
  d.orders.filter(o => o.Status === 'Awaiting payment').forEach(o => alerts.push({ level: 'warn', kind: 'Unpaid order', text: (o.Business || o.Name) + ': $' + money(o['Amount due']) + ' ' + (o.Item || ''), ref: o['Order ID'] }));
  d.requests.filter(r => r.Status === 'Done' && days(r.Updated) !== null && days(r.Updated) >= -2).forEach(r => alerts.push({ level: 'info', kind: 'Agent reply', text: r.Agent + ': ' + String(r.Request).slice(0, 80), ref: r['Request ID'] }));

  const price = (tools, plan) => {
    const tier = /Pro/.test(plan) ? 'Pro' : /Growth/.test(plan) ? 'Growth' : 'Essentials';
    return String(tools || '').split(',').filter(Boolean).reduce((s, t) => s + cfg.PLAN_PRICES[cfg.PROPERTY_TOOLS.indexOf(t.trim()) >= 0 ? 'prop' : 'std'][tier], 0);
  };
  const active = d.licenses.filter(x => ['Active', 'Past due'].indexOf(x.Status) >= 0);
  const mrr = active.reduce((s, x) => s + price(x.Tools, x.Plan), 0);
  const paidOrders = d.orders.filter(o => o.Status === 'Paid');
  const income = d.finance.filter(f => /income/i.test(f.Type)), expense = d.finance.filter(f => /expense/i.test(f.Type));
  const revMonth = paidOrders.filter(o => sameMonth(o.Received)).reduce((s, o) => s + money(o['Amount due']), 0) + income.filter(f => sameMonth(f.Date)).reduce((s, f) => s + money(f.Amount), 0);
  const revYear = paidOrders.filter(o => sameYear(o.Received)).reduce((s, o) => s + money(o['Amount due']), 0) + income.filter(f => sameYear(f.Date)).reduce((s, f) => s + money(f.Amount), 0);
  const costMonth = expense.filter(f => sameMonth(f.Date)).reduce((s, f) => s + Math.abs(money(f.Amount)), 0);
  const costYear = expense.filter(f => sameYear(f.Date)).reduce((s, f) => s + Math.abs(money(f.Amount)), 0);
  const won = d.leads.filter(l => l.Status === 'Won').length, total = d.leads.length;
  const order = { high: 0, warn: 1, info: 2 };
  alerts.sort((a, b) => order[a.level] - order[b.level]);
  return {
    alerts: alerts, pipeline: pipeline,
    counts: { leads: total, newLeads: newLeads.length, prospects: d.prospects.length, trials: d.licenses.filter(x => x.Status === 'Trial').length,
      activeClients: active.length, founding: d.licenses.filter(x => /founding/i.test(x.Plan) && ['Active', 'Past due', 'Paused'].indexOf(x.Status) >= 0).length,
      openRequests: d.requests.filter(r => r.Status !== 'Done').length },
    finance: { mrrEstimate: mrr, revenueMonth: revMonth, revenueYear: revYear, costsMonth: costMonth, costsYear: costYear, profitYear: revYear - costYear },
    conversion: total ? Math.round(100 * won / total) : 0
  };
}

function calendar_() {
  try {
    const start = new Date(), end = new Date(Date.now() + 7 * 86400000);
    return CalendarApp.getDefaultCalendar().getEvents(start, end).slice(0, 25).map(e => ({ title: e.getTitle(), start: e.getStartTime().toISOString(), end: e.getEndTime().toISOString(), where: e.getLocation() }));
  } catch (e) { return []; }
}
/** Every email address in the business's own records (leads, prospects, clients, orders). */
function contacts_(d) {
  const set = {};
  [].concat(d.leads, d.prospects, d.licenses, d.orders).forEach(r => { const e = String(r.Email || '').trim().toLowerCase(); if (e) set[e] = true; });
  return set;
}
/** Pure function: is this message about the business? (unit-tested) */
function isBusinessMail_(from, subject, contacts, cfg) {
  const addr = String((String(from).match(/<([^>]+)>/) || [])[1] || from).trim().toLowerCase();
  const domain = addr.split('@')[1] || '';
  return cfg.BUSINESS_SENDERS.some(s => domain === s || domain.slice(-(s.length + 1)) === '.' + s) || !!contacts[addr] || cfg.BUSINESS_SUBJECT.test(String(subject));
}
/** Unread business email from the last 3 days. Personal mail never appears. */
function inbox_(contacts) {
  try {
    const out = [];
    GmailApp.search(CC.ALERT_QUERY, 0, 60).forEach(t => {
      const m = t.getMessages()[t.getMessageCount() - 1];
      if (!isBusinessMail_(m.getFrom(), m.getSubject(), contacts || {}, CC)) return;
      out.push({ from: m.getFrom(), subject: m.getSubject(), date: m.getDate().toISOString(), business: true, link: 'https://mail.google.com/mail/u/0/#inbox/' + t.getId() });
    });
    return out.slice(0, 25);
  } catch (e) { return []; }
}

/* ======================= actions ======================= */

/** Saves the chosen color theme for this Google account. */
function setTheme(theme) {
  guard_();
  if (['dark', 'light', 'midnight', 'contrast'].indexOf(theme) < 0) throw new Error('Unknown theme');
  PropertiesService.getUserProperties().setProperty('theme', theme);
  return theme;
}


/** License actions go through the lead engine so the usual emails go out. action: record_payment | pause | cancel | resend | mark_founding */
function licenseAction(action, key, env) {
  guard_(); setEnv_(env);
  if (['record_payment', 'pause', 'cancel', 'resend', 'mark_founding'].indexOf(action) < 0) throw new Error('Unknown action');
  if (!/^RFL?-\d{8}-[0-9A-Z]{6}$/.test(String(key))) throw new Error('Bad license key');
  const url = prop_('LEAD_ENGINE_URL'), token = prop_('ADMIN_TOKEN');
  if (!url || token.length < 24) throw new Error('Set LEAD_ENGINE_URL and ADMIN_TOKEN (24+ characters) in Script properties');
  const res = UrlFetchApp.fetch(url, { method: 'post', contentType: 'text/plain;charset=utf-8', muteHttpExceptions: true,
    payload: JSON.stringify({ type: 'admin', env: ENV_ === 'test' ? 'staging' : 'production', token: token, action: action, key: key }) });
  let out; try { out = JSON.parse(res.getContentText()); } catch (e) { out = { ok: false, error: 'bad response ' + res.getResponseCode() }; }
  log_('license:' + action, key, out.ok ? 'ok' : out.error);
  if (!out.ok) throw new Error(out.error || 'Lead engine refused the action');
  return out;
}

/** Change a lead's status by hand (moves automatically too; see syncPipeline in the lead engine). */
function setLeadStatus(row, status) {
  guard_();
  if (CC.STAGES.indexOf(status) < 0) throw new Error('Unknown status');
  const sh = tab_('Leads'); row = Number(row);
  if (!(row >= 2 && row <= sh.getLastRow())) throw new Error('Bad row');
  const before = sh.getRange(row, 3).getValue();
  sh.getRange(row, 3).setValue(status);
  log_('lead:status', sh.getRange(row, 8).getValue(), before + ' → ' + status);
  return true;
}

/* ======================= prospects & pipeline ======================= */

function headerMap_(sh) { const h = sh.getRange(1, 1, 1, sh.getLastColumn ? sh.getLastColumn() : 30).getValues()[0]; const m = {}; h.forEach((k, i) => { if (k) m[k] = i + 1; }); return m; }
function cleanEmail_(v) { v = String(v || '').trim(); if (v && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) throw new Error('That email address does not look right'); return v; }
function clip_(v, n) { return String(v == null ? '' : v).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '').slice(0, n || 200); }
function plain_(s) {
  return String(s == null ? '' : s).replace(/[\u2018\u2019]/g, "'").replace(/[\u201c\u201d]/g, '"').replace(/[\u2013\u2014]/g, '-').replace(/\u2026/g, '...')
    .replace(/\u00a0/g, ' ').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[^\x09\x0A\x0D\x20-\x7E]/g, '');
}
/** Finds the record: by row, confirmed by email, so a re-sorted sheet can never update the wrong person. */
function locate_(kind, ref) {
  const k = KINDS[kind]; if (!k) throw new Error('Unknown record type');
  const sh = tab_(k.tab, kind === 'prospect' ? PROSPECT_HEADERS : null); if (!sh) throw new Error('No ' + k.tab + ' tab yet');
  const h = headerMap_(sh), last = sh.getLastRow(), row = Number(ref && ref.row), email = String(ref && ref.email || '').toLowerCase();
  const emailAt = (r) => String(sh.getRange(r, h.Email).getValue() || '').toLowerCase();
  const nameAt = (r) => String(sh.getRange(r, h.Business).getValue() || '');
  if (row >= 2 && row <= last && (email ? emailAt(row) === email : nameAt(row) === String(ref.business || ''))) return { sh: sh, h: h, row: row, k: k };
  if (email) for (let r = 2; r <= last; r++) if (emailAt(r) === email) return { sh: sh, h: h, row: r, k: k };
  throw new Error('That record moved or was deleted. Refresh and try again.');
}
function note2_(x, text) {
  const c = x.sh.getRange(x.row, x.h.Notes); const stamp = Utilities.formatDate(new Date(), CC.TIMEZONE, 'yyyy-MM-dd');
  c.setValue((c.getValue() ? c.getValue() + ' · ' : '') + stamp + ' ' + clip_(text, 500));
  if (x.h[x.k.activity]) x.sh.getRange(x.row, x.h[x.k.activity]).setValue(new Date());
}

/** Edit a lead or prospect: names, contact details, stage, next step. */
function saveContact(kind, ref, fields, env) {
  guard_(); setEnv_(env);
  const x = locate_(kind, ref), changed = [];
  Object.keys(fields || {}).forEach(f => {
    if (x.k.fields.indexOf(f) < 0 || !x.h[f]) return;
    let v = f === 'Email' ? cleanEmail_(fields[f]) : clip_(fields[f], f === 'Next step' ? 300 : 120);
    if (f === 'Status' && CC.STAGES.indexOf(v) < 0) throw new Error('Unknown status');
    const before = x.sh.getRange(x.row, x.h[f]).getValue();
    if (String(before) !== String(v)) { x.sh.getRange(x.row, x.h[f]).setValue(v); changed.push(f === 'Status' ? 'Status ' + (before || 'New') + ' -> ' + v : f); }
  });
  if (changed.length) { note2_(x, 'edited: ' + changed.join(', ')); log_(kind + ':edit', x.sh.getRange(x.row, x.h.Business).getValue(), changed.join('; ')); }
  return { ok: true, changed: changed };
}

/** Add a dated note to a lead or prospect. */
function addNote(kind, ref, text, env) {
  guard_(); setEnv_(env);
  text = String(text || '').trim(); if (!text) throw new Error('Write a note first');
  const x = locate_(kind, ref); note2_(x, text);
  log_(kind + ':note', x.sh.getRange(x.row, x.h.Business).getValue(), clip_(text, 120));
  return true;
}

/** Add a prospect by hand (walk-in, referral, event). */
function addProspect(fields, env) {
  guard_(); setEnv_(env);
  const f = fields || {};
  const business = clip_(f.Business, 120).trim(); if (!business) throw new Error('Business name is required');
  const email = cleanEmail_(f.Email);
  const sh = tab_('Prospects', PROSPECT_HEADERS), h = headerMap_(sh), row = new Array(Object.keys(h).length).fill('');
  const put = (k, v) => { if (h[k]) row[h[k] - 1] = v; };
  put('Added', new Date()); put('Business', business); put('Contact', clip_(f.Contact, 120)); put('Email', email); put('Phone', clip_(f.Phone, 40));
  put('City', clip_(f.City, 80)); put('Industry', clip_(f.Industry, 80)); put('Tools to pitch', clip_(f['Tools to pitch'], 120));
  put('Source', clip_(f.Source || 'Command Center', 60)); put('Status', 'New'); put('Next step', clip_(f['Next step'], 300));
  put('Notes', f.Notes ? Utilities.formatDate(new Date(), CC.TIMEZONE, 'yyyy-MM-dd') + ' ' + clip_(f.Notes, 500) : '');
  sh.appendRow(row);
  log_('prospect:add', business, email || 'no email');
  return { ok: true, row: sh.getLastRow() };
}

/** Email a lead or prospect from your own Gmail: mode 'send' sends now, 'draft' saves it to Gmail Drafts.
 *  In test data, mail goes to you instead, marked [TEST to ...]. Moves New -> Contacted and logs it. */
function emailContact(kind, ref, subject, body, mode, env) {
  guard_(); setEnv_(env);
  subject = plain_(subject).replace(/\s+/g, ' ').trim(); body = plain_(body).trim();
  if (!subject || !body) throw new Error('Write a subject and a message');
  const x = locate_(kind, ref);
  let to = cleanEmail_(x.sh.getRange(x.row, x.h.Email).getValue()); if (!to) throw new Error('Add an email address first');
  const status = String(x.sh.getRange(x.row, x.h.Status).getValue() || 'New');
  if (status === 'Do not contact') throw new Error('This contact asked not to be emailed');
  if (ENV_ === 'test') { subject = '[TEST to ' + to + '] ' + subject; to = CC.OWNER_EMAIL; }
  if (mode === 'send') GmailApp.sendEmail(to, subject, body, { name: 'Rashad Fambro' });
  else GmailApp.createDraft(to, subject, body, { name: 'Rashad Fambro' });
  if ((CC.RANK[status] || 0) < 1 && mode === 'send') x.sh.getRange(x.row, x.h.Status).setValue('Contacted');
  note2_(x, (mode === 'send' ? 'emailed: ' : 'draft saved: ') + subject);
  log_(kind + ':' + (mode === 'send' ? 'email' : 'draft'), x.sh.getRange(x.row, x.h.Business).getValue(), subject);
  return { ok: true, mode: mode === 'send' ? 'send' : 'draft' };
}

/** Start a 14-day trial for a lead or prospect: the lead engine creates the trial and emails the link (fixed template). */
function startTrial(kind, ref, tools, env) {
  guard_(); setEnv_(env);
  const x = locate_(kind, ref), g = (k) => x.h[k] ? x.sh.getRange(x.row, x.h[k]).getValue() : '';
  const email = cleanEmail_(g('Email')); if (!email) throw new Error('Add an email address first');
  tools = clip_(tools || g('Tools to pitch'), 120).trim(); if (!tools) throw new Error('Choose the tool(s) for the trial');
  const url = prop_('LEAD_ENGINE_URL'); if (!url) throw new Error('Set LEAD_ENGINE_URL in Script properties');
  const res = UrlFetchApp.fetch(url, { method: 'post', contentType: 'text/plain;charset=utf-8', muteHttpExceptions: true,
    payload: JSON.stringify({ type: 'lead', form: 'trial', env: ENV_ === 'test' ? 'staging' : 'production', Name: String(g(x.k.name) || ''), Business: String(g('Business')), Email: email,
      Phone: String(g('Phone') || ''), Package: tools, Workflow: 'Trial started from the Command Center', source: 'command-center', page: 'command-center' }) });
  let out; try { out = JSON.parse(res.getContentText()); } catch (e) { out = { ok: false, error: 'bad response ' + res.getResponseCode() }; }
  if (!out.ok) { log_(kind + ':trial', g('Business'), 'failed: ' + (out.error || '')); throw new Error(out.error || 'The lead engine refused the trial'); }
  if ((CC.RANK[String(g('Status') || 'New')] || 0) < 4) x.sh.getRange(x.row, x.h.Status).setValue('Trial');
  note2_(x, 'trial started: ' + tools);
  log_(kind + ':trial', g('Business'), tools);
  return { ok: true };
}

/** A request for the agent team. A scheduled Claude task reads New requests, does the work and writes the response back. */
function addRequest(agent, priority, topic, text) {
  guard_();
  text = String(text || '').trim();
  if (!text) throw new Error('Write a request first');
  if (CC.AGENTS.indexOf(agent) < 0) agent = 'chief-of-staff';
  if (['High', 'Normal', 'Low'].indexOf(priority) < 0) priority = 'Normal';
  const id = 'Q' + Utilities.formatDate(new Date(), 'UTC', 'yyMMddHHmmss');
  tab_('Requests', REQUEST_HEADERS).appendRow([new Date(), id, agent, priority, String(topic || '').slice(0, 120), text.slice(0, 4000), 'New', '', '', new Date()]);
  log_('request:new', id, agent + ' · ' + priority);
  return id;
}

/** Record income or an expense (software, ads, travel, contractor) for the profit view. */
function addFinance(entry) {
  guard_();
  const type = entry && entry.type === 'Expense' ? 'Expense' : 'Income';
  const amount = Math.abs(Number(entry.amount));
  if (!(amount > 0 && amount < 1e7)) throw new Error('Enter an amount');
  const date = entry.date ? new Date(entry.date + 'T12:00:00') : new Date();
  tab_('Finance', FINANCE_HEADERS).appendRow([date, type, String(entry.category || '').slice(0, 60), String(entry.description || '').slice(0, 200), type === 'Expense' ? -amount : amount,
    String(entry.client || '').slice(0, 80), String(entry.method || '').slice(0, 30), String(entry.reference || '').slice(0, 80)]);
  log_('finance:' + type.toLowerCase(), entry.description || '', amount);
  return true;
}

/* ======================= daily brief & setup ======================= */

/** Emails a short morning brief (installed by setupCommandCenter). */
function dailyBrief() {
  const d = getDashboardForBrief_();
  const s = d.summary, f = s.finance;
  const lines = ['Good morning. Here is today:', '',
    'Alerts (' + s.alerts.length + '):'].concat(s.alerts.slice(0, 15).map(a => '  - ' + a.kind + ': ' + a.text))
    .concat(['', 'Meetings next 7 days: ' + d.calendar.length].concat(d.calendar.slice(0, 8).map(e => '  - ' + Utilities.formatDate(new Date(e.start), CC.TIMEZONE, 'EEE MMM d, h:mm a') + '  ' + e.title)))
    .concat(['', 'Pipeline: ' + Object.keys(s.pipeline).map(k => k + ' ' + s.pipeline[k]).join(', '),
      'Clients: ' + s.counts.activeClients + ' active, ' + s.counts.trials + ' in trial, Est. monthly revenue $' + f.mrrEstimate,
      'Revenue this month $' + f.revenueMonth + ', Year to date $' + f.revenueYear + ', Costs YTD $' + f.costsYear,
      'Open agent requests: ' + s.counts.openRequests, '', 'Open the Command Center: ' + ScriptApp.getService().getUrl()]);
  GmailApp.sendEmail(CC.OWNER_EMAIL, '[Daily brief] ' + s.alerts.length + ' alert(s), ' + d.calendar.length + ' meeting(s) this week', lines.join('\n'), { name: 'Command Center' });
}
function getDashboardForBrief_() {
  const data = { leads: values_('Leads'), prospects: values_('Prospects'), licenses: values_('Licenses'), orders: values_('Orders'), finance: values_('Finance'), requests: values_('Requests') };
  return { summary: summarize_(data, new Date().toISOString(), CC), calendar: calendar_() };
}

/** Run once: creates the Requests and Finance tabs and the 7 AM daily brief. */
function setupCommandCenter() {
  tab_('Requests', REQUEST_HEADERS); tab_('Finance', FINANCE_HEADERS); tab_('Log', ['Time', 'Source', 'Action', 'Target', 'Result']);
  ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'dailyBrief').forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('dailyBrief').timeBased().everyDays(1).atHour(7).inTimezone(CC.TIMEZONE).create();
  log_('setup', 'command-center', 'ok');
  console.log('Done. Now Deploy → New deployment → Web app (Execute as: Me, Who has access: Only myself).');
}
