// Headless Chromium test of the Bucket list's List and Calendar sub-tabs, at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright             (anywhere; it is not a dependency of this repo)
//   node tools/test_calendar.js .      (serves the checkout itself; it changes no file)
//
// Added 2026-10-04 with the calendar, favorites and the sort. Checked against the files read here
// (data/football-rules.json, data/bucket-links-manual.csv, data/holidays-manual.csv):
//  - neither List nor Calendar scrolls sideways or reaches past the screen at 390 px;
//  - the sort has three options, Group order is the default (Earliest and Favorites are kept), and Earliest puts upcoming day-level
//    entries first by date, then month-level ones ("estimated") by month, then undated ones, then
//    past ones in a COLLAPSED "Past" section (checked with the clock moved to June 2027);
//  - Favorites puts starred entries first, each group in Earliest order; the star is a 44 px
//    button with aria-pressed, does not open the card, and the stars and the sort survive a
//    reload; an id in storage that is no bucket entry is ignored; with storage blocked the list
//    still renders and the star still works for the visit;
//  - the calendar, under Europe/Berlin AND UTC with the clock at 2026-10-25 23:30 UTC (already
//    the 26th in Berlin): opens on the local month, marks the local today, and every month from
//    July 2026 to October 2027 places exactly the confirmed day-level items on their days, every
//    month-level item in the "Estimated this month" strip and never on a day, no disputed item
//    anywhere on the grid or strip, and lists the undated ones under "No date";
//  - holiday shading on exactly the days of each block; the school start marked; a month outside
//    the entered holidays says "School holidays not entered for this period"; a movable day
//    (added by this test only, in a served copy of the file) shaded differently from a fixed one;
//  - tapping an item opens a sheet against the bottom bar that scrolls inside itself and holds
//    the same text as the List's opened entry (or Reminders card); a window that belongs to an
//    entry opens that entry; "School holiday: <name>" is shown for an entry whose date is in a
//    block and for no other;
//  - no script error. Prints how long one month takes to render with the CPU slowed 4x.
// Stadia's tiles are stubbed. CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8779, BASE = `http://localhost:${PORT}/Football/`;
const W = 390, H = 844;
const TYPES = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.csv':'text/csv; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
const results = [];
const check = (name, ok, detail='') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ' :: ' + detail : '')); };

function csv(file){
  const text = fs.readFileSync(path.join(ROOT, file), 'utf8');
  const rows = []; let row = [], cell = '', q = false;
  for(let i = 0; i < text.length; i++){
    const ch = text[i];
    if(q){ if(ch === '"' && text[i+1] === '"'){ cell += '"'; i++; } else if(ch === '"') q = false; else cell += ch; }
    else if(ch === '"') q = true; else if(ch === ','){ row.push(cell); cell = ''; }
    else if(ch === '\n' || ch === '\r'){ if(ch === '\r' && text[i+1] === '\n') i++; row.push(cell); rows.push(row); row = []; cell = ''; }
    else cell += ch;
  }
  if(cell || row.length){ row.push(cell); rows.push(row); }
  const head = rows.shift();
  return rows.filter(r => r.some(c => c.trim())).map(r => Object.fromEntries(head.map((h, i) => [h.trim(), (r[i] || '').trim()])));
}
const rules = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/football-rules.json'), 'utf8'));
const evLinks = new Map(csv('data/bucket-links-manual.csv').filter(r => r.ticketEventId).map(r => [r.ticketEventId, r.bucketId]));
const hols = csv('data/holidays-manual.csv').filter(r => r.dateSource === 'confirmed');
const norm = s => String(s).replace(/\s+/g, ' ').trim();

// ---- What the files say, worked out here without asking the page.
const isDay = v => /^\d{4}-\d{2}-\d{2}$/.test(v || '');
const dayN = iso => Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10)) / 864e5;
const isoN = n => new Date(n * 864e5).toISOString().slice(0, 10);
// One date: day-level only when confirmed and whole days; otherwise its month(s).
function place(raw, ds){
  if(!raw || !/^\d{4}-\d{2}/.test(raw)) return null;
  const [a, b] = raw.split('/');
  if(ds === 'confirmed' && isDay(a) && (!b || (isDay(b) && b > a))) return {day: true, from: a, to: b || a};
  return {day: false, from: a.slice(0, 7), to: (b && /^\d{4}-\d{2}/.test(b) ? b : a).slice(0, 7)};
}
const evRaw = e => e.recurring === 'annual' ? e.nextEstimate : (e.date || e.dateEstimate);
function entryDates(b){
  const out = [];
  if(b.date) out.push([b.date, b.dateSource]);
  if(b.nextFixture) out.push([b.nextFixture.dateEstimate || b.nextFixture.date, b.nextFixture.dateSource]);
  (b.fixtures || []).forEach(f => out.push([f.date, f.dateSource]));
  return out.map(([raw, ds]) => ({ds, p: place(raw, ds)})).filter(d => d.p);
}
const want = {days: new Map(), months: new Map(), none: new Set(), disputed: new Set()};   // keys "entry:id" / "event:id"
const addDay = (k, p) => { for(let n = dayN(p.from); n <= dayN(p.to); n++){ const d = isoN(n); if(!want.days.has(d)) want.days.set(d, []); want.days.get(d).push(k); } };
const addMonth = (k, p) => { for(let ym = p.from; ym <= p.to; ym = nextYm(ym)){ if(!want.months.has(ym)) want.months.set(ym, []); want.months.get(ym).push(k); } };
const nextYm = ym => { const [y, m] = ym.split('-').map(Number); return m === 12 ? `${y + 1}-01` : `${y}-${String(m + 1).padStart(2, '0')}`; };
for(const b of rules.bucketList){
  if(b.listOnly) continue;      // added to the List only: never on the calendar
  const k = 'entry:' + b.id, ds = entryDates(b);
  if(!ds.length) want.none.add(k);
  for(const d of ds){ if(d.ds === 'disputed') want.disputed.add(k); else (d.p.day ? addDay : addMonth)(k, d.p); }
}
for(const e of rules.ticketEvents){
  const k = 'event:' + e.id, p = place(evRaw(e), e.dateSource);
  if(!p) want.none.add(k); else if(e.dateSource === 'disputed') want.disputed.add(k); else (p.day ? addDay : addMonth)(k, p);
}

