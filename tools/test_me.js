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
//  - since 2026-10-09 the Me tab has four sub-tabs (Stats, Matches, Events, Tickets/Memberships; all existing checks above run on the fourth),
//    the first three read data/attended.json: the sub-tabs appear in order and fit at 390 px in English and Romanian; the
//    file is not requested before one of them is opened and only once after; the stats and the list counts equal counts made
//    here from the file itself; every match and event is listed in the old app's order and opens the header sheet; en and ro
//    have identical key sets and every key the page uses exists; the page reads no browser storage on them; a failed load says so;
//  - since 2026-10-09 the tapped match or event opens the full detail sheet: line-ups (home side first, with a switch), the pitch as inline SVG
//    (only where the formation adds up; never inferred), timeline in minute order, stats only with a stats block, the factual note labelled
//    unverified, no empty pane; the personal fields (note, ticket, block, row, seat, who I went with) are kept only under football-attended-personal,
//    card numbers are refused on four of them, no storage read or write is an mf_ key, mf_media is untouched; nothing overflows at 390 px;
//  - since 2026-10-09 (device-only additions, none ever committed, nothing migrated from the old app; every storage read and write and every
//    IndexedDB open is recorded and none is an mf_ name): the supporter choice on a match sheet (nothing chosen by default; the chosen button pressed;
//    pressing it again clears it; kept under football-attended-personal as {id: {supported}}), and the win/draw/loss record on My stats worked out
//    here from the file's scores, with "n of total matches counted" (Neutral and no choice left out); a box on My attended matches that accepts
//    the old format (all 23 file matches re-pasted with new ids are accepted), refuses anything invalid or clashing with nothing stored, stores
//    valid matches only under football-attended-imported, marks them "Imported on this device" in the list and the sheet, and counts them in the
//    stats, with their own id space ("imp:" + id); photos and videos on match, imported-match and event sheets in the IndexedDB
//    football-attended-media (added, thumbnailed, viewed, deleted, kept over a reload, a non-media file refused, storage refused and quota
//    exceeded said clearly, none in localStorage or the export); the Me export at version 2 holding the personal fields, the supporter choices and the
//    imported matches and saying photos and videos are not included, its round trip, its refusals (a card number, a clash with the file's ids, a
//    newer version, the old app's export shape), and a version 1 file still importing and leaving those alone; nothing overflows at 390 px in English
//    and Romanian; since 2026-10-12, the kick-off: every kickoff in the file is HH:MM with a kickoffSource, shown as "Kick-off HH:MM (local time)"
//    on its card and in its sheet header and absent from the others, and an imported kickoff accepted (no source) or refused when malformed;
//  - since 2026-10-15 exhibition matches leave the goal stats ("exhibition": true on a match: goals seen, goals per match and penalties scored ignore it,
//    a note says how many goals were excluded; the file's one exhibition match, the validator, the Add/Edit form's Yes/No, its JSON merge rule and the
//    tag), and the Competition and Stadium fields of the match form offer suggestions (every club ground, data/competitions.csv, the coverage leagues,
//    the matches' own texts; ranking, "+ n more", accents, tap, free text, Enter; inside the screen at 390x844 and 390x500; both languages; the CSV
//    unreachable; no storage key and no request beyond the one GET of data/competitions.csv); expected values are worked out from the files here;
//  - since 2026-10-16 the Home team and Away team fields offer team suggestions too (every club of every country file, one row per folded name and country,
//    plus the teams only the matches use, "Used in your matches"; deduplication, order by rank then tier, 8 rows and "+ n more", accents, tap fills only that
//    field and the goal rows' menu, free text, Enter, Edit leaves a stored name unchanged, 390x844 and 390x500, both languages);
//  - since 2026-10-09 the whole interface is translated (English and Romanian, the Romanian written by the assistant and unchecked): the dictionary's
//    key sets, no ro value equal to its en value outside a short whitelist of names, every {placeholder} kept; Settings reached from the top of the
//    Me tab, the choice stored under football-planner-lang and kept over a reload, the fourth sub-tab renamed Tickets/Memberships in both languages;
//    in Romanian every main tab, the four Me sub-tabs, the panels and the sheets are free of English interface text (data-content areas excepted)
//    and fit at 390 px; a change of language redraws an open sheet and keeps a form being filled in;
//  - since 2026-10-09 the Dark/Light theme: the Settings toggle stored under football-planner-theme and kept over a reload (dark by default, an invalid
//    value ignored, blocked storage tolerated, no mf_ key); the theme applied before first paint; no colour literal in index.html outside the two
//    variable sets; text at least 4.5:1 on every main tab, the Me sub-tabs and the sheets in both themes, with no near-black-on-dark or white-on-white
//    pair in light; Stadia's light tiles in light mode with a fall-back to the dark tiles and a note when they keep failing; the palette distinct;
//    nothing overflows at 390 px in either theme;
//  - since 2026-10-18 the personal field Row: order note, ticket, block, row, seat, who I went with on every match sheet and on an event sheet (the ticket, block, row
//    and seat fields only at the stadium), saved as typed and kept over a reload, in the export and back through an import, an older file importing unchanged
//    (a seat reading "Row 8 Seat 8" is not parsed), a card number refused on it, the label in both languages;
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
const PF_ORDER = ['note', 'ticket', 'block', 'row', 'seat', 'withWho'], PF_TICKET = ['ticket', 'block', 'row', 'seat'];   // the personal fields in the order of the sheet; the four that need "I was at the stadium" on an event
const rules = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/football-rules.json'), 'utf8'));
const LINK_ID = 'derby-madonnina';
const linked = rules.bucketList.find(b => b.id === LINK_ID);
// The Milan-home fixture's day is read from football-rules.json, never written here; the ticket the test adds is for that day.
const DERBY_DATE = linked.fixtures.find(f => f.home === 'milan').date;
const DERBY_D = new Date(DERBY_DATE + 'T00:00:00Z');
const DERBY_WORDS = `${['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][DERBY_D.getUTCDay()]},? ${DERBY_D.getUTCDate()} ${['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][DERBY_D.getUTCMonth()]} ${DERBY_D.getUTCFullYear()}`;
const DERBY_DAY_BEFORE = new Date(DERBY_D.getTime() - 864e5).toISOString().slice(0, 10);
const TODAY_YM = '2026-10';                // the test clock's month
const DERBY_MONTHS_AHEAD = (+DERBY_DATE.slice(0, 4) - +TODAY_YM.slice(0, 4)) * 12 + (+DERBY_DATE.slice(5, 7) - +TODAY_YM.slice(5));

