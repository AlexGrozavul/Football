// Headless Chromium test of the Me tab (memberships and tickets held), at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright          (anywhere; it is not a dependency of this repo)
//   node tools/test_me.js .         (serves the checkout itself; it changes no file)
//
// Added 2026-10-04 with the Me tab. Checks, with the clock at 2026-10-04 12:00 Berlin time:
//  - five tabs (since 2026-10-08, Competitions between Ticket info and Me) fit the bottom bar at 390 px: none wider than its slot, none wrapped, none off screen;
//  - add, edit and delete a membership and a ticket; "Renewal due in N days" inside the window,
//    "Renewal overdue by N days" before today, a plain "Renews" date outside it, and the window setting;
//    a non-euro cost with the euro figure in brackets, or "euro figure not entered"; a ticket with no
//    kick-off says "time not set";
//  - everything survives a reload;
//  - a free-text value holding a payment card number (13-19 digits passing Luhn, with or without
//    spaces) is refused with a reason and nothing is saved; digits that fail Luhn are accepted;
//  - a ticket linked to a bucket entry (chosen by id from a dropdown) puts "You hold tickets" on that
//    entry in the List (card and opened detail), in the calendar (day cell and item) and in the sheet,
//    and on no other entry;
//  - "Add to phone calendar" downloads a valid one-event .ics: CRLF lines no longer than 75 octets,
//    VCALENDAR/VEVENT/VALARM properly nested, the required properties, and an alarm that goes off at
//    exactly the lead time chosen (1 day before kick-off; 14 days before a renewal at 09:00; a changed
//    lead time) and the date as typed;
//  - the backup banner shows after an edit (and after a star) and goes after an export; export, delete
//    everything, import gives back exactly what was exported, favorites included;
//  - broken imports are refused with the device unchanged: not JSON, another app's file, a newer
//    version, a ticket with no status, a card number in a note, a repeated id;
//  - with storage blocked the tab still works for the visit and says so;
//  - no horizontal overflow on the tab with forms and cards open;
//  - nothing typed on the tab appears in any network request (URL, headers or body), no request
//    other than GET is made, nothing is in cookies, sessionStorage or IndexedDB, and nothing in the
//    repository holds it;
//  - since 2026-10-09 the Me tab has four sub-tabs (Stats, Matches, Events, Tickets; all existing checks above run on the fourth),
//    the first three read data/attended.json: the sub-tabs appear in order and fit at 390 px in English and Romanian; the
//    file is not requested before one of them is opened and only once after; the stats and the list counts equal counts made
//    here from the file itself; every match and event is listed in the old app's order and opens the header sheet; en and ro
//    have identical key sets and every key the page uses exists; the page reads no browser storage on them; a failed load says so;
//  - since 2026-10-09 the tapped match or event opens the full detail sheet: line-ups (home side first, with a switch), the pitch as inline SVG
//    (only where the formation adds up; never inferred), timeline in minute order, stats only with a stats block, the factual note labelled
//    unverified, no empty pane; the personal fields (note, ticket, seat, block, who I went with) are kept only under football-attended-personal,
//    card numbers are refused on four of them, no storage read or write is an mf_ key, mf_media is untouched; nothing overflows at 390 px;
//  - no script error.
// Stadia's tiles are stubbed. CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path'), { execSync } = require('child_process');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8781, BASE = `http://localhost:${PORT}/Football/`;
const W = 390, H = 844;
const TYPES = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.csv':'text/csv; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
const results = [];
const check = (name, ok, detail='') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ' :: ' + detail : '')); };

// Unique to this run, so finding it anywhere it should not be cannot be a coincidence.
const TAG = 'Zq' + Math.random().toString(36).slice(2, 8);
const rules = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/football-rules.json'), 'utf8'));
const LINK_ID = 'derby-madonnina';          // first leg 1 Nov 2026, confirmed in your notes
const linked = rules.bucketList.find(b => b.id === LINK_ID);

const nonGet = [];
const server = http.createServer((req, res) => {
  if(req.method !== 'GET' && req.method !== 'HEAD') nonGet.push(`${req.method} ${req.url}`);
  const p = decodeURIComponent(req.url.split('?')[0]);
  if(!p.startsWith('/Football/')){ res.writeHead(404); return res.end(); }
  let f = path.join(ROOT, p.slice('/Football/'.length)); if(p.endsWith('/')) f = path.join(f, 'index.html');
  fs.stat(f, (e, st) => {
    if(e || !st.isFile()){ res.writeHead(404); return res.end('nf'); }
    res.writeHead(200, {'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream', 'Cache-Control':'no-store'});
    fs.createReadStream(f).pipe(res);
  });
});

// ---- .ics reading: unfold, check the shape, and work out when the alarm goes off.
function parseIcs(text){
  const raw = text.split('\r\n');
  const problems = [];
  if(!text.endsWith('\r\n')) problems.push('does not end with CRLF');
  if(/[^\r]\n/.test(text)) problems.push('a bare LF');
  raw.forEach((l, i) => { if(Buffer.byteLength(l, 'utf8') > 75) problems.push(`line ${i + 1} is ${Buffer.byteLength(l)} octets`); });
  const lines = [];
  for(const l of raw){ if(l === '') continue; if(/^[ \t]/.test(l)) lines[lines.length - 1] += l.slice(1); else lines.push(l); }
  const stack = [], comps = {VEVENT: 0, VALARM: 0};
  const props = {VCALENDAR: {}, VEVENT: {}, VALARM: {}};
  for(const l of lines){
    const m = l.match(/^([A-Z-]+)((?:;[^:]*)?):(.*)$/);
    if(!m){ problems.push('unreadable line: ' + l); continue; }
    const [, name, params, value] = m;
    if(name === 'BEGIN'){ stack.push(value); if(value in comps) comps[value]++; continue; }
    if(name === 'END'){ if(stack.pop() !== value) problems.push('END:' + value + ' out of order'); continue; }
    const at = stack[stack.length - 1];
    if(!props[at]) problems.push(`${name} outside a known component`); else props[at][name] = {params, value};
  }
  if(stack.length) problems.push('unclosed ' + stack.join(','));
  if(lines[0] !== 'BEGIN:VCALENDAR' || lines[lines.length - 1] !== 'END:VCALENDAR') problems.push('not wrapped in VCALENDAR');
  if(comps.VEVENT !== 1) problems.push(`${comps.VEVENT} VEVENTs`);
  if(comps.VALARM !== 1) problems.push(`${comps.VALARM} VALARMs`);
  for(const k of ['VERSION', 'PRODID']) if(!props.VCALENDAR[k]) problems.push('no ' + k);
  if(props.VCALENDAR.VERSION && props.VCALENDAR.VERSION.value !== '2.0') problems.push('VERSION is not 2.0');
  for(const k of ['UID', 'DTSTAMP', 'DTSTART', 'SUMMARY']) if(!props.VEVENT[k]) problems.push('no ' + k);
  if(props.VEVENT.DTSTAMP && !/^\d{8}T\d{6}Z$/.test(props.VEVENT.DTSTAMP.value)) problems.push('DTSTAMP not UTC date-time');
  for(const k of ['ACTION', 'TRIGGER', 'DESCRIPTION']) if(!props.VALARM[k]) problems.push('VALARM has no ' + k);
  return {problems, ev: props.VEVENT, al: props.VALARM};
}
// The moment the alarm goes off, as a plain local "YYYY-MM-DDTHH:MM" (the event has no time zone).
function alarmAt(ev, al){
  const s = ev.DTSTART.value;
  const start = /^\d{8}$/.test(s) ? Date.UTC(+s.slice(0, 4), +s.slice(4, 6) - 1, +s.slice(6, 8))
    : Date.UTC(+s.slice(0, 4), +s.slice(4, 6) - 1, +s.slice(6, 8), +s.slice(9, 11), +s.slice(11, 13));
  const m = al.TRIGGER.value.match(/^([+-]?)P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$/);
  if(!m) return 'unreadable trigger ' + al.TRIGGER.value;
  const ms = ((+m[2] || 0) * 86400 + (+m[3] || 0) * 3600 + (+m[4] || 0) * 60 + (+m[5] || 0)) * 1000;
  return new Date(start + (m[1] === '-' ? -ms : ms)).toISOString().slice(0, 16);
}

