// Headless Chromium test of the map tab's Near me panel (Clubs and Derbies tabs), at phone width.
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright            (anywhere; it is not a dependency of this repo)
//   node tools/test_nearme.js .       (serves the checkout itself; it changes no file)
//
// Serves the repo at http://localhost:8767/Football/, stubs Stadia's tiles, and checks:
// the Near me chip opens the panel on the Clubs tab and both tabs work; the Clubs list is
// exactly the clubs on the map within the distance (worked out here from the club files,
// independently of the page), nearest first, with name, tier dot, competition, ground and
// the road estimate; the slider, the tier chips and "Show more" change it; no club absent
// from the map appears; tapping a row closes the panel, flies to the club and opens its
// sheet - also for each club of the Grünwalder pair; "Use my location" granted (a mocked
// position in Bucharest gives Romanian clubs), denied, timed out and unavailable; the
// position never reaches storage, the URL or any request, and a reload forgets it; the top
// row (club count, search, home, Route, Near me) does not overlap or cut off at 390x700
// and 390x500; no sideways scroll. It also prints how long the list takes to draw at
// 500 km with the CPU slowed 4x. Exits 1 on any failure.
// CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8767, BASE = `http://localhost:${PORT}/Football/`;
const TYPES = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.csv':'text/csv; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
const results = [];
const check = (name, ok, detail='') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ' :: ' + detail : '')); };

// A position in Bucharest, chosen with digits nothing else in the page carries.
const BUC = {latitude: 44.43217, longitude: 26.10398};
const BUC_MARKS = ['44.432', '26.103', '44,432', '26,103'];

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

// ---- the expected list, worked out from the files, not from the page
const rules = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/football-rules.json'), 'utf8'));
const HOME = rules.settings?.home, MULT = rules.settings?.estimateMultiplier ?? 1.25;
const FILE_CLUBS = [];
for(const f of fs.readdirSync(path.join(ROOT, 'data/clubs')).filter(f => /^[A-Z]{2}\.json$/.test(f))){
  const d = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/clubs', f), 'utf8'));
  for(const c of d.clubs || []) FILE_CLUBS.push({...c, country: d.country});
}
const DRAWABLE = FILE_CLUBS.filter(c => c.lat != null && c.lon != null && c.tier != null);
const UNPLACED = new Set(FILE_CLUBS.filter(c => c.lat == null || c.lon == null).map(c => c.id));
function hav(a, b, c, d){
  const R = 6371, r = Math.PI/180, x = Math.sin((c-a)*r/2)**2 + Math.cos(a*r)*Math.cos(c*r)*Math.sin((d-b)*r/2)**2;
  return 2*R*Math.asin(Math.sqrt(x));
}
const within = (from, km) => DRAWABLE.filter(c => Math.round(hav(from.lat, from.lon, c.lat, c.lon) * MULT) <= km);

async function newPage(browser, opts = {}){
  const ctx = await browser.newContext({viewport: opts.viewport || {width:390, height:844}, isMobile: true, hasTouch: true,
    deviceScaleFactor: 2, serviceWorkers: 'block', ...(opts.ctx || {})});
  await ctx.route('https://tiles.stadiamaps.com/**', r => r.fulfill({status:200, contentType:'image/png',
    headers: {'Access-Control-Allow-Origin': '*'}, body: PNG}));
  await ctx.route('https://api.stadiamaps.com/**', r => r.abort());
  if(opts.init) await ctx.addInitScript(opts.init);
  const page = await ctx.newPage();
  page._errors = [];
  page.on('pageerror', e => page._errors.push(e.message));
  page._requests = [];
  page.on('request', r => page._requests.push(r.url() + ' ' + (r.postData() || '') + ' ' + JSON.stringify(r.headers())));
  await page.goto(BASE);
  // the zoom chip is written once every club file has been read
  await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  return page;
}

