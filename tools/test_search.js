// Headless Chromium test of the map's club search, at phone width (390x844) with the keyboard open.
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright            (anywhere; it is not a dependency of this repo)
//   node tools/test_search.js .       (serves the checkout itself; it changes no file)
//
// The keyboard: headless Chromium has none, so it is stood in for by shrinking the window to
// 390x500 once the box is focused - what a phone does when the keyboard resizes the page. The
// other Android behaviour, the keyboard covering the page without resizing it, is covered by the
// list's cap at the visible height (--vvh); that cap is checked to follow the visible height,
// but no real keyboard has been opened. Checks: the box sits top right; typing matches as you
// type, ignoring case and diacritics ("timisoara" finds "Timișoara"); each suggestion carries a
// country and a competition; only clubs on the map are offered; a no-match says so; with the
// keyboard open the list ends above it and its first row can be tapped; Enter, the arrow keys
// and a tap each fly to the club at a zoom where it is drawn and open its sheet; picking closes
// the keyboard; no sideways scroll; no script error. Stadia's tiles are stubbed.
// CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8769, BASE = `http://localhost:${PORT}/Football/`;
const TYPES = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.csv':'text/csv; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
const results = [];
const check = (name, ok, detail='') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ' :: ' + detail : '')); };

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
  const ctx = await browser.newContext({viewport: {width:390, height:844}, isMobile: true, hasTouch: true,
    deviceScaleFactor: 2, serviceWorkers: 'block'});
  await ctx.route('https://tiles.stadiamaps.com/**', r => r.fulfill({status:200, contentType:'image/png', headers: {'Access-Control-Allow-Origin': '*'}, body: PNG}));
  await ctx.route('https://api.stadiamaps.com/**', r => r.abort());
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(BASE);
  await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  const noSideScroll = () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);
  const hits = () => page.evaluate(() => ({hidden: document.getElementById('searchHits').hidden,
    rows: [...document.querySelectorAll('#searchHits button')].map(b => ({name: b.querySelector('.sn').firstChild.textContent,
      sub: b.querySelector('.rd').textContent})),
    text: document.getElementById('searchHits').textContent}));
  const type = async q => { await page.fill('#searchInput', ''); await page.type('#searchInput', q, {delay: 15}); };

  // ---- where it is
  const box = await page.$eval('#searchBox', el => { const r = el.getBoundingClientRect(); return {top: r.top, right: r.right, left: r.left}; });
  check('the search box is at the top right of the map', box.top < 60 && box.right > 390 - 20 && box.left > 150, JSON.stringify(box));

  // ---- the keyboard opens: focus, then the page shrinks to what is left above it
  await page.tap('#searchInput');
  await page.setViewportSize({width: 390, height: 500});
  await page.waitForTimeout(200);
  check('focusing the box keeps it focused (the keyboard would be up)',
    await page.evaluate(() => document.activeElement === document.getElementById('searchInput')));
  check('the visible-height cap follows the window (--vvh)',
    await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--vvh').trim()) === '500px');

  // ---- matching as you type, without case or diacritics
  await type('timisoara');
  let H = await hits();
  console.log('    "timisoara":', H.rows.map(r => `${r.name} [${r.sub}]`).join('; '));
  check('"timisoara" finds Știința Poli Timișoara', H.rows.some(r => r.name === 'Știința Poli Timișoara'));
  await type('TIMIȘOARA');
  const H2 = await hits();
  check('case and diacritics in the query make no difference', JSON.stringify(H2.rows) === JSON.stringify(H.rows));
  await type('munchen');
  H = await hits();
  check('"munchen" finds FC Bayern München, first', H.rows[0]?.name === 'FC Bayern München', H.rows.map(r => r.name).join('; '));
  await type('Bayern Mun');
  check('suggestions update as you type', (await hits()).rows.length >= 2);
  const all = await page.evaluate(() => {
    const names = new Set(CLUBS.map(c => c.name || c.id));
    return {names: [...names]};
  });
  await type('fc');
  H = await hits();
  check('every suggestion is a club on the map', H.rows.length > 0 && H.rows.every(r => all.names.includes(r.name)), `${H.rows.length} rows`);
  check('every suggestion shows a country and a competition', H.rows.every(r => / · \S/.test(r.sub)), H.rows.map(r => r.sub).join('; '));
  check('the list is short (8 at most) and says how many more there are', H.rows.length <= 8 && /more match/.test(H.text));
  const recorded = await page.evaluate(() => { const c = CLUBS.find(c => !c.competition); return c ? c.name : null; });
  if(recorded){
    await type(recorded);
    H = await hits();
    const row = H.rows.find(r => r.name === recorded);
    check('a club with no recorded competition says "league not recorded", never a guessed name',
      !!row && /league not recorded \(tier \d+\)/.test(row.sub), row ? row.sub : 'not offered');
  }
  // A club in the files that is NOT on the map (no position) must not be offered.
  const offMap = await page.evaluate(async () => {
    for(const f of COUNTRY_FILES){ const d = await (await fetch(f)).json();
      const c = (d.clubs || []).find(c => c.name && (c.lat == null || c.lon == null || c.tier == null) &&
        !CLUBS.some(k => k.name === c.name));
      if(c) return c.name; }
    return null;
  });
  if(offMap){
    await type(offMap);
    H = await hits();
    check(`a club in the files but not on the map ("${offMap}") is not offered`, !H.rows.some(r => r.name === offMap));
  }else console.log('    (every club in the files is on the map, so there is no off-map club to look for)');
  await type('xyzzyq');
  H = await hits();
  check('nothing matching says so', H.rows.length === 0 && /No club on the map matches “xyzzyq”/.test(H.text), H.text);

  // ---- with the keyboard open, the list stays above it and can be tapped
  await type('stuttgart');
  const geo = await page.evaluate(() => {
    const l = document.getElementById('searchHits').getBoundingClientRect();
    const first = document.querySelector('#searchHits button').getBoundingClientRect();
    const el = document.elementFromPoint(first.left + 20, first.top + first.height / 2);
    return {bottom: l.bottom, h: innerHeight, firstOnTop: !!el?.closest('#searchHits button'),
            input: document.getElementById('searchInput').getBoundingClientRect().bottom};
  });
  check('with the keyboard open the list ends above it', geo.bottom <= geo.h, JSON.stringify(geo));
  check('the box itself is in sight above the keyboard', geo.input < geo.h);
  check('the first suggestion is on top and tappable', geo.firstOnTop);
  check('no sideways scroll with the list open', await noSideScroll());
  await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', 'search-keyboard.png')});

  // ---- picking: a tap
  const expectSheet = async (name, how) => {
    await page.waitForFunction(n => !document.getElementById('sheet').hidden &&
      document.querySelector('#sheetHead h3')?.textContent === n, name, {timeout: 8000}).catch(() => {});
    await page.waitForTimeout(300);
    const s = await page.evaluate(n => {
      const c = CLUBS.find(c => c.name === n);
      let drawn = false;
      LAYER.eachLayer(l => { const ll = l.getLatLng(); if(ll.lat === c.lat && ll.lng === c.lon) drawn = true; });
      return {title: document.querySelector('#sheetHead h3')?.textContent, open: !document.getElementById('sheet').hidden,
        zoom: MAP.getZoom(), need: zoomForTier(c.tier), drawn,
        inView: MAP.getBounds().contains([c.lat, c.lon]),
        keyboard: document.activeElement === document.getElementById('searchInput'),
        listHidden: document.getElementById('searchHits').hidden};
    }, name);
    check(`${how} opens the sheet of ${name}`, s.open && s.title === name, JSON.stringify(s));
    check(`${how}: the map is at a zoom where ${name} is drawn, and it is`, s.zoom >= s.need && s.drawn && s.inView, `z${s.zoom}, needs z${s.need}`);
    check(`${how}: the keyboard is closed and the list gone`, !s.keyboard && s.listHidden);
  };
  const tapped = (await hits()).rows[0].name;
  await page.tap('#searchHits button');
  await expectSheet(tapped, 'tapping a suggestion');
  await page.tap('#sheetClose');

  // ---- picking: Enter
  await page.setViewportSize({width: 390, height: 844});
  await page.evaluate(() => MAP.setView([48.8, 9.0], 6, {animate: false}));
  await page.tap('#searchInput');
  await type('kaiserslautern');
  H = await hits();
  await page.keyboard.press('Enter');
  await expectSheet(H.rows[0].name, 'Enter');
  await page.tap('#sheetClose');

  // ---- picking: arrow down, then Enter
  await page.tap('#searchInput');
  await type('Kickers');
  H = await hits();
  if(H.rows.length >= 2){
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    await expectSheet(H.rows[1].name, 'arrow down and Enter');
    await page.tap('#sheetClose');
  }else check('"Kickers" offers at least two clubs, to test the arrow keys', false, H.rows.map(r => r.name).join('; '));

  // ---- a club on a shared ground arrives with its neighbours
  await page.tap('#searchInput');
  await type('Bayern München II');
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => !document.getElementById('sheet').hidden, null, {timeout: 8000});
  await page.waitForTimeout(400);
  const mates = await page.$$eval('#sheetBody .mates button', bs => bs.map(b => b.textContent));
  check('a club on a shared ground opens with "also at this ground"', mates.length >= 1, mates.join(', '));

  check('no sideways scroll', await noSideScroll());
  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