const plEn = (n, one, other) => `${n} ${n === 1 ? one : other}`;   // English: "1 match", "n matches"
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
        const r = document.createRange(); const node = b.querySelector('span')?.firstChild || [...b.childNodes].find(n => n.nodeType === 3); r.selectNodeContents(node);
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
  await add(page, 'ticket', {match: `AC Milan v Inter ${TAG}`, date: DERBY_DATE, kickoff: '20:45', venue: 'San Siro', block: '332',
    seats: '12, 13', whoFor: 'Alexandru, Ana', priceAmount: '75', priceCurrency: 'EUR', boughtFrom: 'Inter ticket office',
    status: 'bought', bucketId: LINK_ID});
  await add(page, 'ticket', {match: 'VfB v KSC', date: '2027-01-30', venue: 'MHPArena', status: 'requested'});
  await add(page, 'ticket', {match: 'Old cup tie', date: '2026-09-01', status: 'bought'});
  let milan = await cardText(page, 'ticket', 'AC Milan'), vfbk = await cardText(page, 'ticket', 'VfB v KSC');
  check('A ticket is added with its fields', new RegExp(DERBY_WORDS + ' · 20:45').test(milan) && /332/.test(milan) && /12, 13/.test(milan) &&
    /75\.00 EUR/.test(milan) && /bought/.test(milan) && milan.includes(`${linked.title} (${LINK_ID})`), milan);
  check('A ticket with no kick-off says "time not set"', /Sat,? 30 Jan 2027\s*time not set/.test(vfbk), vfbk);
  check('A past ticket goes in a collapsed Past section', await page.$eval('#meTickets details.past', d => !d.open && /Old cup tie/.test(d.textContent)), '');
  // 2026-10-15: on this sub-tab the tickets part comes first and the memberships part second; the banner stays at the top, Back up last.
  // The tickets part runs from the Tickets heading's row up to the Memberships heading's row, the memberships part from there up to the alerts heading.
  const ord = await page.evaluate(() => {
    const B = document.getElementById('meBody'), $ = id => document.getElementById(id);
    const before = (a, b) => !!(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
    const tixRow = $('meTixTitle').closest('.mesec'), memRow = $('meMemTitle').closest('.mesec');
    const h2s = [...B.querySelectorAll('h2')], backupH = h2s.filter(h => before(h, $('meExport'))).pop(), alertsH = h2s[h2s.indexOf(backupH) - 1];
    return {
      titles: before($('meTixTitle'), $('meMemTitle')),
      addButtons: before(B.querySelector('button[data-act=add][data-kind=ticket]'), B.querySelector('button[data-act=add][data-kind=membership]')),
      lists: before($('meTickets'), $('meMemberships')),
      pastInTix: before(tixRow, B.querySelector('#meTickets details.past')) && before(B.querySelector('#meTickets details.past'), memRow) && $('meTickets').contains(B.querySelector('details.past')),
      pastOnlyOne: B.querySelectorAll('details.past').length === 1,
      windowInMem: before(memRow, $('meWindow')) && before($('meWindow'), $('meMemberships')) && !$('meTickets').contains($('meWindow')),
      windowAfterTix: before($('meTickets'), $('meWindow')),
      bannerFirst: B.firstElementChild === $('meBackup'),
      backupLast: before($('meMemberships'), alertsH) && before(alertsH, backupH) && before($('meTickets'), backupH) &&
        before(backupH, $('meExport')) && before($('meExport'), $('meImport')) && !B.querySelector('#meExport ~ .mesec, #meExport ~ #meTickets, #meExport ~ #meMemberships'),
      backupNothingAfterButBar: ![...B.querySelectorAll('#meTickets, #meMemberships, #meTixTitle, #meMemTitle, #meWindow')].some(e => before(backupH, e)),
      sectionCounts: [...B.querySelectorAll('#meBody > .mesec')].map(e => e.querySelector('h2').id)
    };
  });
  check('Tickets/Memberships: the Tickets held heading, its Add button and its list come before the Memberships ones', ord.titles && ord.addButtons && ord.lists, JSON.stringify(ord));
  check('...the Past tickets section is inside the tickets part (once), before the memberships part starts', ord.pastInTix && ord.pastOnlyOne, JSON.stringify(ord));
  check('...the renewal-window setting is inside the memberships part, below the tickets', ord.windowInMem && ord.windowAfterTix, JSON.stringify(ord));
  check('...the backup banner is still the first element, the Back up section the last, with its Export and Import buttons', ord.bannerFirst && ord.backupLast && ord.backupNothingAfterButBar, JSON.stringify(ord));
  check('...the two section headings are exactly Tickets, then Memberships', JSON.stringify(ord.sectionCounts) === JSON.stringify(['meTixTitle', 'meMemTitle']), JSON.stringify(ord.sectionCounts));
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
  check('Match .ics: kick-off as typed, the derby day 20:45, no time zone', P.ev.DTSTART.value === DERBY_DATE.replace(/-/g, '') + 'T204500' && !P.ev.DTSTART.params, JSON.stringify(P.ev.DTSTART));
  check('Match .ics: the alarm goes off 1 day before kick-off (the default)', alarmAt(P.ev, P.al) === DERBY_DAY_BEFORE + 'T20:45' && P.al.ACTION.value === 'DISPLAY', alarmAt(P.ev, P.al));
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
  for(let i = 0; i < DERBY_MONTHS_AHEAD; i++) await page.click('[data-cal=next]');
  const cell = await page.$eval(`.cday[data-date="${DERBY_DATE}"]`, c => ({mark: !!c.querySelector('.mheld'), label: c.getAttribute('aria-label')}));
  check('Calendar: the day cell is marked, and its label says you hold tickets', cell.mark && /you hold tickets/.test(cell.label), cell.label);
  const otherMarks = await page.$$eval('.cday .mheld', ms => ms.map(m => m.closest('.cday').dataset.date));
  check('...and no other day in that month is', JSON.stringify(otherMarks) === JSON.stringify([DERBY_DATE]), otherMarks.join(','));
  await page.click(`.cday[data-date="${DERBY_DATE}"]`);
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
  check('Export: one JSON file with a format and a version number', file.format === 'football-planner-me' && file.version === 3 && /\.json$/.test(exp.name), exp.name);
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
    ['a newer version', JSON.stringify(Object.assign({}, good, {version: 4}))],
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
  await add(page2, 'ticket', {match: 'Blocked match', date: DERBY_DATE, status: 'won', bucketId: LINK_ID});
  await page2.click('nav button[data-pane=bucket]');
  check('Storage blocked: the bucket list still shows "You hold tickets"', /You hold tickets/.test(await page2.$eval(`#bucketBody details.bucket[data-id="${LINK_ID}"] summary`, s => s.textContent)), '');
  await ctx2.close();


  // ---- Attended matches and events: the first three sub-tabs, from data/attended.json.
  const ATTF = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/attended.json'), 'utf8'));
  const fx = {
    n: ATTF.matches.length, ne: ATTF.events.length,
    // Goals are the sum of both score numbers; a match whose goals list is shorter than its score is footnoted.
    // Since 2026-10-15 a match with "exhibition": true is left out of goals seen, goals per match and penalties scored, and its goals are reported as excluded.
    nReal: ATTF.matches.filter(m => m.exhibition !== true).length,
    nExh: ATTF.matches.filter(m => m.exhibition === true).length,
    goals: ATTF.matches.filter(m => m.exhibition !== true).reduce((n, m) => { const s = /^(\d+)-(\d+)$/.exec(m.score); return n + (s ? +s[1] + +s[2] : 0); }, 0),
    exclGoals: ATTF.matches.filter(m => m.exhibition === true).reduce((n, m) => { const s = /^(\d+)-(\d+)$/.exec(m.score); return n + (s ? +s[1] + +s[2] : 0); }, 0),
    goalsShort: ATTF.matches.filter(m => m.exhibition !== true).filter(m => { const s = /^(\d+)-(\d+)$/.exec(m.score); return s && m.goals.length < +s[1] + +s[2]; })
      .map(m => { const s = /^(\d+)-(\d+)$/.exec(m.score); return +s[1] + +s[2]; }),
    pens: ATTF.matches.filter(m => m.exhibition !== true).reduce((n, m) => n + m.goals.filter(g => g.pen).length, 0),
    stadiums: new Set(ATTF.matches.map(m => m.stadium)).size,
    yellow: ATTF.matches.filter(m => m.cardsComplete).reduce((n, m) => n + m.cards.filter(c => c.type === 'yellow').length, 0),
    red: ATTF.matches.filter(m => m.cardsComplete).reduce((n, m) => n + m.cards.filter(c => c.type === 'red').length, 0),
    second: ATTF.matches.filter(m => m.cardsComplete).reduce((n, m) => n + m.cards.filter(c => c.type === 'second-yellow').length, 0),
    cardsOk: ATTF.matches.filter(m => m.cardsComplete).length,
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
  check('Four sub-tabs in order: Stats, Matches, Events, Tickets/Memberships', JSON.stringify(subs.labels) === '["Stats","Matches","Events","Tickets/Memberships"]', subs.labels.join(' | '));
  check('The four sub-tabs fit at 390 px: none cut off or off screen, only the long last label wraps (to two lines), each at least 40 px tall', !subs.bad.length && subs.lines.slice(0, 3).every(n => n === 1) && subs.lines[3] <= 2, JSON.stringify(subs));

  const tiles = await p3.$$eval('#meStats .astat', ts => ts.map(t => [t.querySelector('b').textContent.replace(/[^\d]/g, ''), t.querySelector('span').textContent]));
  const tv = tiles.map(t => +t[0]);
  check('Stats: matches, goals, penalties, stadiums, yellow cards and red cards (straight reds plus second yellows) equal the counts in the file',
    JSON.stringify(tv) === JSON.stringify([fx.n, fx.goals, fx.pens, fx.stadiums, fx.yellow, fx.red + fx.second]), JSON.stringify(tv) + ' file ' + JSON.stringify([fx.n, fx.goals, fx.pens, fx.stadiums, fx.yellow, fx.red + fx.second]));
  const goalsAvg = (fx.goals / fx.nReal).toFixed(2) + ' per match';
  check('Stats: "goals seen" shows the sum of the scores of the matches that are not exhibition matches, per non-exhibition match',
    tiles[1][1] === 'goals seen' && await p3.$eval('#meStats .astat:nth-child(2) i', e => e.textContent) === goalsAvg, goalsAvg);
  check('Stats: the file has at least one exhibition match, and the matches card still counts every match, exhibition included', fx.nExh >= 1 && fx.exclGoals > 0 && tv[0] === fx.n && fx.nReal === fx.n - fx.nExh, `${fx.nExh} exhibition, ${fx.exclGoals} goals`);
  const redTile = await p3.$$eval('#meStats .astat', ts => ts[5] && ({label: ts[5].querySelector('span').textContent, lines: [...ts[5].querySelectorAll('i')].map(x => x.textContent)}));
  check('Stats: ONE "red cards" card (no "second yellows" card): the split line gives second yellows and straight reds, then the per-match figure over the matches with complete card data',
    tiles.length === 6 && !tiles.some(t => /second yellow/i.test(t[1])) && tiles[5][1] === 'red cards' &&
    JSON.stringify(redTile.lines) === JSON.stringify([`${plEn(fx.second, 'second yellow', 'second yellows')} · ${plEn(fx.red, 'straight red', 'straight reds')}`, ((fx.red + fx.second) / fx.cardsOk).toFixed(2) + ' per match']), JSON.stringify(redTile));
  check('Stats: the yellow card keeps its per-match figure and the "complete data for a of b matches" note stays',
    await p3.$$eval('#meStats .astat', ts => ts[4].querySelector('i').textContent) === (fx.yellow / fx.cardsOk).toFixed(2) + ' per match' &&
    new RegExp(`Complete data currently exists for ${fx.cardsOk} of ${fx.n} matches`).test(await p3.$eval('#meStats', e => e.textContent)), '');
  const gnote = await p3.$eval('#aGoalsNote', e => e.textContent).catch(() => null);
  check('Stats: the footnote counts goals and matches whose goals list is shorter than the score',
    fx.goalsShort.length ? gnote === `Includes ${plEn(fx.goalsShort.reduce((a, b) => a + b, 0), 'goal', 'goals')} from ${plEn(fx.goalsShort.length, 'match', 'matches')} without a full goals list` : gnote === null, String(gnote));
  const gexcl = await p3.$eval('#aGoalsExcl', e => e.textContent).catch(() => null);
  check('Stats: the exclusion note comes after the goals-list note and names the goals of the exhibition matches, counted by the same rule',
    gexcl === `Doesn't include goals from exhibition matches (${plEn(fx.exclGoals, 'goal', 'goals')} excluded)` &&
    await p3.evaluate(() => { const a = document.getElementById('aGoalsNote'), b = document.getElementById('aGoalsExcl'); return !a || !!(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING); }), String(gexcl));
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
  // Kick-off (2026-10-12): the local time at the ground, as stored, only where the file has one.
  const KO_RE = /^([01]\d|2[0-3]):[0-5]\d$/, koText = m => `Kick-off ${m.kickoff} (local time)`;
  const koBadData = ATTF.matches.filter(m => ('kickoff' in m || 'kickoffSource' in m) &&
    !(typeof m.kickoff === 'string' && KO_RE.test(m.kickoff) && typeof m.kickoffSource === 'string' && (m.kickoffSource === 'user-supplied' || /^https:\/\/\S+$/.test(m.kickoffSource)))).map(m => m.id);
  check('Data: every kickoff in data/attended.json is HH:MM and has a kickoffSource (a URL or "user-supplied"); no source without a time; no event has either',
    !koBadData.length && ATTF.events.every(e => !('kickoff' in e) && !('kickoffSource' in e)), koBadData.join(', '));
  const koCardBad = ATTF.matches.filter(m => { const c = mcards.find(x => x.id === m.id); return !c || (m.kickoff ? !c.text.includes(koText(m)) : /Kick-off/.test(c.text)); }).map(m => m.id);
  check(`Matches: the ${ATTF.matches.filter(m => m.kickoff).length} cards with a kickoff show "Kick-off HH:MM (local time)" beside the date; the others show no kick-off text`, !koCardBad.length, koCardBad.join(', '));
  noSideways('Matches: no sideways scroll at 390 px', await sideways(p3));

  await p3.click('#meTabEvents');
  await p3.waitForSelector('#meEvents .acard');
  const ecards = await p3.$$eval('#meEvents .acard', cs => cs.map(c => ({id: c.dataset.id, text: c.innerText.replace(/\s+/g, ' ')})));
  check('Events: one card per event, in the file\'s order', JSON.stringify(ecards.map(c => c.id)) === JSON.stringify(ATTF.events.map(e => e.id)), `${ecards.length} of ${fx.ne}`);
  check('Events: every card shows its title, place and date', ATTF.events.every((e, i) => ecards[i] && ecards[i].text.includes(e.title.en) && ecards[i].text.includes(e.place.en) &&
    ecards[i].text.includes(String(new Date(e.date + 'T12:00:00').getFullYear()))), '');
  noSideways('Events: no sideways scroll at 390 px', await sideways(p3));
  check('The file was requested once for all three sub-tabs', attReqs() === 1, String(attReqs()));
  // Since 2026-10-09 the stats read the supporter choices and the matches imported on this device: exactly these two keys, nothing else.
  const readsSub = await p3.evaluate(() => window.__reads);
  check('The three sub-tabs read only football-attended-personal and football-attended-imported from browser storage (no mf_ key)',
    readsSub.length > 0 && readsSub.every(k => ['football-attended-personal', 'football-attended-imported'].includes(k)), JSON.stringify([...new Set(readsSub)]));

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
  const koSheetBad = [];
  await p3.click('#meTabMatches');
  for(const m of ATTF.matches){
    await p3.click(`#meMatches .acard[data-id="${m.id}"]`); await p3.waitForTimeout(350);
    const head = await p3.$eval('#asheetHead', h => h.innerText.replace(/\s+/g, ' ')), all = await p3.$eval('#asheet', s => s.innerText.replace(/\s+/g, ' '));
    if(m.kickoff ? !head.includes(koText(m)) : /Kick-off/.test(all)) koSheetBad.push(m.id + ': ' + head.slice(0, 120));
    await p3.click('#asheetClose');
  }
  check('Sheets: a match with a kickoff shows it in the sheet header; a match without one shows no kick-off text anywhere in its sheet', !koSheetBad.length, koSheetBad.slice(0, 3).join(' | '));
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
    if(JSON.stringify(st.pf) !== JSON.stringify(PF_ORDER)) bad('personal fields ' + st.pf);
    if(!(st.pf.indexOf('block') < st.pf.indexOf('row') && st.pf.indexOf('row') < st.pf.indexOf('seat'))) bad('Block, Row, Seat order ' + st.pf);
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
    const need = [e.place.en, 'Factual note'];
    if(st.hidden || need.some(x => !st.text.toLowerCase().includes(x.toLowerCase()))) evBad.push(e.id + ' content ' + need.filter(x => !st.text.toLowerCase().includes(x.toLowerCase())).join('/'));
    if('what' in e || 'why' in e || typeof e.note.en !== 'string') evBad.push(e.id + ' data still has what/why or no note');
    if(JSON.stringify(st.h4.filter(h => /Factual note|What it was|Why it mattered/.test(h))) !== '["Factual note"]') evBad.push(e.id + ' headings ' + st.h4.join('/'));
    const shown = await p3.$eval('#asheetBody .afact', x => ({text: x.innerText, ws: getComputedStyle(x).whiteSpace}));
    if(shown.text.trim() !== e.note.en || shown.ws !== 'pre-line' || !/\n\n/.test(shown.text)) evBad.push(e.id + ' note text/line breaks ' + JSON.stringify(shown).slice(0, 80));
    if(!new RegExp('At the stadium ' + (e.atStadium ? 'yes' : 'no'), 'i').test(st.text)) evBad.push(e.id + ' atStadium flag');
    const want = e.atStadium ? PF_ORDER : PF_ORDER.filter(k => !PF_TICKET.includes(k));
    if(JSON.stringify(st.pf) !== JSON.stringify(want)) evBad.push(e.id + ' personal fields ' + st.pf);
    if(!st.fits || st.empty.length) evBad.push(e.id + ' fit/empty');
    if(st.unv.length !== 1) evBad.push(e.id + ' unverified labels');
    await p3.click('#asheetClose');
  }
  check(`All ${ATTF.events.length} events open their sheet: title, place, one Factual note (the note from the file, line breaks kept, no What it was / Why it mattered headings), the atStadium flag, ticket/block/row/seat only where atStadium (in that order), and one unverified label`, !evBad.length, evBad.slice(0, 3).join(' | '));

  // Personal fields: this device only, under football-attended-personal, never an mf_ key.
  const PK = 'football-attended-personal';
  const pm = ATTF.matches[0], pe = ATTF.events.find(e => e.atStadium);
  await openEntry(p3, 'meMatches', '#meTabMatches', pm.id);
  check('The old app\'s mf_personal key is not read: a seeded note there is not shown', !(await sheetState(p3)).text.includes('OLDAPPNOTE'), '');
  const vals = {note: 'Cold night ' + TAG, ticket: 'T-' + TAG, block: 'Block 12 ' + TAG, row: 'Row 3 ' + TAG, seat: 'Row 7 ' + TAG, withWho: 'Ana and Radu ' + TAG};
  for(const k of Object.keys(vals)) await p3.fill(`#asheetBody [data-pf="${k}"]`, vals[k]);
  const persStored = async () => JSON.parse(await p3.evaluate(k => localStorage.getItem(k), PK) || 'null');
  check('Editing the personal fields saves under football-attended-personal, keyed by entry id, with the old shape plus row (note, ticket, block, row, seat, withWho)',
    JSON.stringify((await persStored())[pm.id]) === JSON.stringify(vals), JSON.stringify(await persStored()));
  await openEntry(p3, 'meEvents', '#meTabEvents', pe.id);
  await p3.fill('#asheetBody [data-pf="withWho"]', 'Friends ' + TAG); await p3.fill('#asheetBody [data-pf="ticket"]', 'E-' + TAG); await p3.fill('#asheetBody [data-pf="row"]', 'ER-' + TAG);
  await p3.click('#asheetClose');
  check('An event\'s personal fields are kept under its own id beside the match\'s', (await persStored())[pe.id].withWho === 'Friends ' + TAG && (await persStored())[pm.id].note === vals.note, JSON.stringify(Object.keys(await persStored())));
  await p3.reload();
  await p3.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await p3.click('nav button[data-pane=me]'); await p3.waitForSelector('#meStats .astat');
  await openEntry(p3, 'meMatches', '#meTabMatches', pm.id);
  const persBack = await p3.evaluate(() => Object.fromEntries([...document.querySelectorAll('#asheetBody [data-pf]')].map(x => [x.dataset.pf, x.value])));
  check('The personal fields, Row included, are still there after a reload, in the order of the sheet', JSON.stringify(persBack) === JSON.stringify(vals) && JSON.stringify(Object.keys(persBack)) === JSON.stringify(PF_ORDER), JSON.stringify(persBack));
  const rowLabel = await p3.$eval('#asheetBody [data-pf="row"]', x => x.closest('label').firstChild.textContent.trim());
  check('The Row field is labelled "Row" and a seat reading "Row 7 ..." is kept as typed, not parsed', rowLabel === 'Row' && persBack.seat === vals.seat && persBack.row === vals.row, rowLabel);
  await p3.click('#asheetClose');
  await openEntry(p3, 'meEvents', '#meTabEvents', pe.id);
  check('An event\'s Row is kept under its own id and shown again after the reload', await p3.$eval('#asheetBody [data-pf="row"]', x => x.value) === 'ER-' + TAG && (await persStored())[pe.id].row === 'ER-' + TAG, '');
  await p3.click('#asheetClose');
  await openEntry(p3, 'meMatches', '#meTabMatches', pm.id);
  // Card numbers are refused on ticket, block, row, seat and who I went with; digits failing Luhn are kept.
  const cardBad = [];
  for(const k of PF_ORDER.filter(k => k !== 'note')){
    const before = (await persStored())[pm.id][k];
    await p3.fill(`#asheetBody [data-pf="${k}"]`, 'card 4111 1111 1111 1111 ok');
    const r = await p3.evaluate(kk => ({err: document.querySelector(`#asheetBody [data-err="${kk}"]`).textContent, inv: document.querySelector(`#asheetBody [data-pf="${kk}"]`).getAttribute('aria-invalid')}), k);
    if(!/payment card number/.test(r.err) || r.inv !== 'true' || (await persStored())[pm.id][k] !== before) cardBad.push(k + ' ' + JSON.stringify(r));
    await p3.fill(`#asheetBody [data-pf="${k}"]`, 'ref 4111 1111 1111 1112');
    if((await persStored())[pm.id][k] !== 'ref 4111 1111 1111 1112' || await p3.$eval(`#asheetBody [data-err="${k}"]`, x => x.textContent)) cardBad.push(k + ' non-card refused');
  }
  check('A payment card number (Luhn) is refused on Ticket, Block, Row, Seat and Who I went with, nothing saved, reason shown; digits failing Luhn are kept', !cardBad.length, cardBad.join(' | '));
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
  const dictKeys = await p3.evaluate(ks => ks.filter(k => !I18N.en[k] || !I18N.ro[k]), STAT_KEYS.map(k => 'sx.' + k).concat(['pf.note', 'pf.ticket', 'pf.block', 'pf.row', 'pf.seat', 'pf.withWho']));
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
  check('Language defaults to English, and the only language buttons are inside the Settings sheet', await p3.evaluate(() => LANG === 'en' && document.documentElement.lang === 'en' &&
    [...document.querySelectorAll('[data-lang]')].every(b => b.closest('#ssheet'))), '');
  await p3.evaluate(() => setLang('ro'));
  const ro = await p3.evaluate(() => ({labels: [...document.querySelectorAll('#meSubs button')].map(b => b.textContent.trim()), stored: localStorage.getItem('football-planner-lang'),
    first: document.querySelector('#meMatches .acard')?.innerText.replace(/\s+/g, ' ')}));
  check('setLang(\'ro\') switches the labels and the data text, and is stored on the device', JSON.stringify(ro.labels) === '["Statistici","Meciuri","Evenimente","Bilete/Abonamente"]' &&
    ro.stored === 'ro' && /Timișoara/.test(ro.first), JSON.stringify(ro));
  const subsRo = await p3.evaluate(() => [...document.querySelectorAll('#meSubs button')].filter(b => { const r = b.getBoundingClientRect(); return b.scrollWidth > b.clientWidth + 1 || r.right > innerWidth + 1 || r.left < -1; }).map(b => b.textContent));
  check('The Romanian sub-tab labels fit at 390 px', !subsRo.length, subsRo.join(', '));
  await p3.click('#meTabStats');
  noSideways('Romanian stats: no sideways scroll at 390 px', await sideways(p3));
  {
    const roPl = (n, one, other, many) => `${n} ${n === 1 ? one : (n >= 20 && (n % 100 === 0 || n % 100 >= 20) ? many : other)}`;
    const rl = await p3.$$eval('#meStats .astat', ts => ts[5] && ({label: ts[5].querySelector('span').textContent, lines: [...ts[5].querySelectorAll('i')].map(x => x.textContent)}));
    const want = `${roPl(fx.second, 'cartonaș galben secund', 'cartonașe galbene secunde', 'de cartonașe galbene secunde')} · ${roPl(fx.red, 'cartonaș roșu direct', 'cartonașe roșii directe', 'de cartonașe roșii directe')}`;
    check('Romanian stats: the red-cards card says its split line with the right plural forms (.many from 20)', rl.label === 'cartonașe roșii' && rl.lines[0] === want, JSON.stringify(rl) + ' want ' + want);
  }
  await p3.click('#meTabEvents');
  noSideways('Romanian events: no sideways scroll at 390 px', await sideways(p3));
  await p3.reload();
  await p3.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  check('The chosen language survives a reload', await p3.evaluate(() => LANG) === 'ro', '');
  await p3.evaluate(() => setLang('en'));
  // Plurals of the stats footnote: English "1 match" / "n matches"; Romanian "1 meci" / "n meciuri", with "de" from 20 (last two digits 00 or 20-99).
  const NS = [0, 1, 2, 19, 20, 21, 99, 100, 101, 119, 120, 1000];
  const pluralsEn = await p3.evaluate(ns => ns.map(n => [tn('st.nMatches', n, {n}), tn('st.nGoals', n, {n})]), NS);
  check('Plurals (English): "1 match" / "1 goal" and "n matches" / "n goals" for every n tried',
    pluralsEn.every(([m, g], i) => m === plEn(NS[i], 'match', 'matches') && g === plEn(NS[i], 'goal', 'goals')), JSON.stringify(pluralsEn.slice(0, 3)));
  await p3.evaluate(() => setLang('ro'));
  const pluralsRo = await p3.evaluate(ns => ns.map(n => [tn('st.nMatches', n, {n}), tn('st.nGoals', n, {n})]), NS);
  const roWant = n => `${n} ${n === 1 ? '' : (n >= 20 && (n % 100 === 0 || n % 100 >= 20)) ? 'de ' : ''}`;
  check('Plurals (Romanian): "1 meci" / "1 gol", "n meciuri" / "n goluri", and "de" from 20 ("20 de meciuri", "21 de goluri", "101 meciuri", "120 de meciuri")',
    pluralsRo.every(([m, g], i) => m === roWant(NS[i]) + (NS[i] === 1 ? 'meci' : 'meciuri') && g === roWant(NS[i]) + (NS[i] === 1 ? 'gol' : 'goluri')) &&
    pluralsRo[4][0] === '20 de meciuri' && pluralsRo[5][1] === '21 de goluri' && pluralsRo[8][0] === '101 meciuri' && pluralsRo[9][1] === '119 goluri' && pluralsRo[10][0] === '120 de meciuri',
    JSON.stringify(pluralsRo));
  await p3.evaluate(() => setLang('en'));
  await ctx3.close();

  {
  // ---- 2026-10-09: supporter choice and record, matches added by pasting JSON, photos and videos, the export at version 2.
  const SUPK = 'football-attended-personal', IMPK = 'football-attended-imported';
  const IMPID = 'imp-' + TAG, IMPKEY = 'imp:' + IMPID;
  const rec5 = {reads: [], writes: [], idb: []};
  const OLD_SEED = {personal: JSON.stringify({'*': {note: 'OLDAPPNOTE', supported: 'home'}}), imported: JSON.stringify([{id: 'OLDIMP' + TAG, date: '2020-01-01', home: {name: 'Old A'}, away: {name: 'Old B'}, score: '1-0'}])};
  const recordInit = seed => {                   // every localStorage read and write and every IndexedDB open, kept for the whole run
    window.__reads = []; window.__writes = []; window.__idb = [];
    const g = Storage.prototype.getItem, w = Storage.prototype.setItem, r = Storage.prototype.removeItem;
    Storage.prototype.getItem = function(k){ window.__reads.push(k); return g.call(this, k); };
    Storage.prototype.setItem = function(k, v){ window.__writes.push(k); return w.call(this, k, v); };
    Storage.prototype.removeItem = function(k){ window.__writes.push(k); return r.call(this, k); };
    const o = IDBFactory.prototype.open;
    IDBFactory.prototype.open = function(n){ window.__idb.push(n); return o.apply(this, arguments); };
    try{ if(g.call(localStorage, 'mf_personal') === null){ w.call(localStorage, 'mf_personal', seed.personal); w.call(localStorage, 'mf_imported', seed.imported); } }catch(e){}   // the old app's keys: never read
  };
  const ctx5 = await newCtx();
  await ctx5.addInitScript(recordInit, OLD_SEED);
  const p5 = await ctx5.newPage();
  p5.on('pageerror', e => errors.push(e.message));
  p5.on('dialog', d => d.accept());
  const harvest = async () => {
    const r = await p5.evaluate(() => { const o = {r: window.__reads.slice(), w: window.__writes.slice(), i: window.__idb.slice()}; window.__reads.length = 0; window.__writes.length = 0; window.__idb.length = 0; return o; });
    rec5.reads.push(...r.r); rec5.writes.push(...r.w); rec5.idb.push(...r.i);
  };
  const open5 = async () => {
    await p5.goto(BASE);
    await p5.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
    await p5.click('nav button[data-pane=me]');
    await p5.waitForSelector('#meStats .astat');
  };
  const sub5 = async (id, panel) => { await p5.click(id); await p5.waitForFunction(sel => !document.querySelector(sel).hidden && !/Loading/.test(document.querySelector(sel).textContent), panel); };
  const lsGet = k => p5.evaluate(k => localStorage.getItem(k), k);
  const tiles = () => p5.evaluate(() => [...document.querySelectorAll('#meStats .agrid')[0].querySelectorAll('.astat b')].map(b => +b.textContent.replace(/[^\d]/g, '')));
  const recordNow = () => p5.evaluate(() => ({label: document.getElementById('aRecCount').textContent,
    wdl: [...document.querySelectorAll('#aRecord .astat b')].map(b => +b.textContent)}));
  const openCard = async (panelTab, panel, key) => {
    await sub5(panelTab, panel);
    await p5.click(`${panel} .acard[data-id="${key}"]`);
    await p5.waitForSelector('#asheet:not([hidden])'); await p5.waitForTimeout(350);
  };
  const closeSheet5 = async () => { await p5.click('#asheetClose'); };
  const over5 = () => p5.evaluate(() => {
    const sh = document.getElementById('asheet'), root = sh.hidden ? document.getElementById('pane-me') : sh, bad = [];
    root.querySelectorAll('*').forEach(x => { const r = x.getBoundingClientRect(); if(r.width > 0 && (r.right > innerWidth + 1 || r.left < -1)) bad.push(x.tagName + '.' + x.className); });
    const b = document.getElementById('asheetBody');
    return {bad: bad.slice(0, 4), doc: document.documentElement.scrollWidth, sb: sh.hidden ? 0 : b.scrollWidth - b.clientWidth};
  });
  const noOver5 = async name => { const o = await over5(); check(name, !o.bad.length && o.doc <= W && o.sb <= 1, JSON.stringify(o)); };
  const sheetText5 = () => p5.$eval('#asheet', s => s.textContent.replace(/\s+/g, ' '));
  const outcome = (m, sup) => { const [h, a] = m.score.split('-').map(Number); return h === a ? 'd' : ((h > a) === (sup === 'home')) ? 'w' : 'l'; };

  await open5();
  // ---- Supporter buttons and the record
  const expRec = {w: 0, d: 0, l: 0, n: 0};
  check('Record: nothing is chosen by default, so it says "0 of N matches counted", shows no W/D/L and no supporter is stored',
    (await recordNow()).label === `0 of ${fx.n} matches counted` && !(await p5.$('#aRecord')) && !/supported/.test(await lsGet(SUPK) || ''), JSON.stringify(await recordNow()));
  // One win, one draw, one loss and one Neutral, chosen from the file's own scores so every part of the record is exercised.
  const dec = attOrder.filter(m => { const [h, a] = m.score.split('-').map(Number); return h !== a; }), drawn = attOrder.find(m => { const [h, a] = m.score.split('-').map(Number); return h === a; });
  const winSide = m => { const [h, a] = m.score.split('-').map(Number); return h > a ? 'home' : 'away'; };
  const picks = [[dec[0], winSide(dec[0])], [drawn, 'home'], [dec[1], winSide(dec[1]) === 'home' ? 'away' : 'home'], [dec[2], 'neutral']];
  check('The test has a win, a draw and a loss to choose from in the file', !!drawn && dec.length >= 3, `${dec.length} decisive`);
  let pickBad = [];
  for(const [m, sup] of picks){
    await openCard('#meTabMatches', '#meMatches', m.id);
    const before = await p5.$$eval('#aSupport button', bs => bs.map(b => [b.dataset.sup, b.getAttribute('aria-pressed'), b.textContent.trim(), b.getBoundingClientRect().height]));
    if(JSON.stringify(before.map(b => b[0])) !== '["home","neutral","away"]' || before.some(b => b[1] !== 'false')) pickBad.push(m.id + ' initial ' + JSON.stringify(before));
    if(before[0][2] !== (m.home.nameEn || m.home.name) || before[2][2] !== (m.away.nameEn || m.away.name) || before[1][2] !== 'Neutral' || before.some(b => b[3] < 44)) pickBad.push(m.id + ' labels/size ' + JSON.stringify(before));
    await p5.click(`#aSupport button[data-sup=${sup}]`);
    const after = await p5.$$eval('#aSupport button', bs => bs.map(b => b.getAttribute('aria-pressed')));
    if(JSON.stringify(after) !== JSON.stringify(['home', 'neutral', 'away'].map(v => String(v === sup)))) pickBad.push(m.id + ' pressed ' + after);
    if(sup !== 'neutral'){ expRec.n++; expRec[outcome(m, sup)]++; }
    await closeSheet5();
  }
  check('Supporter buttons: home, Neutral, away (the team names from the file), 44 px tall, none pressed at first, the chosen one pressed', !pickBad.length, pickBad.join(' | '));
  const sp = JSON.parse(await lsGet(SUPK));
  check('The choice is kept under football-attended-personal as {entry id: {supported: "home"|"neutral"|"away"}}, the old app\'s field name and shape',
    picks.every(([m, sup]) => sp[m.id] && sp[m.id].supported === sup && Object.keys(sp[m.id]).join() === 'supported'), JSON.stringify(sp));
  await openCard('#meTabMatches', '#meMatches', picks[0][0].id);
  await p5.click(`#aSupport button[data-sup=${picks[0][1]}]`);
  check('Pressing the chosen button again clears it (stored as an empty string, none pressed)',
    JSON.parse(await lsGet(SUPK))[picks[0][0].id].supported === '' && (await p5.$$eval('#aSupport button', bs => bs.every(b => b.getAttribute('aria-pressed') === 'false'))), '');
  await p5.click(`#aSupport button[data-sup=${picks[0][1]}]`); await closeSheet5();
  await sub5('#meTabStats', '#meStats');
  let rn = await recordNow();
  check(`Record on My stats equals the file's scores (W-D-L ${expRec.w}-${expRec.d}-${expRec.l}, each non-zero), and the label reads "${expRec.n} of ${fx.n} matches counted"`,
    expRec.w > 0 && expRec.d > 0 && expRec.l > 0 && rn.label === `${expRec.n} of ${fx.n} matches counted` && JSON.stringify(rn.wdl) === JSON.stringify([expRec.w, expRec.d, expRec.l]), JSON.stringify(rn));
  check('...and says Neutral and no choice are left out', /Neutral and no choice are left out/.test(await p5.textContent('#meStats')), '');
  check('The backup banner is raised by a supporter choice (Tickets sub-tab)', await (async () => { await p5.click('#meTabTix'); return !(await p5.$eval('#meBackup', e => e.hidden)); })(), '');
  await sub5('#meTabStats', '#meStats');
  await harvest(); await p5.reload(); await p5.waitForSelector('#meStats .astat').catch(() => {});
  await open5();
  rn = await recordNow();
  check('After a reload the choices and the record are still there', rn.label === `${expRec.n} of ${fx.n} matches counted` && JSON.stringify(rn.wdl) === JSON.stringify([expRec.w, expRec.d, expRec.l]), JSON.stringify(rn));

  // ---- The paste box
  const mk = (id, extra) => Object.assign({id, date: '2025-05-01', competition: {ro: 'Cupa ' + TAG, en: 'Cup ' + TAG}, stage: {ro: 'Finala', en: 'Final'},
    home: {name: 'Imp Casa ' + TAG, nameEn: 'Imp Home ' + TAG, short: 'IMH'}, away: {name: 'Imp Oaspeți ' + TAG, nameEn: 'Imp Away ' + TAG, short: 'IMA'},
    score: '3-1', stadium: 'Imp Ground ' + TAG, city: {ro: 'Orașul', en: 'Town'}, country: {ro: 'Țara', en: 'Land'},
    attendance: {value: fx.big + 1, approx: false, soldOut: false, fullHouse: false},
    goals: [{team: 'home', player: 'P One', minute: 10}, {team: 'home', player: 'P Two', minute: 20, pen: true}, {team: 'home', player: 'P Three', minute: 30}, {team: 'away', player: 'Q One', minute: 40}],
    cards: [], cardsComplete: true}, extra || {});
  await sub5('#meTabMatches', '#meMatches');
  await p5.click('#aAdd summary');
  const paste = async text => { await p5.fill('#aImpBox', typeof text === 'string' ? text : JSON.stringify(text)); await p5.click('#aImpBtn'); return (await p5.textContent('#aImpMsg')).trim(); };
  const bads = [
    ['text that is not JSON', '{"id": ', /not valid JSON/],
    ['an empty list', '[]', /list is empty/],
    ['a match with no score', mk('bad1' + TAG, {score: undefined}), /"score" must look like/],
    ['a score that is not a score', mk('bad2' + TAG, {score: 'big win'}), /"score"/],
    ['an unknown field', mk('bad3' + TAG, {bonus: 1}), /unknown field "bonus"/],
    ['an impossible date', mk('bad4' + TAG, {date: '2025-02-30'}), /"date"/],
    ['an id with a space', mk('has space', {}), /"id"/],
    ['a goal with a text minute', mk('bad5' + TAG, {goals: [{team: 'home', player: 'X', minute: 'ten'}]}), /"minute"/],
    ['a team with no name', mk('bad6' + TAG, {home: {short: 'X'}}), /home\.name/],
    ['an id the file already uses', mk(ATTF.matches[0].id), /already used by a match in data\/attended\.json/],
    ['the same id twice in one paste', [mk('dup' + TAG), mk('dup' + TAG)], /appears twice/],
    ['a list with one good and one bad match', [mk('ok' + TAG), mk('bad7' + TAG, {score: 'x'})], /match 2/],
    ['a kickoff that is not HH:MM', mk('bad8' + TAG, {kickoff: '8pm'}), /"kickoff" must be a time like "20:45"/],
    ['a kickoff hour past 23', mk('bad9' + TAG, {kickoff: '24:00'}), /"kickoff"/],
    ['a kickoff given as a number', mk('bad10' + TAG, {kickoff: 2045}), /"kickoff"/],
  ];
  const badRes = [];
  for(const [what, text, re] of bads){
    const m = await paste(text);
    if(!/^Not added|nothing was stored|Not added/.test(m) || !re.test(m)) badRes.push(`${what}: ${m.slice(0, 160)}`);
  }
  check('Invalid pastes are rejected, each with a reason that names the problem', !badRes.length, badRes.join(' | '));
  check('...and nothing was stored: no football-attended-imported key, the list still has the file\'s matches only',
    await lsGet(IMPK) === null && (await p5.$$('#meMatches .acard')).length === fx.n, String(await lsGet(IMPK)));
  const okMsg = await paste(mk(IMPID, {kickoff: '19:30'}));    // an optional kickoff, no source needed
  check('A valid match is accepted with a message', /^Added 1 imported match/.test(okMsg), okMsg);
  const impStored = JSON.parse(await lsGet(IMPK));
  check('...stored only under football-attended-imported ({version, matches}), with the id as pasted', impStored.version === 1 && impStored.matches.length === 1 && impStored.matches[0].id === IMPID &&
    impStored.matches[0].home.name === 'Imp Casa ' + TAG, JSON.stringify(impStored).slice(0, 120));
  const cards5 = await p5.$$eval('#meMatches .acard', cs => cs.map(c => ({id: c.dataset.id, text: c.textContent.replace(/\s+/g, ' ')})));
  check('The list has one more card; only the imported one is marked "Imported on this device"; its own id space is "imp:" + id',
    cards5.length === fx.n + 1 && cards5.filter(c => /Imported on this device/.test(c.text)).map(c => c.id).join() === IMPKEY && cards5.every(c => c.id === IMPKEY || attOrder.some(m => m.id === c.id)), cards5.map(c => c.id).slice(-2).join());
  check('The imported match is sorted by its date (oldest first) and numbered with the others', cards5.findIndex(c => c.id === IMPKEY) === attOrder.filter(m => m.date <= '2025-05-01').length &&
    cards5.every((c, i) => c.text.startsWith(String(i + 1))), String(cards5.findIndex(c => c.id === IMPKEY)));
  check('Pasting the same id again is rejected as already imported on this device, and the stored list is unchanged',
    /already imported on this device/.test(await paste(mk(IMPID))) && (await lsGet(IMPK)) === JSON.stringify(impStored), '');
  await noOver5('Matches tab with the add box open and a message: nothing overflows at 390 px');
  await sub5('#meTabStats', '#meStats');
  const tl = await tiles();
  check('The imported match is in the stats: matches, goals and stadiums include it', tl[0] === fx.n + 1 && tl[1] === fx.goals + 4 && tl[2] === fx.pens + 1 && tl[3] === fx.stadiums + 1, JSON.stringify(tl) + ` vs ${fx.n + 1},${fx.goals + 4},${fx.pens + 1},${fx.stadiums + 1}`);
  check('...and its crowd is the biggest crowd', /Imp Home .* – Imp Away/.test(await p5.$eval('#meStats', e => e.textContent).then(t => { const i = t.indexOf('Biggest crowd'); return i < 0 ? '' : t.slice(i, i + 160); })), '');
  await openCard('#meTabMatches', '#meMatches', IMPKEY);
  const impSheet = await sheetText5();
  check('An imported match with a kickoff (no source) shows "Kick-off 19:30 (local time)" on its card and in its sheet header', impStored.matches[0].kickoff === '19:30' &&
    cards5.find(c => c.id === IMPKEY).text.includes('Kick-off 19:30 (local time)') && (await p5.$eval('#asheetHead', h => h.innerText)).includes('Kick-off 19:30 (local time)'), '');
  check('The imported match\'s sheet says "Imported on this device", has supporter buttons and a remove control',
    /Imported on this device/.test(impSheet) && !!(await p5.$('#aSupport')) && !!(await p5.$('#aImpRemove')), impSheet.slice(0, 160));
  check('A file match\'s sheet has no "Imported" label and no remove control', await (async () => {
    await closeSheet5(); await openCard('#meTabMatches', '#meMatches', attOrder[5].id); const t = await sheetText5(); const no = !/Imported on this device/.test(t) && !(await p5.$('#aImpRemove')); await closeSheet5(); return no; })(), '');
  await openCard('#meTabMatches', '#meMatches', IMPKEY);
  await p5.click('#aSupport button[data-sup=home]');
  const sp2 = JSON.parse(await lsGet(SUPK));
  check('A supporter choice on the imported match is kept under its own key, beside the file matches\' (ids kept separate)', sp2[IMPKEY] && sp2[IMPKEY].supported === 'home' && !(IMPID in sp2), Object.keys(sp2).join());
  expRec.n++; expRec.w++;
  await closeSheet5(); await sub5('#meTabStats', '#meStats');
  rn = await recordNow();
  check('...and the record counts it: "n of total" grows with the imported match', rn.label === `${expRec.n} of ${fx.n + 1} matches counted` && JSON.stringify(rn.wdl) === JSON.stringify([expRec.w, expRec.d, expRec.l]), JSON.stringify(rn));
  await noOver5('Stats tab with the record: nothing overflows at 390 px');

  // ---- Photos and videos (on the imported match's sheet)
  await openCard('#meTabMatches', '#meMatches', IMPKEY);
  await p5.setInputFiles('#aMfile', [{name: 'a.png', mimeType: 'image/png', buffer: PNG}, {name: 'b.png', mimeType: 'image/png', buffer: PNG},
    {name: 'clip.mp4', mimeType: 'video/mp4', buffer: Buffer.from('not really a video')}, {name: 'notes.txt', mimeType: 'text/plain', buffer: Buffer.from('x')}]);
  await p5.waitForFunction(() => document.querySelectorAll('#aMgrid .amcell').length === 3, null, {timeout: 10000}).catch(() => {});
  const mm = await p5.evaluate(() => ({cells: [...document.querySelectorAll('#aMgrid .amcell')].map(c => c.querySelector('video') ? 'video' : c.querySelector('img') ? 'image' : '?'),
    msg: document.getElementById('aMmsg').textContent, count: document.getElementById('aMcount').textContent, hint: document.getElementById('aMedia').innerText}));
  check('Media: two photos and a video are added, shown as thumbnails; a text file is refused by name', JSON.stringify(mm.cells.sort()) === '["image","image","video"]' && /Added 3/.test(mm.msg) && /notes\.txt is not a photo or a video/.test(mm.msg), JSON.stringify(mm));
  check('...with a count, and a note that files stay on this device only and are not in the export', /3 files/.test(mm.count) && /device only/.test(mm.hint) && /not in the Me tab export/.test(mm.hint), mm.count);
  const idbItems = () => p5.evaluate(() => new Promise((res, rej) => {
    const rq = indexedDB.open('football-attended-media');
    rq.onsuccess = () => { const db = rq.result, g = db.transaction('items').objectStore('items').getAll(); g.onsuccess = () => { db.close(); res(g.result.map(x => ({entryId: x.entryId, name: x.name, kind: x.kind, size: x.size, blob: x.blob instanceof Blob}))); }; };
    rq.onerror = () => rej(rq.error);
  }));
  let items5 = await idbItems();
  check('Stored in the IndexedDB football-attended-media, keyed by the entry id (imp:…), as blobs, with name, kind and size',
    items5.length === 3 && items5.every(i => i.entryId === IMPKEY && i.blob && i.size > 0) && items5.filter(i => i.kind === 'video').map(i => i.name).join() === 'clip.mp4', JSON.stringify(items5));
  check('Nothing of the media is in localStorage', !(await p5.evaluate(() => JSON.stringify(Object.assign({}, localStorage)))).match(/a\.png|clip\.mp4|blob:/), '');
  await noOver5('Imported match sheet with media: nothing overflows at 390 px');
  await p5.click('#aMgrid .amcell >> nth=0');
  await p5.waitForSelector('#amover');
  const vw = await p5.evaluate(() => { const o = document.getElementById('amover'), r = o.getBoundingClientRect(), im = o.querySelector('img, video'), ir = im.getBoundingClientRect();
    return {w: r.width, h: r.height, imgIn: ir.left >= -1 && ir.right <= innerWidth + 1 && ir.bottom <= innerHeight + 1, btns: [...o.querySelectorAll('button')].map(b => b.getBoundingClientRect().height), z: +getComputedStyle(o).zIndex}; });
  check('Tapping a thumbnail opens a full-screen viewer above the sheet with Close and Delete (44 px), the picture inside the screen', vw.w === W && vw.h === H && vw.imgIn && vw.btns.length === 2 && vw.btns.every(h => h >= 44) && vw.z > 1001, JSON.stringify(vw));
  await p5.keyboard.press('Escape');
  check('Escape closes the viewer first and leaves the sheet open', !(await p5.$('#amover')) && !(await p5.$eval('#asheet', s => s.hidden)), '');
  await p5.click('#aMgrid .amcell >> nth=0'); await p5.waitForSelector('#amover');
  await p5.click('#amover [data-mdel]');
  await p5.waitForFunction(() => document.querySelectorAll('#aMgrid .amcell').length === 2 && !document.getElementById('amover'), null, {timeout: 10000}).catch(() => {});
  items5 = await idbItems();
  check('Delete (asks first) removes that one file from the grid and from the database', items5.length === 2 && (await p5.$$('#aMgrid .amcell')).length === 2 && /Deleted/.test(await p5.textContent('#aMmsg')), JSON.stringify(items5.map(i => i.name)));
  await closeSheet5();
  await harvest(); await p5.reload(); await open5();
  await openCard('#meTabMatches', '#meMatches', IMPKEY);
  await p5.waitForFunction(() => document.querySelectorAll('#aMgrid .amcell').length === 2, null, {timeout: 10000}).catch(() => {});
  check('After a reload the two remaining files are still on the sheet, and the imported match is still in the list', (await p5.$$('#aMgrid .amcell')).length === 2 && !(await p5.$eval('#asheet', s => s.hidden)), '');
  await closeSheet5();
  const ev0 = ATTF.events[0];
  await openCard('#meTabEvents', '#meEvents', ev0.id);
  await p5.setInputFiles('#aMfile', [{name: 'ev.png', mimeType: 'image/png', buffer: PNG}]);
  await p5.waitForFunction(() => document.querySelectorAll('#aMgrid .amcell').length === 1, null, {timeout: 10000}).catch(() => {});
  items5 = await idbItems();
  check('An event\'s sheet takes photos too, kept under the event\'s id and separate from the match\'s', items5.filter(i => i.entryId === ev0.id).length === 1 && items5.filter(i => i.entryId === IMPKEY).length === 2, JSON.stringify(items5.map(i => i.entryId)));
  await closeSheet5();

  // ---- The Me export (version 3 since the imported events; version 2 files still import)
  const rowMatch = ATTF.matches.find(m => !picks.some(([pm]) => pm.id === m.id)), ROWV = 'Row 12 ' + TAG;
  await openCard('#meTabMatches', '#meMatches', rowMatch.id);
  await p5.fill('#asheetBody [data-pf="row"]', ROWV); await closeSheet5();
  await sub5('#meTabTix', '#meBody');
  check('The backup banner is up before the export (the attended data changed)', !(await p5.$eval('#meBackup', e => e.hidden)), '');
  const exp5 = await download(p5, () => p5.click('#meExport'));
  const f5 = JSON.parse(exp5.text);
  check('Export: version 3 with the personal fields, the supporter choices, the imported matches and the (empty) imported events',
    f5.version === 3 && Array.isArray(f5.importedEvents) && !f5.importedEvents.length && f5.format === 'football-planner-me' && JSON.stringify(f5.personal) === await lsGet(SUPK) && f5.importedMatches.length === 1 && f5.importedMatches[0].id === IMPID &&
    picks.every(([m, sup]) => f5.personal[m.id].supported === sup) && f5.personal[IMPKEY].supported === 'home', Object.keys(f5).join());
  check('Export: the personal record carries "row" as typed, beside the other fields, and the file stays version 3', f5.personal[rowMatch.id] && f5.personal[rowMatch.id].row === ROWV && Object.keys(f5.personal[rowMatch.id]).join() === 'row' && f5.version === 3, JSON.stringify(f5.personal[rowMatch.id]));
  check('Export: says photos and videos are not included, and holds none (no media name, no blob)', /not in this file/.test(f5.notIncluded || '') && !/a\.png|clip\.mp4|ev\.png|blob:/.test(exp5.text) &&
    /Photos and videos are not included/.test(await p5.textContent('#meMsg')) && /Photos and videos are not in the file/.test(await p5.textContent('#meBody')), f5.notIncluded);
  check('The banner goes after the export', await p5.$eval('#meBackup', e => e.hidden), '');
  const exportFile5 = path.join(require('os').tmpdir(), `me-export5-${TAG}.json`);
  const importFile = async (obj, name) => {
    const fp = path.join(require('os').tmpdir(), `me-${name}-${TAG}.json`);
    fs.writeFileSync(fp, typeof obj === 'string' ? obj : JSON.stringify(obj));
    await p5.setInputFiles('#meFile', []); await p5.setInputFiles('#meFile', fp);
    await p5.waitForFunction(() => document.getElementById('meConfirm') || /Not imported/.test(document.getElementById('meMsg')?.textContent || ''), null, {timeout: 8000}).catch(() => {});
    const r = {confirm: (await p5.$('#meConfirm')) ? await p5.textContent('#meConfirm') : '', msg: (await p5.$('#meMsg')) ? await p5.textContent('#meMsg') : ''};
    fs.unlinkSync(fp); return r;
  };
  const dev = async () => JSON.stringify([await lsGet(SUPK), await lsGet(IMPK)]);
  const devBefore = await dev();
  const refusals = [
    ['a card number in a ticket field', Object.assign({}, f5, {personal: Object.assign({}, f5.personal, {[picks[0][0].id]: {ticket: '4111 1111 1111 1111'}})}), /payment card number/],
    ['a card number in "who I went with"', Object.assign({}, f5, {personal: Object.assign({}, f5.personal, {[picks[0][0].id]: {withWho: '4111-1111-1111-1111'}})}), /payment card number/],
    ['an imported match whose id the file already uses', Object.assign({}, f5, {importedMatches: [Object.assign({}, f5.importedMatches[0], {id: ATTF.matches[0].id})]}), /already used by a match in data\/attended\.json/],
    ['an invalid imported match', Object.assign({}, f5, {importedMatches: [Object.assign({}, f5.importedMatches[0], {score: 'x'})]}), /"score"/],
    ['a supporter choice that is not home, neutral or away', Object.assign({}, f5, {personal: {[picks[0][0].id]: {supported: 'both'}}}), /"supported" must be/],
    ['a card number in the row field', Object.assign({}, f5, {personal: Object.assign({}, f5.personal, {[picks[0][0].id]: {row: '4111 1111 1111 1111'}})}), /payment card number/],
    ['an unknown personal field', Object.assign({}, f5, {personal: {[picks[0][0].id]: {password: 'x'}}}), /unknown field "password"/],
    ['no personal object in a version 2 file', Object.assign({}, f5, {personal: undefined}), /no personal object/],
    ['a newer version', Object.assign({}, f5, {version: 4}), /newer version/],
    ['the old app\'s own export shape (no format, personal + imported)', {personal: {'2021-06-23-por-fra': {supported: 'home'}}, imported: []}, /not a Me-tab export/],
  ];
  const refBad = [];
  for(const [what, obj, re] of refusals){
    const r = await importFile(obj, 'bad');
    if(!/Not imported/.test(r.msg) || !re.test(r.msg) || !/Nothing on this device was changed/.test(r.msg) || r.confirm || await dev() !== devBefore) refBad.push(`${what}: ${r.msg.slice(0, 150)}`);
  }
  check('Import refuses (device unchanged): a card number, a clash with the file\'s ids, an invalid match, a bad choice, an unknown field, a missing object, a newer version, the old app\'s export', !refBad.length, refBad.join(' | '));
  await p5.evaluate(([a, b]) => { localStorage.removeItem(a); localStorage.removeItem(b); }, [SUPK, IMPK]);
  await harvest(); await p5.reload(); await open5(); await sub5('#meTabMatches', '#meMatches');
  check('With the attended data deleted from the device the list is the file\'s alone and the record is empty', (await p5.$$('#meMatches .acard')).length === fx.n, '');
  await p5.click('#meTabTix'); await p5.waitForSelector('#meFile', {state: 'attached'});
  const imp5 = await importFile(f5, 'good');
  check('Import first says what the file holds, including the attended records and imported matches', /holds 0 memberships, 0 tickets and \d+ favorites?, plus \d+ attended-match records? \(notes and supporter choices\) and 1 imported match/.test(imp5.confirm), imp5.confirm);
  await p5.click('[data-act=import-yes]');
  const msg5 = await p5.textContent('#meMsg');
  check('Round trip: the personal fields, supporter choices and imported matches are exactly as exported, and the message says they were replaced',
    await lsGet(SUPK) === JSON.stringify(f5.personal) && JSON.stringify(JSON.parse(await lsGet(IMPK)).matches) === JSON.stringify(f5.importedMatches) && /replaced by the file's/.test(msg5), msg5.slice(-160));
  check('Round trip: the row typed before the export is back, as typed', JSON.parse(await lsGet(SUPK))[rowMatch.id].row === ROWV, await lsGet(SUPK));
  check('...the banner is down after the import', await p5.$eval('#meBackup', e => e.hidden), '');
  await sub5('#meTabMatches', '#meMatches');
  check('...and the imported match is back in the list, marked', (await p5.$$('#meMatches .acard')).length === fx.n + 1 && /Imported on this device/.test(await p5.$eval(`#meMatches .acard[data-id="${IMPKEY}"]`, c => c.textContent)), '');
  await sub5('#meTabStats', '#meStats');
  rn = await recordNow();
  check('...and the record is what it was', rn.label === `${expRec.n} of ${fx.n + 1} matches counted` && JSON.stringify(rn.wdl) === JSON.stringify([expRec.w, expRec.d, expRec.l]), JSON.stringify(rn));
  const dev2 = await dev();
  await p5.click('#meTabTix'); await p5.waitForSelector('#meFile', {state: 'attached'});
  const v1 = await importFile({format: 'football-planner-me', version: 1, memberships: [], tickets: [], favorites: [], settings: {renewWindowDays: 30}}, 'v1');
  await p5.click('[data-act=import-yes]');
  check('A version 1 file still imports and leaves the attended records and imported matches alone (and says so)', !v1.msg.includes('Not imported') && await dev() === dev2 &&
    /left as they are/.test(await p5.textContent('#meMsg')), (await p5.textContent('#meMsg')).slice(-120));

  // An older file (version 2: no row, no imported events; a seat that reads like a row) still imports unchanged, and its seat is kept as written
  const OLDSEAT = 'Row 8 Seat 8', v2old = Object.assign({}, f5, {version: 2, personal: Object.assign({}, f5.personal, {[rowMatch.id]: {block: 'B3', seat: OLDSEAT}})}); delete v2old.importedEvents;
  await p5.click('#meTabTix'); await p5.waitForSelector('#meFile', {state: 'attached'});
  const v2r = await importFile(v2old, 'v2row'); await p5.click('[data-act=import-yes]');
  const oldRec = JSON.parse(await lsGet(SUPK))[rowMatch.id];
  check('An older file without "row" imports; the seat "Row 8 Seat 8" stays exactly as written and nothing is moved into Row', !v2r.msg.includes('Not imported') && JSON.stringify(oldRec) === JSON.stringify({block: 'B3', seat: OLDSEAT}), JSON.stringify(oldRec) + v2r.msg.slice(0, 100));

  // ---- xG, saves, passes and player ratings (2026-10-25)
  const base2 = {id: 'v', date: '2026-01-01', score: '1-0', home: {name: 'A'}, away: {name: 'B'}};
  const newStats = {xg: [1.84, 0.62], saves: [3, 7], passes: [[532, 606], [310, 402]]};
  const vrun = await p5.evaluate(b => {
    const run = ex => { const c = attCheckMatch(Object.assign({}, b, ex)); return c.rec ? 'ok' : c.errs.join('; '); };
    const xi = r => Array.from({length: 11}, (_, i) => Object.assign({no: i + 1, name: 'X' + i}, i === 0 && r !== undefined ? {rating: r} : {}));
    const st = ex => run({stats: Object.assign({xg: [1.8, 0.6], saves: [3, 7], passes: [[532, 606], [310, 402]]}, ex)});
    return {
      all: run({stats: {possession: [55, 45], xg: [1.84, 0.62], saves: [3, 7], passes: [[532, 606], [310, 402]]}, lineups: {home: {formation: '4-4-2', xi: xi(7.4), subs: [{minute: 60, on: 'S', off: 'X1', onRating: 6.8}], bench: [{no: 12, name: 'Bn'}]}}}),
      old: run({stats: {possession: [55, 45], shots: [10, 8]}, lineups: {home: {xi: xi(), bench: [{no: 12, name: 'Bn'}]}}}),
      nulls: run({stats: {xg: null, saves: null, passes: null}, lineups: {home: {xi: xi(null), subs: [{minute: 60, on: 'S', off: 'X1', onRating: null}]}}}),
      zeroTotal: st({passes: [[0, 0], [5, 10]]}), edge: st({xg: [0, 100], saves: [0, 1000], passes: [[0, 5000], [5000, 5000]]}),
      madeOverTotal: st({passes: [[607, 606], [310, 402]]}), xg101: st({xg: [1, 101]}), xgNeg: st({xg: [-0.1, 1]}), saves15: st({saves: [1.5, 7]}), saves1001: st({saves: [3, 1001]}),
      passes5001: st({passes: [[1, 5001], [1, 2]]}), passesDec: st({passes: [[1.5, 6], [1, 2]]}), passesFlat: st({passes: [532, 606]}), xgOne: st({xg: [1.8]}),
      r11: run({lineups: {home: {xi: xi(11)}}}), rNeg: run({lineups: {home: {xi: xi(-1)}}}), rStr: run({lineups: {home: {xi: xi('7')}}}), r10: run({lineups: {home: {xi: xi(10)}}}), r0: run({lineups: {home: {xi: xi(0.5)}}}),
      bench: run({lineups: {home: {xi: xi(), bench: [{no: 12, name: 'Bn', rating: 6}]}}}),
      onR11: run({lineups: {home: {xi: xi(), subs: [{minute: 60, on: 'S', off: 'X1', onRating: 11}]}}}),
      subRating: run({lineups: {home: {xi: xi(), subs: [{minute: 60, on: 'S', off: 'X1', rating: 6}]}}}),
      unknownStat: run({stats: {xgot: [1, 2]}}),
    };
  }, base2);
  check('The validator accepts a block with all the new fields (xg, saves, passes, a rating on an xi item, onRating on a sub), the old shape without them, and nulls as absent',
    vrun.all === 'ok' && vrun.old === 'ok' && vrun.nulls === 'ok', JSON.stringify([vrun.all, vrun.old, vrun.nulls]));
  check('...the limits are inclusive: xg 0 and 100, saves 0 and 1000, passes 0 and 5000, total 0 with made 0, a rating of 0.5 and of 10',
    vrun.edge === 'ok' && vrun.zeroTotal === 'ok' && vrun.r10 === 'ok' && vrun.r0 === 'ok', JSON.stringify([vrun.edge, vrun.zeroTotal, vrun.r10, vrun.r0]));
  const refusedWith = [['madeOverTotal', /stats\.passes.*made not above total/], ['passes5001', /stats\.passes/], ['passesDec', /stats\.passes/], ['passesFlat', /stats\.passes/],
    ['xg101', /stats\.xg.*0 to 100/], ['xgNeg', /stats\.xg/], ['xgOne', /stats\.xg/], ['saves15', /stats\.saves.*whole numbers/], ['saves1001', /stats\.saves/],
    ['r11', /xi 1: "rating" must be a number from 0 to 10/], ['rNeg', /"rating"/], ['rStr', /"rating"/], ['onR11', /subs 1: "onRating" must be a number from 0 to 10/],
    ['bench', /bench 1.*unknown field "rating"/], ['subRating', /subs 1.*unknown field "rating"/], ['unknownStat', /"stats" has an unknown field "xgot"/]];
  check('...and refuses made above total, rating 11 (also -1 and a text), saves 1.5, xg 101, a rating on a bench item or a sub, an unknown stat key, each with a reason that names the field',
    refusedWith.every(([k, re]) => re.test(vrun[k])), JSON.stringify(refusedWith.filter(([k, re]) => !re.test(vrun[k])).map(([k]) => [k, vrun[k]])));
  const NEWID = 'newfields-' + TAG, NEW2 = 'newfields2-' + TAG, OLDID = 'oldfields-' + TAG;
  const xiOf = (tag, rated) => Array.from({length: 11}, (_, i) => Object.assign({no: i + 1, name: `${tag} Player${i + 1}`}, rated && i < 4 ? {rating: [6.5, 7.4, 9, 10][i]} : {}));
  const luHome = {formation: '4-4-2', coach: 'Coach H', xi: xiOf('H', true), subs: [{minute: 60, on: 'H Sub Rated', off: 'H Player5', onRating: 6.8}, {minute: 70, on: 'H Sub Plain', off: 'H Player6'}]};
  const luAway = {coach: 'Coach A', xi: xiOf('A', true), subs: [{minute: 75, on: 'A Sub Rated', off: 'A Player5', onRating: 7.1}]};
  const PASS_FX = [[532, 606], [220, 294]];
  const mNew = mk(NEWID, {stats: {possession: [58, 42], xg: [1.84, 0.62], saves: [3, 7], passes: PASS_FX}, lineups: {home: luHome, away: luAway}});
  const mNew2 = mk(NEW2, {stats: {passes: [[0, 0], [5, 10]]}});
  const mOld = mk(OLDID, {stats: {possession: [58, 42], shots: [12, 9]}, lineups: {home: Object.assign({}, luHome, {xi: xiOf('H', false), subs: [{minute: 60, on: 'H Sub Plain', off: 'H Player5'}]})}});
  const sheetNew = async id => {
    await openCard('#meTabMatches', '#meMatches', 'imp:' + id);
    return p5.evaluate(() => ({
      rows: [...document.querySelectorAll('#aStats .abar')].map(b => [...b.querySelectorAll('.lb b, .lb span')].map(e => e.textContent.trim()).join('|')),
      rt: [...document.querySelectorAll('#asheet svg.apitch .rt')].map(e => e.textContent),
      pitchTexts: document.querySelectorAll('#asheet svg.apitch .nm').length,
      arat: [...document.querySelectorAll('#asheet .arat')].map(e => e.textContent), html: document.getElementById('asheet').innerHTML}));
  };
  await sub5('#meTabMatches', '#meMatches'); if(!(await p5.$eval('#aAdd', d => d.open))) await p5.click('#aAdd summary');
  for(const [m, w] of [[mNew, 'all new fields'], [mNew2, 'passes with a total of 0'], [mOld, 'no new fields']]){
    const msg = await paste(m);
    check(`Pasting a match with ${w} is accepted`, /^Added 1 imported match/.test(msg), msg);
  }
  let sh = await sheetNew(NEWID);
  check('The stats pane draws the six old rows first, then xG, Saves and Passes: "1.84|xG|0.62", "3|Saves|7", passes as the app-worked-out percentage with the counts "88% (532/606)" and "75% (220/294)"',
    JSON.stringify(sh.rows) === JSON.stringify(['58|Possession|42', '1.84|xG|0.62', '3|Saves|7', '88% (532/606)|Passes|75% (220/294)']), JSON.stringify(sh.rows));
  const widths = await p5.evaluate(() => [...document.querySelectorAll('#aStats .abar')].map(b => [...b.querySelectorAll('.tr i')].map(i => i.getBoundingClientRect().width)));
  const pc = PASS_FX.map(q => q[0] / q[1]), wP = widths[widths.length - 1], wX = widths[1], wS = widths[2];
  check('The passes bars are in the ratio of the two percentages worked out from the fixture (532/606 against 220/294), within 2%, on the same scale',
    Math.abs((wP[0] / wP[1]) / (pc[0] / pc[1]) - 1) < 0.02, JSON.stringify({wP, want: pc[0] / pc[1]}));
  check('xG and Saves keep the sizing of the existing rows: each bar is its value\'s share of the two values added up (1.84 : 0.62, 3 : 7), within 2%',
    Math.abs(wX[0] / (wX[0] + wX[1]) - 1.84 / (1.84 + 0.62)) < 0.02 && Math.abs(wS[0] / (wS[0] + wS[1]) - 3 / 10) < 0.02, JSON.stringify({wX, wS}));
  check('The pitch picture shows the four ratings beside the players (6.5, 7.4, 9.0, 10.0), nothing for the other seven; the names are still all there (11)',
    JSON.stringify(sh.rt) === JSON.stringify(['6.5', '7.4', '9.0', '10.0']) && sh.pitchTexts === 11, JSON.stringify([sh.rt, sh.pitchTexts]));
  check('The subs list shows 6.8 beside the rated player who came on and nothing beside the unrated one', JSON.stringify(sh.arat) === JSON.stringify(['6.8']), JSON.stringify(sh.arat));
  const geom = async () => p5.evaluate(() => {
    const sheet = document.getElementById('asheet'), out = {over: sheet.scrollWidth > sheet.clientWidth + 1, clip: [], overlap: []};
    const svg = sheet.querySelector('svg.apitch');
    if(svg){
      const els = [...svg.querySelectorAll('.nm, .rt')].map(e => { const b = e.getBBox(); return {c: e.getAttribute('class'), x: b.x, y: b.y, w: b.width, h: b.height, t: e.textContent}; });
      els.forEach(e => { if(e.x < 0 || e.y < 0 || e.x + e.w > 300 || e.y + e.h > 400) out.clip.push(e.t); });
      for(let i = 0; i < els.length; i++) for(let j = i + 1; j < els.length; j++){
        const a = els[i], b = els[j];
        if(a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h) out.overlap.push(a.t + '/' + b.t);
      }
    }
    sheet.querySelectorAll('.arow .k, .aev .tx').forEach(e => { const r = e.getBoundingClientRect(), sr = sheet.getBoundingClientRect(); if(r.left < sr.left - 1 || r.right > sr.right + 1) out.clip.push(e.textContent.slice(0, 20)); });
    return out;
  });
  await p5.setViewportSize({width: 360, height: 844}); await p5.waitForTimeout(300);
  let g = await geom();
  check('At 360 px wide the pitch picture and the stats pane do not scroll sideways, no name or rating leaves the picture, and no rating overlaps a name or another rating',
    !g.over && !g.clip.length && !g.overlap.length, JSON.stringify(g));
  const statLb = await p5.evaluate(() => [...document.querySelectorAll('#aStats .abar .lb')].map(l => l.scrollWidth <= l.clientWidth + 1));
  check('...and no stats row is wider than its box at 360 px (the passes row with both percentages included)', statLb.every(Boolean), JSON.stringify(statLb));
  await p5.click('#asheet .asw button[data-side=away]'); await p5.waitForTimeout(200);
  const away = await p5.evaluate(() => ({arat: [...document.querySelectorAll('#aluSide .arat')].map(e => e.textContent), pitch: !!document.querySelector('#aluSide svg.apitch'),
    rows: [...document.querySelectorAll('#aluSide .arow .k')].map(e => e.textContent.replace(/\s+/g, ' ').trim()).slice(0, 5)}));
  check('The away side has no formation, so it is a list: the ratings sit beside the names (6.5, 7.4, 9.0, 10.0) and 7.1 beside the player who came on',
    !away.pitch && JSON.stringify(away.arat) === JSON.stringify(['6.5', '7.4', '9.0', '10.0', '7.1']) && away.rows[0] === 'A Player16.5', JSON.stringify(away));
  g = await geom();
  check('At 360 px the list view (names with ratings) stays inside the sheet', !g.over && !g.clip.length, JSON.stringify(g));
  await p5.setViewportSize({width: W, height: H}); await p5.waitForTimeout(200);
  await closeSheet5();
  sh = await sheetNew(NEW2);
  check('Passes with a total of 0 draw a dash, not 0% or NaN, and a total above 0 still draws its percentage: "–|Passes|50% (5/10)"; no xG, no Saves row',
    JSON.stringify(sh.rows) === JSON.stringify(['–|Passes|50% (5/10)']), JSON.stringify(sh.rows));
  const w0 = await p5.evaluate(() => [...document.querySelectorAll('#aStats .abar .tr i')].map(i => i.getBoundingClientRect().width));
  check('...and the side with total 0 has no bar (width 0) while the other side has one', w0[0] === 0 && w0[1] > 0, JSON.stringify(w0));
  await closeSheet5();
  sh = await sheetNew(OLDID);
  check('A match without any new field draws unchanged: two stat rows, no rating on the pitch, in the subs or anywhere, and no ".arat" in the sheet',
    JSON.stringify(sh.rows) === JSON.stringify(['58|Possession|42', '12|Shots|9']) && !sh.rt.length && !sh.arat.length && !/arat/.test(sh.html) && sh.pitchTexts === 11, JSON.stringify([sh.rows, sh.rt, sh.arat]));
  await closeSheet5();
  for(const id of [NEWID, NEW2, OLDID]){
    await openCard('#meTabMatches', '#meMatches', 'imp:' + id); await p5.click('#aImpRemove');
    await p5.waitForFunction(() => document.getElementById('asheet').hidden, null, {timeout: 5000}).catch(() => {}); await p5.waitForTimeout(300);
  }
  check('...the three test matches are removed again (the list is back to the file\'s matches plus the one imported earlier)', (await p5.$$('#meMatches .acard')).length === fx.n + 1, '');

  // ---- Removing an imported match
  await openCard('#meTabMatches', '#meMatches', IMPKEY);
  await p5.click('#aImpRemove');
  await p5.waitForFunction(() => document.getElementById('asheet').hidden, null, {timeout: 5000}).catch(() => {});
  await p5.waitForTimeout(300);
  check('Removing an imported match (asks first) takes it off the list, out of storage, with its notes, its supporter choice and its photos and videos',
    (await p5.$$('#meMatches .acard')).length === fx.n && JSON.parse(await lsGet(IMPK)).matches.length === 0 && !(IMPKEY in JSON.parse(await lsGet(SUPK))) && !(await idbItems()).some(i => i.entryId === IMPKEY), '');

  // ---- Romanian: the new strings fit at 390 px
  await p5.evaluate(() => setLang('ro'));
  await sub5('#meTabMatches', '#meMatches');
  if(!(await p5.$eval('#aAdd', d => d.open))) await p5.click('#aAdd summary');
  await p5.fill('#aImpBox', '{"id": ');
  await p5.click('#aImpBtn');
  check('Romanian: the add box, its hint and its message are in Romanian', /Adaugă un meci/.test(await p5.textContent('#aAdd summary')) && /nu este JSON valid/.test(await p5.textContent('#aImpMsg')), '');
  await noOver5('Romanian: the Matches tab with the add box open does not overflow at 390 px');
  await openCard('#meTabMatches', '#meMatches', attOrder[0].id);
  check('Romanian: the supporter buttons, the media section and the hint', /Cu cine am ținut/.test(await sheetText5()) && /Poze și filmări/.test(await sheetText5()) && /Adaugă din galerie/.test(await sheetText5()), '');
  await noOver5('Romanian: a match sheet does not overflow at 390 px');
  await closeSheet5();
  await sub5('#meTabStats', '#meStats');
  check('Romanian: the record section', /Bilanț cu echipa susținută/.test(await p5.textContent('#meStats')) && /meciuri numărate/.test(await p5.textContent('#aRecCount')), '');
  await noOver5('Romanian: My stats does not overflow at 390 px');
  await p5.evaluate(() => setLang('en'));

  // ---- Every storage read and write, and every IndexedDB open
  await harvest();
  const uniq = a => [...new Set(a)].sort().join(',');
  check('Every storage read made by the page was recorded; none is an mf_ key; both new keys were read', rec5.reads.length > 20 && !rec5.reads.some(k => String(k).startsWith('mf_')) && rec5.reads.includes(SUPK) && rec5.reads.includes(IMPK), uniq(rec5.reads));
  check('Every storage write was recorded; none is an mf_ key; the new keys were written', !rec5.writes.some(k => String(k).startsWith('mf_')) && rec5.writes.includes(SUPK) && rec5.writes.includes(IMPK), uniq(rec5.writes));
  check('Every IndexedDB open was recorded; none is mf_media or any mf_ name; football-attended-media was opened', !rec5.idb.some(n => String(n).startsWith('mf_')) && rec5.idb.includes('football-attended-media'), uniq(rec5.idb));
  check('The old app\'s seeded keys are untouched and not shown (mf_personal, mf_imported), and there is no mf_media database',
    await lsGet('mf_personal') === OLD_SEED.personal && await lsGet('mf_imported') === OLD_SEED.imported && !(await p5.evaluate(() => indexedDB.databases().then(d => d.map(x => x.name)))).includes('mf_media') &&
    !/OLDIMP|OLDAPPNOTE/.test(await p5.evaluate(() => document.body.innerText)), '');
  check('The page wrote nothing to the repository: no request other than GET reached the server', !nonGet.length, nonGet.join(', '));

  // ---- Every match of the file, pasted again with a new id, is accepted: the validator reads the real format
  const rawRound = JSON.parse(JSON.stringify(ATTF.matches)).map(m => Object.assign(m, {id: 'copy-' + m.id}));
  await sub5('#meTabMatches', '#meMatches');
  if(!(await p5.$eval('#aAdd', d => d.open))) await p5.click('#aAdd summary');
  await p5.fill('#aImpBox', JSON.stringify(rawRound));
  await p5.click('#aImpBtn');
  const bigMsg = (await p5.textContent('#aImpMsg')).trim();
  check(`All ${fx.n} matches of data/attended.json, pasted as a list with new ids (line-ups, stats, notes and all), are accepted`, new RegExp(`^Added ${fx.n} imported match`).test(bigMsg) && (await p5.$$('#meMatches .acard')).length === 2 * fx.n, bigMsg.slice(0, 200));
  const sheetsBad = [];
  for(const m of ATTF.matches.filter(m => m.lineups).slice(0, 3)){
    await openCard('#meTabMatches', '#meMatches', 'imp:copy-' + m.id);
    const st = await sheetState(p5);
    if(!st.h4.includes('Line-ups') || !st.h4.includes('Who I supported') || !st.h4.includes('Photos and videos') || (st.empty && st.empty.length)) sheetsBad.push(m.id + ' ' + JSON.stringify(st.h4));
    const o = await over5(); if(o.bad.length || o.sb > 1) sheetsBad.push(m.id + ' overflow ' + JSON.stringify(o));
    await closeSheet5();
  }
  check('...and an imported copy opens the full sheet (line-ups, pitch, supporter buttons, media) with no empty pane and no overflow at 390 px', !sheetsBad.length, sheetsBad.join(' | '));
  await ctx5.close();

  // ---- Refused storage: the page says so and does not fail
  const ctx6 = await newCtx({blockStorage: true});
  await ctx6.addInitScript(() => { IDBFactory.prototype.open = function(){ throw new DOMException('denied', 'SecurityError'); }; });
  const p6 = await ctx6.newPage();
  p6.on('pageerror', e => errors.push(e.message));
  await p6.goto(BASE);
  await p6.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await p6.click('nav button[data-pane=me]');
  await p6.waitForSelector('#meStats .astat');
  await p6.click('#meTabMatches'); await p6.waitForSelector('#meMatches .acard');
  await p6.click('#aAdd summary');
  check('With storage blocked the add box says imported matches would last only until the page is closed', /last only until the page is closed/.test(await p6.textContent('#aAdd')), '');
  await p6.fill('#aImpBox', JSON.stringify(mk('blocked' + TAG)));
  await p6.click('#aImpBtn');
  check('...and a valid paste is refused with the reason (the browser refused to store it)', /refused to store them/.test(await p6.textContent('#aImpMsg')) && (await p6.$$('#meMatches .acard')).length === fx.n, await p6.textContent('#aImpMsg'));
  await p6.click(`#meMatches .acard[data-id="${attOrder[0].id}"]`); await p6.waitForTimeout(350);
  await p6.setInputFiles('#aMfile', [{name: 'a.png', mimeType: 'image/png', buffer: PNG}]);
  await p6.waitForFunction(() => /refuses to store photos and videos/.test(document.getElementById('aMmsg').textContent), null, {timeout: 8000}).catch(() => {});
  check('When the browser refuses to store media, the sheet says so clearly and adds nothing', /refuses to store photos and videos here/.test(await p6.textContent('#aMmsg')) && /refuses to store photos and videos here/.test(await p6.textContent('#aMgrid')) && !(await p6.$('#aMgrid .amcell')), await p6.textContent('#aMmsg'));
  await p6.click('#aSupport button[data-sup=home]');
  check('A supporter tap with storage blocked still works for the visit (no error)', (await p6.getAttribute('#aSupport button[data-sup=home]', 'aria-pressed')) === 'true', '');
  await ctx6.close();
  const ctx7 = await newCtx();
  await ctx7.addInitScript(() => { IDBObjectStore.prototype.add = function(){ throw new DOMException('full', 'QuotaExceededError'); }; });
  const p7 = await ctx7.newPage();
  p7.on('pageerror', e => errors.push(e.message));
  await p7.goto(BASE);
  await p7.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await p7.click('nav button[data-pane=me]'); await p7.click('#meTabMatches'); await p7.waitForSelector('#meMatches .acard');
  await p7.click(`#meMatches .acard[data-id="${attOrder[0].id}"]`); await p7.waitForTimeout(350);
  await p7.setInputFiles('#aMfile', [{name: 'big.png', mimeType: 'image/png', buffer: PNG}]);
  await p7.waitForFunction(() => /no room left/.test(document.getElementById('aMmsg').textContent), null, {timeout: 8000}).catch(() => {});
  check('When the browser\'s quota is exceeded the sheet says there is no room left, naming the file', /There is no room left on this device for big\.png/.test(await p7.textContent('#aMmsg')), await p7.textContent('#aMmsg'));
  await ctx7.close();

  }


  {
  // ---- 2026-10-13: the Add a match form (and Edit this match). Expected values are worked out here from the form's own input and
  //      from data/attended.json, never typed in as results. Own context, so the earlier blocks' counts are not disturbed.
  const IMPK = 'football-attended-imported', SUPK = 'football-attended-personal';
  const reqStart = requests.length;
  const ctxF = await newCtx();
  await ctxF.addInitScript(() => {
    window.__r = []; window.__w = []; window.__i = [];
    const g = Storage.prototype.getItem, w = Storage.prototype.setItem, r = Storage.prototype.removeItem;
    Storage.prototype.getItem = function(k){ window.__r.push(k); return g.call(this, k); };
    Storage.prototype.setItem = function(k, v){ window.__w.push(k); return w.call(this, k, v); };
    Storage.prototype.removeItem = function(k){ window.__w.push(k); return r.call(this, k); };
    const o = IDBFactory.prototype.open;
    IDBFactory.prototype.open = function(n){ window.__i.push(n); return o.apply(this, arguments); };
  });
  const pF = await ctxF.newPage();
  pF.on('pageerror', e => errors.push(e.message));
  pF.on('dialog', d => d.accept());
  await pF.goto(BASE);
  await pF.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await pF.click('nav button[data-pane=me]');
  await pF.waitForSelector('#meStats .astat');
  await pF.click('#meTabMatches'); await pF.waitForSelector('#meMatches .acard');
  const canon = o => JSON.stringify(o, (k, v) => v && typeof v === 'object' && !Array.isArray(v) ? Object.fromEntries(Object.entries(v).sort()) : v);
  const stored = async () => { const v = await pF.evaluate(k => localStorage.getItem(k), IMPK); return v ? JSON.parse(v).matches : []; };
  const openAdd = async () => { if(!(await pF.$eval('#aAdd', d => d.open))) await pF.click('#aAdd summary'); };
  const resetForm = async () => { await pF.click('#aFormCancel'); await openAdd(); };
  const msgF = async () => (await pF.textContent('#aImpMsg')).trim();
  const ferr = async name => (await pF.textContent(`#aForm [data-ferr="${name}"]`)).trim();
  const submitF = async () => { await pF.click('#aImpBtn'); return msgF(); };
  const setForm = async (v, goals = []) => {
    for(const [k, val] of Object.entries(v)) await pF.fill(`#aForm [name=${k}]`, val);
    for(const g of goals){
      await pF.click('#aGoalAdd');
      const row = pF.locator('#aGoals .agoal').last();
      await row.locator('[name=gteam]').selectOption(g.team); await row.locator('[name=gplayer]').fill(g.player); await row.locator('[name=gminute]').fill(g.minute);
    }
  };
  const part = s => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const overF = () => pF.evaluate(() => { const bad = [];
    document.getElementById('pane-me').querySelectorAll('*').forEach(x => { const r = x.getBoundingClientRect(); if(r.width > 0 && (r.right > innerWidth + 1 || r.left < -1)) bad.push(x.tagName + '.' + x.className); });
    return {bad: bad.slice(0, 4), doc: document.documentElement.scrollWidth}; });
  const idRe = /^[A-Za-z0-9._-]{1,80}$/;
  const openCardF = async key => { await pF.click('#meTabMatches'); await pF.waitForSelector('#meMatches .acard'); await pF.click(`#meMatches .acard[data-id="${key}"]`); await pF.waitForSelector('#asheet:not([hidden])'); await pF.waitForTimeout(350); };
  const H = 'Zürich Ünited ' + TAG, A = 'Åland FC ' + TAG, D = '2026-03-14';
  const F = {date: D, kickoff: '18:30', home: H, away: A, sh: '3', sa: '1', competition: 'Cup ' + TAG, stage: 'Round of 16', stadium: 'Ground ' + TAG, city: 'Town ' + TAG,
    attendance: '12345', referee: 'Ref ' + TAG, note: 'Line one ' + TAG + '\nLine two'};
  const FG = [{team: 'home', player: 'ScorerA' + TAG, minute: '10'}, {team: 'away', player: 'ScorerB' + TAG, minute: '67'}];   // one word each: the sheet shows a scorer's surname
  const expectRec = () => ({date: F.date, kickoff: F.kickoff, home: {name: F.home}, away: {name: F.away}, score: `${+F.sh}-${+F.sa}`, competition: F.competition, stage: F.stage,
    stadium: F.stadium, city: F.city, attendance: {value: +F.attendance}, referee: F.referee, note: F.note, goals: FG.map(g => ({team: g.team, player: g.player, minute: +g.minute}))});
  const strip = r => { const c = JSON.parse(JSON.stringify(r)); delete c.id; return c; };

  await openAdd();
  check('The Matches tab has the form: date picker, time picker, the team names, two number boxes for the score, the text fields, Add goal and the JSON box last, labelled optional',
    await pF.evaluate(() => { const f = document.getElementById('aForm'), n = [...f.elements].map(e => e.name || e.id).filter(Boolean);
      return f.elements.date.type === 'date' && f.elements.kickoff.type === 'time' && f.elements.sh.type === 'number' && f.elements.sa.type === 'number' && !!document.getElementById('aGoalAdd') &&
        n.indexOf('aImpBox') > n.indexOf('note') && n.indexOf('date') < n.indexOf('kickoff') && n.indexOf('kickoff') < n.indexOf('home') && n.indexOf('away') < n.indexOf('sh') && /optional/i.test(f.querySelector('.jsonbox .flab').textContent); }), '');
  check('...no field asks for an id', await pF.evaluate(() => ![...document.getElementById('aForm').elements].some(e => /^id$/i.test(e.name))), '');

  // Each missing required field is refused, with a reason next to the field, nothing stored and the rest of what was typed kept.
  const req = {date: ['date', 'date'], home: ['home', 'home'], away: ['away', 'away'], score: ['sa', 'score']};
  const reqBad = [];
  for(const [what, [field, errName]] of Object.entries(req)){
    await resetForm();
    const v = Object.assign({}, F); v[field] = '';
    await setForm(v);
    const m = await submitF();
    const kept = await pF.inputValue('#aForm [name=stadium]');
    if(!/^Not saved/.test(m) || !(await ferr(errName)) || (await stored()).length || kept !== F.stadium) reqBad.push(`${what}: ${m} / ${await ferr(errName)} / ${(await stored()).length} / ${kept}`);
  }
  check('Each missing required field (date, home team, away team, score) is refused with a reason next to that field, nothing is stored and the typed text is kept', !reqBad.length, reqBad.join(' | '));
  await resetForm();
  await setForm(Object.assign({}, F, {attendance: '12.5'}));
  check('A bad attendance is refused next to the field', /^Not saved/.test(await submitF()) && !!(await ferr('attendance')) && !(await stored()).length, '');

  // Goal rows: team names as typed, removable, a row with no scorer is refused next to the row.
  await resetForm();
  await setForm({home: H, away: A});
  await pF.click('#aGoalAdd'); await pF.click('#aGoalAdd');
  const opts = await pF.$$eval('#aGoals .agoal:first-child select option', os => os.map(o => o.textContent));
  check('Add goal adds a row whose team dropdown shows the typed home and away names; two rows are two rows', opts.join() === [H, A].join() && (await pF.$$('#aGoals .agoal')).length === 2, opts.join());
  await pF.fill('#aGoals .agoal:nth-child(2) [name=gminute]', '30');
  await pF.fill('#aForm [name=date]', D); await pF.fill('#aForm [name=sh]', '1'); await pF.fill('#aForm [name=sa]', '0');
  const mg = await submitF();
  check('A goal row with a minute and no scorer is refused next to that row and nothing is stored', /^Not saved/.test(mg) && !!(await ferr('g1')) && !(await stored()).length, mg + ' / ' + await ferr('g1'));
  await pF.click('#aGoals .agoal:nth-child(2) [data-gdel]');
  check('A goal row can be removed', (await pF.$$('#aGoals .agoal')).length === 1, '');

  // The whole form, saved.
  await resetForm();
  await setForm(F, FG);
  const okm = await submitF();
  let st = await stored();
  check('A filled form is saved with a message', /^Added 1 imported match/.test(okm) && st.length === 1, okm);
  check('Every form field lands in the stored record under the validator\'s own field name (date, kickoff, home.name, away.name, score "H-A", competition, stage, stadium, city, attendance.value, referee, note, goals as {team, player, minute})',
    canon(strip(st[0])) === canon(expectRec()), JSON.stringify(st[0]));
  const exId = `${D}-${part(H)}-${part(A)}`;
  check('The id is generated from the date and the team names (ASCII, allowed characters, at most 80)', st[0].id === exId && idRe.test(st[0].id), st[0].id + ' vs ' + exId);
  check('...and the form is empty again', await pF.evaluate(() => [...document.getElementById('aForm').elements].filter(e => /^(date|home|away|sh|sa|stadium|note)$/.test(e.name)).every(e => e.value === '') && !document.querySelector('.agoal')), '');
  await openAdd();
  await setForm(F, FG); const m2 = await submitF();
  await openAdd();
  await setForm(F); const m3 = await submitF();
  st = await stored();
  check('Two identical entries get unique ids: the second ends -2, the third -3', /^Added 1/.test(m2) && /^Added 1/.test(m3) && st.map(m => m.id).join() === [exId, exId + '-2', exId + '-3'].join(), st.map(m => m.id).join());
  await openAdd();
  const longH = 'Alpha '.repeat(11) + TAG, longA = 'Bravo '.repeat(11) + TAG;      // each name within the validator's 80 characters, the id well past 80
  await setForm(Object.assign({}, F, {home: longH, away: longA})); await submitF();
  await openAdd();
  await setForm(Object.assign({}, F, {home: longH, away: longA})); await submitF();
  st = await stored();
  const longIds = st.slice(3).map(m => m.id);
  check('A very long team name still gives a valid id of at most 80 characters, and a repeat is unique', longIds.length === 2 && longIds.every(i => idRe.test(i)) && longIds[0] !== longIds[1] && new Set(st.map(m => m.id)).size === st.length, longIds.map(i => i.length).join());
  const fileIds = new Set(ATTF.matches.map(m => m.id));
  check('No generated id equals an id of data/attended.json', st.every(m => !fileIds.has(m.id)), '');
  // The saved match in the list and its sheet.
  const key1 = 'imp:' + exId;
  await openCardF(key1);
  const sh1 = await pF.$eval('#asheet', s => s.innerText.replace(/\s+/g, ' ')), hd1 = await pF.$eval('#asheetHead', h => h.innerText);
  check('The sheet shows the goals (scorers and minutes), the kick-off, the note, and does not call the user\'s own note "written by an assistant"',
    FG.every(g => sh1.includes(g.player) && sh1.includes(g.minute + "'")) && hd1.includes(`Kick-off ${F.kickoff} (local time)`) && sh1.includes('Line one ' + TAG) && !/Written by an assistant/.test(sh1), sh1.slice(0, 200));
  check('...and has Edit this match and Remove; a match of the file has neither', !!(await pF.$('#aImpEdit')) && !!(await pF.$('#aImpRemove')) && await (async () => {
    await pF.click('#asheetClose'); await openCardF(attOrder[3].id); const no = !(await pF.$('#aImpEdit')); await pF.click('#asheetClose'); return no; })(), '');

  // The JSON box.
  const mj = (id, extra) => Object.assign({id, date: '2025-06-01', competition: {ro: 'Cupa ' + TAG, en: 'Cup ' + TAG}, home: {name: 'Edit Casa ' + TAG, nameEn: 'Edit Home ' + TAG, short: 'EDH'},
    away: {name: 'Edit Oaspeți ' + TAG}, score: '2-2', stadium: 'Old Ground', kickoff: '20:00', kickoffSource: 'user-supplied',
    goals: [{team: 'home', player: 'E One', minute: 5, pen: true}, {team: 'away', player: 'E Two', minute: 50, assist: 'E Three'}], cards: [{team: 'home', type: 'yellow', player: 'Y', minute: 30}],
    stats: {possession: [55, 45]}, lineups: {home: {formation: '4-4-2', coach: 'Coach'}}, note: {ro: 'Notă', en: 'Note'}}, extra || {});
  const jsonRound = async (v, goals, json) => { await resetForm(); await setForm(v, goals); await pF.fill('#aImpBox', typeof json === 'string' ? json : JSON.stringify(json)); return submitF(); };
  const nBefore = (await stored()).length;
  let m = await jsonRound({}, [], [mj('lst1' + TAG), mj('lst2' + TAG)]);
  check('Form empty + a list of two matches in the JSON box: accepted, as before', /^Added 2 imported match/.test(m) && (await stored()).length === nBefore + 2, m);
  const small = {date: '2026-04-01', home: 'Small Home ' + TAG, away: 'Small Away ' + TAG, sh: '1', sa: '0'};
  m = await jsonRound(small, [], [mj('lst3' + TAG)]);
  check('Form filled + a list in the JSON box: refused (one object only), nothing stored', /one match object/.test(m) && (await stored()).length === nBefore + 2, m);
  m = await jsonRound(small, [], '{"stadium": ');
  check('Form filled + JSON that is not JSON: refused, nothing stored', /not valid JSON/.test(m) && (await stored()).length === nBefore + 2, m);
  m = await jsonRound(small, [], {home: {nameEn: 'Small Home EN'}, lineups: {home: {formation: '4-3-3'}}});
  let st2 = await stored(), added = st2[st2.length - 1];
  check('Form filled + one object adding home.nameEn and lineups: accepted, merged at leaf level (the form\'s home.name kept), id generated',
    /^Added 1/.test(m) && st2.length === nBefore + 3 && canon(added.home) === canon({name: small.home, nameEn: 'Small Home EN'}) && added.lineups.home.formation === '4-3-3' && added.score === '1-0' &&
    added.id === `2026-04-01-${part(small.home)}-${part(small.away)}`, JSON.stringify(added).slice(0, 220));
  const cl = [['stadium', {stadium: 'From JSON'}, 'stadium'], ['home.name', {home: {name: 'Other'}}, 'home.name'], ['score', {score: '9-9'}, 'score'], ['date', {date: '2020-01-01'}, 'date'],
    ['competition as a pair', {competition: {ro: 'x', en: 'y'}}, 'competition'], ['note', {note: 'n'}, 'note']];
  const clBad = [];
  for(const [what, j, key] of cl){
    const before = (await stored()).length;
    const mm = await jsonRound(Object.assign({}, small, {stadium: 'Form Ground', competition: 'Form Cup', note: 'Form note'}), [], j);
    if(!(new RegExp(`both the form and the JSON fill "${key.replace('.', '\\.')}"`).test(mm)) || (await stored()).length !== before) clBad.push(`${what}: ${mm.slice(0, 120)}`);
  }
  check('Form filled + JSON repeating a filled field (stadium, home.name, score, date, competition, note): refused, the key named, nothing stored', !clBad.length, clBad.join(' | '));
  m = await jsonRound(small, [{team: 'home', player: 'G ' + TAG, minute: '3'}], {goals: [{team: 'home', player: 'X', minute: 1}]});
  check('Goals count as filled when the form has goal rows: a JSON "goals" is refused naming "goals"', /both the form and the JSON fill "goals"/.test(m), m);
  m = await jsonRound(small, [], {goals: [{team: 'home', player: 'J ' + TAG, minute: 1}]});
  st2 = await stored();
  check('...and with no goal rows in the form the JSON may supply the goals', /^Added 1/.test(m) && st2[st2.length - 1].goals[0].player === 'J ' + TAG, m);
  const noScore = Object.assign({}, small, {sh: '', sa: ''});
  m = await jsonRound(Object.assign({}, noScore, {stadium: ''}), [], {score: '4-4', stadium: 'Supplied ' + TAG, id: 'given-' + TAG});
  st2 = await stored(); added = st2[st2.length - 1];
  check('A field left empty in the form (the score, the stadium) is supplied by the JSON, and the JSON\'s own id is used', /^Added 1/.test(m) && added.score === '4-4' && added.stadium === 'Supplied ' + TAG && added.id === 'given-' + TAG, JSON.stringify(added).slice(0, 160));
  const nn = (await stored()).length;
  m = await jsonRound(small, [], {id: ATTF.matches[0].id});
  check('A JSON id the file already uses is refused', /already used by a match in data\/attended\.json/.test(m) && (await stored()).length === nn, m);
  m = await jsonRound(small, [], {id: 'given-' + TAG});
  check('...and so is one already on the device', /already imported on this device/.test(m) && (await stored()).length === nn, m);
  m = await jsonRound(small, [], {bonus: 1, kickoff: '8pm'});
  check('The merged result goes through the same validator: an unknown field and a bad kickoff are both refused, both reasons given, nothing stored',
    /unknown field "bonus"/.test(m) && /"kickoff" must be a time/.test(m) && (await stored()).length === nn, m);

  // Edit this match.
  const EID = 'edit-' + TAG, EKEY = 'imp:' + EID, orig = mj(EID);
  await jsonRound({}, [], orig);
  await openCardF(EKEY);
  await pF.fill('#asheetBody [data-pf=note]', 'Keep me ' + TAG);
  await pF.click('#aSupport button[data-sup=away]');
  await pF.setInputFiles('#aMfile', [{name: 'e.png', mimeType: 'image/png', buffer: PNG}]);
  await pF.waitForFunction(() => document.querySelectorAll('#aMgrid .amcell').length === 1, null, {timeout: 10000}).catch(() => {});
  await pF.waitForTimeout(300);
  const persBefore = JSON.parse(await pF.evaluate(k => localStorage.getItem(k), SUPK))[EKEY];
  const idbCount = () => pF.evaluate(key => new Promise((res, rej) => { const rq = indexedDB.open('football-attended-media');
    rq.onsuccess = () => { const db = rq.result, g = db.transaction('items').objectStore('items').getAll(); g.onsuccess = () => { db.close(); res(g.result.filter(x => x.entryId === key).length); }; };
    rq.onerror = () => rej(rq.error); }), EKEY);
  const media0 = await idbCount();
  await pF.click('#aImpEdit');
  await pF.waitForSelector('#aForm:not([data-edit=""])');
  const pre = await pF.evaluate(() => { const f = document.getElementById('aForm'); return {date: f.elements.date.value, kickoff: f.elements.kickoff.value, home: f.elements.home.value, away: f.elements.away.value,
    sh: f.elements.sh.value, sa: f.elements.sa.value, stadium: f.elements.stadium.value, competition: f.elements.competition.value, note: f.elements.note.value, goals: f.querySelectorAll('.agoal').length,
    json: !!document.getElementById('aImpBox'), edit: f.dataset.edit}; });
  const [oh, oa] = orig.score.split('-');
  check('Edit this match opens the same form pre-filled from the stored record (same id, score split in two boxes, goal rows), and the JSON box is hidden',
    pre.date === orig.date && pre.kickoff === orig.kickoff && pre.home === orig.home.name && pre.away === orig.away.name && pre.sh === oh && pre.sa === oa && pre.stadium === orig.stadium &&
    pre.goals === orig.goals.length && !pre.json && pre.edit === EID && pre.competition === orig.competition.en, JSON.stringify(pre));
  await pF.fill('#aForm [name=stadium]', 'New Ground ' + TAG); await pF.fill('#aForm [name=sh]', '3');
  await pF.fill('#aGoals .agoal:first-child [name=gminute]', '6');
  await pF.click('#aImpBtn');
  await pF.waitForSelector('#asheet:not([hidden])'); await pF.waitForTimeout(350);
  st2 = await stored();
  const exp = JSON.parse(JSON.stringify(orig)); exp.stadium = 'New Ground ' + TAG; exp.score = `3-${oa}`; exp.goals[0].minute = 6;
  check('Saving replaces only the fields the form covers: the record equals the original with just the stadium, the score and one goal minute changed (line-ups, stats, cards, kickoffSource, the goal\'s pen and assist, nameEn and the {ro, en} texts untouched)',
    canon(st2.find(x => x.id === EID)) === canon(exp) && st2.filter(x => x.id === EID).length === 1, JSON.stringify(st2.find(x => x.id === EID)));
  const persAfter = JSON.parse(await pF.evaluate(k => localStorage.getItem(k), SUPK))[EKEY];
  check('The id is kept, so the note and the supporter choice stay attached, and the sheet is back open on the same match',
    canon(persAfter) === canon(persBefore) && persAfter.note === 'Keep me ' + TAG && persAfter.supported === 'away' && (await pF.$eval('#asheetBody', b => b.dataset.open)) === 'match:' + EKEY, JSON.stringify(persAfter));
  check('...and the photo is still attached', media0 === 1 && (await idbCount()) === 1 && (await pF.$$('#aMgrid .amcell')).length === 1, String(media0));
  check('...and the sheet shows the new score and stadium', /3-2/.test(await pF.$eval('#asheetHead', h => h.innerText)) && /New Ground/.test(await pF.$eval('#asheet', s => s.innerText)), '');
  await pF.click('#asheetClose');
  await openCardF(EKEY); await pF.click('#aImpEdit'); await pF.waitForSelector('#aForm:not([data-edit=""])');
  await pF.fill('#aForm [name=home]', '');
  await pF.click('#aImpBtn');
  check('Editing: an emptied required field is refused next to the field and the stored record is unchanged', !!(await ferr('home')) && canon((await stored()).find(x => x.id === EID)) === canon(exp), '');
  await pF.click('#aFormCancel');
  check('Cancel leaves the form and the record as they were', !(await pF.$('#aForm:not([data-edit=""])')) && canon((await stored()).find(x => x.id === EID)) === canon(exp), '');

  // Both languages at 390 px, errors and goal rows showing.
  const fitBad = [];
  for(const lang of ['en', 'ro']){
    await pF.evaluate(l => setLang(l), lang);
    await pF.click('#meTabMatches'); await pF.waitForSelector('#aForm', {state: 'attached'});
    await openAdd();
    await setForm({home: 'Home ' + 'W'.repeat(30), away: 'Away ' + 'W'.repeat(30), sh: '1'}, [{team: 'away', player: 'P'.repeat(40), minute: ''}]);
    await pF.fill('#aImpBox', '{"x": ');
    await pF.click('#aImpBtn');
    const o = await overF();
    const txt = await pF.$eval('#aForm', f => f.innerText);
    if(o.bad.length || o.doc > W) fitBad.push(lang + ' ' + JSON.stringify(o));
    const want = lang === 'ro' ? [/Echipa gazdă/, /Adaugă gol/, /JSON \(opțional\)/, /Nesalvat/] : [/Home team/, /Add goal/, /JSON \(optional\)/, /Not saved/];
    if(!want.every(r => r.test(txt))) fitBad.push(lang + ' text ' + txt.slice(0, 120));
    await resetForm();
  }
  await pF.evaluate(() => setLang('en'));
  check('The form, its errors, a goal row and the JSON box fit at 390 px with no sideways scroll, in English and in Romanian, and are written in each language', !fitBad.length, fitBad.join(' | '));
  await pF.evaluate(() => setLang('ro'));
  await openCardF(EKEY);
  check('Romanian: the sheet\'s Edit this match button is in Romanian and the sheet does not overflow', /Modifică acest meci/.test(await pF.textContent('#aImpEdit')) && (await pF.evaluate(() => { const b = document.getElementById('asheetBody'); return b.scrollWidth - b.clientWidth; })) <= 1, '');
  await pF.evaluate(() => setLang('en'));

  // Storage and requests.
  const sr = await pF.evaluate(() => ({r: window.__r, w: window.__w, i: window.__i}));
  check('No mf_ key was read or written and no mf_ database opened by any of it', ![...sr.r, ...sr.w, ...sr.i].some(k => String(k).startsWith('mf_')) && sr.w.includes(IMPK), [...new Set(sr.w)].join());
  const typed = [TAG, 'Line one', 'ScorerA', 'Keep me'];
  const leaked = requests.slice(reqStart).filter(r => typed.some(s => (r.url + r.body + r.headers).includes(s) || (r.url + r.body + r.headers).includes(encodeURIComponent(s))));
  check('Nothing typed into the form, the JSON box or the sheet appears in any request (URL, body or headers)', !leaked.length, leaked.map(r => r.method + ' ' + r.url.slice(0, 80)).join(', '));
  check('No request other than GET reached the site during the form tests', !nonGet.length, nonGet.join(', '));
  await ctxF.close();
  }

  {
  // ---- 2026-10-15: exhibition matches leave the goal stats, and the Competition and Stadium fields of the match form offer suggestions.
  //      Expected values are worked out here from data/attended.json, data/competitions.csv and the club files, never typed in as results.
  //      Own context with an empty device, so the counts below are the file's plus what this block adds.
  const IMPK = 'football-attended-imported';
  const reqStart = requests.length, nonGet0 = nonGet.length;
  const FOLDX = {'ß': 'ss', 'ø': 'o', 'đ': 'd', 'ł': 'l', 'æ': 'ae', 'œ': 'oe', 'ı': 'i', 'þ': 'th', 'ð': 'd'};
  const foldN = s => String(s ?? '').toLowerCase().normalize('NFD').replace(/\p{M}/gu, '').replace(/[ßøđłæœıþð]/g, c => FOLDX[c]).replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
  const csvRows = text => { const rows = []; let row = [], cell = '', q = false;
    for(let i = 0; i < text.length; i++){ const ch = text[i];
      if(q){ if(ch === '"' && text[i + 1] === '"'){ cell += '"'; i++; } else if(ch === '"') q = false; else cell += ch; }
      else if(ch === '"') q = true; else if(ch === ','){ row.push(cell); cell = ''; }
      else if(ch === '\n' || ch === '\r'){ if(ch === '\r' && text[i + 1] === '\n') i++; row.push(cell); rows.push(row); row = []; cell = ''; } else cell += ch; }
    if(cell !== '' || row.length){ row.push(cell); rows.push(row); }
    const head = rows.shift(); return rows.filter(r => r.some(c => c.trim())).map(r => Object.fromEntries(head.map((h, i) => [h.trim(), (r[i] || '').trim()]))); };
  const CSVN = csvRows(fs.readFileSync(path.join(ROOT, 'data/competitions.csv'), 'utf8')).filter(r => r.name);
  const CLUBN = [];                                   // the clubs the map draws: a position and a tier, as CLUBS holds them
  for(const f of fs.readdirSync(path.join(ROOT, 'data/clubs')).filter(f => /^[A-Z]{2}\.json$/.test(f))){
    const d = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/clubs', f), 'utf8'));
    for(const c of d.clubs || []) if(c.lat != null && c.lon != null && c.tier != null) CLUBN.push(Object.assign({}, c, {country: d.country}));
  }
  const venueFolds = new Set(CLUBN.filter(c => c.venue && foldN(c.venue)).map(c => foldN(c.venue)));
  const stadiumFolds = new Set([...venueFolds, ...ATTF.matches.filter(m => m.stadium && foldN(m.stadium)).map(m => foldN(m.stadium))]);
  const leagueNames = [...new Set(CLUBN.filter(c => c.competition).map(c => c.competition))];
  const compFoldsNoCsv = new Set(['friendly', 'exhibition', ...leagueNames.map(foldN), ...ATTF.matches.map(m => foldN(m.competition.en))].filter(Boolean));
  const compFolds = new Set([...compFoldsNoCsv, ...CSVN.map(r => foldN(r.name)).filter(Boolean)]);
  // In Romanian the matches' competition texts are the Romanian ones.
  const compFoldsRo = new Set([...leagueNames.map(foldN), ...ATTF.matches.map(m => foldN(m.competition.ro)), ...CSVN.map(r => foldN(r.name))].filter(f => f && f !== 'meci amical' && f !== 'meci demonstrativ'));
  const rankOf = (n, q) => { const f = foldN(q), at = n.indexOf(f); return at === 0 ? 0 : at > 0 && n[at - 1] === ' ' ? 1 : at > 0 ? 2 : 3; };
  const totalFor = (folds, q) => { const ws = foldN(q).split(' '); return [...folds].filter(n => ws.every(w => n.includes(w))).length; };

  const ctxS = await newCtx();
  await ctxS.addInitScript(() => {
    window.__w = [];
    const w = Storage.prototype.setItem, r = Storage.prototype.removeItem;
    Storage.prototype.setItem = function(k, v){ window.__w.push(k); return w.call(this, k, v); };
    Storage.prototype.removeItem = function(k){ window.__w.push(k); return r.call(this, k); };
  });
  const pS = await ctxS.newPage();
  pS.on('pageerror', e => errors.push(e.message));
  pS.on('dialog', d => d.accept());
  await pS.goto(BASE);
  await pS.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await pS.click('nav button[data-pane=me]');
  await pS.waitForSelector('#meStats .astat');
  await pS.click('#meTabMatches'); await pS.waitForSelector('#meMatches .acard');
  const stored = async () => { const v = await pS.evaluate(k => localStorage.getItem(k), IMPK); return v ? JSON.parse(v).matches : []; };
  const openAddS = async () => { await pS.click('#meTabMatches'); await pS.waitForSelector('#aForm', {state: 'attached'}); if(!(await pS.$eval('#aAdd', d => d.open))) await pS.click('#aAdd summary'); };
  const resetS = async () => { await pS.click('#meTabMatches'); await pS.waitForSelector('#aForm', {state: 'attached'}); if(await pS.$eval('#aAdd', d => d.open)) await pS.click('#aFormCancel'); await openAddS(); };
  const msgS = async () => (await pS.textContent('#aImpMsg')).trim();
  const fillS = async v => { for(const [k, val] of Object.entries(v)) await pS.fill(`#aForm [name=${k}]`, val); };
  let seq = 0;
  const base = o => Object.assign({date: '2026-05-0' + (1 + (seq++ % 9)), home: 'Exh Home ' + TAG + seq, away: 'Exh Away ' + TAG, sh: '1', sa: '0'}, o);
  const addS = async (v, {exh, json} = {}) => {      // the form (and the JSON box), submitted; the message
    await resetS(); await fillS(v);
    if(exh != null) await pS.selectOption('#aForm [name=exhibition]', exh);
    if(json != null) await pS.fill('#aImpBox', json);
    await pS.click('#aImpBtn'); return msgS();
  };
  const statsS = async () => { await pS.click('#meTabStats'); await pS.waitForSelector('#meStats .astat');
    return pS.evaluate(() => { const ts = [...document.querySelectorAll('#meStats .astat')], n = s => +s.replace(/[^\d]/g, ''), ex = document.getElementById('aGoalsExcl'), sh = document.getElementById('aGoalsNote');
      return {matches: n(ts[0].querySelector('b').textContent), goals: n(ts[1].querySelector('b').textContent), avg: ts[1].querySelector('i').textContent, pens: n(ts[2].querySelector('b').textContent),
        excl: ex ? ex.textContent : null, short: sh ? sh.textContent : null}; }); };
  const exclN = s => s.excl ? +/\((\d+) goals? excluded\)/.exec(s.excl)[1] : 0;
  const cardsS = async () => { await pS.click('#meTabMatches'); await pS.waitForSelector('#meMatches .acard');
    return pS.$$eval('#meMatches .acard', cs => cs.map(c => ({id: c.dataset.id, exh: [...c.querySelectorAll('.aexh')].map(x => x.textContent)}))); };
  const openCardS = async key => { await pS.click('#meTabMatches'); await pS.waitForSelector('#meMatches .acard'); await pS.click(`#meMatches .acard[data-id="${key}"]`); await pS.waitForSelector('#asheet:not([hidden])'); await pS.waitForTimeout(350); };
  const closeS = async () => { if(await pS.$('#asheet:not([hidden])')){ await pS.click('#asheetClose'); await pS.waitForTimeout(250); } };
  const fileExh = ATTF.matches.filter(m => m.exhibition === true).map(m => m.id);

  // ---- The flag in the file, the validator, the toggle.
  check('data/attended.json: exactly one match carries "exhibition", it is true, and it is the 2019 charity match (7-6, empty goals list)',
    ATTF.matches.filter(m => 'exhibition' in m).length === 1 && fileExh.join() === '2019-05-18-sfr-sfb' && ATTF.matches.find(m => m.exhibition).score === '7-6' && ATTF.matches.find(m => m.exhibition).goals.length === 0, fileExh.join());
  await openAddS();
  const sel = await pS.evaluate(() => { const s = document.querySelector('#aForm [name=exhibition]'); return {tag: s && s.tagName, val: s && s.value, opts: s && [...s.options].map(o => o.value + ':' + o.textContent), label: s && s.closest('label').firstChild.textContent}; });
  check('The Add form has a Yes/No "Exhibition match", default No', sel.tag === 'SELECT' && sel.val === 'no' && sel.opts.join() === 'no:No,yes:Yes' && sel.label === 'Exhibition match', JSON.stringify(sel));
  const vr = await pS.evaluate(() => { const ok = {id: 'v', date: '2026-01-01', score: '1-0', home: {name: 'A'}, away: {name: 'B'}};
    const run = ex => { const c = attCheckMatch(Object.assign({}, ok, ex)); return c.rec ? 'ok' : c.errs.join('; '); };
    return {t: run({exhibition: true}), f: run({exhibition: false}), none: run({}), s: run({exhibition: 'true'}), n: run({exhibition: 1}), o: run({exhibition: {}}), a: run({exhibition: []}), typo: run({exhibitions: true})}; });
  check('The validator accepts exhibition true and false, and refuses a string, a number, an object, a list; an unknown field is still refused',
    vr.t === 'ok' && vr.f === 'ok' && vr.none === 'ok' && [vr.s, vr.n, vr.o, vr.a].every(x => /exhibition/.test(x) && x !== 'ok') && /exhibitions/.test(vr.typo) && vr.typo !== 'ok', JSON.stringify(vr));
  const s0 = await statsS(), c0 = await cardsS();
  check('Baseline: the stats show the file only, exhibition match excluded (goals per match over the other matches, exclusion note)',
    s0.matches === fx.n && s0.goals === fx.goals && s0.avg === (fx.goals / fx.nReal).toFixed(2) + ' per match' && s0.pens === fx.pens && exclN(s0) === fx.exclGoals, JSON.stringify(s0));
  check('The tag "Exhibition" is on the exhibition match\'s card and on no other card', JSON.stringify(c0.filter(c => c.exh.length).map(c => [c.id, c.exh.join()])) === JSON.stringify(fileExh.map(i => [i, 'Exhibition'])), JSON.stringify(c0.filter(c => c.exh.length)));

  const m1 = await addS(base({sh: '5', sa: '2'}), {exh: 'yes'});
  const st1 = await stored(), E1 = st1[0];
  check('Adding with Yes stores "exhibition": true', /^Added 1 imported match/.test(m1) && st1.length === 1 && E1.exhibition === true, m1 + ' ' + JSON.stringify(E1));
  const s1 = await statsS();
  check('...the matches card counts it; goals seen, goals per match and penalties scored do not; the exclusion note grows by its 7 goals',
    s1.matches === s0.matches + 1 && s1.goals === s0.goals && s1.avg === s0.avg && s1.pens === s0.pens && exclN(s1) === exclN(s0) + 7 && s1.short === s0.short, JSON.stringify(s1));
  const c1 = await cardsS();
  check('...its card carries the "Exhibition" tag', c1.filter(c => c.exh.length).map(c => c.id).sort().join() === [...fileExh, 'imp:' + E1.id].sort().join(), '');
  await openCardS('imp:' + E1.id);
  check('...and its sheet header carries the tag', await pS.$$eval('#asheetHead .meta .aexh', x => x.map(e => e.textContent).join()) === 'Exhibition', '');
  await closeS();

  const m2 = await addS(base({sh: '2', sa: '0'}));
  const st2 = await stored(), N1 = st2.find(x => x.id !== E1.id);
  check('Adding with the default No stores no "exhibition" key at all', /^Added 1/.test(m2) && !('exhibition' in N1), JSON.stringify(N1));
  const s2 = await statsS();
  check('...it counts: goals seen +2, goals per match over one more non-exhibition match, the exclusion note unchanged',
    s2.goals === s1.goals + 2 && s2.avg === ((fx.goals + 2) / (fx.nReal + 1)).toFixed(2) + ' per match' && exclN(s2) === exclN(s1) && s2.matches === s1.matches + 1, JSON.stringify(s2));

  // The JSON merge rule: Yes counts as filled, a default No does not.
  const jm1 = await addS(base({}), {json: '{"exhibition": true}'});
  const jm1r = (await stored()).find(x => x.exhibition === true && x.id !== E1.id);
  check('Merge: form left at No, JSON says true -> the JSON supplies it (stored true)', /^Added 1/.test(jm1) && !!jm1r, jm1);
  const n1 = (await stored()).length;
  const jm2 = await addS(base({}), {exh: 'yes', json: '{"exhibition": true}'});
  check('Merge: form says Yes and the JSON fills it too -> refused, "exhibition" named, nothing stored', /exhibition/.test(jm2) && /both the form and the JSON/.test(jm2) && (await stored()).length === n1, jm2);
  const jm3 = await addS(base({}), {json: '{"exhibition": false}'});
  const jm3r = (await stored()).filter(x => x.exhibition === false);
  check('Merge: form at No, JSON says false -> stored false, not an exhibition match', /^Added 1/.test(jm3) && jm3r.length === 1 && !(await cardsS()).find(c => c.id === 'imp:' + jm3r[0].id).exh.length, jm3);
  const n2 = (await stored()).length;
  const jm4 = await addS(base({}), {json: '{"exhibition": "yes"}'});
  check('Merge: a JSON "exhibition" that is not true or false is refused and nothing is stored', /exhibition/.test(jm4) && (await stored()).length === n2, jm4);
  await resetS(); await pS.selectOption('#aForm [name=exhibition]', 'yes'); await pS.click('#aImpBtn');
  check('A form with only the Yes chosen counts as filled (the required fields are asked for, the paste box is not read)',
    /Not saved/.test(await msgS()) && (await pS.textContent('#aForm [data-ferr="date"]')).trim() !== '' && (await stored()).length === n2, await msgS());
  const jm5 = await addS({}, {json: JSON.stringify([{id: 'p1' + TAG, date: '2026-04-01', score: '3-3', home: {name: 'P1'}, away: {name: 'P2'}, exhibition: true}, {id: 'p2' + TAG, date: '2026-04-02', score: '1-0', home: {name: 'P3'}, away: {name: 'P4'}}])});
  check('With the form empty the paste box still takes a list, exhibition included', /^Added 2 imported match/.test(jm5) && (await stored()).filter(x => x.id.startsWith('p') && x.id.endsWith(TAG)).map(x => x.exhibition === true).join() === 'true,false', jm5);

  // Edit shows the stored state and changes it.
  await openCardS('imp:' + E1.id); await pS.click('#aImpEdit'); await pS.waitForSelector('#aForm:not([data-edit=""])');
  check('Edit shows the stored state (Yes for an exhibition match)', await pS.inputValue('#aForm [name=exhibition]') === 'yes', '');
  await pS.selectOption('#aForm [name=exhibition]', 'no'); await pS.click('#aImpBtn'); await pS.waitForSelector('#asheet:not([hidden])'); await pS.waitForTimeout(350);
  const E1b = (await stored()).find(x => x.id === E1.id);
  check('Saving with No removes the key; the tag leaves the sheet and the card; the goals now count',
    !('exhibition' in E1b) && !(await pS.$('#asheetHead .meta .aexh')) && !(await cardsS()).find(c => c.id === 'imp:' + E1.id).exh.length && (await statsS()).goals >= s2.goals + 7, JSON.stringify(E1b).slice(0, 80));
  await closeS(); await openCardS('imp:' + N1.id); await pS.click('#aImpEdit'); await pS.waitForSelector('#aForm:not([data-edit=""])');
  check('Edit shows No for a match without the key', await pS.inputValue('#aForm [name=exhibition]') === 'no', '');
  await pS.selectOption('#aForm [name=exhibition]', 'yes'); await pS.click('#aImpBtn'); await pS.waitForSelector('#asheet:not([hidden])'); await pS.waitForTimeout(350);
  check('Saving with Yes stores true and shows the tag in the sheet', (await stored()).find(x => x.id === N1.id).exhibition === true && (await pS.$$eval('#asheetHead .meta .aexh', x => x.length)) === 1, '');
  await closeS();

  // ---- Suggestions. Typing and tapping store nothing and request nothing.
  await resetS();
  const w0 = await pS.evaluate(() => window.__w.length);
  await pS.focus('#aForm [name=competition]');
  await pS.waitForFunction(() => typeof SUG_COMPS !== 'undefined' && SUG_COMPS);
  const rowsOf = sel => pS.$$eval(`${sel} + .asugg button`, bs => bs.map(b => ({name: b.querySelector('.sn').textContent, sub: (b.querySelector('.rd') || {}).textContent || ''})));
  const moreOf = sel => pS.$eval(`${sel} + .asugg .none`, e => e.textContent).catch(() => null);
  const compSel = 'label:has([name=competition])', stadSel = 'label:has([name=stadium])';
  const typeC = async v => { await pS.fill('#aForm [name=competition]', v); };
  const typeS = async v => { await pS.fill('#aForm [name=stadium]', v); };
  const itemsC = await pS.evaluate(() => sugItems('competition').map(i => fold(i.name)));
  check('Competition suggestions hold every name of data/competitions.csv, every league of the coverage panel, every competition text of the file\'s matches, "Friendly" and "Exhibition", once each',
    itemsC.length === new Set(itemsC).size && [...compFolds].every(f => itemsC.includes(f)) && itemsC.length === compFolds.size, `${itemsC.length} in the page, ${compFolds.size} expected`);
  check('data/competitions.csv was requested once, by GET, when the form opened', requests.slice(reqStart).filter(r => /data\/competitions\.csv/.test(r.url) && r.method === 'GET').length === 1, '');
  await typeC('liga');
  let rc = await rowsOf(compSel), mc = await moreOf(compSel);
  const totLiga = totalFor(compFolds, 'liga');
  check('"liga": 8 rows and "+ n more" with n worked out from the sources', totLiga > 8 && rc.length === 8 && mc === `+ ${totLiga - 8} more`, `${rc.length} rows, ${mc}, expected total ${totLiga}`);
  const ranks = rc.map(r => rankOf(foldN(r.name), 'liga'));
  check('...names that start with what was typed come first, then those with a word that does, then the rest', ranks.every((x, i) => !i || ranks[i - 1] <= x), ranks.join());
  const accented = CSVN.find(r => foldN(r.name) !== r.name.toLowerCase() && /[^\x00-\x7f]/.test(r.name) && totalFor(compFolds, r.name) <= 8);
  await typeC(foldN(accented.name));
  rc = await rowsOf(compSel);
  check('Matching ignores accents and case: the accent-free lower-case name finds the CSV name as written', rc.some(r => r.name === accented.name), accented.name);
  const withCtry = CSVN.find(r => r.country && foldN(r.name) && totalFor(compFolds, r.name) <= 8);
  await typeC(withCtry.name); rc = await rowsOf(compSel);
  check('A CSV row\'s second line gives its country and type', rc.some(r => r.name === withCtry.name && r.sub.length > 0 && r.sub.includes('·')), JSON.stringify(rc.find(r => r.name === withCtry.name)));
  await typeC('friend'); rc = await rowsOf(compSel);
  check('"Friendly" is offered', rc.some(r => r.name === 'Friendly'), JSON.stringify(rc.map(r => r.name)));
  await pS.click(`${compSel} + .asugg .sn:text-is("Friendly")`);
  check('Tapping a row fills the field with the name and closes the list; the exhibition toggle is left alone',
    await pS.inputValue('#aForm [name=competition]') === 'Friendly' && await pS.$eval(`${compSel} + .asugg`, e => e.hidden) && await pS.inputValue('#aForm [name=exhibition]') === 'no', '');
  await typeC('exhib'); rc = await rowsOf(compSel);
  check('"Exhibition" is offered', rc.some(r => r.name === 'Exhibition'), JSON.stringify(rc.map(r => r.name)));
  await pS.click(`${compSel} + .asugg .sn:text-is("Exhibition")`);
  check('Tapping "Exhibition" fills it and switches the toggle on', await pS.inputValue('#aForm [name=competition]') === 'Exhibition' && await pS.inputValue('#aForm [name=exhibition]') === 'yes', '');
  await pS.selectOption('#aForm [name=exhibition]', 'no'); await typeC(withCtry.name);
  await pS.click(`${compSel} + .asugg button >> nth=0`);
  check('Tapping any other suggestion leaves the toggle alone (No stays No)', await pS.inputValue('#aForm [name=exhibition]') === 'no', '');
  await pS.selectOption('#aForm [name=exhibition]', 'yes'); await typeC(withCtry.name);
  await pS.click(`${compSel} + .asugg button >> nth=0`);
  check('...and Yes stays Yes', await pS.inputValue('#aForm [name=exhibition]') === 'yes', '');
  await pS.selectOption('#aForm [name=exhibition]', 'no');
  const FREE = 'Free Cup ' + TAG;
  await typeC(FREE); const nSt = (await stored()).length;
  await pS.press('#aForm [name=competition]', 'Enter');
  check('Free text works: Enter keeps what is typed, closes the list and does not save the form', await pS.inputValue('#aForm [name=competition]') === FREE && (await stored()).length === nSt && !!(await pS.$('#aForm')), '');
  await pS.click('#aForm [name=stage]');
  check('...and leaving the field keeps it', await pS.inputValue('#aForm [name=competition]') === FREE, '');

  // Stadiums.
  const itemsS = await pS.evaluate(() => sugItems('stadium').map(i => fold(i.name)));
  check('Stadium suggestions hold the venue of every club the map draws (all club files) and the stadiums of the file\'s matches, once per folded name',
    itemsS.length === new Set(itemsS).size && [...stadiumFolds].every(f => itemsS.includes(f)) && itemsS.length === stadiumFolds.size && venueFolds.size > 400, `${itemsS.length} in the page, ${stadiumFolds.size} expected, ${venueFolds.size} from clubs`);
  const byCountry = new Map();
  for(const c of CLUBN){ if(!c.venue || byCountry.has(c.country)) continue; const f = foldN(c.venue);
    if(f.length >= 6 && CLUBN.filter(x => x.venue && foldN(x.venue) === f).length === 1 && !ATTF.matches.some(m => m.stadium && foldN(m.stadium) === f)) byCountry.set(c.country, c); }
  const nCountryFiles = fs.readdirSync(path.join(ROOT, 'data/clubs')).filter(f => /^[A-Z]{2}\.json$/.test(f)).length;
  const sampleBad = [];
  for(const [cc, c] of byCountry){
    await typeS(foldN(c.venue));
    const rs = await rowsOf(stadSel), want = await pS.evaluate(x => countryName(x), cc), row = rs.find(r => r.name === c.venue);
    if(!row || !row.sub.includes(c.name || c.id) || !row.sub.includes(want)) sampleBad.push(cc + ':' + c.venue + ' ' + JSON.stringify(rs.slice(0, 2)));
  }
  check('A club of every country file is found by its ground (typed without accents), with the club and the country on the second line', byCountry.size === nCountryFiles && !sampleBad.length, `${byCountry.size} of ${nCountryFiles}; ${sampleBad.join(' | ')}`);
  const fm = ATTF.matches.find(m => m.stadium && !venueFolds.has(foldN(m.stadium)));
  if(fm){ await typeS(foldN(fm.stadium)); check('A stadium that only a file match has is offered too, with its country', (await rowsOf(stadSel)).some(r => r.name === fm.stadium && r.sub.includes(fm.country.en)), fm.stadium); }
  else check('A stadium that only a file match has is offered too (every file stadium is also a club ground)', true, 'none to test');
  await pS.fill('#aForm [name=city]', ''); await typeS(foldN(byCountry.values().next().value.venue));
  await pS.click(`${stadSel} + .asugg button >> nth=0`);
  check('Tapping a stadium fills the stadium and does not fill the city', (await pS.inputValue('#aForm [name=stadium]')).length > 0 && await pS.inputValue('#aForm [name=city]') === '', '');
  const wDuring = await pS.evaluate(w => window.__w.slice(w), w0);
  check('Typing, tapping, Enter and leaving a field wrote nothing to the browser\'s storage', wDuring.length === 0, wDuring.join());

  // Layout: at 390x844, and at 390x500 with the keyboard stood in by the smaller window.
  const placed = () => pS.evaluate(() => { const b = document.querySelector('.asugg:not([hidden])'); if(!b) return null; const r = b.getBoundingClientRect(), nx = b.nextElementSibling, nr = nx && nx.getBoundingClientRect(),
    vh = window.visualViewport ? visualViewport.height : innerHeight, btn = document.getElementById('aImpBtn').getBoundingClientRect(), sc = document.getElementById('pane-me');
    return {top: r.top, bottom: r.bottom, left: r.left, right: r.right, vh, w: innerWidth, nextTop: nr ? nr.top : null, btnTop: btn.top, scrollW: sc.scrollWidth, clientW: sc.clientWidth, rows: b.querySelectorAll('button').length}; });
  await typeC('liga'); let pl = await placed();
  check('At 390x844 the list is inside the screen, sits in the page flow above the next field and the buttons, and nothing scrolls sideways',
    pl && pl.left >= 0 && pl.right <= pl.w && pl.top >= 0 && pl.bottom <= pl.vh && pl.nextTop >= pl.bottom - 1 && pl.btnTop >= pl.bottom - 1 && pl.scrollW <= pl.clientW + 1, JSON.stringify(pl));
  await pS.fill('#aForm [name=competition]', '');
  await pS.focus('#aForm [name=stadium]');
  await pS.setViewportSize({width: 390, height: 500});
  await typeS('stad'); pl = await placed();
  check('At 390x500 with the keyboard stood in, the stadium list ends above the bottom of the visible area and is on screen', pl && pl.rows >= 1 && pl.top >= 0 && pl.bottom <= pl.vh && pl.left >= 0 && pl.right <= pl.w && pl.btnTop >= pl.bottom - 1, JSON.stringify(pl));
  await typeC('liga'); pl = await placed();
  check('...and so does the competition list', pl && pl.top >= 0 && pl.bottom <= pl.vh && pl.nextTop >= pl.bottom - 1, JSON.stringify(pl));
  await pS.setViewportSize({width: 390, height: 844});
  await pS.fill('#aForm [name=competition]', ''); await pS.fill('#aForm [name=stadium]', '');

  // ---- Home team and Away team suggestions (2026-10-16). Expected values are worked out here from the club files, data/attended.json and what the device holds.
  const homeSel = 'label:has([name=home])', awaySel = 'label:has([name=away])';
  const typeT = (n, v) => pS.fill(`#aForm [name=${n}]`, v);
  const tt = o => o == null ? '' : typeof o === 'string' ? o : (o.en || o.ro || '');
  const codes = [...new Set(CLUBN.map(c => c.country))];
  const ctryName = await pS.evaluate(cs => Object.fromEntries(cs.map(c => [c, countryName(c)])), codes);
  const notRec = await pS.evaluate(() => Object.fromEntries([1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => [n, t('gen.leagueNot', {tier: n})])));
  const subOf = c => `${ctryName[c.country]} · ${c.competition || notRec[c.tier]}`;
  const teamModel = imps => {
    const rows = new Map();
    for(const c of CLUBN){ const f = foldN(c.name); if(!f) continue; const key = f + '|' + c.country, p = rows.get(key);
      if(p){ if(c.tier < p.tier){ p.tier = c.tier; p.sub = subOf(c); } continue; }
      rows.set(key, {name: c.name, fs: [f], tier: c.tier, sub: subOf(c), club: true}); }
    const cf = new Set([...rows.values()].map(r => r.fs[0])), mine = new Map();
    for(const m of ATTF.matches.concat(imps)) for(const sd of ['home', 'away']){ const tm = m[sd], nm = tt(tm.nameEn) || tt(tm.name), f = foldN(nm), f2 = foldN(tt(tm.name));
      if(!f || cf.has(f) || mine.has(f)) continue;
      mine.set(f, {name: nm, fs: f2 && f2 !== f ? [f, f2] : [f], tier: 99, sub: 'Used in your matches', club: false}); }
    return [...rows.values(), ...mine.values()];
  };
  const modelHits = (model, q) => { const ws = foldN(q).split(' ');
    return model.map(r => { let best = 9; for(const n of r.fs){ if(!ws.every(w => n.includes(w))) continue; best = Math.min(best, rankOf(n, q)); } return {r, best}; }).filter(h => h.best < 9)
      .sort((a, b) => a.best - b.best || a.r.tier - b.r.tier || a.r.name.localeCompare(b.r.name)); };
  const impNow = await stored();
  const model = teamModel(impNow);
  const itemsT = await pS.evaluate(() => sugItems('team').map(i => [fold(i.name), i.sub, i.tier]));
  const nClubRows = model.filter(r => r.club).length, nMine = model.length - nClubRows;
  check('Team suggestions hold every club of every country file (one row per folded name and country) plus the teams only the file\'s and the device\'s matches use, once each',
    itemsT.length === model.length && JSON.stringify(itemsT.map(i => i[0]).sort()) === JSON.stringify(model.map(r => r.fs[0]).sort()) && nClubRows > 500 && nMine > 5, `${itemsT.length} in the page, ${model.length} expected (${nClubRows} clubs, ${nMine} only in matches)`);
  // Every club, typed with its own name, is offered (worked through in the page, one search each).
  const allBad = await pS.evaluate(cl => cl.filter(c => !sugSearch('team', c.name, 100000).list.some(i => i.name === c.name && i.sub.startsWith(countryName(c.country) + ' · '))).map(c => c.name).slice(0, 5), CLUBN.map(c => ({name: c.name, country: c.country})));
  check(`All ${CLUBN.length} clubs of all ${codes.length} country files are offered for their own name`, !allBad.length, allBad.join(' | '));
  // A sample from each country file, through the field: the row's second line is country and competition as the club search shows them.
  const sampleT = new Map();
  for(const c of CLUBN){ if(sampleT.has(c.country) || !foldN(c.name)) continue;
    const f = foldN(c.name); if(CLUBN.filter(x => foldN(x.name) === f).length !== 1 || ATTF.matches.some(m => ['home', 'away'].some(sd => foldN(tt(m[sd].nameEn) || tt(m[sd].name)) === f))) continue;
    if(modelHits(model, c.name).length > 8) continue; sampleT.set(c.country, c); }
  const sampBad = [];
  for(const [cc, c] of sampleT){ await typeT('home', foldN(c.name)); const rs = await rowsOf(homeSel), row = rs.find(r => r.name === c.name);
    if(!row || row.sub !== subOf(c)) sampBad.push(cc + ':' + c.name + ' ' + JSON.stringify(rs.slice(0, 2))); }
  check('A club of every country file is offered in the Home team field for its typed name, second line "country · competition"', sampleT.size === codes.length && !sampBad.length, `${sampleT.size} of ${codes.length}; ${sampBad.join(' | ')}`);
  const noLeague = CLUBN.find(c => !c.competition && modelHits(model, c.name).length <= 8 && CLUBN.filter(x => foldN(x.name) === foldN(c.name)).length === 1);
  if(noLeague){ await typeT('away', foldN(noLeague.name)); check('A club with no league recorded reads "league not recorded (tier N)" on its second line', (await rowsOf(awaySel)).some(r => r.name === noLeague.name && r.sub === subOf(noLeague) && /league not recorded \(tier \d+\)$/.test(r.sub)), noLeague.name); }
  // Teams only in his matches: a national team and the others.
  const natM = ATTF.matches.flatMap(m => ['home', 'away'].map(sd => m[sd])).find(tm => tm.nameEn && tm.nameEn !== tm.name && model.some(r => !r.club && r.name === tm.nameEn));
  await typeT('home', foldN(natM.nameEn)); let rt = await rowsOf(homeSel);
  check('A national team from the file\'s matches is offered by its English name, second line "Used in your matches"', rt.some(r => r.name === natM.nameEn && r.sub === 'Used in your matches'), JSON.stringify(rt.slice(0, 3)));
  await typeT('home', foldN(natM.name)); rt = await rowsOf(homeSel);
  check('...and typing the stored (Romanian) name finds it too', rt.some(r => r.name === natM.nameEn), natM.name + ' ' + JSON.stringify(rt.slice(0, 3)));
  const mineBad = await pS.evaluate(l => l.filter(n => !sugSearch('team', n, 100000).list.some(i => i.name === n && i.sub === 'Used in your matches')).slice(0, 5), model.filter(r => !r.club).map(r => r.name));
  check(`All ${nMine} teams used only in matches are offered with "Used in your matches" and no country`, !mineBad.length, mineBad.join(' | '));
  const sharedM = ATTF.matches.flatMap(m => ['home', 'away'].map(sd => tt(m[sd].nameEn) || tt(m[sd].name))).filter(n => model.some(r => r.club && r.fs[0] === foldN(n)));
  const dupBad = sharedM.filter(n => itemsT.filter(i => i[0] === foldN(n)).length !== model.filter(r => r.club && r.fs[0] === foldN(n)).length || itemsT.some(i => i[0] === foldN(n) && i[1] === 'Used in your matches'));
  check('Deduplication: a match team that is also a club is the club\'s row, not a second one', sharedM.length > 3 && !dupBad.length, `${sharedM.length} shared; ${dupBad.join(', ')}`);
  const dd = await pS.evaluate(() => {
    const keep = CLUBS.length; CLUBS.push({name: 'Zz Dup FC', country: 'DE', tier: 3, competition: 'League A'}, {name: 'ZZ-Dup FC', country: 'DE', tier: 1, competition: 'League B'}, {name: 'zz dup fc', country: 'RO', tier: 2, competition: 'League C'});
    const r = sugItems('team').filter(i => fold(i.name) === 'zz dup fc').map(i => i.sub + '#' + i.tier);
    CLUBS.length = keep; return {r}; });
  check('Deduplication: the same folded name and the same country is one row (the more senior tier\'s), the same name in another country is a second row',
    dd.r.length === 2 && dd.r.some(x => /League B#1$/.test(x)) && dd.r.some(x => /League C#2$/.test(x)) && !dd.r.some(x => /League A/.test(x)), JSON.stringify(dd));
  // Order, 8 rows and the more-count, accent-insensitive match.
  await typeT('home', 'fc'); rt = await rowsOf(homeSel); let mt = await moreOf(homeSel);
  const hf = modelHits(model, 'fc'), tierOf = n => (model.find(r => r.name === n) || {tier: 99}).tier;
  const seq8 = rt.map(r => [rankOf(foldN(r.name), 'fc'), tierOf(r.name)]);
  check('"fc": 8 rows and "+ n more" with n worked out from the sources', hf.length > 8 && rt.length === 8 && mt === `+ ${hf.length - 8} more`, `${rt.length} rows, ${mt}, expected total ${hf.length}`);
  check('...names starting with it first, then names with a word that does, then the rest; within each the more senior tier first',
    seq8.every((x, i) => !i || x[0] > seq8[i - 1][0] || (x[0] === seq8[i - 1][0] && x[1] >= seq8[i - 1][1])), JSON.stringify(seq8));
  check('...the 8 rows are the first 8 of the expected order (tier, then name inside equal rank and tier)',
    JSON.stringify(rt.map(r => r.name)) === JSON.stringify(hf.slice(0, 8).map(h => h.r.name)), JSON.stringify(rt.map(r => r.name)) + ' vs ' + JSON.stringify(hf.slice(0, 8).map(h => h.r.name)));
  const accC = CLUBN.find(c => foldN(c.name) !== c.name.toLowerCase() && /[^\x00-\x7f]/.test(c.name) && modelHits(model, c.name).length <= 8);
  await typeT('away', foldN(accC.name)); rt = await rowsOf(awaySel);
  check('Matching ignores accents and case: the accent-free lower-case name finds the club as written', rt.some(r => r.name === accC.name), accC.name);
  // Tap fills only that field; independence; the goal rows' menu.
  await resetS(); await pS.click('#aGoalAdd');
  const before = await pS.evaluate(() => Object.fromEntries([...document.querySelector('#aForm').elements].filter(e => e.name).map(e => [e.name, e.value])));
  await typeT('home', foldN(sampleT.values().next().value.name)); const hRows = await rowsOf(homeSel);
  await pS.click(`${homeSel} + .asugg button >> nth=0`);
  const homeVal = await pS.inputValue('#aForm [name=home]');
  const after = await pS.evaluate(() => Object.fromEntries([...document.querySelector('#aForm').elements].filter(e => e.name).map(e => [e.name, e.value])));
  const changed = Object.keys(after).filter(k => before[k] !== after[k]);
  check('Tapping a team row fills the field with the name as written, closes the list and fills nothing else', homeVal === hRows[0].name && await pS.$eval(`${homeSel} + .asugg`, e => e.hidden) && changed.join() === 'home', changed.join() + ' ' + homeVal);
  check('The goal rows\' team menu shows the tapped name', (await pS.$$eval('#aForm select[name=gteam] option', o => o.map(x => x.textContent)))[0] === homeVal, '');
  await typeT('away', 'zzz'); check('Away is independent: typing in Away a text nothing matches shows no suggestion and leaves Home alone', await pS.inputValue('#aForm [name=home]') === homeVal && !(await rowsOf(awaySel)).length, '');
  await typeT('away', foldN(accC.name)); await pS.click(`${awaySel} + .asugg button >> nth=0`);
  check('...and tapping in Away fills Away only; Home keeps its name and its list stays closed', await pS.inputValue('#aForm [name=home]') === homeVal && (await pS.inputValue('#aForm [name=away]')).length > 0 && !(await pS.$('.asugg:not([hidden])')), '');
  check('...and the goal rows\' menu now shows both names', JSON.stringify(await pS.$$eval('#aForm select[name=gteam] option', o => o.map(x => x.textContent))) === JSON.stringify([homeVal, await pS.inputValue('#aForm [name=away]')]), '');
  // Free text and Enter.
  await typeT('home', 'Free Home ' + TAG); const nSt2 = (await stored()).length;
  await pS.press('#aForm [name=home]', 'Enter');
  check('Free text in a team field: Enter keeps what is typed and does not save the form', await pS.inputValue('#aForm [name=home]') === 'Free Home ' + TAG && (await stored()).length === nSt2 && !!(await pS.$('#aForm')), '');
  await typeT('home', 'fc'); await pS.press('#aForm [name=home]', 'Enter');
  check('Enter with the list open closes it and keeps the text', await pS.inputValue('#aForm [name=home]') === 'fc' && await pS.$eval(`${homeSel} + .asugg`, e => e.hidden), '');
  // Layout.
  const placedT = () => pS.evaluate(() => { const b = document.querySelector('.asugg:not([hidden])'); if(!b) return null; const r = b.getBoundingClientRect(), nx = b.nextElementSibling, nr = nx && nx.getBoundingClientRect(),
    vh = window.visualViewport ? visualViewport.height : innerHeight, btn = document.getElementById('aImpBtn').getBoundingClientRect(), sc = document.getElementById('pane-me');
    return {top: r.top, bottom: r.bottom, left: r.left, right: r.right, vh, w: innerWidth, nextTop: nr ? nr.top : null, btnTop: btn.top, scrollW: sc.scrollWidth, clientW: sc.clientWidth, rows: b.querySelectorAll('button').length}; });
  await typeT('home', 'fc'); let plT = await placedT();
  check('At 390x844 the Home list is on screen, in the page flow above the next field and the buttons, nothing scrolls sideways',
    plT && plT.rows === 8 && plT.left >= 0 && plT.right <= plT.w && plT.top >= 0 && plT.bottom <= plT.vh && plT.nextTop >= plT.bottom - 1 && plT.btnTop >= plT.bottom - 1 && plT.scrollW <= plT.clientW + 1, JSON.stringify(plT));
  await pS.focus('#aForm [name=away]'); await pS.setViewportSize({width: 390, height: 500});
  for(const n of ['away', 'home']){ await typeT(n, 'fc'); plT = await placedT();
    check(`At 390x500 with the keyboard stood in, the ${n === 'home' ? 'Home' : 'Away'} team list ends above the bottom of the visible area and is on screen`, plT && plT.rows >= 1 && plT.top >= 0 && plT.bottom <= plT.vh && plT.left >= 0 && plT.right <= plT.w && plT.btnTop >= plT.bottom - 1, JSON.stringify(plT)); }
  await pS.setViewportSize({width: 390, height: 844});
  // Saved with free text, then Edit leaves the stored names unchanged and the saved free names are offered.
  const FH = 'Free Home ' + TAG, FA = 'Free Away ' + TAG;
  await resetS(); await fillS(base({home: FH, away: FA})); await pS.click('#aImpBtn');
  const savedT = (await stored()).find(x => x.home.name === FH);
  check('A match saved with free text in both team fields stores the names as typed', /^Added 1/.test(await msgS()) && savedT && savedT.away.name === FA, JSON.stringify(savedT && savedT.home));
  await resetS(); await typeT('home', 'free home'); rt = await rowsOf(homeSel);
  check('A team saved on the device is offered next time, as "Used in your matches"', rt.some(r => r.name === FH && r.sub === 'Used in your matches'), JSON.stringify(rt.slice(0, 2)));
  await closeS(); await openCardS('imp:' + savedT.id); await pS.click('#aImpEdit'); await pS.waitForSelector('#aForm:not([data-edit=""])');
  const preT = [await pS.inputValue('#aForm [name=home]'), await pS.inputValue('#aForm [name=away]')];
  await typeT('home', 'free'); const edRows = await rowsOf(homeSel);
  check('Edit: the fields open with the stored names and offer the same suggestions', preT.join() === [FH, FA].join() && edRows.some(r => r.name === FH), JSON.stringify(preT));
  await pS.click('#aForm [name=stage]'); await typeT('home', FH);
  const edBefore = JSON.stringify(savedT);
  await pS.click('#aImpBtn'); await pS.waitForSelector('#asheet:not([hidden])'); await pS.waitForTimeout(350);
  const savedT2 = (await stored()).find(x => x.id === savedT.id);
  check('Edit: opening it, typing in the field and saving does not change a stored name', savedT2.home.name === FH && savedT2.away.name === FA && JSON.stringify(savedT2) === edBefore, JSON.stringify(savedT2).slice(0, 120));
  await closeS(); await openCardS('imp:' + savedT.id); await pS.click('#aImpEdit'); await pS.waitForSelector('#aForm:not([data-edit=""])');
  await typeT('away', foldN(accC.name)); await pS.click(`${awaySel} + .asugg button >> nth=0`);
  await pS.click('#aImpBtn'); await pS.waitForSelector('#asheet:not([hidden])'); await pS.waitForTimeout(350);
  const savedT3 = (await stored()).find(x => x.id === savedT.id);
  check('Edit: choosing a suggestion in Away changes Away only (Home untouched, same id)', savedT3.away.name === accC.name && savedT3.home.name === FH && savedT3.id === savedT.id, JSON.stringify(savedT3.away));
  await closeS();

  // Saving a match with free text.
  const nowN = (await stored()).length;
  await resetS(); await fillS(base({})); await typeC(FREE); await typeS('Free Ground ' + TAG); await pS.click('#aImpBtn');
  const svr = (await stored()).find(x => x.competition === FREE);
  check('A match saved with free text in both fields stores it as typed', /^Added 1/.test(await msgS()) && svr && svr.stadium === 'Free Ground ' + TAG && (await stored()).length === nowN + 1, JSON.stringify(svr).slice(0, 100));

  // Romanian: labels in Romanian, stored values in English, nothing overflows.
  await pS.evaluate(() => setLang('ro'));
  await resetS();
  await pS.focus('#aForm [name=competition]');
  await typeC('amical'); rc = await rowsOf(compSel);
  check('Romanian: "Meci amical" is offered', rc.some(r => r.name === 'Meci amical'), JSON.stringify(rc.map(r => r.name)));
  await pS.click(`${compSel} + .asugg .sn:text-is("Meci amical")`);
  check('...tapping it stores the English word "Friendly"', await pS.inputValue('#aForm [name=competition]') === 'Friendly', await pS.inputValue('#aForm [name=competition]'));
  await typeC('demonstrativ'); rc = await rowsOf(compSel);
  await pS.click(`${compSel} + .asugg .sn:text-is("Meci demonstrativ")`);
  check('Romanian: the "Meci demonstrativ" row stores "Exhibition" and switches the toggle on', await pS.inputValue('#aForm [name=competition]') === 'Exhibition' && await pS.inputValue('#aForm [name=exhibition]') === 'yes', '');
  await typeC('liga');
  const totRo = totalFor(compFoldsRo, 'liga');
  const roTxt = await pS.$eval(`${compSel} + .asugg`, e => e.querySelector('.none') ? e.querySelector('.none').textContent : '');
  const roOver = await pS.evaluate(() => { const bad = []; document.getElementById('pane-me').querySelectorAll('*').forEach(x => { const r = x.getBoundingClientRect(); if(r.width > 0 && (r.right > innerWidth + 1 || r.left < -1)) bad.push(x.tagName + '.' + x.className); }); return bad.slice(0, 4); });
  check('Romanian: the "+ n more" line is in Romanian and nothing overflows at 390 px', totRo > 8 && roTxt === `+ încă ${totRo - 8}` && !roOver.length, roTxt + ' expected ' + (totRo - 8) + ' ' + JSON.stringify(roOver));
  // Romanian: the team lists.
  await resetS();
  const modelRo = teamModel(await stored());
  await typeT('home', 'fc'); rt = await rowsOf(homeSel); mt = await moreOf(homeSel);
  const hfRo = modelHits(modelRo, 'fc');
  const ctryRo = await pS.evaluate(cs => Object.fromEntries(cs.map(c => [c, countryName(c)])), codes);
  check('Romanian: the team list gives 8 rows and "+ încă n", and a club\'s second line starts with its Romanian country name',
    hfRo.length > 8 && rt.length === 8 && mt === `+ încă ${hfRo.length - 8}` && rt.filter(r => CLUBN.some(c => c.name === r.name)).every(r => r.sub.startsWith(ctryRo[CLUBN.find(c => c.name === r.name).country] + ' · ')), `${mt} ${hfRo.length} ${rt[0] && rt[0].sub}`);
  await typeT('away', 'free home'); rt = await rowsOf(awaySel);
  check('Romanian: a team only in his matches reads "Folosit în meciurile tale"', rt.some(r => r.name === FH && r.sub === 'Folosit în meciurile tale'), JSON.stringify(rt.slice(0, 2)));
  await pS.click(`${awaySel} + .asugg button >> nth=0`);
  check('Romanian: tapping stores the name as written, not translated', await pS.inputValue('#aForm [name=away]') === FH, await pS.inputValue('#aForm [name=away]'));
  await typeT('home', 'fc');
  const roOverT = await pS.evaluate(() => { const bad = []; document.getElementById('pane-me').querySelectorAll('*').forEach(x => { const r = x.getBoundingClientRect(); if(r.width > 0 && (r.right > innerWidth + 1 || r.left < -1)) bad.push(x.tagName + '.' + x.className); }); return bad.slice(0, 4); });
  check('Romanian: nothing overflows at 390 px with a team list open', !roOverT.length, JSON.stringify(roOverT));
  await pS.evaluate(() => setLang('en'));
  await closeS();

  const keys = await pS.evaluate(() => [...new Set(window.__w)]);
  check('No new storage key: the only keys written are the imported matches\', the backup banner\'s "unsaved" flag and the language (all existing)', keys.every(k => k === IMPK || k === 'football-planner-lang' || k === 'football-planner-me-unsaved'), keys.join());
  const sreq = requests.slice(reqStart);
  check('No request other than GET reached the site, and data/competitions.csv was requested once', nonGet.length === nonGet0 && sreq.filter(r => /data\/competitions\.csv/.test(r.url)).length === 1, nonGet.slice(nonGet0).join());
  await ctxS.close();

  // The CSV cannot load: the other sources still work and nothing breaks.
  const ctxX = await newCtx();
  await ctxX.route('**/data/competitions.csv', r => r.abort());
  const pX = await ctxX.newPage();
  const errX = errors.length;
  pX.on('pageerror', e => errors.push(e.message));
  await pX.goto(BASE);
  await pX.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await pX.click('nav button[data-pane=me]'); await pX.waitForSelector('#meStats .astat');
  await pX.click('#meTabMatches'); await pX.waitForSelector('#aForm', {state: 'attached'}); await pX.click('#aAdd summary');
  await pX.focus('#aForm [name=competition]'); await pX.waitForTimeout(600);
  await pX.fill('#aForm [name=competition]', 'friend');
  const xr = await pX.$$eval('label:has([name=competition]) + .asugg button .sn', b => b.map(x => x.textContent));
  const csvOnly = CSVN.find(r => foldN(r.name) && !compFoldsNoCsv.has(foldN(r.name)));
  await pX.fill('#aForm [name=competition]', csvOnly ? csvOnly.name : 'zzzz');
  const xo = await pX.$$eval('label:has([name=competition]) + .asugg button .sn', b => b.map(x => x.textContent));
  const gv = CLUBN.find(c => c.venue).venue;
  await pX.fill('#aForm [name=stadium]', foldN(gv));
  const xs = await pX.$$eval('label:has([name=stadium]) + .asugg button .sn', b => b.map(x => x.textContent));
  check('CSV unreachable: "Friendly" and the club grounds are still offered, a CSV-only name is not, and there is no script error',
    xr.includes('Friendly') && xs.includes(gv) && (!csvOnly || !xo.includes(csvOnly.name)) && errors.length === errX, JSON.stringify({xr, csvOnly: csvOnly && csvOnly.name, xo, xs: xs.slice(0, 2)}));
  await ctxX.close();
  }

  {
  // ---- 2026-10-13: the Add an event form (and Edit this event), the imported events, and the version 3 backup file. Expected values are worked
  //      out here from the form's own input and from data/attended.json, never typed in as results. Own context, so the earlier counts are not disturbed.
  const IMPK = 'football-attended-imported', PERK = 'football-attended-personal';
  const reqStart = requests.length;
  const ctxE = await newCtx();
  await ctxE.addInitScript(() => {
    window.__r = []; window.__w = []; window.__i = [];
    const g = Storage.prototype.getItem, w = Storage.prototype.setItem, r = Storage.prototype.removeItem;
    Storage.prototype.getItem = function(k){ window.__r.push(k); return g.call(this, k); };
    Storage.prototype.setItem = function(k, v){ window.__w.push(k); return w.call(this, k, v); };
    Storage.prototype.removeItem = function(k){ window.__w.push(k); return r.call(this, k); };
    const o = IDBFactory.prototype.open;
    IDBFactory.prototype.open = function(n){ window.__i.push(n); return o.apply(this, arguments); };
  });
  const pE = await ctxE.newPage();
  pE.on('pageerror', e => errors.push(e.message));
  pE.on('dialog', d => d.accept());
  await pE.goto(BASE);
  await pE.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await pE.click('nav button[data-pane=me]');
  await pE.waitForSelector('#meStats .astat');
  const toEvents = async () => { await pE.click('#meTabEvents'); await pE.waitForSelector('#aEvForm', {state: 'attached'}); };
  await toEvents();
  const evKeys = [...new Set(ATTF.events.flatMap(e => Object.keys(e)))].sort();         // the fields the events hold
  const lsE = k => pE.evaluate(x => localStorage.getItem(x), k);
  const storedAll = async () => { const v = await lsE(IMPK); return v ? JSON.parse(v) : {matches: [], events: undefined}; };
  const storedEv = async () => (await storedAll()).events || [];
  const openAddE = async () => { if(!(await pE.$eval('#aEvAdd', d => d.open))) await pE.click('#aEvAdd summary'); };
  const msgE = async () => (await pE.textContent('#aEvMsg')).trim();
  const ferrE = async name => (await pE.textContent(`#aEvForm [data-ferr="${name}"]`)).trim();
  const submitE = async () => { await pE.click('#aEvBtn'); return msgE(); };
  const fillE = async v => { for(const [k, val] of Object.entries(v)) { if(k === 'atStadium') await pE.selectOption('#aEvForm [name=atStadium]', val); else await pE.fill(`#aEvForm [name=${k}]`, val); } };
  const resetE = async () => { await openAddE(); await pE.click('#aEvCancel'); await openAddE(); };
  const strip = r => { const c = JSON.parse(JSON.stringify(r)); delete c.id; return c; };
  const canon = o => JSON.stringify(o, (k, v) => v && typeof v === 'object' && !Array.isArray(v) ? Object.fromEntries(Object.entries(v).sort()) : v);
  const partE = s => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const idRe = /^[A-Za-z0-9._-]{1,80}$/;
  const overE = () => pE.evaluate(() => { const bad = [];
    document.querySelectorAll('#pane-me *, #asheet *').forEach(x => { const r = x.getBoundingClientRect(); if(r.width > 0 && (r.right > innerWidth + 1 || r.left < -1)) bad.push(x.tagName + '.' + x.className); });
    return {bad: bad.slice(0, 4), doc: document.documentElement.scrollWidth}; });
  const openEvCard = async key => { await pE.click('#meTabEvents'); await pE.waitForSelector('#meEvents .acard'); await pE.click(`#meEvents .acard[data-id="${key}"]`); await pE.waitForSelector('#asheet:not([hidden])'); await pE.waitForTimeout(350); };
  const sheetE = () => pE.evaluate(() => ({text: document.getElementById('asheetBody').innerText, head: document.getElementById('asheetHead').innerText,
    pf: [...document.querySelectorAll('#asheetBody [data-pf]')].map(x => x.dataset.pf), btn: [...document.querySelectorAll('#asheetBody .ab')].map(x => x.id)}));
  const closeE = async () => { if(!(await pE.$eval('#asheet', x => x.hidden))) await pE.click('#asheetClose'); };
  const idbE = () => pE.evaluate(() => new Promise((res, rej) => {
    const rq = indexedDB.open('football-attended-media');
    rq.onsuccess = () => { const db = rq.result, g = db.transaction('items').objectStore('items').getAll(); g.onsuccess = () => { db.close(); res(g.result.map(x => x.entryId)); }; };
    rq.onerror = () => rej(rq.error);
  }));
  const stor = {r: [], w: [], i: []};          // the page's storage log, collected before every reload (a reload starts a new log)
  const harvestE = async () => { const x = await pE.evaluate(() => ({r: window.__r, w: window.__w, i: window.__i})); stor.r.push(...x.r); stor.w.push(...x.w); stor.i.push(...x.i); };
  const T = 'Fan walk ' + TAG, D = '2026-05-09';
  const F = {title: T, date: D, place: 'Marktplatz ' + TAG, atStadium: 'yes', note: 'Line one ' + TAG + '\nLine two'};
  const expectRec = () => ({date: F.date, title: F.title, place: F.place, note: F.note, atStadium: true});

  check('The Events sub-tab has a collapsed "Add an event" above the list, and the file\'s events are listed as before', (await pE.$eval('#aEvAdd', d => ({open: d.open, s: d.querySelector('summary').textContent}))).s === 'Add an event' &&
    !(await pE.$eval('#aEvAdd', d => d.open)) && JSON.stringify(await pE.$$eval('#meEvents .acard', cs => cs.map(c => c.dataset.id))) === JSON.stringify(ATTF.events.map(e => e.id)), '');
  await openAddE();
  const labels = await pE.$$eval('#aEvForm label, #aEvForm .flab', ls => ls.map(l => l.firstChild.textContent.trim()));
  check('The form has the fields in the order the event sheet shows them: name, date, place, at the stadium, factual note; then the optional JSON box last', JSON.stringify(labels) === JSON.stringify(['Name', 'Date', 'Place', 'I was at the stadium', 'Factual note', 'JSON (optional)']), JSON.stringify(labels));
  check('...and every form field is named after a real field of the events (title, date, place, atStadium, note)',
    JSON.stringify(await pE.$$eval('#aEvForm input, #aEvForm select, #aEvForm textarea:not(#aEvBox)', xs => xs.map(x => x.name))) === JSON.stringify(['title', 'date', 'place', 'atStadium', 'note']) &&
    ['title', 'date', 'place', 'atStadium', 'note'].every(k => evKeys.includes(k)), evKeys.join());
  check('"I was at the stadium" is a Yes/No choice that starts on No', await pE.$eval('#aEvForm [name=atStadium]', x => x.value + '|' + [...x.options].map(o => o.textContent).join('/')) === 'no|No/Yes', '');

  // Each missing required field is refused, with a reason next to it, nothing stored and the rest of what was typed kept.
  const reqBad = [];
  for(const [what, [field, kept]] of Object.entries({'the name': ['title', 'place'], 'the date': ['date', 'title']})){
    await resetE(); await fillE(F); await pE.fill(`#aEvForm [name=${field}]`, '');
    const m = await submitE();
    if(!/^Not saved/.test(m) || !(await ferrE(field)) || (await storedEv()).length || await pE.inputValue(`#aEvForm [name=${kept}]`) !== F[kept]) reqBad.push(`${what}: ${m} / ${await ferrE(field)}`);
  }
  check('Each missing required field (name, date) is refused: "Not saved", the reason beside the field, nothing stored, everything else typed kept', !reqBad.length, reqBad.join(' | '));

  // A full save: every field stored under the real names.
  await resetE(); await fillE(F);
  const mAdd = await submitE();
  const st1 = await storedAll();
  check('A saved event is stored in football-attended-imported under "events" with every field under its real name, "matches" untouched, version still 1',
    st1.version === 1 && Array.isArray(st1.matches) && st1.events.length === 1 && canon(strip(st1.events[0])) === canon(expectRec()) && Object.keys(st1.events[0]).every(k => evKeys.includes(k)) && /Added 1 imported event/.test(mAdd), JSON.stringify(st1).slice(0, 220) + ' / ' + mAdd);
  const id1 = st1.events[0].id;
  check('The generated id is date and name, ASCII, allowed characters only, at most 80', idRe.test(id1) && id1 === `${D}-${partE(T)}`.slice(0, 76) && /^[\x20-\x7e]+$/.test(id1), id1);
  check('The new event is listed after the file\'s, marked "Imported on this device", and its card is addressed impev:<id>',
    await pE.$$eval('#meEvents .acard', cs => cs.map(c => c.dataset.id)).then(a => a.length === ATTF.events.length + 1 && a[a.length - 1] === 'impev:' + id1) &&
    /Imported on this device/.test(await pE.$eval('#meEvents .acard:last-of-type', c => c.textContent)), '');
  await openEvCard('impev:' + id1);
  const sh1 = await sheetE();
  const afactE = await pE.$eval('#asheetBody .afact', x => x.innerText);
  const conds1 = {place: sh1.text.includes(F.place), stad: /At the stadium\s*yes/i.test(sh1.text), note: sh1.text.includes('Line one ' + TAG) && /Factual note/i.test(sh1.text), noLabel: !/Written by an assistant/.test(sh1.text),
    tag: /Imported on this device/i.test(sh1.head), btn: JSON.stringify(sh1.btn.filter(x => x.startsWith('aEv'))) === '["aEvEdit","aEvRemove"]', br: afactE === F.note};
  check('Its sheet shows the date, place, "At the stadium yes", one Factual note with the line break kept, no "written by an assistant" label, the tag, and Edit and Remove', Object.values(conds1).every(Boolean), JSON.stringify(conds1) + JSON.stringify(afactE));
  check('The stadium Yes shows ticket, block, row and seat beside the notes and who I went with, in that order', JSON.stringify(sh1.pf) === JSON.stringify(PF_ORDER), JSON.stringify(sh1.pf));
  const fileEv = ATTF.events.find(e => e.atStadium === true), noEv = ATTF.events.find(e => e.atStadium === false);
  await closeE(); await openEvCard(noEv.id);
  const shNo = await sheetE();
  check('A file event keeps its "written by an assistant" label and has no Edit or Remove; with the stadium No only notes and who I went with show',
    /Written by an assistant from memory/.test(shNo.text) && !shNo.btn.some(x => x.startsWith('aEv')) && JSON.stringify(shNo.pf) === '["note","withWho"]', JSON.stringify(shNo));
  await closeE();

  // Personal fields and a photo, keyed by the address.
  await openEvCard('impev:' + id1);
  await pE.fill('#asheetBody [data-pf=note]', 'Mine ' + TAG);
  await pE.fill('#asheetBody [data-pf=ticket]', 'T-' + TAG);
  await pE.setInputFiles('#aMfile', [{name: 'ev.png', mimeType: 'image/png', buffer: PNG}]);
  await pE.waitForFunction(() => document.querySelectorAll('#aMgrid .amcell').length === 1, null, {timeout: 10000}).catch(() => {});
  const per1 = JSON.parse(await lsE(PERK) || '{}');
  check('Its personal fields and photo are keyed impev:<id>, in the personal record and the media database', per1['impev:' + id1]?.note === 'Mine ' + TAG && per1['impev:' + id1]?.ticket === 'T-' + TAG &&
    !(id1 in per1) && (await idbE()).filter(k => k === 'impev:' + id1).length === 1, JSON.stringify(Object.keys(per1)) + JSON.stringify(await idbE()));
  await closeE();

  // Ids stay unique across all the id spaces, in both orders.
  await resetE(); await fillE(F);
  const mDup = await submitE(); const stDup = (await storedEv());
  check('The same date and name again gets -2 (then -3): ids never repeat', stDup.length === 2 && stDup[1].id === id1 + '-2', stDup.map(e => e.id).join());
  await resetE(); await fillE(F); await submitE();
  check('...and -3', (await storedEv()).map(e => e.id).join() === [id1, id1 + '-2', id1 + '-3'].join(), (await storedEv()).map(e => e.id).join());
  const longT = 'Long name ' + 'abc '.repeat(40) + TAG;
  await resetE(); await fillE({title: longT, date: D, atStadium: 'no'}); await submitE();
  const longEv = (await storedEv()).pop();
  check('A very long name still gives a valid id of at most 80 characters, and an event typed with the stadium No stores atStadium false', idRe.test(longEv.id) && longEv.id.length <= 80 && longEv.atStadium === false, longEv.id);
  // an imported match and an imported event with the same date and name
  const MD = '2026-06-01';
  await pE.click('#meTabMatches'); await pE.waitForSelector('#aForm', {state: 'attached'});
  if(!(await pE.$eval('#aAdd', d => d.open))) await pE.click('#aAdd summary');
  for(const [k, val] of Object.entries({date: MD, home: 'Alpha ' + TAG, away: 'Beta', sh: '1', sa: '0'})) await pE.fill(`#aForm [name=${k}]`, val);
  await pE.click('#aImpBtn');
  const matchId = (await storedAll()).matches[0].id;
  await toEvents(); await openAddE(); await fillE({title: 'Alpha ' + TAG + ' Beta', date: MD}); await submitE();
  const evSame = (await storedEv()).pop();
  check('An imported event and an imported match with the same date and name never clash: the event\'s id differs, and a match added after an event gets a new id too',
    matchId === `${MD}-${partE('Alpha ' + TAG)}-beta` && evSame.id === matchId + '-2', matchId + ' / ' + evSame.id);
  await toEvents(); await openAddE(); await fillE({title: 'Gamma ' + TAG + ' Delta', date: MD}); await submitE();
  const ev2 = (await storedEv()).pop();
  await pE.click('#meTabMatches'); await pE.waitForSelector('#aForm', {state: 'attached'});
  if(!(await pE.$eval('#aAdd', d => d.open))) await pE.click('#aAdd summary');
  await pE.fill('#aForm [name=date]', MD); await pE.fill('#aForm [name=home]', 'Gamma ' + TAG); await pE.fill('#aForm [name=away]', 'Delta'); await pE.fill('#aForm [name=sh]', '2'); await pE.fill('#aForm [name=sa]', '2');
  await pE.click('#aImpBtn');
  const m2 = (await storedAll()).matches.pop();
  const allIds = [...ATTF.events.map(e => e.id), ...ATTF.matches.map(m => m.id), ...(await storedAll()).matches.map(m => m.id), ...(await storedEv()).map(e => e.id)];
  check('...in the other order too (an event first, then a match with the same date and name: the match gets -2), and no id is used twice anywhere (file events, file matches, imported matches, imported events)',
    ev2.id === `${MD}-${partE('Gamma ' + TAG)}-delta` && m2.id === ev2.id + '-2' && new Set(allIds).size === allIds.length, m2.id + ' / ' + ev2.id);
  await toEvents();

  // The JSON box.
  const base = (await storedEv()).length;
  await resetE();
  const rA = await (async () => { await pE.fill('#aEvBox', JSON.stringify([{id: 'json-a-' + TAG, date: '2026-07-01', title: 'JSON A ' + TAG}, {id: 'json-b-' + TAG, date: '2026-07-02', title: {ro: 'Ro ' + TAG, en: 'En ' + TAG}, place: 'P', note: 'N', atStadium: true}])); return submitE(); })();
  check('Form empty + a list in the JSON box: accepted as a plain import (two events, the object form of title kept)', (await storedEv()).length === base + 2 && /Added 2 imported event/.test(rA) &&
    canon((await storedEv()).find(e => e.id === 'json-b-' + TAG).title) === canon({ro: 'Ro ' + TAG, en: 'En ' + TAG}), rA);
  await openAddE(); await fillE({title: 'Form ' + TAG, date: '2026-08-01'}); await pE.fill('#aEvBox', JSON.stringify([{id: 'json-c-' + TAG, date: '2026-08-02', title: 'C'}]));
  const rB = await submitE();
  check('Form filled + a list in the JSON box: refused (one object needed), nothing stored, the form keeps what was typed', /one event object/.test(rB) && (await storedEv()).length === base + 2 && await pE.inputValue('#aEvForm [name=title]') === 'Form ' + TAG, rB);
  await pE.fill('#aEvBox', JSON.stringify({place: 'From JSON ' + TAG, note: 'Json note', id: 'json-d-' + TAG}));
  const rC = await submitE();
  const evC = (await storedEv()).find(e => e.id === 'json-d-' + TAG);
  check('Form filled + one object that only adds keys the form left empty (place, note, id): accepted, merged key by key, atStadium false', !!evC && canon(strip(evC)) === canon({date: '2026-08-01', title: 'Form ' + TAG, place: 'From JSON ' + TAG, note: 'Json note', atStadium: false}) && /Added 1/.test(rC), rC + JSON.stringify(evC));
  await resetE(); await fillE({title: 'Form2 ' + TAG, date: '2026-08-03'}); await pE.fill('#aEvBox', JSON.stringify({title: 'Other', id: 'json-e-' + TAG}));
  const rD = await submitE(); const n3 = (await storedEv()).length;
  check('A JSON object repeating a field the form filled is refused with its key named, nothing stored', /both the form and the JSON fill "title"/.test(rD) && n3 === base + 3, rD);
  await pE.fill('#aEvBox', JSON.stringify({atStadium: true}));
  await pE.selectOption('#aEvForm [name=atStadium]', 'yes');
  const rD2 = await submitE();
  check('...the Yes of the stadium choice counts as filled: a JSON atStadium is then refused by key', /both the form and the JSON fill "atStadium"/.test(rD2) && (await storedEv()).length === n3, rD2);
  await pE.selectOption('#aEvForm [name=atStadium]', 'no');
  await pE.fill('#aEvBox', JSON.stringify({atStadium: true, foo: 1, id: 'json-f-' + TAG}));
  const rE = await submitE();
  check('The merged result goes through the same validator: an unknown field is refused, every reason shown, nothing stored', /Not added, nothing was stored/.test(rE) && /unknown field "foo"/.test(rE) && (await storedEv()).length === n3, rE);
  await pE.fill('#aEvBox', JSON.stringify({id: 'json-g-' + TAG, atStadium: 'yes'}));
  const rE2 = await submitE();
  check('...a field of the wrong type is refused', /"atStadium" must be true or false/.test(rE2) && (await storedEv()).length === n3, rE2);
  await resetE();
  const clashes = [['an id the file\'s events use', ATTF.events[0].id], ['an id the file\'s matches use', ATTF.matches[0].id], ['an imported match', matchId], ['an imported event', id1]];
  const clBad = [];
  for(const [what, cid] of clashes){
    await pE.fill('#aEvBox', JSON.stringify({id: cid, date: '2026-09-01', title: 'Clash'})); const m = await submitE();
    if(!/Not added/.test(m) || !new RegExp(cid.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).test(m) || (await storedEv()).length !== n3) clBad.push(`${what}: ${m.slice(0, 100)}`);
  }
  check('A JSON id already used in any of the four spaces is refused, naming the id', !clBad.length, clBad.join(' | '));
  await pE.fill('#aEvBox', JSON.stringify([{id: 'x1', date: '2026-09-01', title: 'a'}, {id: 'x1', date: '2026-09-01', title: 'b'}]));
  check('...and so is the same id twice in one paste', /appears twice/.test(await submitE()) && (await storedEv()).length === n3, '');
  await pE.fill('#aEvBox', JSON.stringify({id: 'bad-date', date: '2026-02-31', title: 'x'}));
  check('...an impossible date in the JSON is refused by the validator', /"date" must be a real day/.test(await submitE()) && (await storedEv()).length === n3, '');
  await pE.fill('#aEvBox', JSON.stringify(Array.from({length: 51}, (_, i) => ({id: `lim-${i}`, date: '2026-09-01', title: 'L' + i}))));
  const rL = await submitE();
  check('Limits: 51 events in one paste are refused (50 at a time), and 200,001 characters are refused', /at most 50 events/.test(rL) && (await (async () => { await pE.fill('#aEvBox', 'x'.repeat(200001)); return /Too much text/.test(await submitE()); })()) && (await storedEv()).length === n3, rL);
  // up to 100 in all
  const room = 100 - n3;
  for(let from = 0; from < room; from += 50){
    await pE.fill('#aEvBox', JSON.stringify(Array.from({length: Math.min(50, room - from)}, (_, i) => ({id: `fill-${from + i}`, date: '2026-09-01', title: 'F' + (from + i)}))));
    await submitE(); await openAddE();
  }
  check('Exactly 100 imported events can be held', (await storedEv()).length === 100, String((await storedEv()).length));
  await openAddE(); await pE.fill('#aEvBox', JSON.stringify({id: 'over-1', date: '2026-09-01', title: 'Over'}));
  const rO = await submitE();
  check('The 101st is refused ("at most 100 imported events") and the matches have their own count (50 per paste, 300 in all) apart from it', /at most 100 imported events/.test(rO) && (await storedEv()).length === 100, rO);
  // back to a handful: keep the first five stored events
  const all100 = await storedEv(), keep = all100.slice(0, 4).concat(all100.filter(e => e.id === 'json-b-' + TAG));
  await pE.evaluate(([k, ev]) => { const v = JSON.parse(localStorage.getItem(k)); v.events = ev; localStorage.setItem(k, JSON.stringify(v)); }, [IMPK, keep]);
  await harvestE(); await pE.reload(); await pE.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await pE.click('nav button[data-pane=me]'); await toEvents();

  // Edit this event.
  const target = keep[1];
  await openEvCard('impev:' + target.id);
  await pE.click('#aEvEdit');
  await pE.waitForSelector('#aEvForm[data-edit]');
  const pre = await pE.evaluate(() => ({title: document.querySelector('#aEvForm [name=title]').value, date: document.querySelector('#aEvForm [name=date]').value, place: document.querySelector('#aEvForm [name=place]').value,
    st: document.querySelector('#aEvForm [name=atStadium]').value, note: document.querySelector('#aEvForm [name=note]').value, box: !!document.getElementById('aEvBox'), edit: document.getElementById('aEvForm').dataset.edit}));
  check('Edit this event opens the same form pre-filled from the stored record (same id), and the JSON box is hidden', pre.edit === target.id && pre.title === target.title && pre.date === target.date && pre.place === target.place &&
    pre.st === (target.atStadium ? 'yes' : 'no') && pre.note === target.note && !pre.box, JSON.stringify(pre));
  await pE.fill('#aEvForm [name=title]', 'Renamed ' + TAG); await pE.selectOption('#aEvForm [name=atStadium]', target.atStadium ? 'no' : 'yes');
  await pE.click('#aEvBtn');
  await pE.waitForSelector('#asheet:not([hidden])'); await pE.waitForTimeout(300);
  const after = (await storedEv()).find(e => e.id === target.id);
  check('Saving an edit keeps the id and replaces only the covered fields; the sheet reopens on the same event', !!after && canon(after) === canon(Object.assign({}, target, {title: 'Renamed ' + TAG, atStadium: !target.atStadium})) &&
    (await storedEv()).length === 5 && /Renamed/.test((await sheetE()).head), JSON.stringify(after));
  const sh2 = await sheetE();
  check('...the stadium toggle shows or hides ticket, block, row and seat (now ' + (target.atStadium ? 'No' : 'Yes') + ')', JSON.stringify(sh2.pf) === JSON.stringify(target.atStadium ? PF_ORDER.filter(k => !PF_TICKET.includes(k)) : PF_ORDER), JSON.stringify(sh2.pf));
  await closeE();
  // personal fields and the media record of the first event stayed attached (id1 is the first stored event)
  await openEvCard('impev:' + id1); await pE.click('#aEvEdit'); await pE.waitForSelector('#aEvForm[data-edit]');
  await pE.fill('#aEvForm [name=place]', 'Edited place ' + TAG); await pE.click('#aEvBtn');
  await pE.waitForSelector('#asheet:not([hidden])'); await pE.waitForTimeout(300);
  const per2 = JSON.parse(await lsE(PERK) || '{}');
  check('Editing keeps the personal fields and the media record attached to the same address', per2['impev:' + id1]?.note === 'Mine ' + TAG && per2['impev:' + id1]?.ticket === 'T-' + TAG &&
    (await idbE()).filter(k => k === 'impev:' + id1).length === 1 && /Edited place/.test((await sheetE()).text), JSON.stringify(per2['impev:' + id1]));
  await closeE();
  // a stored {ro,en} title is kept when the name is not touched
  const objEv = (await storedEv()).find(e => e.title && typeof e.title === 'object');
  if(objEv){
    await openEvCard('impev:' + objEv.id); await pE.click('#aEvEdit'); await pE.waitForSelector('#aEvForm[data-edit]');
    await pE.fill('#aEvForm [name=place]', 'Moved ' + TAG); await pE.click('#aEvBtn'); await pE.waitForSelector('#asheet:not([hidden])'); await pE.waitForTimeout(300);
    const o2 = (await storedEv()).find(e => e.id === objEv.id);
    check('A stored {ro, en} name that was not changed in the form stays an {ro, en} pair', canon(o2.title) === canon(objEv.title) && o2.place === 'Moved ' + TAG, JSON.stringify(o2));
    await closeE();
  }else check('A stored {ro, en} name stays a pair when untouched', false, 'no object-title event kept');
  await openEvCard('impev:' + target.id); await pE.click('#aEvEdit'); await pE.waitForSelector('#aEvForm[data-edit]');
  await pE.fill('#aEvForm [name=title]', ''); await pE.click('#aEvBtn');
  check('An edit that empties the name is refused and nothing changes', /^Not saved/.test(await msgE()) && (await storedEv()).find(e => e.id === target.id).title === 'Renamed ' + TAG, '');
  await pE.click('#aEvCancel'); await pE.waitForSelector('#aEvAdd summary');

  // Remove this imported event.
  await openEvCard('impev:' + id1);
  const nBefore = (await storedEv()).length, mBefore = (await storedAll()).matches.length;
  await pE.click('#aEvRemove');
  await pE.waitForFunction(() => document.getElementById('asheet').hidden, null, {timeout: 5000}).catch(() => {});
  await pE.waitForTimeout(300);
  const per3 = JSON.parse(await lsE(PERK) || '{}');
  check('Removing an imported event (asked first) deletes it, its personal fields and its media; the other events and the matches are untouched', (await storedEv()).length === nBefore - 1 &&
    !(await storedEv()).some(e => e.id === id1) && !(('impev:' + id1) in per3) && !(await idbE()).includes('impev:' + id1) && (await storedAll()).matches.length === mBefore, '');

  // The backup file.
  await pE.click('#meTabTix'); await pE.waitForSelector('#meExport');
  const dlE = async click => { const [d] = await Promise.all([pE.waitForEvent('download'), click()]); return {name: d.suggestedFilename(), text: fs.readFileSync(await d.path(), 'utf8')}; };
  const expE = await dlE(() => pE.click('#meExport'));
  const fE = JSON.parse(expE.text);
  const evNow = await storedEv();
  check('Export: version 3 with importedEvents exactly as stored, and the Back up text and the message say events are in it, photos and videos are not', fE.version === 3 && canon(fE.importedEvents) === canon(evNow) && /not in this file/.test(fE.notIncluded || '') &&
    /imported events/.test(await pE.textContent('#meMsg')) && /imported events/.test(await pE.textContent('#meBody')), (await pE.textContent('#meMsg')).slice(-140));
  const importE = async (obj, name) => {
    const fp = path.join(require('os').tmpdir(), `me-${name}-${TAG}.json`);
    fs.writeFileSync(fp, typeof obj === 'string' ? obj : JSON.stringify(obj));
    await pE.setInputFiles('#meFile', []); await pE.setInputFiles('#meFile', fp);
    await pE.waitForFunction(() => document.getElementById('meConfirm') || /Not imported/.test(document.getElementById('meMsg')?.textContent || ''), null, {timeout: 8000}).catch(() => {});
    const r = {confirm: (await pE.$('#meConfirm')) ? await pE.textContent('#meConfirm') : '', msg: (await pE.$('#meMsg')) ? await pE.textContent('#meMsg') : ''};
    fs.unlinkSync(fp); return r;
  };
  const devE = async () => JSON.stringify([await lsE(PERK), await lsE(IMPK)]);
  const devBeforeE = await devE();
  const refE = [
    ['a version 3 file with no importedEvents list', Object.assign({}, fE, {importedEvents: undefined}), /no importedEvents list/],
    ['an invalid imported event', Object.assign({}, fE, {importedEvents: [Object.assign({}, evNow[0], {date: '2026-13-40'})]}), /"date"/],
    ['an imported event with an unknown field', Object.assign({}, fE, {importedEvents: [Object.assign({}, evNow[0], {secret: 'x'})]}), /unknown field "secret"/],
    ['an imported event whose id a file event uses', Object.assign({}, fE, {importedEvents: [Object.assign({}, evNow[0], {id: ATTF.events[0].id})]}), /already used by a match or an event in data\/attended\.json/],
    ['an imported event whose id a file match uses', Object.assign({}, fE, {importedEvents: [Object.assign({}, evNow[0], {id: ATTF.matches[0].id})]}), /already used by a match or an event in data\/attended\.json/],
    ['the same event id twice', Object.assign({}, fE, {importedEvents: [evNow[0], evNow[0]]}), /the same id twice/],
    ['101 imported events', Object.assign({}, fE, {importedEvents: Array.from({length: 101}, (_, i) => ({id: `e${i}`, date: '2026-01-01', title: 'E'}))}), /more than 100 imported events/],
    ['a card number in a personal field of an imported event', Object.assign({}, fE, {personal: Object.assign({}, fE.personal, {['impev:' + evNow[0].id]: {ticket: '4111 1111 1111 1111'}})}), /payment card number/],
    ['a newer version', Object.assign({}, fE, {version: 4}), /newer version/],
  ];
  const refBadE = [];
  for(const [what, obj, re] of refE){
    const r = await importE(obj, 'bade');
    if(!/Not imported/.test(r.msg) || !re.test(r.msg) || !/Nothing on this device was changed/.test(r.msg) || r.confirm || await devE() !== devBeforeE) refBadE.push(`${what}: ${r.msg.slice(0, 160)}`);
  }
  check('Import refuses (device unchanged): a missing importedEvents list, an invalid event, an unknown field, an id clash with the file\'s events or matches, a repeated id, more than 100, a card number, a newer version', !refBadE.length, refBadE.join(' | '));
  // round trip: remove one event, import the export, it is back
  await pE.evaluate(([k, ev]) => { const v = JSON.parse(localStorage.getItem(k)); v.events = ev; localStorage.setItem(k, JSON.stringify(v)); }, [IMPK, evNow.slice(0, 1)]);
  const impE = await importE(fE, 'good');
  check('A version 3 file first says what it holds, including its imported events', /plus \d+ attended-match records? \(notes and supporter choices\) and \d+ imported match(es)?, as well as 4 imported events/.test(impE.confirm), impE.confirm);
  await pE.click('[data-act=import-yes]');
  const msgImp = await pE.textContent('#meMsg');
  check('Round trip: the imported events are exactly as exported and the message says they were replaced', canon(await storedEv()) === canon(evNow) && /imported events on this device were replaced/.test(msgImp), msgImp.slice(-170));
  const devKeep = await devE();
  const v2file = Object.assign({}, fE, {version: 2}); delete v2file.importedEvents;
  await pE.click('#meTabTix'); await pE.waitForSelector('#meFile', {state: 'attached'});
  const r2 = await importE(v2file, 'v2'); await pE.click('[data-act=import-yes]');
  const m2msg = await pE.textContent('#meMsg');
  check('A version 2 file still imports and leaves the imported events alone (and says so)', !/Not imported/.test(r2.msg) && canon(await storedEv()) === canon(evNow) && /imported events on this device were left as they are/.test(m2msg), m2msg.slice(-170));
  const r1 = await importE({format: 'football-planner-me', version: 1, memberships: [], tickets: [], favorites: [], settings: {renewWindowDays: 30}}, 'v1e'); await pE.click('[data-act=import-yes]');
  check('A version 1 file leaves the imported events alone too (and says so)', !/Not imported/.test(r1.msg) && canon(await storedEv()) === canon(evNow) && /left as they are/.test(await pE.textContent('#meMsg')), (await pE.textContent('#meMsg')).slice(-120));
  // a stored record from before this feature (no "events" at all) reads as no events and keeps its matches
  await pE.evaluate(([k, m]) => localStorage.setItem(k, JSON.stringify({version: 1, matches: m})), [IMPK, (await storedAll()).matches]);
  await harvestE(); await pE.reload(); await pE.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await pE.click('nav button[data-pane=me]'); await toEvents();
  check('A stored record without "events" reads as no events, its matches are untouched, and nothing is rewritten by reading', (await pE.$$('#meEvents .acard')).length === ATTF.events.length && (await storedAll()).matches.length === mBefore && (await storedAll()).events === undefined, '');
  await pE.evaluate(k => localStorage.setItem(k, JSON.stringify({version: 1, matches: [], events: [{id: 'ok-1', date: '2026-01-01', title: 'Fine'}, {id: 'bad id', date: '2026-01-01', title: 'x'}, 7]})), IMPK);
  await harvestE(); await pE.reload(); await pE.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await pE.click('nav button[data-pane=me]'); await toEvents();
  check('A stored event that no longer validates is left out and counted on the tab; the good one stays', (await pE.$$('#meEvents .acard')).length === ATTF.events.length + 1 && /2 stored imported event\(s\) could not be read/.test(await pE.textContent('#meEvents')), '');

  // Romanian, at 390 px.
  await pE.evaluate(() => setLang('ro'));
  await toEvents(); await openAddE();
  const roTxt = await pE.textContent('#meEvents');
  const roLab = await pE.$$eval('#aEvForm label, #aEvForm .flab', ls => ls.map(l => l.firstChild.textContent.trim()));
  check('Romanian: the form and its labels are in Romanian and nothing overflows at 390 px', /Adaugă un eveniment/.test(roTxt) && JSON.stringify(roLab) === JSON.stringify(['Nume', 'Data', 'Locul', 'Am fost la stadion', 'Notă factuală', 'JSON (opțional)']) &&
    JSON.stringify(await pE.$$eval('#aEvForm [name=atStadium] option', o => o.map(x => x.textContent))) === '["Nu","Da"]' && !(await overE()).bad.length && (await overE()).doc <= 390, JSON.stringify(roLab) + JSON.stringify(await overE()));
  await pE.click('#aEvCancel');
  await pE.click('#meEvents .acard:last-of-type'); await pE.waitForSelector('#asheet:not([hidden])'); await pE.waitForTimeout(350);
  const roSh = await sheetE();
  check('Romanian: the imported event\'s sheet has its buttons in Romanian and fits', /Modifică acest eveniment/.test(await pE.textContent('#aEvEdit')) && /Șterge acest eveniment importat/.test(await pE.textContent('#aEvRemove')) && !(await overE()).bad.length, JSON.stringify(await overE()));
  await closeE(); await pE.evaluate(() => setLang('en'));
  await toEvents(); await openAddE();
  await pE.fill('#aEvForm [name=title]', 'Keep me typed'); 
  noSideways('Events tab with the form open: no sideways scroll at 390 px', await sideways(pE));

  // Storage, and what leaves the device.
  await harvestE(); const srE = stor;
  check('No mf_ key was read or written and no mf_ database opened by any of it', ![...srE.r, ...srE.w, ...srE.i].some(k => String(k).startsWith('mf_')) && srE.w.includes(IMPK), [...new Set(srE.w)].join());
  const typedE = [TAG, 'Line one', 'Keep me typed', 'Mine ', 'From JSON'];
  const leakedE = requests.slice(reqStart).filter(r => typedE.some(s => (r.url + r.body + r.headers).includes(s) || (r.url + r.body + r.headers).includes(encodeURIComponent(s))));
  check('Nothing typed into the event form, the JSON box or the sheet appears in any request (URL, body or headers)', !leakedE.length, leakedE.map(r => r.method + ' ' + r.url.slice(0, 80)).join(', '));
  check('data/attended.json was only ever fetched (GET), never written, and no request other than GET reached the site', !nonGet.length && !requests.slice(reqStart).some(r => r.method !== 'GET' && r.method !== 'HEAD' && r.url.startsWith(BASE)), nonGet.join(', '));
  await ctxE.close();
  }

  {
  // ---- 2026-10-09: the whole interface in two languages. The dictionary, the Settings sheet, the choice kept on the device, every
  //      main tab and the four Me sub-tabs in Romanian at 390 px, no English left outside the data's own text, and a live change.
  const NAMES_SAME = new Set(['tl.pen', 'sx.xg', 'st.redSplit', 'imp.placeholder', 'md.video', 'sheet.club', 'tk.link', 'tk.max', 'rt.cost.km', 'rt.cost.l100', 'cn.AT', 'cn.RS',
    'oc.sold-out', 'cov.club.one', 'cnm.Austria', 'cnm.Argentina', 'cnm.Serbia', 'cnm.Bulgaria', 'cnm.Chile', 'cnm.Slovenia', 'cnm.Uruguay', 'iso.AR', 'iso.AT', 'iso.BG', 'iso.CL',
    'iso.RS', 'iso.SI', 'iso.UY', 'kind.derby', 'ctopic.format', 'me.cost', 'me.plus', 'bk.tabCal', 'nl.context', 'nl.bonus', 'nl.realism']);       // names, units and abbreviations that are the same word in Romanian
  const ctxL = await newCtx();
  const pL = await ctxL.newPage();
  pL.on('pageerror', e => errors.push(e.message));
  await pL.goto(BASE);
  await pL.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await pL.waitForFunction(() => document.querySelector('#bucketBody details.bucket'), null, {timeout: 15000});
  const dict = await pL.evaluate(() => ({en: I18N.en, ro: I18N.ro}));
  const same = Object.keys(dict.en).filter(k => dict.en[k] === dict.ro[k] && !NAMES_SAME.has(k));
  check('en and ro have identical key sets across the whole interface (' + Object.keys(dict.en).length + ' keys), none empty',
    JSON.stringify(Object.keys(dict.en).sort()) === JSON.stringify(Object.keys(dict.ro).sort()) && Object.values(dict.en).every(Boolean) && Object.values(dict.ro).every(Boolean) && Object.keys(dict.en).length > 400, '');
  check('No ro value equals its en value, except the short whitelist of names, units and abbreviations', !same.length, same.slice(0, 10).join(', '));
  const placeholders = Object.keys(dict.en).filter(k => JSON.stringify((dict.en[k].match(/\{\w+\}/g) || []).sort()) !== JSON.stringify((dict.ro[k].match(/\{\w+\}/g) || []).sort()));
  check('Every {placeholder} in an English text is in its Romanian text and no other', !placeholders.length, placeholders.slice(0, 10).join(', '));

  // English first: the renamed sub-tab, and Settings reached from the top of the Me tab.
  await pL.click('nav button[data-pane=me]');
  const en0 = await pL.evaluate(() => ({labels: [...document.querySelectorAll('#meSubs button')].map(b => b.textContent.trim()), lang: document.documentElement.lang,
    btn: !!document.querySelector('#pane-me .mehead #settingsBtn'), nav: [...document.querySelectorAll('nav button')].map(b => b.textContent.replace(/[^A-Za-z ]/g, '').trim())}));
  check('English: the fourth sub-tab is "Tickets/Memberships", the page language is en, Settings is a small button at the top of the Me tab (no new tab)',
    JSON.stringify(en0.labels) === '["Stats","Matches","Events","Tickets/Memberships"]' && en0.lang === 'en' && en0.btn && en0.nav.length === 5 && en0.nav.includes('Ticket info'), JSON.stringify(en0));
  const subFit = async name => {
    const bad = await pL.evaluate(() => [...document.querySelectorAll('#meSubs button')].filter(b => { const r = b.getBoundingClientRect();
      return b.scrollWidth > b.clientWidth + 1 || r.right > innerWidth + 1 || r.left < -1 || r.width < 40; }).map(b => b.textContent));
    const heights = await pL.evaluate(() => [...document.querySelectorAll('#meSubs button')].map(b => Math.round(b.getBoundingClientRect().height)));
    check(name, !bad.length, JSON.stringify({bad, heights}));
  };
  await subFit('English: the four Me sub-tabs fit at 390 px (each tab as wide as its label, nothing overflows)');
  await pL.click('#settingsBtn');
  check('Settings opens as a sheet with English and Română, English chosen', await pL.evaluate(() => { const s = document.getElementById('ssheet');
    return !s.hidden && [...s.querySelectorAll('[data-lang]')].map(b => b.textContent + ':' + b.getAttribute('aria-pressed')).join() === 'English:true,Română:false'; }), '');
  // The toggle: stored under the existing key, applied at once, kept over a reload.
  await pL.click('#ssheet button[data-lang=ro]');
  const r1 = await pL.evaluate(() => ({stored: localStorage.getItem('football-planner-lang'), lang: document.documentElement.lang, LANG,
    labels: [...document.querySelectorAll('#meSubs button')].map(b => b.textContent.trim()), pressed: document.querySelector('#ssheet [data-lang=ro]').getAttribute('aria-pressed'),
    nav: [...document.querySelectorAll('nav button')].map(b => b.textContent.replace(/[^A-Za-zĂÂÎȘȚăâîșț ]/g, '').trim())}));
  check('Choosing Română: stored under football-planner-lang, <html lang="ro">, the sub-tab labels and the bottom bar change at once',
    r1.stored === 'ro' && r1.lang === 'ro' && r1.LANG === 'ro' && r1.pressed === 'true' && JSON.stringify(r1.labels) === '["Statistici","Meciuri","Evenimente","Bilete/Abonamente"]' &&
    r1.nav.join() === 'Hartă,Dorințe,Info bilete,Competiții,Eu', JSON.stringify(r1));
  await subFit('Romanian: the four Me sub-tabs fit at 390 px');
  check('Romanian: the five bottom-bar labels each fit their slot and none overlaps another', await pL.evaluate(() => {
    const bs = [...document.querySelectorAll('nav button')];
    const spans = bs.map(b => { const r = document.createRange(); r.selectNodeContents(b.querySelector('span')); return r.getBoundingClientRect(); });
    return bs.every((b, i) => { const r = b.getBoundingClientRect(); return spans[i].left >= r.left - 0.5 && spans[i].right <= r.right + 0.5 && b.querySelector('span').getClientRects().length === 1; }) &&
      spans.every((x, i) => !i || spans[i - 1].right <= x.left + 0.5);
  }), '');
  await pL.click('#ssheetClose');
  await pL.reload();
  await pL.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  check('The choice is kept over a reload (and English stays the default on a device that never chose)', await pL.evaluate(() => LANG === 'ro' && document.documentElement.lang === 'ro' &&
    document.getElementById('zoomChip').textContent.includes('cluburi')), '');

  // Romanian: no text of the interface left in English, at 390 px, on every main tab and sub-tab and their sheets.
  const roVals = new Set(Object.values(dict.ro));      // a Romanian word that is also an English UI word ("Favorite") is not English
  const enVals = Object.keys(dict.en).filter(k => dict.en[k] !== dict.ro[k] && !/\{/.test(dict.en[k]) && dict.en[k].length > 2 && !roVals.has(dict.en[k])).map(k => dict.en[k]);
  const scanEnglish = () => pL.evaluate(vals => {
    const set = new Set(vals), bad = [];
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for(let n; (n = w.nextNode());){
      const el = n.parentElement;
      if(!el || el.closest('script,style,[hidden],[data-content]') || el.closest('#map .leaflet-control-attribution')) continue;
      const txt = n.textContent.replace(/\s+/g, ' ').trim();
      if(txt && set.has(txt)) bad.push(txt);
    }
    return [...new Set(bad)];
  }, enVals);
  const fits = () => pL.evaluate(() => { const wrap = document.querySelector('.pane.on .wrap');
    return {doc: document.documentElement.scrollWidth, wrap: wrap ? [wrap.scrollWidth, wrap.clientWidth] : null}; });
  const view = async (name, fn) => {
    if(fn) await fn();
    const bad = await scanEnglish(), f = await fits();
    check(`Romanian, ${name}: no interface text left in English, no sideways scroll at 390 px`, !bad.length && f.doc <= W && (!f.wrap || f.wrap[0] <= f.wrap[1]), JSON.stringify({bad: bad.slice(0, 8), f}));
  };
  await view('Map (legend, chips)', async () => { await pL.click('nav button[data-pane=map]'); await pL.click('#legendToggle').catch(() => {}); });
  await view('club sheet', async () => { await pL.evaluate(() => openSheet(CLUBS.find(c => c.id === 'Q4512'))); await pL.waitForFunction(() => document.querySelector('#sheetTix .tix') && document.querySelector('#sheetFix .fx, #sheetFix .unavail'), null, {timeout: 15000}); await pL.click('#sheetTix details summary').catch(() => {}); });
  await view('coverage panel', async () => { await pL.click('#sheetClose'); await pL.click('#zoomChip'); await pL.waitForSelector('#covBody .covtiers'); });
  await view('route panel', async () => { await pL.click('#covClose'); await pL.click('#routeChip'); });
  await view('Near me (clubs)', async () => { await pL.click('#routeClose'); await pL.click('#nearChip'); await pL.waitForSelector('#nearList .rclub'); });
  await view('Near me (derbies)', async () => { await pL.click('#tabDerbies'); await pL.waitForSelector('#derbyBody .rclub'); });
  await view('Bucket list (List)', async () => { await pL.click('#nearClose'); await pL.click('nav button[data-pane=bucket]'); await pL.click('#bucketBody details.bucket summary h3'); await pL.waitForTimeout(600); });
  await view('Bucket list (filter panel)', async () => { await pL.click('#bfChip'); await pL.waitForSelector('#fpBody .fopt'); });
  await view('Bucket list (Calendar)', async () => { await pL.click('#fpClose'); await pL.click('#tabCal'); await pL.waitForSelector('#calBody .calgrid'); });
  await view('Ticket info', async () => { await pL.click('nav button[data-pane=tickets]'); await pL.waitForSelector('#ticketBody details.tclub'); await pL.click('#ticketBody details.tclub summary'); await pL.waitForTimeout(800); });
  await view('Competitions (list)', async () => { await pL.click('nav button[data-pane=competitions]'); await pL.waitForSelector('#compBody .comprow'); });
  await view('Competitions (sheet)', async () => { await pL.evaluate(nr => { [...document.querySelectorAll('#compBody .comprow')].find(b => b.querySelector('em').textContent !== nr).click(); }, dict.ro['comp.notResearched']); await pL.waitForSelector('#csheetBody h4'); });
  for(const [id, name] of [['#meTabStats', 'Me, Stats'], ['#meTabMatches', 'Me, Matches'], ['#meTabEvents', 'Me, Events'], ['#meTabTix', 'Me, Tickets/Memberships']])
    await view(name, async () => { await pL.click('nav button[data-pane=me]'); await pL.click(id); await pL.waitForTimeout(500); });
  await view('Me, Tickets/Memberships with the add-membership form open', async () => { await pL.click('[data-act=add][data-kind=membership]'); await pL.waitForSelector('form.meform'); });
  await view('Me, a match sheet', async () => { await pL.click('[data-act=cancel]'); await pL.click('#meTabMatches'); await pL.waitForSelector('#meMatches .acard'); await pL.click('#meMatches .acard'); await pL.waitForTimeout(500); });
  await view('Settings sheet', async () => { await pL.click('#asheetClose'); await pL.click('#settingsBtn'); });
  await pL.click('#ssheetClose');

  // Live change: an open sheet and the open tab are redrawn when the language changes, nothing is lost.
  await pL.click('nav button[data-pane=map]');
  await pL.evaluate(() => openSheet(CLUBS.find(c => c.id === 'Q4512')));
  await pL.waitForSelector('#sheetTix .tix');
  const before = await pL.evaluate(() => document.querySelector('#sheetBody h4').textContent);
  await pL.evaluate(() => setLang('en'));
  await pL.waitForFunction(() => document.querySelector('#sheetBody h4')?.textContent === 'Club', null, {timeout: 5000}).catch(() => {});
  const after = await pL.evaluate(() => ({h: document.querySelector('#sheetBody h4').textContent, open: !document.getElementById('sheet').hidden, chip: document.getElementById('zoomChip').textContent}));
  check('Changing the language while a club sheet is open redraws the sheet in place (still open) and the map chips',
    before === 'Club' && after.h === 'Club' && after.open && /clubs/.test(after.chip) && await pL.evaluate(() => document.querySelector('#sheetTix .tix h5')?.textContent.startsWith('Country rules')), JSON.stringify({before, after}));
  await pL.evaluate(() => setLang('ro'));
  await pL.waitForFunction(() => /Reguli naționale/.test(document.querySelector('#sheetTix .tix h5')?.textContent || ''), null, {timeout: 5000}).catch(() => {});
  check('... and back to Romanian: the ticket section and the Bucket list are redrawn without reopening anything',
    await pL.evaluate(() => /Reguli naționale/.test(document.querySelector('#sheetTix .tix h5')?.textContent || '') && /Filtru/.test(document.getElementById('bfChip').textContent)), '');
  // A form that is open is not thrown away by a language change.
  await pL.click('nav button[data-pane=me]'); await pL.click('#meTabTix'); await pL.click('[data-act=add][data-kind=membership]');
  await pL.fill('form.meform input[name=club]', 'Typed ' + TAG);
  await pL.evaluate(() => setLang('en'));
  check('A form being filled in keeps what was typed when the language changes', await pL.inputValue('form.meform input[name=club]') === 'Typed ' + TAG, '');
  await pL.evaluate(() => setLang('en'));
  await ctxL.close();
  }

  {
  // ---- 2026-10-11: Romanian translations of data-file texts (data/ro/<source>.json), the original-English switch, the note on
  //      sheets, and the codes of the ticket files said in words. English stays the original and is checked unchanged.
  const roFile = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/ro/football-rules.json'), 'utf8'));
  const pilot = Object.keys(roFile).filter(k => /^bucketList:.+#why$/.test(k)).map(k => k.slice('bucketList:'.length, -'#why'.length));
  const stale0 = pilot[0], withAssistant = pilot.find(id => rules.bucketList.find(b => b.id === id).whyAssistant), plain = pilot[1];
  const untranslated = rules.bucketList.find(b => b.why && !pilot.includes(b.id)).id;
  const whyOf = id => rules.bucketList.find(b => b.id === id).why;
  const roOf = id => roFile['bucketList:' + id + '#why'].ro;
  const TN_RO = 'Traducere automată, originalul este în engleză.';
  const reqN = () => requests.filter(r => /\/data\/ro\//.test(r.url)).length;
  const openCard = async (page, id) => {
    await page.evaluate(i => { const d = document.querySelector(`#bucketBody details.bucket[data-id="${i}"]`); d.scrollIntoView(); d.open = true; }, id);
    await page.waitForFunction(i => document.querySelector(`#bucketBody details.bucket[data-id="${i}"] .tix .bwhy:not(.bwhyc)`), id, {timeout: 15000});
  };
  const detailWhy = (page, id) => page.evaluate(i => { const e = document.querySelector(`#bucketBody details.bucket[data-id="${i}"] .tix p.bwhy:not([data-why])`);
    return e ? {text: e.textContent, lang: e.getAttribute('lang'), tx: e.getAttribute('data-tx')} : null; }, id);
  const ready = async page => { await page.goto(BASE); await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
    await page.waitForFunction(() => document.querySelector('#bucketBody details.bucket'), null, {timeout: 15000}); };

  // The fingerprint: the page and the checker agree on the fixture, including accented text, an NBSP edge and an astral character.
  const fixture = JSON.parse(fs.readFileSync(path.join(ROOT, 'tools/translation-fingerprints.json'), 'utf8'));
  check('The fingerprint fixture has accented, padded and astral strings', fixture.length >= 10 && fixture.some(c => /[ăîșț]/.test(c.text)) && fixture.some(c => /^\s|\s$/.test(c.text)) && fixture.some(c => /\u{1F3DF}/u.test(c.text)), String(fixture.length));
  let regJson = null;
  try{ regJson = JSON.parse(execSync('python3 tools/check_translations.py --root . --registry', {cwd: ROOT, encoding: 'utf8'})); }catch(e){ regJson = null; }
  check('tools/check_translations.py --registry lists the translated fields of every source', !!regJson && Object.keys(regJson).length === 9 && regJson['football-rules'].length > 300, regJson ? Object.keys(regJson).join() : 'did not run');

  // ---- English: unchanged, and not a single data/ro request.
  const ctxE = await newCtx();
  const pE = await ctxE.newPage();
  pE.on('pageerror', e => errors.push(e.message));
  const reqBefore = reqN();
  await ready(pE);
  const fxBad = await pE.evaluate(fx => fx.filter(c => fnv1a(c.text) !== c.fp).map(c => c.text), fixture);
  check('The page\'s fnv1a() reproduces every fingerprint of the fixture (the same function as the checker\'s)', !fxBad.length, JSON.stringify(fxBad));
  const srcs = await pE.evaluate(() => RO_SOURCES.slice().sort());
  check('The page lists exactly the sources that have a data/ro file, and the checker registers the same', JSON.stringify(srcs) === JSON.stringify(fs.readdirSync(path.join(ROOT, 'data/ro')).filter(f => f.endsWith('.json')).map(f => f.slice(0, -5)).sort()) &&
    regJson && JSON.stringify(Object.keys(regJson).sort()) === JSON.stringify(srcs), JSON.stringify(srcs));
  // The page's list of translated football-rules.json paths equals the checker's, leaf by leaf.
  const reg = new Set((regJson ? regJson['football-rules'] : []).map(r => r.row + '#' + r.field));
  const leaves = [];
  const walk = (o, p, kind, row) => { if(o && typeof o === 'object'){ for(const [k, v] of Object.entries(o)) walk(v, Array.isArray(o) ? `${p}[${k}]` : (p ? p + '.' : '') + k, kind, row); }
    else if(typeof o === 'string' && o.trim()) leaves.push({kind, row, p, str: true}); };
  for(const b of rules.bucketList) walk(b, '', 'bucketList', 'bucketList:' + b.id);
  for(const c of rules.clubs) walk(c, '', 'clubs', 'clubs:' + c.id);
  const pageSays = await pE.evaluate(ls => ls.map(l => txPathOk(l.kind, l.p)), leaves);
  const disagree = leaves.filter((l, i) => pageSays[i] !== reg.has(l.row + '#' + l.p));
  check(`The page and the checker translate the same ${reg.size} string leaves of football-rules.json (and no other of ${leaves.length})`, !disagree.length && reg.size > 300, JSON.stringify(disagree.slice(0, 4)));
  await openCard(pE, pilot[0]);
  const eW = await detailWhy(pE, pilot[0]);
  check('English: a pilot entry shows the English why exactly, with no lang attribute, no marker and no note anywhere', eW && eW.text === whyOf(pilot[0]) && eW.lang === null && eW.tx === null &&
    !(await pE.$('#bucketBody [data-tx], #bucketBody [lang], .txnote')), JSON.stringify(eW));
  check('English: no data/ro file is requested', reqN() === reqBefore, String(reqN() - reqBefore));
  // English codes are the codes: the view is the one it always was.
  await pE.click('nav button[data-pane=tickets]'); await pE.waitForSelector('#ticketBody details.tclub');
  const expandAll = async page => {
    await page.evaluate(() => document.querySelectorAll('#ticketBody details.tclub, #ticketBody details.tcountry').forEach(d => { d.open = true; }));
    await page.waitForFunction(() => { const open = [...document.querySelectorAll('#ticketBody details.card[open] > .tix')];
      return open.length > 5 && open.every(x => x.querySelector('h5.tix-country, .crule, .err, .tix-nonat')); }, null, {timeout: 30000});
    await page.evaluate(() => document.querySelectorAll('#ticketBody .tix details').forEach(d => { d.open = true; })); await page.waitForTimeout(400); };
  await expandAll(pE);
  const eCodes = await pE.evaluate(() => [...document.querySelectorAll('#ticketBody .tix b')].map(b => b.textContent));
  check('English: topic codes are shown as written (sales-channel, risk-classification), nothing re-worded', eCodes.includes('sales-channel') && eCodes.includes('risk-classification'), eCodes.slice(0, 6).join(','));
  const eOver = await pE.evaluate(() => document.documentElement.scrollWidth);
  check('English: Ticket info with every card open does not scroll sideways at 390 px', eOver <= W, String(eOver));
  await pE.click('nav button[data-pane=me]'); await pE.click('#settingsBtn');
  check('Settings has "Show original English for data texts", off by default, nothing stored', await pE.evaluate(() => { const b = document.getElementById('txOrigBtn');
    return b && b.getAttribute('aria-pressed') === 'false' && /Show original English for data texts/.test(b.textContent) && localStorage.getItem('football-planner-tx-original') === null; }), '');
  const swFit = await pE.evaluate(() => { const r = document.getElementById('txOrigBtn').getBoundingClientRect(), s = document.getElementById('ssheetBody');
    return {right: r.right, left: r.left, h: r.height, sw: s.scrollWidth, cw: s.clientWidth, doc: document.documentElement.scrollWidth}; });
  check('Settings: the new switch is at least 44 px tall and inside the sheet at 390 px, no sideways scroll', swFit.h >= 44 && swFit.right <= W && swFit.left >= 0 && swFit.sw <= swFit.cw && swFit.doc <= W, JSON.stringify(swFit));
  await ctxE.close();

  // ---- Romanian: the pilot entries, the order they were picked in, stale entries, the note, the switch.
  const ctxR = await newCtx();
  await ctxR.addInitScript(() => { try{ if(!localStorage.getItem('football-planner-lang')) localStorage.setItem('football-planner-lang', 'ro'); }catch(e){} });
  const pR = await ctxR.newPage();
  pR.on('pageerror', e => errors.push(e.message));
  const reqB2 = reqN();
  await ready(pR);
  check('Romanian: all nine data/ro files are requested (and only now)', reqN() - reqB2 === 9, String(reqN() - reqB2));
  const order = await pR.evaluate(() => [...document.querySelectorAll('#bucketBody details.bucket')].map(d => d.dataset.id));
  const firstWithWhy = order.filter(id => rules.bucketList.find(b => b.id === id).why).slice(0, 25);
  check('The pilot is the first 25 entries with a why in the List\'s own order (Group order), and the file holds exactly those', pilot.length === 25 && JSON.stringify(firstWithWhy) === JSON.stringify(pilot), JSON.stringify(firstWithWhy.filter((x, i) => x !== pilot[i])));
  await openCard(pR, pilot[0]); await openCard(pR, withAssistant); await openCard(pR, untranslated);
  const rW = await detailWhy(pR, pilot[0]);
  check('Romanian: a translated entry renders in Romanian, marked lang="ro" and data-tx', rW && rW.text === roOf(pilot[0]) && rW.lang === 'ro' && rW.tx === 'ro', JSON.stringify(rW));
  const rA = await pR.evaluate(id => { const e = document.querySelector(`#bucketBody details.bucket[data-id="${id}"] .tix [data-why=added] [data-content]`);
    return e ? {lang: e.getAttribute('lang'), tx: e.getAttribute('data-tx')} : null; }, withAssistant);
  check('Romanian: the assistant\'s note of the same entry has no translation, so it stays English and says so (lang="en")', rA && rA.lang === 'en' && rA.tx === null, JSON.stringify(rA));
  const rU = await detailWhy(pR, untranslated);
  check('Romanian: an entry with no translation shows the English, lang="en"', rU && rU.text === whyOf(untranslated) && rU.lang === 'en' && rU.tx === null, JSON.stringify(rU));
  const card = await pR.evaluate(id => { const e = document.querySelector(`#bucketBody details.bucket[data-id="${id}"] summary p.bwhyc`); return e ? {text: e.textContent, lang: e.getAttribute('lang')} : null; }, plain);
  check('Romanian: the collapsed card shows the Romanian why too', card && card.text === roOf(plain) && card.lang === 'ro', JSON.stringify(card));
  const note = await pR.evaluate(() => { const n = document.querySelector('#bucketBody .txnote'); return n ? n.textContent : null; });
  check('Romanian: the tab holding translated text carries "Automatic translation, English is the original." (in Romanian)', note === TN_RO, String(note));
  await pR.evaluate(id => openBSheet('entry', id), pilot[2]);
  await pR.waitForFunction(() => document.querySelector('#bsheetBody .bwhy'), null, {timeout: 10000});
  check('Romanian: a sheet holding translated text carries the note, and a sheet without any does not', await pR.evaluate(() => document.querySelector('#bsheetBody .txnote')?.textContent) === TN_RO &&
    await pR.evaluate(id => { openBSheet('entry', id); return new Promise(r => setTimeout(() => r(!document.querySelector('#bsheetBody [data-tx]') && !document.querySelector('#bsheetBody .txnote')), 2500)); }, untranslated), '');
  const ov = await pR.evaluate(() => ({doc: document.documentElement.scrollWidth, tab: document.getElementById('bucketBody').scrollWidth, tabC: document.getElementById('bucketBody').clientWidth,
    sheet: document.getElementById('bsheetBody').scrollWidth, sheetC: document.getElementById('bsheetBody').clientWidth}));
  check('Romanian: the List and the sheet with translated text do not scroll sideways at 390 px', ov.doc <= W && ov.tab <= ov.tabC && ov.sheet <= ov.sheetC, JSON.stringify(ov));
  await pR.evaluate(() => closeBSheet());

  // The switch: English everywhere for data texts, the interface stays Romanian, kept over a reload; off again restores Romanian.
  await pR.click('nav button[data-pane=me]'); await pR.click('#settingsBtn');
  const swRo = await pR.evaluate(() => ({text: document.getElementById('txOrigBtn').textContent, h4: document.querySelector('#ssheetBody [data-i18n="set.tx"]').textContent}));
  check('Romanian: the switch is labelled in Romanian', swRo.text === 'Arată originalul în engleză pentru textele din date', JSON.stringify(swRo));
  await pR.click('#txOrigBtn');
  await pR.click('#ssheetClose'); await pR.click('nav button[data-pane=bucket]');
  await pR.waitForFunction(i => document.querySelector(`#bucketBody details.bucket[data-id="${i}"] .tix p.bwhy:not([data-why])`)?.getAttribute('lang') === 'en', pilot[0], {timeout: 15000}).catch(() => {});
  const swOn = await pR.evaluate(i => { const e = document.querySelector(`#bucketBody details.bucket[data-id="${i}"] .tix p.bwhy:not([data-why])`);
    return {stored: localStorage.getItem('football-planner-tx-original'), pressed: document.getElementById('txOrigBtn').getAttribute('aria-pressed'), LANG, text: e && e.textContent,
      lang: e && e.getAttribute('lang'), tx: !!document.querySelector('#bucketBody [data-tx]'), note: !!document.querySelector('#bucketBody .txnote'), nav: document.querySelector('nav button[data-pane=map] span').textContent}; }, pilot[0]);
  check('Switch on: the data text is the English original (lang="en"), no translated marker or note, the interface stays Romanian, the choice is stored',
    swOn.stored === '1' && swOn.pressed === 'true' && swOn.LANG === 'ro' && swOn.text === whyOf(pilot[0]) && swOn.lang === 'en' && !swOn.tx && !swOn.note && swOn.nav === 'Hartă', JSON.stringify(swOn));
  await pR.reload(); await ready(pR);
  check('Switch on is kept over a reload', await pR.evaluate(() => TX_ORIG === true), '');
  await pR.click('nav button[data-pane=me]'); await pR.click('#settingsBtn'); await pR.click('#txOrigBtn'); await pR.click('#ssheetClose'); await pR.click('nav button[data-pane=bucket]');
  await openCard(pR, pilot[0]); await pR.waitForFunction(i => document.querySelector(`#bucketBody details.bucket[data-id="${i}"] .tix p.bwhy:not([data-why])`)?.getAttribute('lang') === 'ro', pilot[0], {timeout: 15000}).catch(() => {});
  check('Switch off again: the Romanian is back', (await detailWhy(pR, pilot[0])).text === roOf(pilot[0]) && await pR.evaluate(() => localStorage.getItem('football-planner-tx-original')) === '0', '');

  // Codes of the ticket files in words: no raw code on Ticket info (every club open, every list open) or in the derby and Frankenderby entries.
  const csvCol = (file, col, sep) => { const rows = fs.readFileSync(path.join(ROOT, 'data', file), 'utf8').split('\n'); const head = rows[0].split(','), i = head.indexOf(col);
    const out = new Set(); for(const r of rows.slice(1)){ const cells = r.match(/("([^"]|"")*"|[^,]*)(,|$)/g) || []; const v = (cells[i] || '').replace(/,$/, '').replace(/^"|"$/g, ''); (sep ? v.split(';') : [v]).forEach(x => x.trim() && out.add(x.trim())); } return out; };
  const RAW = new Set();
  for(const [f, cols] of [['club-ticket-rules.csv', ['topic', 'scope']], ['country-ticket-rules.csv', ['topic', 'authorityKind']], ['club-ticket-prices.csv', ['competition', 'stage', 'opponentTier', 'priceClass', 'kind', 'priceBasis']],
    ['club-ticket-demand.csv', ['outcome']], ['club-tickets.csv', ['access', 'salesModel', 'requestTypes', 'closesEarly', 'demand', 'resale', 'updateTracking', 'minorEligibility']], ['club-ticket-windows.csv', ['basis']]])
    for(const c of cols) for(const v of csvCol(f, c, true)) RAW.add(v);
  for(const v of ['yes', 'general', 'sold-out']) RAW.delete(v);       // 'sold-out' is the Romanian word too (oc.sold-out)
  const rawIn = (page, root) => page.evaluate(([root, raw]) => { const set = new Set(raw), bad = [], w = document.createTreeWalker(document.querySelector(root), NodeFilter.SHOW_TEXT);
    for(let n; (n = w.nextNode());){ const el = n.parentElement; if(!el || el.closest('[data-content],[lang=en],.src a,script,style')) continue;     // data texts, left in English on purpose, and source titles
      for(const piece of n.textContent.split(/\s·\s|,\s|:\s|\s\(|\)/)) if(set.has(piece.trim())) bad.push(piece.trim()); }
    return [...new Set(bad)]; }, [root, [...RAW]]);
  await pR.click('nav button[data-pane=tickets]'); await pR.waitForSelector('#ticketBody details.tclub');
  await expandAll(pR);
  const rawT = await rawIn(pR, '#ticketBody');
  const roLabels = await pR.evaluate(() => [...document.querySelectorAll('#ticketBody .tix b')].map(b => b.textContent));
  check(`Romanian Ticket info (every club and list open): none of the ${RAW.size} codes of the ticket files appears raw, and the Romanian labels do`, !rawT.length && roLabels.includes('canal de vânzare') && roLabels.includes('clasificarea riscului'), JSON.stringify(rawT.slice(0, 8)));
  const tover = await pR.evaluate(() => document.documentElement.scrollWidth);
  check('Romanian Ticket info with every card open does not scroll sideways at 390 px', tover <= W, String(tover));
  await pR.click('nav button[data-pane=bucket]');
  for(const id of ['frankenderby', 'derby-madonnina']){
    await openCard(pR, id).catch(() => {}); await pR.waitForTimeout(1500);
    await pR.evaluate(i => document.querySelectorAll(`#bucketBody details.bucket[data-id="${i}"] .tix details`).forEach(d => { d.open = true; }), id);
  }
  const rawB = await rawIn(pR, '#bucketBody');
  check('Romanian Bucket list (Frankenderby, Milan derby, every list open): no raw code of the ticket files appears', !rawB.length, JSON.stringify(rawB.slice(0, 8)));
  await ctxR.close();

  // ---- A stale entry: the English changed after it was translated, so the English is shown (the file is edited in flight, not on disk).
  const ctxS = await newCtx();
  await ctxS.addInitScript(() => { try{ localStorage.setItem('football-planner-lang', 'ro'); }catch(e){} });
  await ctxS.route('**/data/ro/football-rules.json', async r => {
    const j = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/ro/football-rules.json'), 'utf8'));
    j['bucketList:' + stale0 + '#why'].en = '00000000';
    r.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify(j)});
  });
  const pS = await ctxS.newPage();
  pS.on('pageerror', e => errors.push(e.message));
  await ready(pS);
  await openCard(pS, stale0); await openCard(pS, pilot[1]);
  const sA = await detailWhy(pS, stale0), sB = await detailWhy(pS, pilot[1]);
  check('A stale fingerprint renders the English (lang="en") while the next, matching entry stays Romanian',
    sA && sA.text === whyOf(stale0) && sA.lang === 'en' && sA.tx === null && sB && sB.text === roOf(pilot[1]) && sB.lang === 'ro', JSON.stringify({sA, sB}));
  await ctxS.close();

  // ---- A data/ro file that cannot be loaded: English, no error.
  const ctxF = await newCtx();
  await ctxF.addInitScript(() => { try{ localStorage.setItem('football-planner-lang', 'ro'); }catch(e){} });
  await ctxF.route('**/data/ro/derbies.json', r => r.fulfill({status: 404, body: 'nf'}));
  const pF = await ctxF.newPage();
  pF.on('pageerror', e => errors.push(e.message));
  await ready(pF);
  await openCard(pF, pilot[0]);
  const fW = await detailWhy(pF, pilot[0]);
  check('One missing data/ro file leaves its texts in English, the page works, no script error (the others still translate)', fW && fW.text === whyOf(pilot[0]) && fW.lang === 'en', JSON.stringify(fW));
  await ctxF.close();

  // ---- The dictionary doc is regenerated.
  const docRows = fs.readFileSync(path.join(ROOT, 'docs/ro-review.md'), 'utf8').split('\n## Texts from data files')[0].split('\n').filter(l => /^\| `/.test(l)).length;
  const keyN = await (async () => { const c = await newCtx(), p = await c.newPage(); await ready(p); const n = await p.evaluate(() => Object.keys(I18N.en).length); await c.close(); return n; })();
  check('docs/ro-review.md has one row for every key of the dictionary', docRows === keyN, `${docRows} rows, ${keyN} keys`);
  }


  // ---- Theme (Dark / Light), 2026-10-09: the toggle in Settings, applied before first paint, kept under football-planner-theme;
  //      every colour a CSS variable; readable text in both themes; light tiles with a fall-back to dark; nothing overflows at 390 px.
  {
  const THEME_KEY = 'football-planner-theme';
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  const hi = html.indexOf('<script>(function(){var t="dark"');
  check('The pre-paint script is a tiny inline script in <head>, before the stylesheet and the body, reading only football-planner-theme',
    hi > html.indexOf('<head>') && hi < html.indexOf('<style>') && hi < html.indexOf('<body') && html.slice(hi, html.indexOf('</script>', hi)).includes(THEME_KEY)
    && html.indexOf('</script>', hi) - hi < 700 && !/mf_/.test(html.slice(hi, html.indexOf('</script>', hi))), '');
  const scanContrast = function scanContrast(rootSel){
  const parse = s => { const m = String(s).match(/rgba?\(([^)]+)\)/); if(!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = c => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b); };
  const over = (top, bot) => { const a = top.a + bot.a * (1 - top.a);
    return a === 0 ? {r: 0, g: 0, b: 0, a: 0} : {r: (top.r * top.a + bot.r * bot.a * (1 - top.a)) / a, g: (top.g * top.a + bot.g * bot.a * (1 - top.a)) / a, b: (top.b * top.a + bot.b * bot.a * (1 - top.a)) / a, a}; };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const page = parse(getComputedStyle(document.documentElement).backgroundColor);
  const base = page && page.a ? page : {r: 255, g: 255, b: 255, a: 1};
  const backdrop = el => {            // the colour behind el's content, or null when it is an image / gradient / faded
    const layers = []; let open = true;
    for(let e = el; e; e = e.parentElement){
      const cs = getComputedStyle(e);
      if(+cs.opacity < 1) return null;
      if(open){
        if(cs.backgroundImage !== 'none') return null;
        const c = parse(cs.backgroundColor);
        if(c && c.a > 0){ layers.push(c); if(c.a === 1) open = false; }
      }
    }
    let acc = base; for(let i = layers.length - 1; i >= 0; i--) acc = over(layers[i], acc);
    return acc;
  };
  const root = document.querySelector(rootSel);
  const out = {checked: 0, skipped: 0, fails: [], pairs: []};
  if(!root) return {error: 'no ' + rootSel};
  const light = document.documentElement.getAttribute('data-theme') === 'light';
  const seen = new Set();
  const test = (el, fgStr, label) => {
    const bg = backdrop(el); if(!bg){ out.skipped++; return; }
    let fg = parse(fgStr); if(!fg){ out.skipped++; return; }
    if(fg.a < 1) fg = over(fg, bg);
    out.checked++;
    const r = ratio(fg, bg), cls = typeof el.className === 'string' ? el.className.trim().split(/\s+/)[0] : '';
    const id = `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : cls ? '.' + cls : ''} "${label.slice(0, 28)}"`;
    if(r < 4.5) out.fails.push(`${id} ${r.toFixed(2)} fg ${fgStr} on ${Math.round(bg.r)},${Math.round(bg.g)},${Math.round(bg.b)}`);
    if(light){
      const lf = lum(fg), lb = lum(bg);
      if((lf <= .05 && lb <= .1) || (lf >= .8 && lb >= .8)) out.pairs.push(`${id} text ${Math.round(fg.r)},${Math.round(fg.g)},${Math.round(fg.b)} on ${Math.round(bg.r)},${Math.round(bg.g)},${Math.round(bg.b)}`);
    }
  };
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for(let n; (n = w.nextNode());){
    const el = n.parentElement; const txt = n.nodeValue.trim();
    if(!txt || seen.has(el) || el.closest('svg,script,style,[hidden],option')) continue;
    seen.add(el);
    if(!el.getClientRects().length || getComputedStyle(el).visibility === 'hidden' || el.closest('[disabled]')) continue;
    test(el, getComputedStyle(el).color, txt);
  }
  for(const el of root.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=file]):not([type=range]),textarea,select')){
    if(!el.getClientRects().length || el.disabled || el.closest('[hidden]')) continue;
    if(el.tagName === 'SELECT' || el.value) test(el, getComputedStyle(el).color, el.value || 'select');
    else if(el.placeholder) test(el, getComputedStyle(el, '::placeholder').color, el.placeholder);
  }
  return out;
};
  const track = ctx => ctx.addInitScript(() => {
    window.__keys = []; const g = Storage.prototype.getItem, s = Storage.prototype.setItem;
    Storage.prototype.getItem = function(k){ window.__keys.push('r:' + k); return g.call(this, k); };
    Storage.prototype.setItem = function(k, v){ window.__keys.push('w:' + k); return s.call(this, k, v); };
  });
  const openPage = async (ctx, tiles) => {
    const p = await ctx.newPage(); p.on('pageerror', e => errors.push(e.message));
    if(tiles) p.on('request', r => { if(r.url().includes('tiles.stadiamaps.com')) tiles.push(r.url()); });
    await p.goto(BASE);
    await p.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
    await p.waitForFunction(() => document.querySelector('#bucketBody details.bucket'), null, {timeout: 15000});
    return p;
  };
  const themeOf = p => p.evaluate(() => ({attr: document.documentElement.getAttribute('data-theme'), stored: localStorage.getItem('football-planner-theme'),
    meta: document.querySelector('meta[name="theme-color"]').content, bg: getComputedStyle(document.body).backgroundColor,
    pressed: [...document.querySelectorAll('#ssheet button[data-theme]')].map(b => b.textContent + ':' + b.getAttribute('aria-pressed')).join()}));

  // Default, toggle, persistence, languages.
  const ctxT = await newCtx(); await track(ctxT);
  const tilesT = [];
  const pT = await openPage(ctxT, tilesT);
  const d0 = await themeOf(pT);
  check('First visit: dark, theme-color #0d1117, the body as it always was, and loading writes nothing under the theme key',
    d0.attr === 'dark' && d0.meta === '#0d1117' && d0.bg === 'rgb(13, 17, 23)' && d0.stored === null, JSON.stringify(d0));
  check('Dark mode keeps the existing look: the original variables are unchanged',
    JSON.stringify(await pT.evaluate(() => ['--bg', '--panel', '--line', '--ink', '--dim', '--t1', '--t2', '--t3', '--t4', '--t5', '--t6', '--t7', '--t8', '--ok', '--warn', '--bad', '--surf', '--surf2', '--field']
      .map(n => getComputedStyle(document.documentElement).getPropertyValue(n).trim()))) ===
    JSON.stringify(['#0d1117', '#161b22', '#26303b', '#e6edf3', '#8b949e', '#e8543f', '#e8a33f', '#3fa0e8', '#2aab8e', '#4caf50', '#9b6bd6', '#e8629f', '#825e35', '#3fb950', '#d29922', '#f85149', '#1b2230', '#11161d', '#0d1117']), '');
  check('Dark tiles are asked for first, and no request carries a key', tilesT.length > 0 && tilesT.every(u => u.includes('/alidade_smooth_dark/') && !/api_key|key=/.test(u)), tilesT[0]);
  await pT.click('nav button[data-pane=me]'); await pT.click('#settingsBtn');
  check('Settings has a Theme group, Dark pressed, Light not', (await themeOf(pT)).pressed === 'Dark:true,Light:false', (await themeOf(pT)).pressed);
  const n0 = tilesT.length;
  await pT.click('#ssheet button[data-theme=light]');
  const d1 = await themeOf(pT);
  check('Choosing Light: stored under football-planner-theme, data-theme and theme-color follow, the body is light, the button is pressed',
    d1.attr === 'light' && d1.stored === 'light' && d1.meta === '#f6f8fa' && d1.bg === 'rgb(246, 248, 250)' && d1.pressed === 'Dark:false,Light:true', JSON.stringify(d1));
  check('The language buttons are not disturbed by the theme buttons', await pT.evaluate(() => [...document.querySelectorAll('#ssheet button[data-lang]')].map(b => b.getAttribute('aria-pressed')).join()) === 'true,false', '');
  await pT.click('#ssheetClose'); await pT.click('nav button[data-pane=map]');
  await pT.waitForTimeout(800);
  const newTiles = tilesT.slice(n0);
  check('In light mode the light tiles (alidade_smooth) are asked for, with no key', newTiles.some(u => /\/alidade_smooth\/\d/.test(u)) && newTiles.every(u => !/api_key|key=/.test(u)), newTiles.slice(0, 2).join(' '));
  check('Map markers follow the theme: the tier and route colours in the page are the light variables',
    await pT.evaluate(() => { const v = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
      return [1, 2, 3, 4, 5, 6, 7, 8].every(k => TIER_COLOUR[k] === v('--t' + k)) && ROUTE_COLOUR === v('--route') && TIER_COLOUR[1] === '#c9301d'; }), '');
  await pT.reload(); await pT.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  check('Light is kept over a reload', (await themeOf(pT)).attr === 'light' && (await themeOf(pT)).meta === '#f6f8fa', JSON.stringify(await themeOf(pT)));
  await pT.click('nav button[data-pane=me]'); await pT.click('#settingsBtn');
  await pT.evaluate(() => setLang('ro'));
  check('Romanian: the Theme group, Dark and Light and the note are translated',
    await pT.evaluate(() => { const s = document.getElementById('ssheet'); return [...s.querySelectorAll('h4')].map(h => h.textContent).includes('Temă') &&
      [...s.querySelectorAll('button[data-theme]')].map(b => b.textContent).join() === 'Întunecată,Luminoasă' && /Culorile aplicației/.test(s.textContent); }), '');
  await pT.evaluate(() => setLang('en'));
  await pT.click('#ssheet button[data-theme=dark]');
  const d2 = await themeOf(pT);
  check('Choosing Dark again: stored dark, theme-color back to #0d1117', d2.attr === 'dark' && d2.stored === 'dark' && d2.meta === '#0d1117' && d2.pressed === 'Dark:true,Light:false', JSON.stringify(d2));
  const keys = await pT.evaluate(() => window.__keys);
  check('The theme reads and writes only football-planner-theme (and the language key); no mf_ key', keys.some(k => k === 'w:' + THEME_KEY) && !keys.some(k => k.includes('mf_')), [...new Set(keys)].join(','));
  await ctxT.close();

  // A stored value that is not light or dark is ignored; blocked storage still works for the visit.
  const ctxB = await newCtx(); await ctxB.addInitScript(() => { try{ localStorage.setItem('football-planner-theme', 'blue'); }catch(e){} });
  const pB = await openPage(ctxB);
  check('A stored value other than light or dark is ignored: dark', (await themeOf(pB)).attr === 'dark', '');
  await ctxB.close();
  const ctxK = await newCtx({blockStorage: true});
  const pK = await openPage(ctxK);
  await pK.click('nav button[data-pane=me]'); await pK.click('#settingsBtn'); await pK.click('#ssheet button[data-theme=light]');
  check('With storage blocked the page opens dark and the toggle still works for the visit', await pK.evaluate(() => document.documentElement.getAttribute('data-theme')) === 'light', '');
  await ctxK.close();

  // Applied before first paint: the attribute is set before the browser's first paint, and the body is already light then.
  const ctxP = await newCtx();
  await ctxP.addInitScript(() => {
    try{ localStorage.setItem('football-planner-theme', 'light'); }catch(e){}
    window.__t = {order: [], bg: null};
    // The order the parser reaches things: the theme attribute must come before the first stylesheet and the body exist, so nothing can paint in the wrong theme.
    new MutationObserver(recs => { for(const r of recs){
      if(r.type === 'attributes') window.__t.order.push('theme=' + document.documentElement.getAttribute('data-theme'));
      for(const n of r.addedNodes) if(['STYLE', 'LINK', 'BODY'].includes(n.nodeName)) window.__t.order.push(n.nodeName); } })
      .observe(document, {attributes: true, childList: true, subtree: true, attributeFilter: ['data-theme']});
    document.addEventListener('DOMContentLoaded', () => { window.__t.bg = getComputedStyle(document.body).backgroundColor + '|' + document.documentElement.getAttribute('data-theme'); });
  });
  const pP = await openPage(ctxP);
  const tm = await pP.evaluate(() => Object.assign({}, window.__t, {scheme: document.documentElement.style.colorScheme}));
  check('Applied before first paint: data-theme is set before the first stylesheet and the body exist (parser order), the canvas colour scheme with it, and the body is light at DOMContentLoaded',
    tm.order[0] === 'theme=light' && tm.order.length > 1 && tm.order.indexOf('BODY') > 0 && tm.scheme === 'light' && tm.bg === 'rgb(246, 248, 250)|light', JSON.stringify(tm));
  await ctxP.close();

  // Light tiles failing: back to the dark tiles for the session, with a short note; the stored choice is untouched.
  const ctxF = await newCtx(); await ctxF.addInitScript(() => { try{ localStorage.setItem('football-planner-theme', 'light'); }catch(e){} });
  await ctxF.route('https://tiles.stadiamaps.com/tiles/alidade_smooth/**', r => r.fulfill({status: 503, headers: {'Access-Control-Allow-Origin': '*'}, body: ''}));
  const tilesF = [];
  const pF = await openPage(ctxF, tilesF);
  await pF.waitForFunction(() => !document.getElementById('mapNote').hidden, null, {timeout: 15000}).catch(() => {});
  await pF.waitForTimeout(800);
  const f1 = await pF.evaluate(() => ({note: document.getElementById('mapNote').hidden ? null : document.getElementById('mapNote').textContent, card: !document.getElementById('mapOffline').hidden,
    theme: document.documentElement.getAttribute('data-theme'), stored: localStorage.getItem('football-planner-theme')}));
  check('Light tiles failing repeatedly: the dark tiles are used, a short note says the light map is unavailable, and no "needs a connection" card',
    /light map is unavailable/.test(f1.note || '') && !f1.card && tilesF.some(u => /\/alidade_smooth_dark\//.test(u)) && f1.theme === 'light' && f1.stored === 'light', JSON.stringify(f1) + ' ' + tilesF.length);
  const nF = tilesF.length; await pF.evaluate(() => MAP.panBy([300, 0], {animate: false})); await pF.waitForTimeout(600);
  check('After the fall-back no more light tiles are asked for in this session, and no key is used', tilesF.slice(nF).every(u => u.includes('/alidade_smooth_dark/') && !/api_key|key=/.test(u)), tilesF.slice(nF).slice(0, 2).join(' '));
  await pF.click('nav button[data-pane=me]'); await pF.click('#settingsBtn'); await pF.evaluate(() => setLang('ro'));
  check('The note is translated', /Harta luminoasă nu este disponibilă/.test(await pF.textContent('#mapNote')), '');
  await ctxF.close();

  // Colours: nothing hard-coded outside the two variable sets, the pre-paint script and the theme-color meta.
  const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>'));
  const rootEnd = css.indexOf(':root[data-theme="light"]'); const lightEnd = css.indexOf('}', rootEnd);
  const outside = (css.slice(0, css.indexOf(':root{')) + css.slice(lightEnd) + html.slice(html.indexOf('</style>'))).split('\n')
    .filter(l => /#[0-9a-fA-F]{3,8}\b|rgba?\(\s*\d|hsla?\(/.test(l) && !/theme-color|data-theme|getPropertyValue|setAttribute\("content"/.test(l));
  check('Every colour in index.html is a CSS variable: no hex, rgb() or hsl() literal outside the two variable sets', !outside.length, outside.slice(0, 4).map(l => l.trim().slice(0, 80)).join(' | '));

  // Contrast, both themes: every main tab, the Me sub-tabs and the sheets; 4.5:1 for all text; light mode no near-black-on-dark / white-on-white pair.
  for(const th of ['dark', 'light']){
    const ctxC = await newCtx(); await ctxC.addInitScript(t => { try{ localStorage.setItem('football-planner-theme', t); }catch(e){} }, th);
    const pC = await openPage(ctxC);
    const sections = [];
    const run = async (name, sel) => { const o = await pC.evaluate(scanContrast, sel); sections.push(name);
      check(`${th}: ${name} - text is at least 4.5:1 against its background (${o.checked} checked, ${o.skipped} skipped: gradient or faded)`, !o.error && o.checked > 0 && !o.fails.length, o.error || [...new Set(o.fails)].slice(0, 6).join(' | '));
      if(th === 'light') check(`light: ${name} - no near-black text on a dark background and no white on white`, !o.error && !o.pairs.length, (o.pairs || []).slice(0, 4).join(' | ')); };
    const hideAll = () => pC.evaluate(() => { for(const id of ['routePanel', 'nearPanel', 'coveragePanel', 'filterPanel', 'ssheet', 'asheet', 'sheet']) document.getElementById(id).hidden = true; });
    await pC.click('#legendToggle'); await run('map and legend', '#pane-map');
    await pC.click('#zoomChip'); await pC.waitForTimeout(300); await run('coverage panel', '#coveragePanel'); await hideAll();
    await pC.click('#nearChip'); await pC.waitForTimeout(500); await run('Near me panel', '#nearPanel'); await hideAll();
    await pC.click('#routeChip'); await pC.waitForTimeout(300); await run('route panel', '#routePanel'); await hideAll();
    await pC.evaluate(() => openSheet(CLUBS.find(c => c.id === 'Q4512'))); await pC.waitForTimeout(400); await run('club sheet (VfB Stuttgart)', '#sheet'); await hideAll();
    await pC.click('nav button[data-pane=bucket]'); await run('Bucket list', '#pane-bucket');
    await pC.click('#bfChip'); await pC.waitForTimeout(300); await run('filter panel', '#filterPanel'); await hideAll();
    await pC.click('#tabCal'); await run('Bucket calendar', '#pane-bucket');
    await pC.click('nav button[data-pane=tickets]'); await pC.waitForTimeout(300);
    await pC.evaluate(() => document.querySelectorAll('#ticketBody details').forEach((d, i) => { if(i < 4) d.open = true; })); await run('Ticket info', '#pane-tickets');
    await pC.click('nav button[data-pane=competitions]'); await pC.waitForTimeout(400); await run('Competitions', '#pane-competitions');
    await pC.click('nav button[data-pane=me]');
    for(const [id, name] of [['Stats', 'Me - Stats'], ['Matches', 'Me - Matches'], ['Events', 'Me - Events'], ['Tix', 'Me - Tickets/Memberships']]){
      await pC.click('#meTab' + id); await pC.waitForTimeout(500); await run(name, '#pane-me'); }
    await pC.click('#meTabMatches'); await pC.click('#meMatches .acard'); await pC.waitForTimeout(500); await run('a match sheet', '#asheet'); await hideAll();
    await pC.click('#meTabTix'); await pC.click('[data-act=add][data-kind=membership]'); await run('Me form open', '#pane-me');
    await pC.click('#settingsBtn'); await run('Settings', '#ssheet'); await hideAll();

    // Nothing overflows at 390 px in this theme.
    const over = [];
    for(const [pane, sub] of [['map'], ['bucket'], ['tickets'], ['competitions'], ['me', 'Stats'], ['me', 'Matches'], ['me', 'Events'], ['me', 'Tix']]){
      await pC.click(`nav button[data-pane=${pane}]`); if(sub) await pC.click('#meTab' + sub); await pC.waitForTimeout(200);
      const o = await pC.evaluate(p => { const el = document.getElementById('pane-' + p);
        return {doc: document.documentElement.scrollWidth, pane: el.scrollWidth - el.clientWidth, bad: [...el.querySelectorAll('*')].filter(x => { const r = x.getBoundingClientRect(); return r.width > 0 && (r.right > innerWidth + 1 || r.left < -1) && !x.closest('.leaflet-container,svg,[hidden],.sheet'); }).slice(0, 3).map(x => x.tagName + '.' + x.className)}; }, pane);
      if(o.doc > W || o.pane > 0 || o.bad.length) over.push(`${pane}${sub || ''} ${JSON.stringify(o)}`);
    }
    check(`${th}: every main tab and Me sub-tab fits 390 px, nothing overflows`, !over.length, over.join(' | '));

    // The palette: tier colours, markers and the route line stay distinct from each other and from the map, on this theme's tiles.
    const pal = await pC.evaluate(() => { const v = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
      return {tiers: [1, 2, 3, 4, 5, 6, 7, 8].map(k => v('--t' + k)), route: v('--route'), map: v('--map-bg'), ink: v('--pin-ink'), grass: v('--pitch-grass'), pink: v('--pitch-ink'), disc: v('--pitch-disc')}; });
    const rgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
    const lumH = h => { const [r, g, b] = rgb(h).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }); return .2126 * r + .7152 * g + .0722 * b; };
    const cr = (a, b) => { const x = lumH(a), y = lumH(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
    const lab = h => { const f = v => { v /= 255; return v <= .04045 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
      const [r, g, b] = rgb(h).map(f); const X = (r * .4124 + g * .3576 + b * .1805) / .95047, Y = r * .2126 + g * .7152 + b * .0722, Z = (r * .0193 + g * .1192 + b * .9505) / 1.08883;
      const q = t => t > .008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116; return [116 * q(Y) - 16, 500 * (q(X) - q(Y)), 200 * (q(Y) - q(Z))]; };
    const dE = (a, b) => Math.hypot(...lab(a).map((v, i) => v - lab(b)[i]));
    const all = [...pal.tiers.map((c, i) => ['tier ' + (i + 1), c]), ['route', pal.route]];
    const close = [], weak = [];
    for(let i = 0; i < all.length; i++){
      for(let j = i + 1; j < all.length; j++) if(dE(all[i][1], all[j][1]) < 10) close.push(`${all[i][0]}/${all[j][0]} dE ${dE(all[i][1], all[j][1]).toFixed(1)}`);
      if(cr(all[i][1], pal.map) < 3 && cr(pal.ink, pal.map) < 3) weak.push(`${all[i][0]} ${cr(all[i][1], pal.map).toFixed(1)}`);
    }
    check(`${th}: the eight tier colours and the route colour are pairwise distinct (colour difference at least 10)`, !close.length, close.join(', '));
    check(`${th}: every tier and route colour, or else the marker outline, stands out from the map background by 3:1`, !weak.length, weak.join(', ') + ' outline ' + cr(pal.ink, pal.map).toFixed(1));
    check(`${th}: the line-up pitch text is at least 4.5:1 on the grass and on the number discs`, cr(pal.pink, pal.grass) >= 4.5 && cr(pal.pink, pal.disc) >= 4.5, cr(pal.pink, pal.grass).toFixed(1));
    await ctxC.close();
  }
  }

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