const openNear = async page => {
  if(await page.evaluate(() => document.getElementById('nearPanel').hidden)) await page.tap('#nearChip');
  await page.waitForSelector('#nearBody #nearCount');
  await page.waitForTimeout(400);                      // the panel slides up for 0.22 s
};
const rowsOf = page => page.evaluate(() => [...document.querySelectorAll('#nearList .rclub')].map(b => ({
  id: b.dataset.id, name: b.querySelector('.rn').firstChild.textContent,
  rd: [...b.querySelectorAll('.rd')].map(x => x.textContent),
  km: Number(b.querySelector('.nkm').textContent.match(/≈ (\d+) km/)[1]),
  dot: b.querySelector('i').style.background})));
const count = page => page.$eval('#nearCount', el => el.textContent);
const setKm = (page, km) => page.$eval('#nearKm', (el, km) => { el.value = String(km); el.dispatchEvent(new Event('input')); }, km);
async function allRows(page){
  while(await page.$('#nearMore')) await page.$eval('#nearMore', b => b.click());
  return rowsOf(page);
}
const sorted = rows => rows.every((r, i) => !i || rows[i-1].km <= r.km);

(async () => {
  await new Promise(r => server.listen(PORT, r));
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || undefined, headless: true});

  // ================================================================ 1. tabs, list, filters
  let page = await newPage(browser);
  await page.tap('#nearChip');
  await openNear(page);
  let st = await page.evaluate(() => ({
    panelUp: document.getElementById('nearPanel').getBoundingClientRect().top < innerHeight - 100,
    clubsOn: document.getElementById('tabClubs').getAttribute('aria-selected') === 'true' && !document.getElementById('nearBody').hidden &&
      document.getElementById('derbyBody').hidden,
    from: document.getElementById('nearFrom').textContent, title: document.getElementById('derbyTitle').textContent,
    locBtn: document.getElementById('nearLocate')?.textContent, stays: /Your location stays on this device\./.test(document.getElementById('nearBody').textContent),
    km: document.getElementById('nearKm').value, min: document.getElementById('nearKm').min, max: document.getElementById('nearKm').max,
    tiers: [...document.querySelectorAll('.ntiers button')].map(b => [Number(b.dataset.tier), b.getAttribute('aria-pressed')]),
    notTravel: /not a travel time/.test(document.getElementById('nearBody').textContent)}));
  check('Near me opens the panel on screen, Clubs tab first', st.panelUp && st.clubsOn, JSON.stringify(st));
  check('origin line reads "From: <home> (home)" with a "Use my location" button',
    st.from === `From: ${HOME.label} (home)` && st.locBtn === 'Use my location', `${st.from} / ${st.locBtn}`);
  check('the panel says "Your location stays on this device."', st.stays);
  check('slider defaults to 100 km, range 10-500', st.km === '100' && st.min === '10' && st.max === '500', `${st.km} ${st.min}-${st.max}`);
  const dataTiers = [...new Set(DRAWABLE.map(c => c.tier))].sort((a, b) => a - b);
  check('one tier chip per tier on the map, all on', JSON.stringify(st.tiers.map(t => t[0])) === JSON.stringify(dataTiers) &&
    st.tiers.every(t => t[1] === 'true'), JSON.stringify(st.tiers));
  check('the "not a travel time" wording is there', st.notTravel);

  let rows = await allRows(page);
  const exp100 = within(HOME, 100);
  const byTier = {};
  for(const c of exp100) byTier[c.tier] = (byTier[c.tier] || 0) + 1;
  console.log(`    within 100 km of ${HOME.label}: ${exp100.length} clubs - ` +
    Object.entries(byTier).map(([t, n]) => `tier ${t}: ${n}`).join(', '));
  check('the list is exactly the clubs on the map within 100 km (worked out from the club files)',
    rows.length === exp100.length && exp100.every(c => rows.some(r => r.id === c.id)), `${rows.length} listed, ${exp100.length} expected`);
  check('count line reads "N clubs within 100 km"', await count(page) === `${exp100.length} clubs within 100 km`, await count(page));
  check('nearest first', sorted(rows));
  check('every distance is within 100 km and reads "by road (estimate)"',
    rows.every(r => r.km <= 100 && /≈ \d+ km by road \(estimate\)$/.test(r.rd[2])));
  const fileById = new Map(FILE_CLUBS.map(c => [c.id, c]));
  check('each row shows the club\'s competition (or "league not recorded (tier N)") and its ground', rows.every(r => {
    const c = fileById.get(r.id);
    return r.name === (c.name || c.id) && r.rd[0] === (c.competition || `league not recorded (tier ${c.tier})`) &&
      r.rd[1] === (c.venue || 'ground not recorded');
  }));
  check('each row has its tier\'s colour dot', await page.evaluate(() => [...document.querySelectorAll('#nearList .rclub')].every(b => {
    const c = CLUBS.find(x => x.id === b.dataset.id), probe = document.createElement('i');
    probe.style.background = 'var(--t' + c.tier + ')'; return b.querySelector('i').style.background === probe.style.background;
  })));
  const exactDist = rows.every(r => { const c = fileById.get(r.id);
    return r.km === Math.round(hav(HOME.lat, HOME.lon, c.lat, c.lon) * MULT); });
  check('distance is straight line × the settings multiplier, from home', exactDist);

  // the slider
  await setKm(page, 50);
  rows = await allRows(page);
  check('slider at 50 km: fewer clubs, all within 50 km, still nearest first',
    rows.length === within(HOME, 50).length && rows.length < exp100.length && rows.every(r => r.km <= 50) && sorted(rows),
    `${rows.length} at 50 km`);
  await setKm(page, 10);
  const none = await page.$eval('#nearList', el => el.textContent);
  check('nothing in range says "No clubs within 10 km. Widen the distance."',
    within(HOME, 10).length ? true : /No clubs within 10 km\. Widen the distance\./.test(none), none.slice(0, 120));

  // the tier filter, at 500 km
  await setKm(page, 500);
  let first = await rowsOf(page);
  const exp500 = within(HOME, 500);
  check('500 km: the first 50 rows, and a "Show more" button', first.length === Math.min(50, exp500.length) &&
    (exp500.length <= 50 || !!await page.$('#nearMore')), `${first.length} shown of ${exp500.length}`);
  await page.$eval('#nearMore', b => b.click());
  check('"Show more" adds the next 50', (await rowsOf(page)).length === Math.min(100, exp500.length));
  rows = await allRows(page);
  check('500 km: every club on the map within 500 km, none other', rows.length === exp500.length &&
    new Set(rows.map(r => r.id)).size === rows.length && exp500.every(c => rows.some(r => r.id === c.id)), `${rows.length}/${exp500.length}`);
  check('no club absent from the map appears (none without a position, none outside the club files)',
    rows.every(r => !UNPLACED.has(r.id) && DRAWABLE.some(c => c.id === r.id)));
  check('...and every listed club is drawn at z9', await page.evaluate(ids => {
    MAP.setView(MAP.getCenter(), 9, {animate: false});
    const drawn = new Set(CLUBS.filter(c => zoomForTier(c.tier) <= 9).map(c => c.id));
    return ids.every(id => drawn.has(id));
  }, rows.map(r => r.id)));
  const t4 = exp500.filter(c => c.tier === 4).length;
  await page.tap('.ntiers button[data-tier="4"]');
  rows = await allRows(page);
  check('turning tier 4 off removes the tier 4 clubs, and only them',
    rows.length === exp500.length - t4 && rows.every(r => fileById.get(r.id).tier !== 4) && sorted(rows) &&
    await page.$eval('.ntiers button[data-tier="4"]', b => b.getAttribute('aria-pressed')) === 'false', `${rows.length} left`);
  await page.tap('.ntiers button[data-tier="4"]');
  check('turning it back on restores the list', (await allRows(page)).length === exp500.length);
  for(const t of dataTiers) await page.$eval(`.ntiers button[data-tier="${t}"]`, b => b.click());
  check('every tier off says so and lists nothing', (await rowsOf(page)).length === 0 &&
    /in the tiers chosen/.test(await page.$eval('#nearList', el => el.textContent)));
  for(const t of dataTiers) await page.$eval(`.ntiers button[data-tier="${t}"]`, b => b.click());
  check('no sideways scroll with the list open', await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));

  // timing at 500 km, CPU slowed 4x
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', {rate: 4});
  const times = await page.evaluate(async () => {
    const el = document.getElementById('nearKm'), out = [], empty = [];
    const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    for(let i = 0; i < 8; i++){ const t0 = performance.now(); await frame(); empty.push(performance.now() - t0); }
    for(let i = 0; i < 16; i++){
      el.value = i % 2 ? '500' : '490';
      await frame();
      const t0 = performance.now();
      el.dispatchEvent(new Event('input'));
      const t1 = performance.now();
      await frame();
      if(el.value === '500') out.push([t1 - t0, performance.now() - t0]);
    }
    return {out, empty: empty.sort((a, b) => a - b)[4]};
  });
  await cdp.send('Emulation.setCPUThrottlingRate', {rate: 1});
  const med = a => a.slice().sort((x, y) => x - y)[Math.floor(a.length / 2)];
  const T = times.out;
  console.log(`    500 km (${exp500.length} clubs, first 50 drawn), CPU 4x, median of ${T.length}: list built in ` +
    `${med(T.map(t => t[0])).toFixed(1)} ms (worst ${Math.max(...T.map(t => t[0])).toFixed(1)}); to the painted frame ` +
    `${med(T.map(t => t[1])).toFixed(1)} ms (worst ${Math.max(...T.map(t => t[1])).toFixed(1)}), of which an empty ` +
    `two-frame wait is ${times.empty.toFixed(1)} ms - measured, not judged`);

  // the Derbies tab, and back
  await page.tap('#tabDerbies');
  await page.waitForSelector('#derbyBody h4');
  st = await page.evaluate(() => ({derbies: !document.getElementById('derbyBody').hidden && document.getElementById('nearBody').hidden,
    title: document.getElementById('derbyTitle').textContent, head: document.querySelector('#derbyBody h4').textContent}));
  check('the Derbies tab shows the derby list', st.derbies && st.title === 'Derbies near home' && /within 100 km/.test(st.head), JSON.stringify(st));
  await page.tap('#tabClubs');
  st = await page.evaluate(() => ({clubs: !document.getElementById('nearBody').hidden && document.getElementById('derbyBody').hidden,
    km: document.getElementById('nearKm').value}));
  check('the Clubs tab comes back with its distance kept', st.clubs && st.km === '500', JSON.stringify(st));

  // ================================================================ 2. tapping a row
  await setKm(page, 100);
  rows = await rowsOf(page);
  const target = rows[0];
  await page.tap(`#nearList .rclub[data-id="${target.id}"]`);
  await page.waitForFunction(() => !document.getElementById('sheet').hidden, null, {timeout: 5000});
  await page.waitForTimeout(1500);                     // the fly takes 0.8 s
  st = await page.evaluate(id => {
    const c = CLUBS.find(x => x.id === id);
    return {panel: document.getElementById('nearPanel').hidden, head: document.querySelector('#sheetHead h3').textContent,
      zoom: MAP.getZoom(), want: Math.max(zoomForTier(c.tier), 10), inView: MAP.getBounds().contains([c.lat, c.lon])};
  }, target.id);
  check(`tapping a row closes the panel, flies to the club and opens its sheet (${target.name})`,
    st.panel && st.head === target.name && st.zoom === st.want && st.inView, JSON.stringify(st));

  for(const [id, other] of [['Q131603', 'Q994701'], ['Q994701', 'Q131603']]){
    await page.tap('#nearChip');
    await openNear(page);
    await setKm(page, 300);
    while(!await page.$(`#nearList .rclub[data-id="${id}"]`) && await page.$('#nearMore')) await page.$eval('#nearMore', b => b.click());
    const name = fileById.get(id).name, otherName = fileById.get(other).name;
    if(!await page.$(`#nearList .rclub[data-id="${id}"]`)){ check(`shared ground: ${name} is listed at 300 km`, false); continue; }
    await page.tap(`#nearList .rclub[data-id="${id}"]`);
    await page.waitForFunction(n => !document.getElementById('sheet').hidden &&
      document.querySelector('#sheetHead h3')?.textContent === n, name, {timeout: 5000}).catch(() => {});
    await page.waitForTimeout(1200);
    st = await page.evaluate(() => ({head: document.querySelector('#sheetHead h3').textContent, panel: document.getElementById('nearPanel').hidden,
      mates: [...document.querySelectorAll('#sheetBody .mates button')].map(b => b.textContent)}));
    check(`shared ground (Grünwalder): tapping ${name} opens its own sheet, ${otherName} listed as also there`,
      st.head === name && st.panel && st.mates.includes(otherName), JSON.stringify(st));
  }
  check('no script error (list, tabs, taps)', !page._errors.length, page._errors.join(' | '));
  await page.context().close();

  // ================================================================ 3. Use my location: granted
  page = await newPage(browser, {ctx: {permissions: ['geolocation'], geolocation: BUC}});
  const reqBefore = page._requests.length;
  await page.tap('#nearChip');
  await openNear(page);
  await page.tap('#nearLocate');
  await page.waitForFunction(() => /your current location/.test(document.getElementById('nearFrom').textContent), null, {timeout: 10000});
  st = await page.evaluate(() => ({from: document.getElementById('nearFrom').textContent, back: !!document.getElementById('nearHome'),
    title: document.getElementById('derbyTitle').textContent}));
  rows = await allRows(page);
  const expBuc = within({lat: BUC.latitude, lon: BUC.longitude}, 100);
  check('granted: origin reads "From: your current location (approx.)" with "Back to home"',
    st.from === 'From: your current location (approx.)' && st.back, JSON.stringify(st));
  check('granted: Bucharest gives Romanian clubs only, the list re-sorted from there', rows.length > 0 &&
    rows.every(r => fileById.get(r.id).country === 'RO') && rows.length === expBuc.length && sorted(rows),
    `${rows.length} clubs, ${[...new Set(rows.map(r => fileById.get(r.id).country))].join(',')}`);
  check('granted: distances read "from your location"', rows.every(r => /by road from your location \(estimate\)$/.test(r.rd[2])));
  // the position: never in storage, the URL or a request
  const stored = await page.evaluate(async () => {
    const out = [location.href, document.cookie, JSON.stringify({...localStorage}), JSON.stringify({...sessionStorage})];
    for(const db of (await indexedDB.databases?.()) || []){
      const d = await new Promise(r => { const q = indexedDB.open(db.name); q.onsuccess = () => r(q.result); q.onerror = () => r(null); });
      if(!d) continue;
      for(const s of d.objectStoreNames){
        out.push(JSON.stringify(await new Promise(r => { const q = d.transaction(s).objectStore(s).getAll(); q.onsuccess = () => r(q.result); q.onerror = () => r([]); })));
      }
      d.close();
    }
    for(const k of await caches.keys()) out.push(k);
    return out.join('\n');
  });
  // open a club's sheet too: it loads fixture files, which must not carry the position either
  await page.tap('#nearList .rclub');
  await page.waitForFunction(() => !document.getElementById('sheet').hidden);
  await page.waitForTimeout(1500);
  const sent = page._requests.slice(reqBefore).join('\n');
  check('the position is in no storage, cookie or URL', !BUC_MARKS.some(m => stored.includes(m)));
  check(`the position is in no request (${page._requests.length - reqBefore} made after it was asked)`, !BUC_MARKS.some(m => sent.includes(m)));
  await page.tap('#nearChip');
  await openNear(page);
  await page.tap('#nearHome');
  st = await page.evaluate(() => ({from: document.getElementById('nearFrom').textContent, loc: document.getElementById('nearLocate').textContent}));
  rows = await allRows(page);
  check('"Back to home" restores home and the home list', st.from === `From: ${HOME.label} (home)` && st.loc === 'Use my location' &&
    rows.length === exp100.length, JSON.stringify(st));
  await page.tap('#nearLocate');
  await page.waitForFunction(() => /your current location/.test(document.getElementById('nearFrom').textContent));
  await page.reload();
  await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent));
  await page.tap('#nearChip');
  await openNear(page);
  check('a reload forgets the position', await page.$eval('#nearFrom', el => el.textContent) === `From: ${HOME.label} (home)`);
  check('no script error (granted)', !page._errors.length, page._errors.join(' | '));
  await page.context().close();

  // ================================================================ 4. denied, timed out, unavailable
  const failures = [
    ['denied', 'Location was not allowed', null],
    ['timed out', 'took too long', `navigator.geolocation.getCurrentPosition = (ok, err, opt) => {
       window.__geoOpt = opt; setTimeout(() => err({code: 3, message: 'Timeout expired'}), 1200); };`],
    ['unavailable', 'could not be found', `navigator.geolocation.getCurrentPosition = (ok, err) =>
       setTimeout(() => err({code: 2, message: 'Position unavailable'}), 300);`],
    ['not supported', 'cannot share a location', `Object.defineProperty(Navigator.prototype, 'geolocation', {get: () => undefined});`],
  ];
  for(const [kind, words, init] of failures){
    page = await newPage(browser, {init});
    if(kind === 'denied'){
      // No permission granted: Chromium refuses the request, as when a person taps "Block".
      await page.context().clearPermissions();
    }
    await page.tap('#nearChip');
    await openNear(page);
    await page.tap('#nearLocate');
    if(kind === 'timed out'){
      st = await page.evaluate(() => ({msg: document.getElementById('nearMsg').textContent, dis: document.getElementById('nearLocate').disabled}));
      check('while waiting, "Finding your location…" shows and the button is disabled', st.msg === 'Finding your location…' && st.dis, JSON.stringify(st));
    }
    await page.waitForFunction(() => !/Finding/.test(document.getElementById('nearMsg').textContent) &&
      document.getElementById('nearMsg').textContent.length > 0, null, {timeout: 20000}).catch(() => {});
    st = await page.evaluate(() => ({msg: document.getElementById('nearMsg').textContent, from: document.getElementById('nearFrom').textContent,
      opt: window.__geoOpt || null}));
    rows = await allRows(page);
    check(`${kind}: a plain message, and the list stays on home`, st.msg.includes(words) && /stays on home/.test(st.msg) &&
      st.from === `From: ${HOME.label} (home)` && rows.length === exp100.length, JSON.stringify(st));
    if(kind === 'timed out') check('the request asks with a time limit', st.opt && Number.isFinite(st.opt.timeout) && st.opt.timeout <= 30000,
      JSON.stringify(st.opt));
    check(`no script error (${kind})`, !page._errors.length, page._errors.join(' | '));
    await page.context().close();
  }

  // ================================================================ 5. opened before every club file has loaded
  {
    const ctx = await browser.newContext({viewport: {width:390, height:844}, isMobile: true, hasTouch: true, serviceWorkers: 'block'});
    await ctx.route('https://tiles.stadiamaps.com/**', r => r.fulfill({status:200, contentType:'image/png', headers: {'Access-Control-Allow-Origin': '*'}, body: PNG}));
    await ctx.route('https://api.stadiamaps.com/**', r => r.abort());
    // Germany is read first and holds every tier, so it is served here with its tier 1 clubs only:
    // tiers 2-4 then arrive only with the later files, each held back 1 s (they load one after another).
    const de = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/clubs/DE.json'), 'utf8'));
    de.clubs = de.clubs.filter(c => c.tier === 1);
    await ctx.route(/data\/clubs\/DE\.json/, r => r.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify(de)}));
    await ctx.route(/data\/clubs\/(?!DE)[A-Z]{2}\.json/, async r => { await new Promise(x => setTimeout(x, 1000)); r.continue(); });
    const lateTiers = [...new Set(DRAWABLE.filter(c => c.country !== 'DE' || c.tier === 1).map(c => c.tier))].sort((a, b) => a - b);
    const p = await ctx.newPage();
    const errs = []; p.on('pageerror', e => errs.push(e.message));
    await p.goto(BASE);
    await p.waitForFunction(() => typeof CLUBS !== 'undefined' && CLUBS.length > 0, null, {timeout: 30000});
    await p.tap('#nearChip');
    await p.waitForSelector('#nearBody #nearCount');
    const early = await p.evaluate(() => new Set(CLUBS.map(c => c.country)).size);
    await p.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 60000});
    await p.tap('#tabDerbies'); await p.tap('#tabClubs');
    const tiers = await p.$$eval('.ntiers button', bs => bs.map(b => [Number(b.dataset.tier), b.getAttribute('aria-pressed')]));
    console.log(`    the panel opened with ${early} of 12 country files read`);
    await setKm(p, 500);                               // within 100 km of Leonberg every club is German
    const rowsLate = await allRows(p);
    check('opened before every club file loaded: a tier that loaded later has its chip, on, and its clubs listed',
      JSON.stringify(tiers.map(t => t[0])) === JSON.stringify(lateTiers) && tiers.every(t => t[1] === 'true') &&
      rowsLate.some(r => fileById.get(r.id).tier !== 1), JSON.stringify(tiers) + ` ${rowsLate.length} rows`);
    check('no script error (early open)', !errs.length, errs.join(' | '));
    await ctx.close();
  }

  // ================================================================ 6. the top row at 390x700 and 390x500
  for(const height of [700, 500]){
    page = await newPage(browser, {viewport: {width: 390, height}});
    for(const z of [3, 8, 9, 10, 13]){
      await page.evaluate(z => MAP.setView([48.80, 9.02], z, {animate: false}), z);
      await page.waitForTimeout(150);
      const r = await page.evaluate(() => {
        const ids = ['zoomChip', 'searchInput', 'homeChip', 'routeChip', 'nearChip'];
        const box = id => document.getElementById(id).getBoundingClientRect();
        const bad = [];
        for(let i = 0; i < ids.length; i++){
          const a = box(ids[i]);
          if(a.left < 0 || a.right > innerWidth || a.top < 0 || a.width < 1) bad.push(`${ids[i]} off screen`);
          for(let j = i + 1; j < ids.length; j++){
            const b = box(ids[j]);
            if(a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom) bad.push(`${ids[i]} overlaps ${ids[j]}`);
          }
          const el = document.getElementById(ids[i]);
          if(el.tagName !== 'INPUT' && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)) bad.push(`${ids[i]} text cut off`);
        }
        // The search box's placeholder must fit inside the box.
        const inp = document.getElementById('searchInput'), cs = getComputedStyle(inp);
        const ctx = document.createElement('canvas').getContext('2d');
        ctx.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
        const room = inp.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
        const need = ctx.measureText(inp.placeholder).width;
        if(need > room) bad.push(`search placeholder cut off (${need.toFixed(0)} > ${room.toFixed(0)} px)`);
        return {bad, chip: document.getElementById('zoomChip').textContent,
          widths: ids.map(id => `${id} ${Math.round(box(id).width)}`).join(', '),
          rows: [box('zoomChip').top, box('homeChip').top].map(Math.round)};
      });
      console.log(`    390x${height} z${z}: "${r.chip}" - ${r.widths}`);
      check(`top row at 390x${height}, z${z}: no overlap, nothing cut off or off screen`, !r.bad.length, r.bad.join('; '));
    }
    await page.tap('#nearChip');
    await openNear(page);
    check(`no sideways scroll at 390x${height} with the panel open`, await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1 &&
      document.getElementById('nearPanel').scrollWidth <= document.getElementById('nearPanel').clientWidth + 1));
    const tabs = await page.evaluate(() => [...document.querySelectorAll('.ntabs button')].map(b => b.getBoundingClientRect())
      .every(r => r.top >= 0 && r.bottom <= innerHeight && r.height >= 36));
    check(`both tabs fully on screen and tappable at 390x${height}`, tabs);
    await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', `nearme-390x${height}.png`)});
    check(`no script error (390x${height})`, !page._errors.length, page._errors.join(' | '));
    await page.context().close();
  }

  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
