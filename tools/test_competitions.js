// Headless Chromium test of the Competitions tab, at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright                 (anywhere; it is not a dependency of this repo)
//   node tools/test_competitions.js .      (serves the checkout itself; it changes no file)
//
// Added 2026-10-08. Everything is checked against data/competitions.csv, competition-info.csv and
// competition-sources.csv read here; no count is written into this file:
//  - the tab exists, fifth of five, between Ticket info and Me, and all five labels fit 390 px
//    (none wider than its slot, none wrapped, none off screen);
//  - every competition in competitions.csv is in the list; the list runs Germany, Romania, other
//    countries A-Z, then Europe and international; a competition with no info row says
//    "Not researched yet", and its sheet says nothing else;
//  - a researched competition's sheet (the DFB-Pokal, among the rest) shows the seven topics in the fixed order,
//    each researched row with its status label ("Confirmed", "Estimated, based on past seasons" or
//    "Not yet verified"), its source link to the URL in the sources file, and "Checked on <date>";
//  - no day-level FUTURE date renders anywhere in the list or in any sheet;
//  - the country filter and the name search narrow the list, an empty result says "No competitions
//    match", and "Show all" resets; no sideways scroll; no script error.
// Stadia's tiles are stubbed. CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8784, BASE = `http://localhost:${PORT}/Football/`;
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
const comps = csv('data/competitions.csv');
const info = csv('data/competition-info.csv');
const sources = Object.fromEntries(csv('data/competition-sources.csv').map(s => [s.sourceId, s]));
const TOPICS = ['format', 'qualification', 'promotion-relegation', 'season-window', 'schedule-announcement', 'tracking', 'other'];
const STATUS = {confirmed: 'Confirmed', inferred: 'Estimated, based on past seasons', unverified: 'Not yet verified'};
const researched = new Set(info.map(r => r.competitionId));
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const wordsOf = iso => { const [y, m, d] = iso.split('-'); return `${+d} ${MONTHS[+m - 1]} ${y}`; };
// A day-level date not in the past, in any form the page could print one.
const todayIso = new Date().toISOString().slice(0, 10);
function futureDays(text){
  const out = [];
  for(const m of text.matchAll(/\b(\d{4})-(\d{2})-(\d{2})\b/g)) if(m[0] > todayIso) out.push(m[0]);
  for(const m of text.matchAll(/\b(\d{1,2})(?:st|nd|rd|th)?\.?\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b/g)) {
    const iso = `${m[3]}-${String(['January','February','March','April','May','June','July','August','September','October','November','December'].indexOf(m[2]) + 1).padStart(2, '0')}-${m[1].padStart(2, '0')}`;
    if(iso > todayIso) out.push(m[0]);
  }
  return out;
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
  const ctx = await browser.newContext({viewport: {width: W, height: H}, isMobile: true, hasTouch: true,
    deviceScaleFactor: 2, serviceWorkers: 'block'});
  await ctx.route('https://tiles.stadiamaps.com/**', r => r.fulfill({status:200, contentType:'image/png', headers: {'Access-Control-Allow-Origin': '*'}, body: PNG}));
  await ctx.route('https://api.stadiamaps.com/**', r => r.abort());
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(BASE);
  await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});

  // ---------------------------------------------------------------- the bottom bar
  const nav = await page.evaluate(() => {
    const bs = [...document.querySelectorAll('nav button')];
    return {n: bs.length, labels: bs.map(b => b.textContent.replace(/\s+/g, ' ').trim()), panes: bs.map(b => b.dataset.pane),
      navW: document.querySelector('nav').scrollWidth,
      bad: bs.filter(b => { const r = b.getBoundingClientRect(); return b.scrollWidth > b.clientWidth + 1 || r.right > innerWidth + 1 || r.left < -1; }).map(b => b.textContent.trim()),
      heights: bs.map(b => Math.round(b.getBoundingClientRect().height)),
      lines: bs.map(b => { const node = [...b.childNodes].find(n => n.nodeType === 3); const r = document.createRange(); r.selectNodeContents(node); return r.getClientRects().length; })};
  });
  check('The Competitions tab exists: five tabs, fourth, between Ticket info and Me',
    nav.n === 5 && nav.panes[2] === 'tickets' && nav.panes[3] === 'competitions' && nav.panes[4] === 'me' && /Competitions$/.test(nav.labels[3]), nav.labels.join(' | '));
  check('All five labels fit at 390 px: none wider than its slot or off screen', !nav.bad.length && nav.navW <= W, JSON.stringify(nav.bad) + ` nav ${nav.navW}`);
  check('No label wraps to a second line, all the same height', nav.lines.every(n => n === 1) && new Set(nav.heights).size === 1, JSON.stringify({lines: nav.lines, heights: nav.heights}));

  // ---------------------------------------------------------------- the list
  await page.click('nav button[data-pane=competitions]');
  await page.waitForSelector('#compBody .comprow', {timeout: 15000});
  const rows = await page.$$eval('#compBody .comprow', bs => bs.map(b => ({id: b.dataset.id, name: b.querySelector('.rn').firstChild.textContent, st: b.querySelector('em').textContent})));
  const ids = rows.map(r => r.id);
  check(`Every competition in competitions.csv is in the list (${comps.length})`,
    ids.length === comps.length && comps.every(c => ids.includes(c.id)), comps.filter(c => !ids.includes(c.id)).map(c => c.id).join(','));
  check('Each row shows the competition\'s name as written', comps.every(c => rows.find(r => r.id === c.id)?.name === c.name));
  const heads = await page.$$eval('#compBody h2', hs => hs.map(h => h.textContent.replace(/ — \d+$/, '')));
  const rest = heads.slice(2, heads.includes('Europe and international') ? -1 : undefined);
  const hasDE = comps.some(c => c.country === 'DE'), hasRO = comps.some(c => c.country === 'RO');
  check('The list runs Germany, Romania, other countries A-Z, then Europe and international',
    (!hasDE || heads[0] === 'Germany') && (!hasRO || heads[hasDE ? 1 : 0] === 'Romania') &&
    JSON.stringify(rest) === JSON.stringify([...rest].sort((a, b) => a.localeCompare(b))) &&
    (!comps.some(c => !c.country) || heads[heads.length - 1] === 'Europe and international'), heads.join(' | '));
  const order = (cid) => ['league', 'cup', 'supercup', 'playoff', 'international', 'tournament'].indexOf(comps.find(c => c.id === cid).type);
  const de = rows.filter(r => comps.find(c => c.id === r.id).country === 'DE').map(r => comps.find(c => c.id === r.id));
  check('Inside a country: leagues by level, then cups, super cups and play-offs',
    de.every((c, i) => !i || order(de[i - 1].id) < order(c.id) || (order(de[i - 1].id) === order(c.id) && (de[i - 1].level || 99) <= (c.level || 99))),
    de.map(c => c.name).join(' | '));
  check('A competition with no info row says "Not researched yet" in the list; one with rows does not',
    rows.every(r => researched.has(r.id) ? !/Not researched yet/.test(r.st) : /Not researched yet/.test(r.st)));
  let s = await page.evaluate(() => { const el = document.getElementById('pane-competitions'); return {sw: el.scrollWidth, cw: el.clientWidth, doc: document.documentElement.scrollWidth}; });
  check('The Competitions tab does not scroll sideways', s.sw <= s.cw + 1 && s.doc <= W + 1);
  check('The chip reads "n of total"', new RegExp(`${comps.length} of ${comps.length}\\b`).test(await page.textContent('#cfChip')));

  // ---------------------------------------------------------------- sheets
  const open = async id => {
    await page.click(`#compBody .comprow[data-id="${id}"]`);
    await page.waitForSelector('#csheet:not([hidden])');
    await page.waitForTimeout(350);      // the sheet slides up for 220 ms
    return page.evaluate(() => ({
      text: document.getElementById('csheetBody').innerText,
      head: document.getElementById('csheetHead').innerText,
      topics: [...document.querySelectorAll('#csheetBody h4')].map(h => h.textContent),
      blocks: [...document.querySelectorAll('#csheetBody [data-status]')].map(b => ({topic: b.dataset.topic, status: b.dataset.status,
        label: b.querySelector('.tag').textContent.trim(), text: b.querySelector('.cpara').textContent,
        links: [...b.querySelectorAll('[data-f=source] a')].map(a => a.href), checked: (b.querySelector('[data-f=checked]') || {}).textContent || '',
        hasSource: !!b.querySelector('[data-f=source]')})),
      wide: document.getElementById('csheetBody').scrollWidth > document.getElementById('csheetBody').clientWidth + 1 ||
        document.getElementById('csheet').getBoundingClientRect().right > innerWidth + 1,
      above: document.getElementById('csheet').getBoundingClientRect().bottom <= document.querySelector('nav').getBoundingClientRect().top + 1}));
  };
  const close = async () => { await page.click('#csheetClose'); await page.waitForSelector('#csheet[hidden]', {state: 'attached'}); };

  const none = comps.find(c => !researched.has(c.id));
  if(none){
    const o = await open(none.id);
    check(`An unresearched competition (${none.name}) shows only "Not researched yet"`, /Not researched yet/.test(o.text) && !o.topics.length && !o.blocks.length, o.text.slice(0, 120));
    await close();
  }else check('there is an unresearched competition to check', false, 'every competition has info rows');

  const pokal = comps.find(c => c.id === 'de-dfb-pokal');
  check('data has a DFB-Pokal competition with researched rows', !!pokal && researched.has('de-dfb-pokal'));
  let allFuture = [];
  for(const c of comps.filter(c => researched.has(c.id))){
    const mine = info.filter(r => r.competitionId === c.id);
    const o = await open(c.id);
    const idx = o.blocks.map(b => TOPICS.indexOf(b.topic));
    check(`${c.name}: the seven topics in the fixed order`, o.topics.length === TOPICS.length && idx.every((v, i) => !i || idx[i - 1] <= v) &&
      o.blocks.length === mine.length, o.topics.join(' | '));
    const fine = mine.every(r => {
      const b = o.blocks.find(x => x.topic === r.topic && x.status === r.status && x.text.startsWith(r.text.slice(0, 40)));
      if(!b) return false;
      const urls = r.sourceId.split(';').map(x => x.trim()).filter(Boolean).map(id => sources[id]?.url);
      return b.label === STATUS[r.status] && urls.length && urls.every(u => b.links.includes(u)) &&
        b.checked === (r.checkedOn ? 'Checked on ' + wordsOf(r.checkedOn) : 'No check date recorded');
    });
    check(`${c.name}: every row has its status label, its source link(s) and "Checked on <date>"`, fine,
      JSON.stringify(o.blocks.map(b => [b.topic, b.label, b.links.length, b.checked])).slice(0, 300));
    check(`${c.name}: the topics without a row say "Not researched yet"`,
      TOPICS.filter(t => !mine.some(r => r.topic === t)).length === (o.text.match(/Not researched yet/g) || []).length);
    check(`${c.name}: the sheet fits 390 px and sits above the bottom bar`, !o.wide && o.above);
    allFuture.push(...futureDays(o.text).map(d => `${c.id}: ${d}`));
    await close();
  }
  check('No day-level future date renders in any sheet', !allFuture.length, allFuture.join(' | '));
  check('No day-level future date in the list', !futureDays(await page.innerText('#compBody')).length);

  // ---------------------------------------------------------------- the filter and the search
  await page.click('#cfChip');
  await page.waitForSelector('#filterPanel:not([hidden])');
  const facets = await page.$$eval('#fpBody .fopt', bs => bs.map(b => ({v: b.dataset.v, n: +b.querySelector('em').textContent})));
  const want = {}; for(const c of comps) want[c.country || '~'] = (want[c.country || '~'] || 0) + 1;
  check('Competition filter: Country shows only countries that exist, with counts',
    JSON.stringify(facets.map(f => [f.v, f.n]).sort()) === JSON.stringify(Object.entries(want).sort()));
  check('Competition filter: there is no Type group (the country filter only)', (await page.$$eval('#fpBody .covc', d => d.map(x => x.textContent))).join() === 'Country');
  await page.click('#fpBody .fopt[data-v=DE]');
  const deIds = comps.filter(c => c.country === 'DE').map(c => c.id);
  const got = await page.$$eval('#compBody .comprow', bs => bs.map(b => b.dataset.id));
  check('Country = Germany lists exactly the German competitions', got.length === deIds.length && got.every(i => deIds.includes(i)), `${got.length} of ${deIds.length}`);
  check('The chip follows', new RegExp(`${deIds.length} of ${comps.length}\\b`).test(await page.textContent('#cfChip')));
  await page.click('#fpClose');
  await page.fill('#compSearch', 'zzzzqq');
  check('An empty result says "No competitions match" with a reset button',
    /No competitions match/.test(await page.textContent('#compBody')) && !!(await page.$('#compBody [data-freset=comp]')));
  await page.click('#compBody [data-freset=comp]');
  await page.waitForTimeout(150);
  check('"Show all" clears the filter and the search',
    (await page.$$eval('#compBody .comprow', bs => bs.length)) === comps.length && (await page.inputValue('#compSearch')) === '');
  const probe = comps.find(c => c.name.length > 5);
  await page.fill('#compSearch', probe.name.slice(0, 5).toUpperCase());
  const found = await page.$$eval('#compBody .comprow', bs => bs.map(b => b.dataset.id));
  check('The name search finds a competition by the start of its name, ignoring case', found.includes(probe.id) && found.length < comps.length, `${found.length} for "${probe.name.slice(0, 5)}"`);
  await page.fill('#compSearch', '');
  s = await page.evaluate(() => ({doc: document.documentElement.scrollWidth}));
  check('No sideways scroll after filtering', s.doc <= W + 1);
  await page.click('nav button[data-pane=me]');
  check('Leaving the tab closes the sheet and the filter panel', await page.evaluate(() => document.getElementById('csheet').hidden && document.getElementById('filterPanel').hidden));

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