const server = http.createServer((req, res) => {
  const p = decodeURIComponent(req.url.split('?')[0]);
  if(!p.startsWith('/Football/')){ res.writeHead(404); return res.end(); }
  let f = path.join(ROOT, p.slice('/Football/'.length)); if(p.endsWith('/')) f = path.join(f, 'index.html');
  fs.stat(f, (e, st) => {
    if(e || !st.isFile()){ res.writeHead(404); return res.end('nf'); }
    res.writeHead(200, {'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream', 'Cache-Control':'no-store'});
    fs.createReadStream(f).pipe(res);
  });
});

(async () => {
  await new Promise(r => server.listen(PORT, r));
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || undefined, headless: true});
  const errors = [];
  async function open({tz = 'Europe/Berlin', at = '2026-10-25T23:30:00Z', blockStorage = false, holidays = null, init = null, sort = 'earliest'} = {}){
    const ctx = await browser.newContext({viewport: {width: W, height: H}, isMobile: true, hasTouch: true,
      deviceScaleFactor: 2, serviceWorkers: 'block', timezoneId: tz});
    await ctx.clock.setFixedTime(new Date(at));
    await ctx.route('https://tiles.stadiamaps.com/**', r => r.fulfill({status:200, contentType:'image/png', headers: {'Access-Control-Allow-Origin': '*'}, body: PNG}));
    await ctx.route('https://api.stadiamaps.com/**', r => r.abort());
    if(holidays) await ctx.route('**/data/holidays-manual.csv', r => r.fulfill({status: 200, contentType: 'text/csv; charset=utf-8', body: holidays}));
    if(blockStorage) await ctx.addInitScript(() => {
      Object.defineProperty(window, 'localStorage', {get(){ throw new Error('storage blocked'); }});
    });
    // The List now opens in Group order; the older checks below are about Earliest, so they ask for it
    // (sort: null leaves the default alone).
    if(sort) await ctx.addInitScript(v => { try{ localStorage.setItem('football-planner-bucket-sort', v); }catch(e){} }, sort);
    if(init) await ctx.addInitScript(init);
    const page = await ctx.newPage();
    page.on('pageerror', e => errors.push(`${tz}${blockStorage ? ' blocked' : ''}: ${e.message}`));
    await page.goto(BASE);
    await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
    await page.click('nav button[data-pane=bucket]');
    await page.waitForFunction(() => document.querySelector('#bucketBody details.bucket'), null, {timeout: 15000});
    return {ctx, page};
  }
  const sideways = page => page.evaluate(() => {
    const el = document.getElementById('pane-bucket');
    const over = [...el.querySelectorAll('*')].filter(x => { const r = x.getBoundingClientRect(); return r.width > 0 && (r.right > innerWidth + 1 || r.left < -1); });
    return {sw: el.scrollWidth, cw: el.clientWidth, doc: document.documentElement.scrollWidth,
      over: over.slice(0, 5).map(x => `${x.tagName}.${x.className} "${x.textContent.trim().slice(0, 40)}"`)};
  });
  const listOrder = page => page.evaluate(() => {
    const out = [];
    let sec = null;
    for(const el of document.querySelectorAll('#bucketBody h2[data-sec], #bucketBody .bsub, #bucketBody details.past, #bucketBody details.bucket')){
      if(el.matches('h2, .bsub')) sec = el.dataset.sec || el.textContent.replace(/ — \d+$/, '');
      else if(el.matches('details.past')) sec = 'past';
      else out.push({id: el.dataset.id, sec: el.closest('details.past') ? 'past' : sec,
        group: el.querySelector('.bwhen').dataset.group, inPastOpen: el.closest('details.past')?.open});
    }
    return out;
  });

  // ==================================================================== List
  let {ctx, page} = await open({sort: null});
  let s = await sideways(page);
  check(`List: no sideways scroll at ${W} px (${s.sw} wide in ${s.cw})`, s.sw <= s.cw + 1 && s.doc <= W + 1 && !s.over.length, s.over.join(' | '));
  const sortUi = await page.$$eval('.bsort button', bs => bs.map(b => ({sort: b.dataset.sort, checked: b.getAttribute('aria-checked'), h: b.getBoundingClientRect().height})));
  check('Sort: three options, Group order, Earliest and Favorites, Group order chosen by default, each at least 44 px tall',
    sortUi.length === 3 && sortUi.map(b => b.sort).join() === 'group,earliest,favorites' && sortUi[0].checked === 'true' && sortUi.every(b => b.h >= 44),
    JSON.stringify(sortUi));

  // ---- Group order (the default): the entries with a sortKey in sortKey order under their group's heading, then the rest in file order.
  const keyed = rules.bucketList.filter(b => b.sortKey != null).sort((a, c) => a.sortKey - c.sortKey);
  const unkeyed = rules.bucketList.filter(b => b.sortKey == null);
  const addedL = rules.bucketList.filter(b => b.listOnly);
  const groupDom = await page.evaluate(() => [...document.querySelectorAll('#bucketBody h2[data-sec^="group:"], #bucketBody .bsub[data-sec^="country:"], #bucketBody details.bucket')]
    .map(el => el.matches('details.bucket') ? {id: el.dataset.id, when: el.querySelector('.bwhen').textContent, tags: el.querySelector('.meta').textContent,
      why: el.querySelector('.bwhyc')?.textContent || ''} : {head: el.dataset.sec, text: el.textContent}));
  const gotIds = groupDom.filter(x => x.id).map(x => x.id);
  check(`Group order: ${keyed.length} entries with a sortKey (10, 20 ... ${keyed.length * 10}, no gap, no repeat), shown in sortKey order, then ${unkeyed.length} entries without one in file order`,
    keyed.every((b, i) => b.sortKey === (i + 1) * 10) && gotIds.join() === keyed.concat(unkeyed).map(b => b.id).join(),
    gotIds.slice(0, 5).join());
  const wantHeads = [...new Set(keyed.map(b => b.group))];
  const gotHeads = groupDom.filter(x => x.head && x.head.startsWith('group:') && x.head !== 'group:ungrouped').map(x => x.head.slice(6));
  check('Group order: the group headings come in the order of the first sortKey of each group, once each', gotHeads.join('|') === wantHeads.join('|'), gotHeads.join('|'));
  const subHeads = groupDom.filter(x => x.head && x.head.startsWith('country:')).map(x => x.head.slice(8));
  const wantSub = []; for(const b of keyed.filter(b => b.group === 'Club fixtures, other countries')) if(wantSub[wantSub.length - 1] !== b.country) wantSub.push(b.country);
  check(`Group order: the "other countries" group has a sub-heading for each of its ${wantSub.length} countries, in order`, subHeads.join('|') === wantSub.join('|'), subHeads.join('|'));
  const dated = new Set(rules.bucketList.filter(b => entryDates(b).length).map(b => b.id));
  const undatedCards = groupDom.filter(x => x.id && !dated.has(x.id));
  check('Undated entries say "Date not set"', undatedCards.length > 0 && undatedCards.every(x => x.when === 'Date not set'), undatedCards.filter(x => x.when !== 'Date not set').map(x => x.id + ':' + x.when).join(', '));
  const newCards = groupDom.filter(x => x.id && addedL.some(b => b.id === x.id));
  check(`All ${addedL.length} added entries are cards, each undated, each showing its why text and the label "Not yet verified"`,
    newCards.length === addedL.length && newCards.every(x => x.when === 'Date not set' && /Not yet verified/.test(x.tags) && x.why.length > 10),
    newCards.filter(x => !(x.when === 'Date not set' && /Not yet verified/.test(x.tags) && x.why.length > 10)).map(x => x.id).join(', '));
  const LCT = 'Needs a league check: both clubs must share a league or cup in that season';
  const lcWant = new Set(rules.bucketList.filter(b => b.leagueCheck).map(b => b.id));
  check(`The league-check label is on exactly the ${lcWant.size} entries flagged leagueCheck`,
    groupDom.filter(x => x.id).every(x => x.tags.includes(LCT) === lcWant.has(x.id)) && lcWant.size > 0);
  // The sheet of a flagged entry's opened card holds the why and the labels too.
  const lcId = [...lcWant].find(id => addedL.some(b => b.id === id));
  await page.click(`details.bucket[data-id="${lcId}"] summary h3`);
  await page.waitForFunction(id => !/^Loading…/.test(document.querySelector(`details.bucket[data-id="${id}"] .bdetail`).textContent.trim()), lcId, {timeout: 10000});
  const opened = await page.$eval(`details.bucket[data-id="${lcId}"]`, d => d.textContent);
  const lcEntry = rules.bucketList.find(b => b.id === lcId);
  check('An opened added entry shows its why text', opened.includes(lcEntry.why), lcId);
  // Existing entries kept their dates: the snapshot below is HEAD's, from before the 160 were added.
  const SNAP = {"klassiker-away":{},"away-end-first":{},"poli-uta":{},"el-final-2027":{"date":"2027-05-26","kickoff":"21:00","dateSource":"confirmed"},"frankenderby":{"nextFixture":{"matchday":19,"dateEstimate":"2027-01-30/2027-02-01","derivation":"Inferred from the mirrored fixture list - matchday 20 is Bielefeld away on 6 Feb 2027. Verify against the DFL schedule.","missed":"First leg at the Ronhof, 15 Aug 2026.","dateSource":"inferred"}},"sudwest-derby":{"nextFixture":{"matchday":19,"dateEstimate":"2027-01-29/2027-01-31","missed":"First leg on the Betzenberg, 15 Aug 2026.","dateSource":"inferred"}},"derby-madonnina":{"fixtures":[{"date":"2026-11-01","home":"milan","matchday":10,"saleRoute":"Cuore Rossonero phase then free sale. Card needed well in advance.","dateSource":"confirmed"},{"date":"2027-02-14","home":"inter","matchday":24,"saleRoute":"Phase 1, open worldwide, primo anello rosso/arancio.","dateSource":"confirmed"}]},"revierderby":{},"pokal-first-round":{},"liga2-playoff":{},"relegation":{},"vfb-regular":{},"womens-football":{},"eternal-derby-belgrade":{},"intercontinental-derby":{},"old-firm":{},"derby-eternal-enemies":{},"fcsb-dinamo":{},"derby-du-nord":{},"ostderby":{},"prague-derby":{}};
  const drift = Object.keys(SNAP).filter(id => { const b = rules.bucketList.find(x => x.id === id);
    return !b || ['date', 'kickoff', 'dateSource', 'nextFixture', 'fixtures'].some(k => JSON.stringify(b[k]) !== JSON.stringify(SNAP[id][k])); });
  check(`The ${Object.keys(SNAP).length} entries that existed before kept their dates, kickoffs, dateSources, nextFixtures and fixtures`, drift.length === 0, drift.join(', '));
  // None of the added entries is on the calendar, in any month the calendar can show.
  await page.click('#tabCal');
  const onCal = await page.evaluate(ids => { const hit = [];
    for(let ym = '2026-07'; ym <= '2027-12'; ym = (m => m === 12 ? `${+ym.slice(0, 4) + 1}-01` : `${ym.slice(0, 4)}-${String(m + 1).padStart(2, '0')}`)(+ym.slice(5))){
      CAL.month = ym; CAL.sel = null; renderCalendar();
      for(const b of document.querySelectorAll('#calBody .calitem')) if(ids.some(id => b.dataset.open === 'entry:' + id)) hit.push(ym + ' ' + b.dataset.open);
      for(const id of ids){ for(const d of document.querySelectorAll('#calBody .cday')) if((d.getAttribute('aria-label') || '').includes(id)) hit.push(ym + ' cell ' + id); }
    }
    return hit; }, addedL.map(b => b.id));
  check(`None of the ${addedL.length} added entries is on the calendar (grid, strip, "No date" or "Not placed") in July 2026 to December 2027`, onCal.length === 0, onCal.slice(0, 5).join(' | '));
  await page.click('#tabList');
  await page.click('.bsort button[data-sort=earliest]');

  // Earliest, worked out from the files with today = 2026-10-26.
  const today0 = '2026-10-26';
  function earliest(items, today){
    const PR = {high: 0, medium: 1, low: 2}, held = b => (b.status === 'blocked' || b.status === 'deferred') ? 1 : 0;
    const w = b => {
      const ds = entryDates(b).filter(d => d.ds !== 'disputed');
      const past = d => d.p.day ? d.p.to < today : d.p.to < today.slice(0, 7);
      const up = ds.filter(d => !past(d)).sort((a, c) => a.p.from.localeCompare(c.p.from));
      const day = up.find(d => d.p.day), mon = up.find(d => !d.p.day);
      if(day) return {g: 'day', k: day.p.from};
      if(mon) return {g: 'month', k: mon.p.from + '-01'};
      if(ds.length) return {g: 'past', k: ds.map(d => d.p.from).sort().pop()};
      return {g: 'none', k: ''};
    };
    const W2 = new Map(items.map(b => [b.id, w(b)]));
    const tie = (a, c) => (held(a) - held(c)) || ((PR[a.priority] ?? 9) - (PR[c.priority] ?? 9));
    return ['day', 'month', 'none', 'past'].flatMap(g => items.filter(b => W2.get(b.id).g === g)
      .sort((a, c) => W2.get(a.id).k.localeCompare(W2.get(c.id).k) || tie(a, c)).map(b => ({id: b.id, g})));
  }
  let got = await listOrder(page);
  let exp = earliest(rules.bucketList, today0);
  check(`Earliest: ${exp.length} entries - upcoming to the day by date, then estimated by month, then no date, then past`,
    JSON.stringify(got.map(x => x.id)) === JSON.stringify(exp.map(x => x.id)) && got.every((x, i) => x.group === exp[i].g),
    got.map(x => `${x.id}:${x.group}`).join(', '));
  const counts = ['day', 'month', 'none', 'past'].map(g => exp.filter(x => x.g === g).length);
  console.log(`  entries: ${counts[0]} day-level upcoming, ${counts[1]} month-level (estimated), ${counts[2]} undated, ${counts[3]} past (today ${today0})`);
  const monthText = await page.$$eval('#bucketBody .bwhen[data-group="month"]', es => es.map(e => e.textContent));
  check('Earliest: every month-level entry is labelled "estimated" and shows no day', monthText.length > 0 &&
    monthText.every(t => /^estimated: /.test(t) && !/\b\d{1,2} [A-Z][a-z]{2}\b|\d{4}-\d{2}-\d{2}/.test(t)), monthText.join(' | '));

  // The star.
  const starId = 'revierderby';
  const star = `details.bucket[data-id="${starId}"] .star`;
  const box = await page.$eval(star, b => { const r = b.getBoundingClientRect(); return {w: r.width, h: r.height, pressed: b.getAttribute('aria-pressed')}; });
  check('Star: a button at least 44x44 with aria-pressed="false" to start', box.w >= 44 && box.h >= 44 && box.pressed === 'false', JSON.stringify(box));
  await page.click(star);
  const after = await page.$eval(`details.bucket[data-id="${starId}"]`, d => ({open: d.open, pressed: d.querySelector('.star').getAttribute('aria-pressed'), text: d.querySelector('.star').textContent}));
  check('Star: a tap stars the entry and does not open the card', after.pressed === 'true' && !after.open && after.text === '★', JSON.stringify(after));
  await page.click('.bsort button[data-sort=favorites]');
  got = await listOrder(page);
  const favExp = earliest(rules.bucketList.filter(b => b.id === starId), today0).concat(earliest(rules.bucketList.filter(b => b.id !== starId), today0));
  check('Favorites: the starred entry first, then the rest in Earliest order',
    JSON.stringify(got.map(x => x.id)) === JSON.stringify(favExp.map(x => x.id)) && got[0].id === starId, got.map(x => x.id).slice(0, 6).join(', '));
  await page.reload();
  await page.click('nav button[data-pane=bucket]');
  await page.waitForFunction(() => document.querySelector('#bucketBody details.bucket'), null, {timeout: 15000});
  const kept = await page.evaluate(id => ({sort: document.querySelector('.bsort button[aria-checked="true"]')?.dataset.sort,
    first: document.querySelector('#bucketBody details.bucket')?.dataset.id,
    pressed: document.querySelector(`details.bucket[data-id="${id}"] .star`).getAttribute('aria-pressed')}), starId);
  check('After a reload: the sort is still Favorites and the star is still on', kept.sort === 'favorites' && kept.first === starId && kept.pressed === 'true', JSON.stringify(kept));
  // Unstar, back to Earliest.
  await page.click(star);
  await page.click('.bsort button[data-sort=earliest]');
  check('Unstarred and back to Earliest', (await listOrder(page)).map(x => x.id).join() === exp.map(x => x.id).join());
  await ctx.close();

  // An id in storage that is no bucket entry is ignored.
  ({ctx, page} = await open({init: () => { try{ localStorage.setItem('football-planner-favorites', JSON.stringify(['no-such-entry', 'revierderby']));
    localStorage.setItem('football-planner-bucket-sort', 'favorites'); }catch(e){} }}));
  const stale = await page.evaluate(() => ({head: document.querySelector('#bucketBody h2[data-sec=favorites]')?.textContent,
    first: document.querySelector('#bucketBody details.bucket')?.dataset.id}));
  check('A stored favorite id that is no entry is ignored (Favorites — 1)', /Favorites — 1$/.test(stale.head || '') && stale.first === 'revierderby', JSON.stringify(stale));
  await ctx.close();

  // Storage blocked.
  ({ctx, page} = await open({blockStorage: true}));
  await page.click(star);
  await page.click('.bsort button[data-sort=favorites]');
  const blocked = await page.evaluate(id => ({first: document.querySelector('#bucketBody details.bucket')?.dataset.id,
    pressed: document.querySelector(`details.bucket[data-id="${id}"] .star`)?.getAttribute('aria-pressed'),
    cards: document.querySelectorAll('#bucketBody details.bucket').length}), starId);
  check('Storage blocked: the list renders, and the star and the sort work for the visit',
    blocked.cards === rules.bucketList.length && blocked.first === starId && blocked.pressed === 'true', JSON.stringify(blocked));
  await ctx.close();

  // Past, with the clock in June 2027.
  ({ctx, page} = await open({at: '2027-06-01T10:00:00Z'}));
  got = await listOrder(page);
  exp = earliest(rules.bucketList, '2027-06-01');
  const pastIds = exp.filter(x => x.g === 'past').map(x => x.id);
  const pastSec = await page.evaluate(() => { const d = document.querySelector('#bucketBody details.past'); return d ? {open: d.open, n: d.querySelectorAll('details.bucket').length, sum: d.querySelector('summary').textContent} : null; });
  check(`Past (clock at 1 Jun 2027): ${pastIds.length} entries, last, in a collapsed "Past" section`,
    pastIds.length > 0 && !!pastSec && !pastSec.open && pastSec.n === pastIds.length && /^Past — /.test(pastSec.sum) &&
    JSON.stringify(got.map(x => x.id)) === JSON.stringify(exp.map(x => x.id)) && got.filter(x => x.sec === 'past').map(x => x.id).join() === pastIds.join(),
    `${pastIds.join(', ')}; ${JSON.stringify(pastSec)}`);
  await ctx.close();

  // ==================================================================== Calendar, two time zones
  const months = []; for(let ym = '2026-07'; ym <= '2027-10'; ym = nextYm(ym)) months.push(ym);
  const shown = {};
  for(const [tz, today] of [['Europe/Berlin', '2026-10-26'], ['UTC', '2026-10-25']]){
    ({ctx, page} = await open({tz}));
    await page.click('#tabCal');
    await page.waitForSelector('#calTitle');
    const head = await page.evaluate(() => ({title: document.getElementById('calTitle').textContent,
      today: document.querySelector('.cday.today')?.dataset.date, sel: document.querySelector('.cday[aria-pressed="true"]')?.dataset.date}));
    check(`${tz}: the calendar opens on October 2026 and marks the local today, ${today}`,
      head.title === 'October 2026' && head.today === today && head.sel === today, JSON.stringify(head));
    s = await sideways(page);
    check(`${tz}: Calendar: no sideways scroll at ${W} px (${s.sw} wide in ${s.cw})`, s.sw <= s.cw + 1 && s.doc <= W + 1 && !s.over.length, s.over.join(' | '));
    const cell = await page.$eval('.cday[data-date]', b => { const r = b.getBoundingClientRect(); return {w: r.width, h: r.height}; });
    check(`${tz}: day cells are tappable (${Math.round(cell.w)}x${Math.round(cell.h)} px)`, cell.w >= 40 && cell.h >= 44);
    // Go back to July 2026, then walk every month forward.
    for(let i = 0; i < 3; i++) await page.click('[data-cal=prev]');
    shown[tz] = {};
    for(const ym of months){
      const M = await page.evaluate(() => {
        const cells = [...document.querySelectorAll('.cday[data-date]')];
        return {title: document.getElementById('calTitle').textContent,
          cells: cells.map(c => ({d: c.dataset.date, hol: c.classList.contains('shol'), mov: c.classList.contains('mov'), start: c.classList.contains('start'),
            marks: c.querySelectorAll('.mk .mev, .mk .mtw').length, more: (c.querySelector('.mk')?.textContent.match(/\+(\d+)/) || [0, 0])[1] * 1})),
          est: [...document.querySelectorAll('#calEst .calitem')].map(b => b.dataset.open),
          estDs: [...document.querySelectorAll('#calEst .calitem')].map(b => b.dataset.ds),
          notice: [...document.querySelectorAll('.calnotice')].map(n => n.textContent),
          none: [...document.querySelectorAll('#calNone .calitem')].map(b => b.dataset.open),
          disputed: [...document.querySelectorAll('#calDisputed .calitem')].map(b => b.dataset.open)};
      });
      shown[tz][ym] = M;
      // Items on each marked day, read by tapping it.
      const onDays = {};
      for(const c of M.cells.filter(c => c.marks)){
        await page.click(`.cday[data-date="${c.d}"]`);
        onDays[c.d] = await page.$$eval('#calDay .calitem', bs => bs.map(b => ({k: b.dataset.open, ds: b.dataset.ds})));
      }
      const wantDays = [...want.days.entries()].filter(([d]) => d.startsWith(ym));
      const gotKeys = Object.entries(onDays).map(([d, xs]) => d + '=' + xs.map(x => x.k).sort().join('+')).sort();
      const wantKeys = wantDays.map(([d, ks]) => d + '=' + ks.slice().sort().join('+')).sort();
      check(`${tz} ${ym}: day cells hold exactly the confirmed day-level items (${wantKeys.length} day(s))`,
        JSON.stringify(gotKeys) === JSON.stringify(wantKeys) && Object.values(onDays).flat().every(x => x.ds === 'confirmed'), gotKeys.join(' ') + ' / want ' + wantKeys.join(' '));
      const wantEst = (want.months.get(ym) || []).slice().sort();
      check(`${tz} ${ym}: the estimated strip holds exactly the month-level items (${wantEst.length}), none on a day cell`,
        JSON.stringify(M.est.slice().sort()) === JSON.stringify(wantEst) && !M.estDs.includes('confirmed') &&
        !Object.values(onDays).flat().some(x => wantEst.includes(x.k)), M.est.join(', '));
      check(`${tz} ${ym}: no disputed item on the grid or the strip; "No date" holds every undated item`,
        ![...want.disputed].some(k => M.est.includes(k) || Object.values(onDays).flat().some(x => x.k === k)) &&
        JSON.stringify(M.disputed.slice().sort()) === JSON.stringify([...want.disputed].sort()) &&
        JSON.stringify(M.none.slice().sort()) === JSON.stringify([...want.none].sort()));
      // Holidays.
      const wantHol = M.cells.filter(c => hols.some(r => r.kind === 'school-holiday' && r.start <= c.d && c.d <= r.end)).map(c => c.d);
      const wantStart = M.cells.filter(c => hols.some(r => r.kind === 'school-start' && r.start <= c.d && c.d <= r.end)).map(c => c.d);
      check(`${tz} ${ym}: shaded days are exactly the holiday blocks (${wantHol.length}); school start marked (${wantStart.length})`,
        JSON.stringify(M.cells.filter(c => c.hol).map(c => c.d)) === JSON.stringify(wantHol) &&
        JSON.stringify(M.cells.filter(c => c.start).map(c => c.d)) === JSON.stringify(wantStart) && !M.cells.some(c => c.mov));
      const first = hols.map(r => r.start).sort()[0], last = hols.map(r => r.end).sort().pop();
      const lastDay = M.cells[M.cells.length - 1].d, out = lastDay < first || `${ym}-01` > last, part = !out && (`${ym}-01` < first || lastDay > last);
      check(`${tz} ${ym}: ${out ? 'outside the entered holidays, says so' : part ? 'partly outside, says so' : 'inside the entered holidays, no not-entered notice'}`,
        out ? M.notice.some(t => t === 'School holidays not entered for this period.')
          : part ? M.notice.some(t => /^School holidays not entered for this period (before|after) /.test(t))
          : !M.notice.some(t => /not entered for this period/.test(t)), M.notice.join(' | '));
      if(ym !== months[months.length - 1]) await page.click('[data-cal=next]');
    }
    // Today goes back to the local month and day.
    await page.click('[data-cal=today]');
    const back = await page.evaluate(() => ({title: document.getElementById('calTitle').textContent, sel: document.querySelector('.cday[aria-pressed="true"]')?.dataset.date}));
    check(`${tz}: "Today" goes back to October 2026, ${today} chosen`, back.title === 'October 2026' && back.sel === today, JSON.stringify(back));
    if(tz === 'Europe/Berlin'){
      await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', 'calendar.png'), fullPage: false});
      const hn = await page.$eval('.cday[data-date="2026-10-26"] .hn', e => e.textContent).catch(() => '');
      check('October 2026: the holiday name is on its first shaded day', hn === 'Herbstferien', hn);
    }
    if(tz === 'UTC'){
      const same = months.every(ym => JSON.stringify(shown.UTC[ym].cells.map(c => [c.d, c.hol, c.start, c.marks])) ===
        JSON.stringify(shown['Europe/Berlin'][ym].cells.map(c => [c.d, c.hol, c.start, c.marks])));
      check('UTC and Europe/Berlin draw every month identically (no day shifted)', same);
    }
    await ctx.close();
  }

  // ==================================================================== The sheet
  ({ctx, page} = await open());
  const listText = async (sel) => {
    await page.click('#tabList');
    const t = await page.evaluate(async sel => {
      const d = document.querySelector(sel);
      if(d.tagName === 'DETAILS'){ d.open = true; }
      for(let i = 0; i < 200 && /Loading…/.test(d.querySelector('.tix')?.textContent || d.textContent); i++) await new Promise(r => setTimeout(r, 100));
      const tix = d.matches('.tix') ? d : d.querySelector('.tix');
      return tix.textContent;
    }, sel);
    return norm(t);
  };
  const sheetOpen = async (ym, key, from = 'day') => {
    await page.click('#tabCal');
    await page.evaluate(ym => { CAL.month = ym; CAL.sel = null; renderCalendar(); }, ym);
    const d = (want.days.size && [...want.days.entries()].find(([d, ks]) => d.startsWith(ym) && ks.includes(key)) || [])[0];
    if(from === 'day') await page.click(`.cday[data-date="${d}"]`);
    await page.click(`${from === 'day' ? '#calDay' : from === 'est' ? '#calEst' : '#calNone'} .calitem[data-open="${key}"]`);
    await page.waitForFunction(() => !document.getElementById('bsheet').hidden && !/Loading…/.test(document.getElementById('bsheetBody').textContent), null, {timeout: 60000});
    await page.waitForTimeout(400);   // the sheet slides up over 0.22 s
    if(key === 'entry:derby-madonnina' && process.env.SHOT_DIR) await page.screenshot({path: path.join(process.env.SHOT_DIR, 'calendar-sheet.png')});
    return page.evaluate(() => {
      const sh = document.getElementById('bsheet'), body = document.getElementById('bsheetBody');
      const r = sh.getBoundingClientRect(), nav = document.querySelector('nav').getBoundingClientRect();
      return {text: body.textContent, head: document.getElementById('bsheetHead').innerText, bottom: r.bottom, navTop: nav.top,
        scrolls: getComputedStyle(body).overflowY === 'auto' && body.scrollHeight > body.clientHeight,
        paneScroll: document.getElementById('pane-bucket').scrollTop, focus: body.querySelector('.ev.focus')?.dataset.ev || null};
    });
  };
  const mad = 'derby-madonnina';
  let S = await sheetOpen('2026-11', 'entry:' + mad);
  check('Tapping 1 Nov 2026, then the Milan derby, opens a sheet against the bottom bar',
    Math.abs(S.bottom - S.navTop) <= 1 && /Derby della Madonnina|Madonnina/i.test(S.head), `sheet bottom ${S.bottom}, nav top ${S.navTop}`);
  check('The sheet scrolls inside itself', S.scrolls);
  await page.click('#bsheetClose');
  let L = await listText(`details.bucket[data-id="${mad}"]`);
  check("The sheet holds the same text as the List's opened entry (Milan derby)", norm(S.text) === L, `${norm(S.text).length} against ${L.length} characters`);
  check('The Milan derby says nothing about a school holiday (1 Nov and 14 Feb are in no block)', !/School holiday:/.test(S.text));
  const elf = 'el-final-2027';
  S = await sheetOpen('2027-05', 'entry:' + elf);
  await page.click('#bsheetClose');
  L = await listText(`details.bucket[data-id="${elf}"]`);
  const elHol = hols.find(r => r.kind === 'school-holiday' && r.start <= '2027-05-26' && '2027-05-26' <= r.end);
  check(`${elf}: the sheet matches the List's entry and says "School holiday: ${elHol?.name}"`,
    norm(S.text) === L && !!elHol && S.text.includes(`School holiday: ${elHol.name}`) && L.includes(`School holiday: ${elHol.name}`));
  // A window that belongs to an entry opens that entry, at the window.
  const linked = rules.ticketEvents.find(e => evLinks.has(e.id) && e.dateSource === 'inferred' && evRaw(e));
  if(linked){
    S = await sheetOpen(evRaw(linked).slice(0, 7), 'event:' + linked.id, 'est');
    await page.click('#bsheetClose');
    L = await listText(`details.bucket[data-id="${evLinks.get(linked.id)}"]`);
    check(`Ticket window ${linked.id} opens its entry ${evLinks.get(linked.id)}, at the window`, norm(S.text) === L && S.focus === linked.id, S.focus);
  }
  // A reminder no entry claims opens its own card.
  const loose = rules.ticketEvents.find(e => !evLinks.has(e.id) && e.dateSource === 'inferred' && evRaw(e));
  if(loose){
    S = await sheetOpen(evRaw(loose).slice(0, 7), 'event:' + loose.id, 'est');
    await page.click('#bsheetClose');
    await page.click('#tabList');
    const R = norm(await page.$eval(`#bucketBody .evcard .ev[data-ev="${loose.id}"]`, e => e.closest('.evcard').textContent));
    check(`Reminder ${loose.id}: the sheet matches its Reminders card`, norm(S.text) === R);
  }
  // Leaving the tab closes the sheet.
  await sheetOpen('2026-11', 'entry:' + mad);
  await page.click('nav button[data-pane=map]');
  check('Switching to the map closes the sheet', await page.$eval('#bsheet', e => e.hidden));
  await ctx.close();

  // ==================================================================== A movable day, in a served copy only
  const movRow = 'Beweglicher Ferientag,2026-11-02,2026-11-02,school-holiday-movable,confirmed,test fixture (tools/test_calendar.js only),';
  const csvText = fs.readFileSync(path.join(ROOT, 'data/holidays-manual.csv'), 'utf8').replace(/\n?$/, '\n') + movRow + '\n';
  ({ctx, page} = await open({holidays: csvText}));
  await page.click('#tabCal');
  await page.click('[data-cal=next]');
  const mov = await page.evaluate(() => {
    const m = document.querySelector('.cday[data-date="2026-11-02"]'), o = document.querySelector('.cday[data-date="2026-10-30"]');
    const style = e => getComputedStyle(e).backgroundImage + ' ' + getComputedStyle(e).backgroundColor + ' ' + getComputedStyle(e).borderStyle;
    return {mov: m.classList.contains('mov'), hol: m.classList.contains('shol'), name: m.querySelector('.hn')?.textContent,
      differs: style(m) !== style(document.querySelector('.cday[data-date="2026-10-26"]') || m), notice: [...document.querySelectorAll('.calnotice')].map(n => n.textContent).join(' | ')};
  });
  check('A movable day (served test copy) is shaded differently from a fixed holiday and named', mov.mov && !mov.hol && mov.name === 'Beweglicher Ferientag', JSON.stringify(mov));
  await page.click('[data-cal=prev]');
  const fixedVsMov = await page.evaluate(() => getComputedStyle(document.querySelector('.cday[data-date="2026-10-26"]')).backgroundImage);
  check('...and the fixed holiday has no hatching', fixedVsMov === 'none', fixedVsMov);
  check('With a movable day entered, the "not entered" warning about movable days is gone', !/Movable school days/.test(mov.notice), mov.notice);
  await ctx.close();

  // ==================================================================== Render time
  ({ctx, page} = await open());
  await page.click('#tabCal');
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', {rate: 4});
  const times = await page.evaluate(async () => {
    const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    const out = {render: [], painted: []};
    for(let i = 0; i < 15; i++){
      CAL.month = i % 2 ? '2026-11' : '2026-10'; CAL.sel = null;
      await frame();
      const t0 = performance.now();
      renderCalendar();
      const t1 = performance.now();
      await frame();
      out.render.push(t1 - t0); out.painted.push(performance.now() - t0);
    }
    const med = a => a.slice().sort((x, y) => x - y)[Math.floor(a.length / 2)];
    return {render: med(out.render), renderMax: Math.max(...out.render), painted: med(out.painted)};
  });
  await cdp.send('Emulation.setCPUThrottlingRate', {rate: 1});
  console.log(`  render time, one month, CPU slowed 4x (median of 15): renderCalendar() ${times.render.toFixed(1)} ms ` +
    `(worst ${times.renderMax.toFixed(1)}), to a painted frame ${times.painted.toFixed(1)} ms (includes a two-frame wait)`);
  check('A month renders in under 100 ms with the CPU slowed 4x', times.render < 100, times.render.toFixed(1) + ' ms');
  await ctx.close();

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