(async () => {
  await new Promise(r => server.listen(PORT, r));
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || undefined, headless: true});
  const errors = [], requests = [];
  async function newCtx({blockStorage = false} = {}){
    const ctx = await browser.newContext({viewport: {width: W, height: H}, isMobile: true, hasTouch: true,
      deviceScaleFactor: 2, serviceWorkers: 'block', timezoneId: 'Europe/Berlin', acceptDownloads: true});
    await ctx.clock.setFixedTime(new Date('2026-10-04T10:00:00Z'));
    await ctx.route('https://tiles.stadiamaps.com/**', r => r.fulfill({status:200, contentType:'image/png', headers: {'Access-Control-Allow-Origin': '*'}, body: PNG}));
    await ctx.route('https://api.stadiamaps.com/**', r => r.abort());
    if(blockStorage) await ctx.addInitScript(() => {
      Object.defineProperty(window, 'localStorage', {get(){ throw new Error('storage blocked'); }});
    });
    ctx.on('request', req => requests.push({url: req.url(), method: req.method(), body: req.postData() || '',
      headers: JSON.stringify(req.headers())}));
    return ctx;
  }
  async function openMe(ctx, page){
    page = page || await ctx.newPage();
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(BASE);
    await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
    await page.waitForFunction(() => document.querySelector('#bucketBody details.bucket'), null, {timeout: 15000});
    await page.click('nav button[data-pane=me]');
    await page.click('#meTabTix');           // the existing content is the fourth sub-tab
    await page.waitForSelector('#meMemTitle');
    return page;
  }
  const sideways = page => page.evaluate(() => {
    const el = document.getElementById('pane-me');
    const over = [...el.querySelectorAll('*')].filter(x => { const r = x.getBoundingClientRect(); return r.width > 0 && (r.right > innerWidth + 1 || r.left < -1); });
    return {sw: el.scrollWidth, cw: el.clientWidth, doc: document.documentElement.scrollWidth,
      over: over.slice(0, 5).map(x => `${x.tagName}.${x.className} "${x.textContent.trim().slice(0, 40)}"`)};
  });
  const noSideways = (name, s) => check(name, s.sw <= s.cw && s.doc <= W && !s.over.length, JSON.stringify(s));
  const cardText = (page, kind, h3) => page.evaluate(([kind, h3]) => {
    const c = [...document.querySelectorAll(`.mecard[data-kind=${kind}]`)].find(c => c.querySelector('h3').textContent.includes(h3));
    return c ? c.innerText.replace(/\s+/g, ' ') : null;
  }, [kind, h3]);
  async function fill(page, values){
    for(const [k, v] of Object.entries(values)){
      const el = await page.$(`form.meform [name="${k}"]`);
      if(!el) throw new Error('no field ' + k);
      if(await el.evaluate(e => e.tagName === 'SELECT')) await el.selectOption(v);
      else await el.fill(String(v));
    }
  }
  async function add(page, kind, values){
    await page.click(`button[data-act=add][data-kind=${kind}]`);
    await page.waitForSelector('form.meform');
    await fill(page, values);
    await page.click('form.meform button[type=submit]');
  }
  async function download(page, click){
    const [d] = await Promise.all([page.waitForEvent('download'), click()]);
    return {name: d.suggestedFilename(), text: fs.readFileSync(await d.path(), 'utf8')};
  }
  const stored = page => page.evaluate(() => localStorage.getItem('football-planner-me'));

  // ---------------------------------------------------------------- first visit
  const ctx = await newCtx();
  const page = await openMe(ctx);

  // Five tabs at 390 px.
  const nav = await page.evaluate(() => {
    const bs = [...document.querySelectorAll('nav button')];
    return {n: bs.length, labels: bs.map(b => b.textContent.replace(/\s+/g, ' ').trim()), navW: document.querySelector('nav').scrollWidth,
      bad: bs.filter(b => { const r = b.getBoundingClientRect(); return b.scrollWidth > b.clientWidth + 1 || r.right > innerWidth + 1 || r.left < -1; })
        .map(b => b.textContent.trim()),
      heights: bs.map(b => Math.round(b.getBoundingClientRect().height)),
      lines: bs.map(b => { const t = [...b.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('');
        const r = document.createRange(); const node = [...b.childNodes].find(n => n.nodeType === 3); r.selectNodeContents(node);
        return r.getClientRects().length; })};
  });
  check('Five tabs in the bottom bar, "Competitions" fourth and "Me" fifth', nav.n === 5 && /Competitions$/.test(nav.labels[3]) && /Me$/.test(nav.labels[4]), nav.labels.join(' | '));
  check('All five fit at 390 px: none wider than its slot or off screen', !nav.bad.length && nav.navW <= W, JSON.stringify(nav.bad) + ` nav ${nav.navW}`);
  check('No tab label wraps to a second line, all the same height', nav.lines.every(n => n === 1) && new Set(nav.heights).size === 1,
    JSON.stringify({lines: nav.lines, heights: nav.heights}));

  const intro = await page.textContent('#meBody');
  check('The tab says it is kept on this device only and that clearing site data deletes it',
    /Kept on this device only/.test(intro) && /Clearing Chrome's site data/.test(intro), '');
  check('The tab says why codes and card numbers are not stored: export files end up in cloud backups',
    /barcode/.test(intro) && /QR code/.test(intro) && /password/.test(intro) && /card number/.test(intro) && /cloud backups/.test(intro), '');
  check('No backup banner before any edit', await page.$eval('#meBackup', e => e.hidden), '');
  const fieldNames = await page.evaluate(async () => {
    const out = [];
    for(const k of ['membership', 'ticket']){
      document.querySelector(`button[data-act=add][data-kind=${k}]`).click();
      out.push(...[...document.querySelectorAll('form.meform [name]')].map(e => e.name + ' ' + (c => c ? (c.querySelectorAll('select').forEach(x => x.remove()), c.textContent) : '')(e.closest('label')?.cloneNode(true))));   // the caption, not the bucket entries listed in a dropdown
      document.querySelector('form.meform [data-act=cancel]').click();
    }
    return out;
  });
  check('No field for a barcode, QR code, password or card number', !fieldNames.some(f => /barcode|qr|password|card|pin\b|cvv/i.test(f)), fieldNames.length + ' fields');

  // ---- Memberships: add three, around the 30-day window.
  await add(page, 'membership', {club: `VfB Stuttgart ${TAG}`, whoFor: 'Alexandru', scheme: 'Mitgliedschaft', costAmount: '84',
    costCurrency: 'EUR', frequency: 'yearly', renewal: '2026-10-20', benefits: 'presale right', notes: `call ${TAG} +49 170 1234567`});
  check('A membership is added', !!(await cardText(page, 'membership', 'VfB Stuttgart')), '');
  await add(page, 'membership', {club: 'Poli Timisoara', scheme: 'Abonament', costAmount: '250', costCurrency: 'ron', costEur: '50.25',
    frequency: 'per season', renewal: '2026-09-30'});
  await add(page, 'membership', {club: 'UTA Arad', scheme: 'Card', costAmount: '100', costCurrency: 'RON', renewal: '2027-03-01'});
  let vfb = await cardText(page, 'membership', 'VfB Stuttgart'), poli = await cardText(page, 'membership', 'Poli'), uta = await cardText(page, 'membership', 'UTA');
  check('Renewal within the window: "Renewal due in 16 days"', /Renewal due in 16 days/.test(vfb), vfb);
  check('Renewal before today: "Renewal overdue by 4 days"', /Renewal overdue by 4 days/.test(poli), poli);
  check('Renewal outside the window: a plain date, no "due"', /Renews Mon,? 1 Mar 2027/.test(uta) && !/due|overdue/.test(uta), uta);
  check('Cost in its own currency with the euro figure in brackets', /250\.00 RON \(50\.25 EUR\)/.test(poli), poli);
  check('A non-euro cost with no euro figure says so, nothing worked out', /100\.00 RON \(euro figure not entered\)/.test(uta), uta);
  check('A euro cost has no brackets', /84\.00 EUR/.test(vfb) && !/84\.00 EUR \(/.test(vfb), '');
  const order = await page.$$eval('#meMemberships .mecard h3', hs => hs.map(h => h.textContent));
  check('Overdue first, then the soonest renewal', /Poli/.test(order[0]) && /VfB/.test(order[1]) && /UTA/.test(order[2]), order.join(' | '));
  check('The backup banner shows after an edit', !(await page.$eval('#meBackup', e => e.hidden)) &&
    /Back up your data — export/.test(await page.textContent('#meBackup')), '');
  await page.fill('#meWindow', '200'); await page.dispatchEvent('#meWindow', 'change');
  uta = await cardText(page, 'membership', 'UTA');
  check('Widening the window to 200 days makes the March renewal "due in 148 days"', /Renewal due in 148 days/.test(uta), uta);
  await page.fill('#meWindow', '30'); await page.dispatchEvent('#meWindow', 'change');

  // Edit and delete.
  await page.click('.mecard[data-kind=membership]:has(h3:text("UTA")) [data-act=edit]');
  check('Edit opens the form with what was saved', await page.inputValue('form.meform [name=scheme]') === 'Card' &&
    await page.inputValue('form.meform [name=renewal]') === '2027-03-01', '');
  await fill(page, {scheme: 'Card Gold'}); await page.click('form.meform button[type=submit]');
  check('The edit is saved', /UTA Arad · Card Gold/.test(await cardText(page, 'membership', 'UTA')), '');
  await page.click('.mecard[data-kind=membership]:has(h3:text("UTA")) [data-act=delete]');
  check('Delete asks first', !!(await page.$('[data-act=delete-yes]')) && !!(await cardText(page, 'membership', 'UTA')), '');
  await page.click('[data-act=delete-yes]');
  check('Delete removes it', !(await cardText(page, 'membership', 'UTA')) && /Memberships — 2/.test(await page.textContent('#meMemTitle')), '');

  // ---- Card numbers are refused.
  const before = await stored(page);
  for(const [what, v] of [['spaced 16-digit Visa test number', '4111 1111 1111 1111'], ['13-digit number passing Luhn', '4222222222222'],
                          ['19-digit number passing Luhn, with hyphens', '6011-0000-0000-0000-001']]){
    await page.click('button[data-act=add][data-kind=membership]');
    await fill(page, {club: 'Test club', notes: `card ${v}`});
    await page.click('form.meform button[type=submit]');
    const err = await page.textContent('form.meform .meerr');
    check(`A ${what} is refused with a reason`, /Not saved/.test(err) && /payment card number/.test(err), err);
    await page.click('form.meform [data-act=cancel]');
  }
  check('...and nothing was saved', await stored(page) === before, '');
  await page.click('button[data-act=add][data-kind=ticket]');
  await fill(page, {match: 'x', seats: '4111111111111111'});
  await page.click('form.meform button[type=submit]');
  check('A card number in a ticket field (seats) is refused too', /Seats looks like/.test(await page.textContent('form.meform .meerr')), '');
  await page.click('form.meform [data-act=cancel]');
  await add(page, 'membership', {club: 'Luhn fails', notes: 'ref 4111 1111 1111 1112'});
  check('16 digits that fail the Luhn check are accepted', !!(await cardText(page, 'membership', 'Luhn fails')), '');
  await page.click('.mecard[data-kind=membership]:has(h3:text("Luhn fails")) [data-act=delete]'); await page.click('[data-act=delete-yes]');

  // ---- Tickets.
  const opts = await page.evaluate(() => { document.querySelector('button[data-act=add][data-kind=ticket]').click();
    const o = [...document.querySelectorAll('form.meform [name=bucketId] option')].map(o => o.value);
    document.querySelector('form.meform [data-act=cancel]').click(); return o; });
  check('"Link to bucket event" lists every bucket entry by id, plus none', opts[0] === '' &&
    JSON.stringify(opts.slice(1)) === JSON.stringify(rules.bucketList.map(b => b.id)), `${opts.length - 1} options`);
  await add(page, 'ticket', {match: `AC Milan v Inter ${TAG}`, date: '2026-11-01', kickoff: '20:45', venue: 'San Siro', block: '332',
    seats: '12, 13', whoFor: 'Alexandru, Ana', priceAmount: '75', priceCurrency: 'EUR', boughtFrom: 'Inter ticket office',
    status: 'bought', bucketId: LINK_ID});
  await add(page, 'ticket', {match: 'VfB v KSC', date: '2027-01-30', venue: 'MHPArena', status: 'requested'});
  await add(page, 'ticket', {match: 'Old cup tie', date: '2026-09-01', status: 'bought'});
  let milan = await cardText(page, 'ticket', 'AC Milan'), vfbk = await cardText(page, 'ticket', 'VfB v KSC');
  check('A ticket is added with its fields', /Sun,? 1 Nov 2026 · 20:45/.test(milan) && /332/.test(milan) && /12, 13/.test(milan) &&
    /75\.00 EUR/.test(milan) && /bought/.test(milan) && milan.includes(`${linked.title} (${LINK_ID})`), milan);
  check('A ticket with no kick-off says "time not set"', /Sat,? 30 Jan 2027\s*time not set/.test(vfbk), vfbk);
  check('A past ticket goes in a collapsed Past section', await page.$eval('#meTickets details.past', d => !d.open && /Old cup tie/.test(d.textContent)), '');
  await page.click('.mecard[data-kind=ticket]:has(h3:text("VfB v KSC")) [data-act=edit]');
  await fill(page, {status: 'won', alertDays: '3'}); await page.click('form.meform button[type=submit]');
  check('A ticket edit is saved', /won/.test(await cardText(page, 'ticket', 'VfB v KSC')), '');
  await page.evaluate(() => document.querySelector('#meTickets details.past').open = true);
  await page.click('.mecard[data-kind=ticket]:has(h3:text("Old cup tie")) [data-act=delete]'); await page.click('[data-act=delete-yes]');
  check('A ticket is deleted', !(await cardText(page, 'ticket', 'Old cup tie')) && /Tickets held — 2/.test(await page.textContent('#meTixTitle')), '');

  noSideways('No sideways scroll on the Me tab with cards', await sideways(page));
  await page.click('button[data-act=add][data-kind=ticket]');
  noSideways('No sideways scroll with the ticket form open', await sideways(page));
  await page.click('form.meform [data-act=cancel]');
  await page.click('button[data-act=add][data-kind=membership]');
  noSideways('No sideways scroll with the membership form open', await sideways(page));
  await page.click('form.meform [data-act=cancel]');

  // ---- .ics files.
  let f = await download(page, () => page.click('.mecard[data-kind=ticket]:has(h3:text("AC Milan")) [data-act=ics]'));
  let P = parseIcs(f.text);
  check('Match .ics: a valid one-event file with an alarm', !P.problems.length && /\.ics$/.test(f.name), P.problems.join('; ') || f.name);
  check('Match .ics: kick-off as typed, 1 Nov 2026 20:45, no time zone', P.ev.DTSTART.value === '20261101T204500' && !P.ev.DTSTART.params, JSON.stringify(P.ev.DTSTART));
  check('Match .ics: the alarm goes off 1 day before kick-off (the default)', alarmAt(P.ev, P.al) === '2026-10-31T20:45' && P.al.ACTION.value === 'DISPLAY', alarmAt(P.ev, P.al));
  check('Match .ics: a comma in a text value is escaped (seats "12, 13")', P.ev.DESCRIPTION.value.includes('Seats: 12\\, 13'), P.ev.DESCRIPTION.value);
  check('Match .ics: summary and venue as typed', P.ev.SUMMARY.value === `AC Milan v Inter ${TAG}` && P.ev.LOCATION.value === 'San Siro', P.ev.SUMMARY.value);
  f = await download(page, () => page.click('.mecard[data-kind=ticket]:has(h3:text("VfB v KSC")) [data-act=ics]'));
  P = parseIcs(f.text);
  check('No kick-off: a whole-day event on the day typed', !P.problems.length && P.ev.DTSTART.value === '20270130' && /VALUE=DATE/.test(P.ev.DTSTART.params) &&
    P.ev.DTEND?.value === '20270131', P.problems.join('; ') + ' ' + JSON.stringify(P.ev.DTSTART));
  check('A lead time changed to 3 days: the alarm goes off 3 days before, at 09:00', alarmAt(P.ev, P.al) === '2027-01-27T09:00', alarmAt(P.ev, P.al));
  check('...and the summary says the time is not set', /time not set/.test(P.ev.SUMMARY.value), P.ev.SUMMARY.value);
  f = await download(page, () => page.click('.mecard[data-kind=membership]:has(h3:text("VfB Stuttgart")) [data-act=ics]'));
  P = parseIcs(f.text);
  check('Renewal .ics: valid, a whole day on the renewal date', !P.problems.length && P.ev.DTSTART.value === '20261020', P.problems.join('; '));
  check('Renewal .ics: the alarm goes off 14 days before (the default), at 09:00', alarmAt(P.ev, P.al) === '2026-10-06T09:00', alarmAt(P.ev, P.al));
  check('Renewal .ics: line breaks in the description escaped, the long line folded', P.ev.DESCRIPTION.value.includes('\\nCost: 84.00 EUR\\n') &&
    /\r\n /.test(f.text), P.ev.DESCRIPTION.value.slice(0, 60));

  // ---- "You hold tickets" on the linked entry.
  await page.click('nav button[data-pane=bucket]');
  const held = await page.$$eval('#bucketBody details.bucket', ds => ds.filter(d => /You hold tickets/.test(d.querySelector('summary').textContent)).map(d => d.dataset.id));
  check('List: "You hold tickets" on the linked entry and no other', JSON.stringify([...new Set(held)]) === JSON.stringify([LINK_ID]), held.join(','));
  await page.evaluate(id => { const d = document.querySelector(`#bucketBody details.bucket[data-id="${id}"]`); d.open = true; }, LINK_ID);
  await page.waitForFunction(id => !/Loading/.test(document.querySelector(`#bucketBody details.bucket[data-id="${id}"] .tix`).textContent), LINK_ID, {timeout: 15000});
  const det = await page.$eval(`#bucketBody details.bucket[data-id="${LINK_ID}"] .tix`, e => e.querySelector('.heldbox')?.innerText || '');
  check('List: the opened entry lists the ticket held', /You hold tickets/i.test(det) && det.includes(`AC Milan v Inter ${TAG}`) && /bought/.test(det), det.replace(/\s+/g, ' '));
  await page.click('#tabCal');
  await page.click('[data-cal=next]');
  const cell = await page.$eval('.cday[data-date="2026-11-01"]', c => ({mark: !!c.querySelector('.mheld'), label: c.getAttribute('aria-label')}));
  check('Calendar: the day cell is marked, and its label says you hold tickets', cell.mark && /you hold tickets/.test(cell.label), cell.label);
  const otherMarks = await page.$$eval('.cday .mheld', ms => ms.map(m => m.closest('.cday').dataset.date));
  check('...and no other day in November is', JSON.stringify(otherMarks) === '["2026-11-01"]', otherMarks.join(','));
  await page.click('.cday[data-date="2026-11-01"]');
  const item = await page.$eval(`#calDay .calitem[data-open="entry:${LINK_ID}"]`, b => b.textContent);
  check('Calendar: the entry\'s item says "You hold tickets"', /You hold tickets/.test(item), item);
  await page.click(`#calDay .calitem[data-open="entry:${LINK_ID}"]`);
  await page.waitForFunction(() => !document.getElementById('bsheet').hidden && !/Loading/.test(document.getElementById('bsheetBody').textContent), null, {timeout: 15000});
  const sh = await page.evaluate(() => ({head: document.getElementById('bsheetHead').textContent, box: document.querySelector('#bsheetBody .heldbox')?.textContent || ''}));
  check('Sheet: the header and the body say "You hold tickets"', /You hold tickets/.test(sh.head) && sh.box.includes(`AC Milan v Inter ${TAG}`), sh.head);
  await page.click('#bsheetClose');
  await page.click('#tabList');

  // ---- Reload: everything is still there.
  const snap = await stored(page);
  await page.reload();
  await page.waitForFunction(() => document.querySelector('#bucketBody details.bucket'), null, {timeout: 30000});
  await page.click('nav button[data-pane=me]'); await page.click('#meTabTix');
  check('After a reload: both memberships and both tickets are back', await stored(page) === snap &&
    /Memberships — 2/.test(await page.textContent('#meMemTitle')) && /Tickets held — 2/.test(await page.textContent('#meTixTitle')) &&
    /Renewal due in 16 days/.test(await cardText(page, 'membership', 'VfB')), '');
  check('...and the backup banner is still up, nothing having been exported', !(await page.$eval('#meBackup', e => e.hidden)), '');
  await page.click('nav button[data-pane=bucket]');
  check('...and "You hold tickets" is still on the entry', /You hold tickets/.test(await page.$eval(`#bucketBody details.bucket[data-id="${LINK_ID}"] summary`, s => s.textContent)), '');

  // ---- Export, delete everything, import.
  await page.click(`#bucketBody details.bucket[data-id="el-final-2027"] .star`);
  await page.click('nav button[data-pane=me]'); await page.click('#meTabTix');
  let exp = await download(page, () => page.click('#meExport'));
  const file = JSON.parse(exp.text);
  check('Export: one JSON file with a format and a version number', file.format === 'football-planner-me' && file.version === 1 && /\.json$/.test(exp.name), exp.name);
  check('Export: it holds the memberships, tickets and favorites', file.memberships.length === 2 && file.tickets.length === 2 &&
    JSON.stringify(file.favorites) === '["el-final-2027"]', JSON.stringify({m: file.memberships.length, t: file.tickets.length, f: file.favorites}));
  check('The backup banner goes after an export', await page.$eval('#meBackup', e => e.hidden), '');
  await page.click('nav button[data-pane=bucket]');
  await page.click(`#bucketBody details.bucket[data-id="poli-uta"] .star`);
  await page.click('nav button[data-pane=me]'); await page.click('#meTabTix');
  check('A star is an edit too: the banner is back', !(await page.$eval('#meBackup', e => e.hidden)), '');
  for(const kind of ['membership', 'ticket']){
    while(await page.$(`.mecard[data-kind=${kind}] [data-act=delete]`)){
      await page.click(`.mecard[data-kind=${kind}] [data-act=delete]`); await page.click('[data-act=delete-yes]');
    }
  }
  check('Everything deleted', /Memberships — 0/.test(await page.textContent('#meMemTitle')) && /Tickets held — 0/.test(await page.textContent('#meTixTitle')), '');
  const exportPath = path.join(require('os').tmpdir(), `me-export-${TAG}.json`);
  fs.writeFileSync(exportPath, exp.text);
  await page.setInputFiles('#meFile', exportPath);
  await page.waitForSelector('#meConfirm');
  const conf = await page.textContent('#meConfirm');
  check('Import first says what the file holds and what it replaces', /holds 2 memberships, 2 tickets and 1 favorite/.test(conf) &&
    /replaces the 0 memberships, 0 tickets and 2 favorites/.test(conf), conf);
  await page.click('[data-act=import-yes]');
  const msg = await page.textContent('#meMsg');
  check('Import says clearly what was imported', /Imported 2 memberships, 2 tickets and 1 favorite from me-export-/.test(msg), msg);
  const back = JSON.parse(await stored(page));
  check('Round trip: memberships and tickets exactly as exported', JSON.stringify(back.memberships) === JSON.stringify(file.memberships) &&
    JSON.stringify(back.tickets) === JSON.stringify(file.tickets), '');
  check('Round trip: favorites exactly as exported', await page.evaluate(() => localStorage.getItem('football-planner-favorites')) === '["el-final-2027"]', '');
  check('After an import the banner is down (the device holds what the file holds)', await page.$eval('#meBackup', e => e.hidden), '');
  await page.click('nav button[data-pane=bucket]');
  const stars = await page.$$eval('#bucketBody .star[aria-pressed=true]', s => [...new Set(s.map(x => x.dataset.fav))]);
  check('...and the bucket list shows the imported favorite and the held tickets again', JSON.stringify(stars) === '["el-final-2027"]' &&
    /You hold tickets/.test(await page.$eval(`#bucketBody details.bucket[data-id="${LINK_ID}"] summary`, s => s.textContent)), stars.join(','));
  await page.click('nav button[data-pane=me]'); await page.click('#meTabTix');

  // ---- Broken imports are refused, nothing changed.
  const good = JSON.parse(exp.text);
  const broken = [
    ['not JSON', '{"format": "football-planner-me", '],
    ['another app\'s file (a saved-routes export)', JSON.stringify({format: 'football-planner-saved-routes', version: 1, routes: []})],
    ['a newer version', JSON.stringify(Object.assign({}, good, {version: 2}))],
    ['a ticket with no status', JSON.stringify(Object.assign({}, good, {tickets: [Object.assign({}, good.tickets[0], {status: undefined})]}))],
    ['a card number in a membership note', JSON.stringify(Object.assign({}, good, {memberships: [Object.assign({}, good.memberships[0], {notes: 'pay 4111111111111111'})]}))],
    ['the same id twice', JSON.stringify(Object.assign({}, good, {tickets: [good.tickets[0], good.tickets[0]]}))],
    ['no tickets list', JSON.stringify(Object.assign({}, good, {tickets: undefined}))],
  ];
  const keep = {me: await stored(page), fav: await page.evaluate(() => localStorage.getItem('football-planner-favorites'))};
  for(const [what, text] of broken){
    const p = path.join(require('os').tmpdir(), `me-broken-${TAG}.json`);
    fs.writeFileSync(p, text);
    await page.setInputFiles('#meFile', []);
    await page.setInputFiles('#meFile', p);
    await page.waitForFunction(() => /Not imported/.test(document.getElementById('meMsg')?.textContent || ''), null, {timeout: 5000}).catch(() => {});
    const m = (await page.$('#meMsg')) ? await page.textContent('#meMsg') : '';
    const same = await stored(page) === keep.me && await page.evaluate(() => localStorage.getItem('football-planner-favorites')) === keep.fav;
    check(`A broken import is refused (${what}) and the device is unchanged`, /Not imported/.test(m) && /Nothing on this device was changed/.test(m) && same &&
      !(await page.$('#meConfirm')), m);
    fs.unlinkSync(p);
  }
  fs.unlinkSync(exportPath);

  // ---- Nothing leaves the device.
  const leaked = requests.filter(r => (r.url + r.body + r.headers).includes(TAG));
  check('Nothing typed on the tab is in any network request (URL, headers or body)', !leaked.length, `${requests.length} requests; ${leaked.map(r => r.url).join(', ')}`);
  check('No request other than GET reached the site', !nonGet.length && !requests.some(r => !['GET', 'HEAD'].includes(r.method) && r.url.startsWith(BASE)), nonGet.join(', '));
  const where = await page.evaluate(async tag => {
    const ls = Object.keys(localStorage).filter(k => localStorage.getItem(k).includes(tag));
    const ss = Object.keys(sessionStorage).length;
    const idb = indexedDB.databases ? (await indexedDB.databases()).map(d => d.name) : [];
    return {ls, ss, cookie: document.cookie, idb, url: location.href};
  }, TAG);
  check('Kept only in this browser\'s localStorage under the Me key: no cookie, no sessionStorage, not in the URL',
    JSON.stringify(where.ls) === '["football-planner-me"]' && !where.ss && !where.cookie && !where.url.includes(TAG), JSON.stringify(where));
  check('Not in IndexedDB (saved routes are untouched)', !where.idb.includes('football-planner-me'), where.idb.join(','));
  let inRepo = '';
  try{ inRepo = execSync(`git -C "${ROOT}" grep -l "${TAG}"`, {encoding: 'utf8'}).trim(); }catch(err){ inRepo = ''; }
  check('Nothing typed on the tab is in the repository', !inRepo, inRepo);
  await ctx.close();

  // ---- Storage blocked.
  const ctx2 = await newCtx({blockStorage: true});
  const page2 = await openMe(ctx2);
  check('Storage blocked: the tab says what you add lasts only for this visit', /lasts only until the page is closed/.test(await page2.textContent('#meBody')), '');
  await add(page2, 'membership', {club: `Blocked club ${TAG}`, renewal: '2026-10-10'});
  check('Storage blocked: a membership can still be added for the visit', /Renewal due in 6 days/.test(await cardText(page2, 'membership', 'Blocked club') || ''), '');
  await add(page2, 'ticket', {match: 'Blocked match', date: '2026-11-01', status: 'won', bucketId: LINK_ID});
  await page2.click('nav button[data-pane=bucket]');
  check('Storage blocked: the bucket list still shows "You hold tickets"', /You hold tickets/.test(await page2.$eval(`#bucketBody details.bucket[data-id="${LINK_ID}"] summary`, s => s.textContent)), '');
  await ctx2.close();


  // ---- Attended matches and events: the first three sub-tabs, from data/attended.json.
  const ATTF = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/attended.json'), 'utf8'));
  const fx = {
    n: ATTF.matches.length, ne: ATTF.events.length,
    goals: ATTF.matches.reduce((n, m) => n + m.goals.length, 0),
    pens: ATTF.matches.reduce((n, m) => n + m.goals.filter(g => g.pen).length, 0),
    stadiums: new Set(ATTF.matches.map(m => m.stadium)).size,
    yellow: ATTF.matches.filter(m => m.cardsComplete).reduce((n, m) => n + m.cards.filter(c => c.type === 'yellow').length, 0),
    red: ATTF.matches.filter(m => m.cardsComplete).reduce((n, m) => n + m.cards.filter(c => c.type !== 'yellow').length, 0),
    cities: new Set(ATTF.matches.map(m => m.city.en)).size,
    countries: new Set(ATTF.matches.map(m => m.country.en)).size,
    comps: new Set(ATTF.matches.map(m => (m.competitionKey || m.competition).en)).size,
    big: Math.max(...ATTF.matches.map(m => m.attendance && m.attendance.value || 0)),
    small: Math.min(...ATTF.matches.filter(m => m.attendance && m.attendance.value).map(m => m.attendance.value))
  };
  const attOrder = ATTF.matches.map((m, i) => [m, i]).sort((a, b) => a[0].date < b[0].date ? -1 : a[0].date > b[0].date ? 1 : a[1] - b[1]).map(x => x[0]);

  const reqs3 = [];
  const ctx3 = await newCtx();
  await ctx3.addInitScript(() => {            // every localStorage read, to show the new sub-tabs read none
    window.__reads = []; window.__writes = [];
    const g = Storage.prototype.getItem, w = Storage.prototype.setItem;
    Storage.prototype.getItem = function(k){ window.__reads.push(k); return g.call(this, k); };
    Storage.prototype.setItem = function(k, v){ window.__writes.push(k); return w.call(this, k, v); };
    try{ w.call(localStorage, 'mf_personal', JSON.stringify({'*': {note: 'OLDAPPNOTE'}})); }catch(e){}   // the old app's key: must never be read
  });
  const p3 = await ctx3.newPage();
  p3.on('pageerror', e => errors.push(e.message));
  p3.on('request', r => reqs3.push(r.url()));
  await p3.goto(BASE);
  await p3.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await p3.waitForFunction(() => document.querySelector('#bucketBody details.bucket'), null, {timeout: 15000});
  const attReqs = () => reqs3.filter(u => u.includes('attended.json')).length;
  check('data/attended.json is not requested before a Me sub-tab is opened', attReqs() === 0, String(attReqs()));
  await p3.evaluate(() => { window.__reads.length = 0; });
  await p3.click('nav button[data-pane=me]');
  await p3.waitForSelector('#meStats .astat');
  check('Opening the Me tab opens Stats first and requests the file once', attReqs() === 1 &&
    await p3.$eval('#meTabStats', b => b.getAttribute('aria-selected')) === 'true', String(attReqs()));

  const subs = await p3.evaluate(() => {
    const bs = [...document.querySelectorAll('#meSubs button')];
    return {labels: bs.map(b => b.textContent.trim()), roles: bs.map(b => b.getAttribute('role')),
      bad: bs.filter(b => { const r = b.getBoundingClientRect(); return b.scrollWidth > b.clientWidth + 1 || r.right > innerWidth + 1 || r.left < -1 || r.height < 40; }).map(b => b.textContent),
      lines: bs.map(b => { const r = document.createRange(); r.selectNodeContents(b); return new Set([...r.getClientRects()].map(x => Math.round(x.top))).size; })};
  });
  check('Four sub-tabs in order: Stats, Matches, Events, Tickets', JSON.stringify(subs.labels) === '["Stats","Matches","Events","Tickets"]', subs.labels.join(' | '));
  check('The four sub-tabs fit at 390 px: none cut off or off screen, none wrapped, each at least 40 px tall', !subs.bad.length && subs.lines.every(n => n === 1), JSON.stringify(subs));

  const tiles = await p3.$$eval('#meStats .astat', ts => ts.map(t => [t.querySelector('b').textContent.replace(/[^\d]/g, ''), t.querySelector('span').textContent]));
  const tv = tiles.map(t => +t[0]);
  check('Stats: matches, goals, penalties, stadiums, yellow and red cards equal the counts in the file',
    JSON.stringify(tv) === JSON.stringify([fx.n, fx.goals, fx.pens, fx.stadiums, fx.yellow, fx.red]), JSON.stringify(tv) + ' file ' + JSON.stringify([fx.n, fx.goals, fx.pens, fx.stadiums, fx.yellow, fx.red]));
  const lists = await p3.evaluate(() => {
    const out = {};
    document.querySelectorAll('#meStats .aeye').forEach(h => {
      const rows = []; let n = h.nextElementSibling;
      while(n && !n.classList.contains('aeye')){ if(n.classList.contains('arow')) rows.push([n.querySelector('.k').textContent, n.querySelector('.v')?.textContent || '']); n = n.nextElementSibling; }
      out[h.textContent] = rows;
    });
    return out;
  });
  const sum = rows => rows.reduce((n, r) => n + (+r[1].replace(/\D/g, '') || 0), 0);
  check('Stats: the stadium, city, country and competition lists have the file\'s distinct counts, each summing to the match count',
    lists.Stadiums.length === fx.stadiums && lists.Cities.length === fx.cities && lists.Countries.length === fx.countries && lists.Competitions.length === fx.comps &&
    [lists.Stadiums, lists.Cities, lists.Countries, lists.Competitions].every(r => sum(r) === fx.n),
    [lists.Stadiums.length, lists.Cities.length, lists.Countries.length, lists.Competitions.length].join(','));
  check('Stats: biggest and smallest crowd are the file\'s largest and smallest figures',
    lists['Biggest crowd'].every(r => +r[1].replace(/\D/g, '') === fx.big) && lists['Smallest crowd'].every(r => +r[1].replace(/\D/g, '') === fx.small),
    JSON.stringify([lists['Biggest crowd'], lists['Smallest crowd'], fx.big, fx.small]));
  check('Stats: a most-seen team is named', lists['Most-seen team'].length >= 1 && +lists['Most-seen team'][0][1] >= 2, JSON.stringify(lists['Most-seen team']));
  noSideways('Stats: no sideways scroll at 390 px', await sideways(p3));

  await p3.click('#meTabMatches');
  await p3.waitForSelector('#meMatches .acard');
  const mcards = await p3.$$eval('#meMatches .acard', cs => cs.map(c => ({id: c.dataset.id, n: c.querySelector('.an').textContent, text: c.innerText.replace(/\s+/g, ' ')})));
  check('Matches: one card per match in the file', mcards.length === fx.n && new Set(mcards.map(c => c.id)).size === fx.n, `${mcards.length} of ${fx.n}`);
  check('Matches: oldest first by date, the same date in the file\'s order, numbered 1..n',
    JSON.stringify(mcards.map(c => c.id)) === JSON.stringify(attOrder.map(m => m.id)) && mcards.every((c, i) => c.n === String(i + 1)), mcards.map(c => c.id).join(' ').slice(0, 120));
  const missingText = [];
  ATTF.matches.forEach(m => {
    const c = mcards.find(x => x.id === m.id);
    const need = [(m.home.nameEn || m.home.name), (m.away.nameEn || m.away.name), m.score, m.competition.en, m.stage.en, m.stadium, m.city.en, new Date(m.date + 'T12:00:00').getFullYear() + ''];
    if(!c || need.some(x => !c.text.includes(x))) missingText.push(m.id);
  });
  check('Matches: every card shows teams, score, competition, stage, stadium, city and the date', !missingText.length, missingText.join(', '));
  noSideways('Matches: no sideways scroll at 390 px', await sideways(p3));

  await p3.click('#meTabEvents');
  await p3.waitForSelector('#meEvents .acard');
  const ecards = await p3.$$eval('#meEvents .acard', cs => cs.map(c => ({id: c.dataset.id, text: c.innerText.replace(/\s+/g, ' ')})));
  check('Events: one card per event, in the file\'s order', JSON.stringify(ecards.map(c => c.id)) === JSON.stringify(ATTF.events.map(e => e.id)), `${ecards.length} of ${fx.ne}`);
  check('Events: every card shows its title, place and date', ATTF.events.every((e, i) => ecards[i] && ecards[i].text.includes(e.title.en) && ecards[i].text.includes(e.place.en) &&
    ecards[i].text.includes(String(new Date(e.date + 'T12:00:00').getFullYear()))), '');
  noSideways('Events: no sideways scroll at 390 px', await sideways(p3));
  check('The file was requested once for all three sub-tabs', attReqs() === 1, String(attReqs()));
  check('The three sub-tabs read nothing from browser storage', (await p3.evaluate(() => window.__reads)).length === 0, JSON.stringify(await p3.evaluate(() => window.__reads)));

  // Every entry opens the header sheet.
  const sheetBad = [];
  async function tapAll(sub, tabId, entries, need){
    await p3.click(tabId);
    for(const e of entries){
      await p3.click(`#${sub} .acard[data-id="${e.id}"]`);
      await p3.waitForTimeout(350);               // the sheet's slide-in
      const r = await p3.evaluate(() => {
        const s = document.getElementById('asheet'), rc = s.getBoundingClientRect(), nav = document.querySelector('nav').getBoundingClientRect();
        return {hidden: s.hidden, text: s.innerText.replace(/\s+/g, ' '), right: rc.right, left: rc.left, bottom: rc.bottom, navTop: nav.top,
          body: document.getElementById('asheetBody').scrollWidth <= document.getElementById('asheetBody').clientWidth + 1};
      });
      if(r.hidden || need(e).some(x => !r.text.includes(x)) || r.right > W + 1 || r.left < -1 || r.bottom > r.navTop + 1 || !r.body) sheetBad.push(e.id + ' ' + JSON.stringify(r).slice(0, 200));
      await p3.click('#asheetClose');
      if(!(await p3.$eval('#asheet', s => s.hidden))) sheetBad.push(e.id + ' did not close');
    }
  }
  await tapAll('meMatches', '#meTabMatches', ATTF.matches, m => [m.home.nameEn || m.home.name, m.away.nameEn || m.away.name, m.score, m.competition.en, m.stage.en, m.stadium, m.city.en, m.country.en]);
  await tapAll('meEvents', '#meTabEvents', ATTF.events, e => [e.title.en, e.place.en]);
  check(`Tapping any of the ${fx.n} matches and ${fx.ne} events opens the header sheet above the bottom bar, inside 390 px, and Close shuts it`, !sheetBad.length, sheetBad.slice(0, 2).join(' | '));
  await p3.click('#meTabMatches'); await p3.click('#meMatches .acard');
  await p3.click('nav button[data-pane=bucket]');
  check('Leaving the Me tab shuts the sheet', await p3.$eval('#asheet', s => s.hidden), '');
  await p3.click('nav button[data-pane=me]');
  check('The Me tab reopens on the sub-tab that was open', await p3.$eval('#meTabMatches', b => b.getAttribute('aria-selected')) === 'true', '');
  await p3.click('#meTabMatches');


  // ---- The full detail sheet (2026-10-09): line-ups with the pitch, timeline, stats, factual note, personal fields.
  const hasSide = (m, s) => !!(m.lineups && m.lineups[s]);
  const pitchOk = lu => !!(lu && typeof lu.formation === 'string' && Array.isArray(lu.xi) && lu.xi.length === 11 &&
    lu.formation.split('-').map(Number).every(n => Number.isInteger(n) && n > 0) && lu.formation.split('-').map(Number).reduce((a, b) => a + b, 0) === 10);
  const nm = tm => tm.nameEn || tm.name;
  const STAT_KEYS = ['possession', 'shots', 'onTarget', 'fouls', 'corners', 'offsides'];
  const expectedTimeline = m => {
    const ev = [];
    m.goals.forEach(g => ev.push([g.minute, g.added || 0, `${g.minute}${g.added ? '+' + g.added : ''}'`]));
    m.cards.forEach(c => ev.push([c.minute == null ? -1 : c.minute, c.added || 0, c.minute == null ? '—' : `${c.minute}${c.added ? '+' + c.added : ''}'`]));
    if(m.lineups) ['home', 'away'].forEach(sd => { if(m.lineups[sd]) (m.lineups[sd].subs || []).forEach(x => ev.push([x.minute, 0, `${x.minute}'`])); });
    return ev.sort((a, b) => (a[0] - b[0]) || (a[1] - b[1])).map(e => e[2]);
  };
  const sheetState = pg => pg.evaluate(() => {
    const b = document.getElementById('asheetBody'), sh = document.getElementById('asheet'), rc = sh.getBoundingClientRect(), nav = document.querySelector('nav').getBoundingClientRect();
    const svg = b.querySelector('svg.apitch'), sr = svg && svg.getBoundingClientRect();
    const texts = svg ? [...svg.querySelectorAll('text')].map(x => x.getBBox()) : [];
    const names = svg ? [...svg.querySelectorAll('text.nm')].map(x => x.getBBox()) : [];
    let overlap = 0;
    for(let i = 0; i < names.length; i++) for(let j = i + 1; j < names.length; j++){
      const a = names[i], c = names[j];
      if(a.x < c.x + c.width - .5 && c.x < a.x + a.width - .5 && a.y < c.y + c.height - .5 && c.y < a.y + a.height - .5) overlap++;
    }
    const empty = [...b.querySelectorAll('h4')].filter(h => { const n = h.nextElementSibling; return !n || n.tagName === 'H4' || !n.textContent.trim(); }).map(h => h.textContent);
    return {hidden: sh.hidden, h4: [...b.querySelectorAll('h4')].map(h => h.textContent),
      fits: b.scrollWidth <= b.clientWidth + 1 && rc.right <= innerWidth + 1 && rc.left >= -1 && rc.bottom <= nav.top + 1 && document.documentElement.scrollWidth <= innerWidth + 1,
      svgIn: !svg || (sr.left >= -0.5 && sr.right <= innerWidth + .5 && sr.width <= b.clientWidth + 1),
      svgTextOut: texts.filter(x => x.x < 0 || x.y < 0 || x.x + x.width > 300 || x.y + x.height > 400).length, overlap, empty,
      pitchNames: svg ? [...svg.querySelectorAll('g.aplr')].map(g => g.dataset.name) : [],
      listNames: [...b.querySelectorAll('#aluSide .alist:not(:has(.aev)) .arow .k')].map(x => x.textContent.replace(' (C)', '')),
      switchBtns: [...b.querySelectorAll('button[data-side]')].map(x => [x.textContent, x.getAttribute('aria-pressed')]),
      coach: (b.querySelector('.acoach') || {}).textContent || '',
      tlMin: [...b.querySelectorAll('#aTimeline .aev .m')].map(x => x.textContent),
      tlAway: [...b.querySelectorAll('#aTimeline .aev')].map(x => x.classList.contains('away')),
      statRows: b.querySelectorAll('#aStats .abar').length, statsPane: !!b.querySelector('#aStats'),
      note: (b.querySelector('.afact') || {}).textContent || '', unv: [...b.querySelectorAll('.aunv')].map(x => x.textContent),
      text: b.innerText.replace(/\s+/g, ' '), pf: [...b.querySelectorAll('[data-pf]')].map(x => x.dataset.pf)};
  });
  const openEntry = async (pg, sub, tab, id) => {
    await pg.click(tab); await pg.click(`#${sub} .acard[data-id="${id}"]`); await pg.waitForTimeout(350);
  };
  const detailBad = [], detailNote = [];
  let nPitch = 0;
  for(const m of ATTF.matches){
    await openEntry(p3, 'meMatches', '#meTabMatches', m.id);
    const st = await sheetState(p3);
    const bad = x => detailBad.push(m.id + ': ' + x);
    const sides = ['home', 'away'].filter(sd => hasSide(m, sd));
    if(st.hidden) bad('sheet did not open');
    if(!st.fits) bad('overflows 390 px or the bottom bar');
    if(!st.svgIn || st.svgTextOut || st.overlap) bad(`pitch: inside=${st.svgIn} textOut=${st.svgTextOut} overlap=${st.overlap}`);
    if(st.empty.length) bad('empty pane ' + st.empty.join(','));
    if(st.h4.includes('Line-ups') !== (sides.length > 0)) bad('line-ups pane presence');
    if(st.h4.includes('Timeline') !== (expectedTimeline(m).length > 0)) bad('timeline pane presence');
    if(st.h4.includes('Stats') !== !!m.stats || st.statsPane !== !!m.stats) bad('stats pane presence');
    if(m.stats && st.statRows !== STAT_KEYS.filter(k => m.stats[k]).length) bad('stat rows ' + st.statRows);
    if(st.h4.includes('Factual note') !== !!m.note) bad('note pane presence');
    if(m.note && (!st.unv.includes('Written by an assistant from memory, not yet verified') || st.note !== m.note.en)) bad('note text or label');
    if(JSON.stringify(st.tlMin) !== JSON.stringify(expectedTimeline(m))) bad('timeline order ' + st.tlMin.join(' ') + ' vs ' + expectedTimeline(m).join(' '));
    if(!st.pf.includes('note') || !st.pf.includes('ticket') || !st.pf.includes('seat') || !st.pf.includes('block') || !st.pf.includes('withWho')) bad('personal fields ' + st.pf);
    if(sides.length === 2){
      if(JSON.stringify(st.switchBtns) !== JSON.stringify([[nm(m.home), 'true'], [nm(m.away), 'false']])) bad('switch ' + JSON.stringify(st.switchBtns));
    }else if(st.switchBtns.length) bad('a switch with one side');
    for(const sd of sides){
      if(sides.length === 2 && sd === 'away'){ await p3.click('button[data-side="away"]'); }
      const s2 = await sheetState(p3), lu = m.lineups[sd];
      const names = lu.xi.map(p => p.name);
      if(sides.length === 2 && s2.switchBtns[sd === 'home' ? 0 : 1][1] !== 'true') bad(sd + ' button not pressed');
      if(!s2.coach.includes(lu.coach || 'not recorded')) bad(sd + ' coach');
      if(pitchOk(lu)){
        nPitch++;
        if(JSON.stringify(s2.pitchNames) !== JSON.stringify(names)) bad(sd + ' pitch players');
        if(!s2.text.includes(lu.formation)) bad(sd + ' formation label');
      }else if(s2.pitchNames.length || JSON.stringify(s2.listNames.slice(0, 11)) !== JSON.stringify(names)) bad(sd + ' list without pitch');
      for(const p of (lu.bench || [])) if(!s2.text.includes(p.name)) bad(sd + ' bench ' + p.name);
      for(const x of (lu.subs || [])) if(!s2.text.includes(x.on) || !s2.text.includes(x.off)) bad(sd + ' sub ' + x.on);
      if(!s2.fits || !s2.svgIn || s2.svgTextOut || s2.overlap) bad(sd + ' side overflows: ' + JSON.stringify({f: s2.fits, i: s2.svgIn, o: s2.svgTextOut, v: s2.overlap}));
    }
    if(sides.length === 2){ await p3.click('button[data-side="home"]'); const s3 = await sheetState(p3); if(s3.switchBtns[0][1] !== 'true') bad('switch back to home'); }
    await p3.click('#asheetClose');
  }
  const nLU = ATTF.matches.filter(m => hasSide(m, 'home') || hasSide(m, 'away')).length;
  const nFormations = ATTF.matches.reduce((n, m) => n + ['home', 'away'].filter(sd => m.lineups && m.lineups[sd] && m.lineups[sd].formation).length, 0);
  console.log(`   (file: ${ATTF.matches.length} matches, ${nLU} with line-ups, ${nFormations} team formations, ${ATTF.matches.filter(m => m.stats).length} with stats, ${nPitch} pitches drawn)`);
  check(`Every one of the ${ATTF.matches.length} match sheets: line-ups only where the file has them, home side first and selected with a working switch, coach/bench/substitutions listed, pitch players equal the starting eleven`,
    !detailBad.length, detailBad.slice(0, 3).join(' | '));
  check('Match sheets: the timeline lists goals, cards and substitutions in minute order (stoppage time after its minute, a card with no minute first), as worked out from the file',
    !detailBad.some(x => /timeline/.test(x)), '');
  check('Match sheets: the stats pane appears only for matches with a stats block; no pane is ever empty; the factual note carries the "Written by an assistant from memory, not yet verified" label',
    !detailBad.some(x => /stats|empty|note/.test(x)), '');
  const noLUm = ATTF.matches.find(m => !m.lineups && !m.stats);
  if(noLUm){
    await openEntry(p3, 'meMatches', '#meTabMatches', noLUm.id);
    const st = await sheetState(p3);
    check('A match with no line-ups shows no line-ups pane, no switch and no empty heading', !st.h4.includes('Line-ups') && !st.switchBtns.length && !st.empty.length && !/Line-ups/.test(st.text), JSON.stringify(st.h4));
    await p3.click('#asheetClose');
  }else detailNote.push('no match without line-ups and stats');
  check('Every sheet drew pitches (one per team with a consistent formation), none with text outside the pitch, none with overlapping names, nothing wider than 390 px', nPitch > 0 && !detailBad.some(x => /pitch|overflow/.test(x)), String(nPitch));

  // Events: title, place, what, why, atStadium, personal fields.
  const evBad = [];
  for(const e of ATTF.events){
    await openEntry(p3, 'meEvents', '#meTabEvents', e.id);
    const st = await sheetState(p3);
    const head = await p3.$eval('#asheetHead', h => h.textContent);
    if(!head.includes(e.title.en)) evBad.push(e.id + ' title');
    const need = [e.place.en, e.what.en, 'What it was'].concat(e.why ? [e.why.en, 'Why it mattered'] : []);
    if(st.hidden || need.some(x => !st.text.toLowerCase().includes(x.toLowerCase()))) evBad.push(e.id + ' content ' + need.filter(x => !st.text.toLowerCase().includes(x.toLowerCase())).join('/'));
    if(!new RegExp('At the stadium ' + (e.atStadium ? 'yes' : 'no'), 'i').test(st.text)) evBad.push(e.id + ' atStadium flag');
    const want = e.atStadium ? ['note', 'ticket', 'seat', 'block', 'withWho'] : ['note', 'withWho'];
    if(JSON.stringify(st.pf) !== JSON.stringify(want)) evBad.push(e.id + ' personal fields ' + st.pf);
    if(!st.fits || st.empty.length) evBad.push(e.id + ' fit/empty');
    if(st.unv.length !== 1 + (e.why ? 1 : 0)) evBad.push(e.id + ' unverified labels');
    await p3.click('#asheetClose');
  }
  check(`All ${ATTF.events.length} events open their sheet: title, place, what, why, the atStadium flag, ticket/seat/block only where atStadium, and the unverified label`, !evBad.length, evBad.slice(0, 3).join(' | '));

  // Personal fields: this device only, under football-attended-personal, never an mf_ key.
  const PK = 'football-attended-personal';
  const pm = ATTF.matches[0], pe = ATTF.events.find(e => e.atStadium);
  await openEntry(p3, 'meMatches', '#meTabMatches', pm.id);
  check('The old app\'s mf_personal key is not read: a seeded note there is not shown', !(await sheetState(p3)).text.includes('OLDAPPNOTE'), '');
  const vals = {note: 'Cold night ' + TAG, ticket: 'T-' + TAG, seat: 'Row 7 ' + TAG, block: 'Block 12 ' + TAG, withWho: 'Ana and Radu ' + TAG};
  for(const k of Object.keys(vals)) await p3.fill(`#asheetBody [data-pf="${k}"]`, vals[k]);
  const persStored = async () => JSON.parse(await p3.evaluate(k => localStorage.getItem(k), PK) || 'null');
  check('Editing the personal fields saves under football-attended-personal, keyed by entry id, with the old shape (note, ticket, seat, block, withWho)',
    JSON.stringify((await persStored())[pm.id]) === JSON.stringify(vals), JSON.stringify(await persStored()));
  await openEntry(p3, 'meEvents', '#meTabEvents', pe.id);
  await p3.fill('#asheetBody [data-pf="withWho"]', 'Friends ' + TAG); await p3.fill('#asheetBody [data-pf="ticket"]', 'E-' + TAG);
  await p3.click('#asheetClose');
  check('An event\'s personal fields are kept under its own id beside the match\'s', (await persStored())[pe.id].withWho === 'Friends ' + TAG && (await persStored())[pm.id].note === vals.note, JSON.stringify(Object.keys(await persStored())));
  await p3.reload();
  await p3.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await p3.click('nav button[data-pane=me]'); await p3.waitForSelector('#meStats .astat');
  await openEntry(p3, 'meMatches', '#meTabMatches', pm.id);
  const persBack = await p3.evaluate(() => Object.fromEntries([...document.querySelectorAll('#asheetBody [data-pf]')].map(x => [x.dataset.pf, x.value])));
  check('The personal fields are still there after a reload', JSON.stringify(persBack) === JSON.stringify(vals), JSON.stringify(persBack));
  // Card numbers are refused on ticket, seat, block and who I went with; digits failing Luhn are kept.
  const cardBad = [];
  for(const k of ['ticket', 'seat', 'block', 'withWho']){
    const before = (await persStored())[pm.id][k];
    await p3.fill(`#asheetBody [data-pf="${k}"]`, 'card 4111 1111 1111 1111 ok');
    const r = await p3.evaluate(kk => ({err: document.querySelector(`#asheetBody [data-err="${kk}"]`).textContent, inv: document.querySelector(`#asheetBody [data-pf="${kk}"]`).getAttribute('aria-invalid')}), k);
    if(!/payment card number/.test(r.err) || r.inv !== 'true' || (await persStored())[pm.id][k] !== before) cardBad.push(k + ' ' + JSON.stringify(r));
    await p3.fill(`#asheetBody [data-pf="${k}"]`, 'ref 4111 1111 1111 1112');
    if((await persStored())[pm.id][k] !== 'ref 4111 1111 1111 1112' || await p3.$eval(`#asheetBody [data-err="${k}"]`, x => x.textContent)) cardBad.push(k + ' non-card refused');
  }
  check('A payment card number (Luhn) is refused on Ticket, Seat, Block and Who I went with, nothing saved, reason shown; digits failing Luhn are kept', !cardBad.length, cardBad.join(' | '));
  const stReads = await p3.evaluate(() => window.__reads), stWrites = await p3.evaluate(() => window.__writes);
  check('Every storage read the page made is recorded, and none is an mf_ key; football-attended-personal was read',
    stReads.length > 0 && !stReads.some(k => String(k).startsWith("mf_")) && stReads.includes(PK), [...new Set(stReads)].join(','));
  check('Every storage write is recorded, and none is an mf_ key (only football-attended-personal and the language on these sheets)',
    !stWrites.some(k => String(k).startsWith("mf_")) && stWrites.includes(PK), [...new Set(stWrites)].join(','));
  const idb = await p3.evaluate(async () => indexedDB.databases ? (await indexedDB.databases()).map(d => d.name) : []);
  check('IndexedDB mf_media is not touched or created', !idb.includes('mf_media'), idb.join(','));
  const lsKeys = await p3.evaluate(() => Object.keys(localStorage).filter(k => k.startsWith('mf_')));
  check('The only mf_ key in storage is the one this test seeded, unchanged', JSON.stringify(lsKeys) === '["mf_personal"]' && await p3.evaluate(() => localStorage.getItem('mf_personal')) === JSON.stringify({'*': {note: 'OLDAPPNOTE'}}), lsKeys.join(','));
  check('Nothing typed is in a cookie or sessionStorage', await p3.evaluate(tag => !document.cookie.includes(tag) && !JSON.stringify(Object.assign({}, sessionStorage)).includes(tag), TAG), '');
  await p3.click('#asheetClose');
  const dictKeys = await p3.evaluate(ks => ks.filter(k => !I18N.en[k] || !I18N.ro[k]), STAT_KEYS.map(k => 'sx.' + k).concat(['pf.note', 'pf.ticket', 'pf.seat', 'pf.block', 'pf.withWho']));
  check('The new strings exist in both en and ro (statistics labels, personal field labels)', !dictKeys.length, dictKeys.join(','));
  await p3.click('#meTabMatches');

  // A team with no formation (or one that does not add up) gets the line-up list and no pitch; a formation is never inferred.
  const ctx5 = await newCtx();
  const both2 = ATTF.matches.filter(m => hasSide(m, 'home') && hasSide(m, 'away') && pitchOk(m.lineups.home) && pitchOk(m.lineups.away));
  const mNo = both2[0], mOdd = both2[1];
  const mod = JSON.parse(JSON.stringify(ATTF));
  delete mod.matches.find(m => m.id === mNo.id).lineups.home.formation;
  mod.matches.find(m => m.id === mOdd.id).lineups.home.formation = '4-4-4';
  await ctx5.route('**/data/attended.json', r => r.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify(mod)}));
  const p5 = await ctx5.newPage();
  p5.on('pageerror', e => errors.push(e.message));
  await p5.goto(BASE);
  await p5.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await p5.click('nav button[data-pane=me]'); await p5.waitForSelector('#meStats .astat');
  const noPitchBad = [];
  for(const [mm, why] of [[mNo, 'no formation'], [mOdd, 'formation not adding up']]){
    await openEntry(p5, 'meMatches', '#meTabMatches', mm.id);
    const st = await sheetState(p5);
    if(st.pitchNames.length || JSON.stringify(st.listNames.slice(0, 11)) !== JSON.stringify(mm.lineups.home.xi.map(p => p.name)) || !st.fits) noPitchBad.push(why + ' ' + JSON.stringify([st.pitchNames.length, st.listNames.length, st.fits]));
    await p5.click('button[data-side="away"]');
    const s2 = await sheetState(p5);
    if(s2.pitchNames.length !== 11) noPitchBad.push(why + ': the away pitch should still be drawn');
    await p5.click('#asheetClose');
  }
  check('A team with no formation, or one that does not add up to ten outfield players, shows the line-up list and no pitch; the other team\'s pitch is unaffected', !noPitchBad.length, noPitchBad.join(' | '));
  await ctx5.close();
  await p3.click('#meTabMatches');

  // Languages.
  const keys = await p3.evaluate(() => ({en: Object.keys(I18N.en).sort(), ro: Object.keys(I18N.ro).sort(),
    emptyEn: Object.entries(I18N.en).filter(([, v]) => !v).length, emptyRo: Object.entries(I18N.ro).filter(([, v]) => !v).length}));
  check('en and ro have identical key sets, none empty', JSON.stringify(keys.en) === JSON.stringify(keys.ro) && !keys.emptyEn && !keys.emptyRo && keys.en.length > 20, `${keys.en.length} / ${keys.ro.length}`);
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  const used = new Set([...html.matchAll(/\bt\('([a-z]+(?:\.[A-Za-z]+)+)'/g)].map(m => m[1]).concat([...html.matchAll(/data-i18n(?:-aria)?="([^"]+)"/g)].map(m => m[1])));
  const unknown = [...used].filter(k => !keys.en.includes(k));
  check('Every key the page asks t() or data-i for exists in the dictionary', used.size > 15 && !unknown.length, unknown.join(', '));
  check('Language defaults to English and no language toggle is shown', await p3.evaluate(() => LANG === 'en' && document.documentElement.lang === 'en' &&
    !document.querySelector('#langBtn,[data-lang],.langtoggle')), '');
  await p3.evaluate(() => setLang('ro'));
  const ro = await p3.evaluate(() => ({labels: [...document.querySelectorAll('#meSubs button')].map(b => b.textContent.trim()), stored: localStorage.getItem('football-planner-lang'),
    first: document.querySelector('#meMatches .acard')?.innerText.replace(/\s+/g, ' ')}));
  check('setLang(\'ro\') switches the labels and the data text, and is stored on the device', JSON.stringify(ro.labels) === '["Statistici","Meciuri","Evenimente","Bilete"]' &&
    ro.stored === 'ro' && /Timișoara/.test(ro.first), JSON.stringify(ro));
  const subsRo = await p3.evaluate(() => [...document.querySelectorAll('#meSubs button')].filter(b => { const r = b.getBoundingClientRect(); return b.scrollWidth > b.clientWidth + 1 || r.right > innerWidth + 1 || r.left < -1; }).map(b => b.textContent));
  check('The Romanian sub-tab labels fit at 390 px', !subsRo.length, subsRo.join(', '));
  await p3.click('#meTabStats');
  noSideways('Romanian stats: no sideways scroll at 390 px', await sideways(p3));
  await p3.click('#meTabEvents');
  noSideways('Romanian events: no sideways scroll at 390 px', await sideways(p3));
  await p3.reload();
  await p3.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  check('The chosen language survives a reload', await p3.evaluate(() => LANG) === 'ro', '');
  await p3.evaluate(() => setLang('en'));
  await ctx3.close();

  // A failed load says so.
  const ctx4 = await newCtx();
  await ctx4.route('**/data/attended.json', r => r.abort());
  const p4 = await ctx4.newPage();
  p4.on('pageerror', e => errors.push(e.message));
  await p4.goto(BASE);
  await p4.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await p4.click('nav button[data-pane=me]');
  await p4.waitForSelector('#meStats .aerr');
  check('A failed load of the file says so and shows no numbers', /Could not load data\/attended\.json/.test(await p4.textContent('#meStats')) && !(await p4.$('#meStats .astat')), await p4.textContent('#meStats'));
  await ctx4.close();

  check('no script error', !errors.length, errors.slice(0, 3).join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
