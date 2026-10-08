// Headless Chromium test of the map tab's route panel and its saved routes, at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page; it can also be run by hand:
//
//   npm install playwright            (anywhere; it is not a dependency of this repo)
//   node tools/test_routes.js . /tmp  (serves the checkout itself; it changes no file;
//                                      the second argument is where a browser profile goes)
//
// Serves the repo at http://localhost:8767/Football/ and stubs EVERY Stadia request: tiles, place
// search (two canned answers) and routing (a canned Leonberg-Munich line), counting each one, so it
// spends no credit. Checks: a search and a route; the same search again answered from the device's
// saved copy with no request, and asked again once the copy is 8 days old; saving a route (name,
// encoded line, ends, options, length, time, dates, NO club list; a searched end kept as the typed
// words and the line's own end point, never the search answer); a reload; opening the saved route
// with no request and the same club list worked out again; rename; route back with no request,
// labelled approximate; refresh at one request; the credit estimate; opening it offline (club list
// works, map shows its needs-a-connection card); export to a file, delete, import, a bad file
// refused, a second import left alone; a second tab in the same profile seeing the same routes; no
// sideways scroll; no script error. Since the fuel cost estimate: the one-way range for the known
// 268.4 km route at made-up test prices (DE 2.000, RO 1.500 - a fixture served in place of
// data/fuel-prices.json, not a real price), a manual price (decimal comma) overriding it, bad numbers
// refused, the allowance on its own line, the "Enter a diesel price" message, the same range on a
// saved route "at current settings" and following the settings, an older saved route with no
// distance showing none and asking Stadia for nothing, the tolls/ferries line, and no sideways scroll
// with the cost block open. Exits 1 on any failure.
// CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const TMP = process.argv[3] || require('os').tmpdir();
const PORT = 8767, BASE = `http://localhost:${PORT}/Football/`;
const TYPES = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.csv':'text/csv; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
const CORS = {'Access-Control-Allow-Origin': '*'};
const results = [];
const check = (name, ok, detail='') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ' :: ' + detail : '')); };

// Valhalla's polyline6, the same encoding the page decodes and stores.
function encode(pts){
  const enc = v => { v = v < 0 ? ~(v << 1) : (v << 1); let s = '';
    while(v >= 0x20){ s += String.fromCharCode((0x20 | (v & 0x1f)) + 63); v >>>= 5; } return s + String.fromCharCode(v + 63); };
  let out = '', a0 = 0, b0 = 0;
  for(const [la, lo] of pts){ const a = Math.round(la * 1e6), b = Math.round(lo * 1e6); out += enc(a - a0) + enc(b - b0); a0 = a; b0 = b; }
  return out;
}
// A made-up road Leonberg - Stuttgart - Ulm - Augsburg - Munich, points every ~1 km.
const WAY = [[48.8003, 9.0167], [48.7758, 9.1829], [48.3984, 9.9916], [48.3705, 10.8978], [48.1351, 11.5820]];
const LINE = [];
for(let i = 1; i < WAY.length; i++) for(let k = 0; k < 60; k++){
  const t = k / 60; LINE.push([WAY[i-1][0] + t * (WAY[i][0] - WAY[i-1][0]), WAY[i-1][1] + t * (WAY[i][1] - WAY[i-1][1])]); }
LINE.push(WAY[WAY.length - 1]);
const SHAPE = encode(LINE);
// The search answers: deliberately NOT on the line's ends, so a save that kept them would show.
const GEO = {
  leonberg: {label: 'Leonberg, Baden-Württemberg, Germany', lat: 48.8011, lon: 9.0144},
  münchen:  {label: 'Munich, Bavaria, Germany', lat: 48.1374, lon: 11.5755}};

// Test fixture served in place of data/fuel-prices.json: invented round prices, so the expected
// ranges below can be worked out by hand. Never a real price.
const FUEL = {fuel: 'diesel', bulletinWeek: '2026-10-05', sourceUrl: 'https://example.invalid/bulletin.xlsx',
  prices: {DE: 2.0, RO: 1.5}, missing: {}};
let TOLL = false;
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(req.url.split('?')[0]);
  if(!p.startsWith('/Football/')){ res.writeHead(404); return res.end(); }
  if(p === '/Football/data/fuel-prices.json'){
    res.writeHead(200, {'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}); return res.end(JSON.stringify(FUEL)); }
  let f = path.join(ROOT, p.slice('/Football/'.length)); if(p.endsWith('/')) f = path.join(f, 'index.html');
  fs.stat(f, (e, st) => {
    if(e || !st.isFile()){ res.writeHead(404); return res.end('nf'); }
    res.writeHead(200, {'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-cache'});
    fs.createReadStream(f).pipe(res);
  });
});

(async () => {
  await new Promise(r => server.listen(PORT, r));
  // A persistent profile: the service worker, IndexedDB and a second tab all live in it, as on a phone.
  const prof = fs.mkdtempSync(path.join(TMP, 'routes-profile-'));
  const ctx = await chromium.launchPersistentContext(prof, {executablePath: process.env.CHROMIUM_PATH || undefined,
    headless: true, viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true, deviceScaleFactor: 2,
    acceptDownloads: true});
  let offline = false;
  const count = {search: 0, route: 0, tile: 0};
  await ctx.route('https://tiles.stadiamaps.com/**', r => { count.tile++;
    return offline ? r.abort('internetdisconnected') : r.fulfill({status: 200, contentType: 'image/png', headers: CORS, body: PNG}); });
  await ctx.route('https://api.stadiamaps.com/**', async r => {
    if(offline) return r.abort('internetdisconnected');
    const u = new URL(r.request().url());
    if(r.request().method() === 'OPTIONS') return r.fulfill({status: 204, headers: {...CORS, 'Access-Control-Allow-Headers': 'content-type', 'Access-Control-Allow-Methods': 'POST'}});
    if(u.pathname.startsWith('/geocoding/v1/search')){
      count.search++;
      const g = GEO[u.searchParams.get('text').toLowerCase()];
      return r.fulfill({status: 200, contentType: 'application/json', headers: CORS, body: JSON.stringify({features: g ?
        [{geometry: {type: 'Point', coordinates: [g.lon, g.lat]}, properties: {label: g.label}}] : []})});
    }
    if(u.pathname.startsWith('/route/v1')){
      count.route++;
      return r.fulfill({status: 200, contentType: 'application/json', headers: CORS, body: JSON.stringify({trip: {
        legs: [{shape: SHAPE}], summary: {length: 268.4, time: 9720, has_toll: TOLL, has_highway: true, has_ferry: false}}})});
    }
    return r.fulfill({status: 404, headers: CORS, body: '{}'});
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const loaded = () => page.waitForFunction(() => typeof CLUBS !== 'undefined' && CLUBS.length > 400 && HOME, null, {timeout: 30000});
  const noSideScroll = () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);
  const pt = (end, sel) => `#routeBody .pt[data-end="${end}"] ${sel}`;
  const clubNames = () => page.$$eval('#routeList .rclub .rn', els => els.map(e => e.firstChild.textContent));
  const routeText = () => page.textContent('#routeOut');
  const idbRoutes = () => page.evaluate(() => new Promise((res, rej) => {
    const r = indexedDB.open('football-planner-device');
    r.onsuccess = () => { const q = r.result.transaction('routes').objectStore('routes').getAll(); q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error); };
    r.onerror = () => rej(r.error); }));
  const openPanel = async () => { await page.click('#routeChip'); await page.waitForTimeout(400); };
  const search = async (end, text) => {
    await page.fill(pt(end, 'input'), text);
    await page.click(pt(end, 'button[data-act="find"]'));
    await page.waitForFunction(s => { const h = document.querySelector(s); return h.querySelector('button') || h.querySelector('.err'); }, pt(end, '.hits'), {timeout: 10000});
  };
  const listReady = () => page.waitForFunction(() => document.querySelector('#routeList h4'), null, {timeout: 15000});

  await page.goto(BASE); await loaded();
  await page.waitForFunction(() => !!navigator.serviceWorker.controller, null, {timeout: 15000});

  // ---- 1. a search and a route
  await openPanel();
  await search('from', 'Leonberg'); await page.click(pt('from', '.hits button'));
  await search('to', 'München');    await page.click(pt('to', '.hits button'));
  check('two place searches asked Stadia twice', count.search === 2, JSON.stringify(count));
  await page.click('#routeGo'); await listReady();
  const fresh = await clubNames();
  check('Get route: one routing request, clubs listed along the line', count.route === 1 && fresh.length > 5 && fresh.some(n => /Augsburg/.test(n)),
    `${fresh.length} clubs, e.g. ${fresh.slice(0, 3).join(', ')}`);
  const defName = await page.inputValue('#routeName');
  check('the suggested name is "Start → End", from the typed words', defName === 'Leonberg → München', defName);

  // ---- 1b. fuel cost: 268.4 km x 7 l/100 km x 2.000 EUR/L = 37.58, 10% either way = 34 to 41
  const costTxt = () => page.textContent('#costResult');
  await page.waitForFunction(() => /fuel estimate/.test(document.getElementById('costResult').textContent), null, {timeout: 8000})
    .catch(async e => { console.log('COST BOX: ' + await page.textContent('#costResult')); throw e; });
  let ct = await costTxt();
  check('cost: known distance gives the range, rounded to whole euros', /One way, fuel estimate: about €34 to €41/.test(ct), ct);
  check('cost: shows distance, consumption, price used, its source and the bulletin week',
    /268 km/.test(ct) && /7 l\/100 km/.test(ct) && /€2\.000\/L/.test(ct) && /EU Weekly Oil Bulletin/.test(ct) && /week of 5 Oct 2026/.test(ct), ct);
  check('cost: no tolls line when Stadia says there are none', !/tolls/.test(ct));
  check('cost: the settings block is in the route result with the default consumption',
    (await page.inputValue('#costL100')) === '7' && /Cost settings/.test(await routeText()));
  await page.fill('#costPrice', '1,5');            // decimal comma, a manual price
  ct = await costTxt();
  check('cost: a manual price (decimal comma) overrides the fetched one: 25 to 31',
    /about €25 to €31/.test(ct) && /€1\.500\/L \(your entry\)/.test(ct) && !/Bulletin week/.test(ct), ct);
  const stored = await page.evaluate(() => [localStorage.getItem('football-planner-route-cost'), localStorage.getItem('football-planner-me')]);
  check('cost: settings kept on the device, and not in the Me tab data', JSON.parse(stored[0]).price === 1.5 && !(stored[1] || '').includes('route-cost'), stored[0]);
  for(const bad of ['abc', '0', '-3', '1,2,3']){
    await page.fill('#costPrice', bad);
    const inv = await page.getAttribute('#costPrice', 'aria-invalid'), msg = await page.textContent('#costMsg');
    check(`cost: "${bad}" is refused, the last good price still used`, inv === 'true' && /above zero/.test(msg) && /about €25 to €31/.test(await costTxt()), msg);
  }
  await page.fill('#costExtra', '0.1');
  ct = await costTxt();
  check('cost: the allowance is on its own line, not in the fuel figure', /Extra allowance \(separate\)/.test(ct) && /about €27/.test(ct) &&
    /about €25 to €31/.test(ct), ct);
  await page.fill('#costExtra', '');
  await page.fill('#costPrice', '');
  ct = await costTxt();
  check('cost: back to the bulletin price once the manual one is cleared', /about €34 to €41/.test(ct), ct);
  await page.evaluate(() => { window.__fuel = FUELDATA; FUELDATA = {...FUELDATA, prices: {}}; renderCost(); });
  ct = await costTxt();
  check('cost: no price at all says to enter one', /Enter a diesel price to see the cost/.test(ct) && !/fuel estimate/.test(ct), ct);
  await page.evaluate(() => { FUELDATA = window.__fuel; renderCost(); });
  check('cost: the route panel with the cost block open does not scroll sideways', await noSideScroll());

  // ---- 2. the same search again: the saved copy, no request
  await search('from', 'leonberg');
  const hitTxt = await page.textContent(pt('from', '.hits'));
  check('a repeated search makes no request and is marked as the saved copy', count.search === 2 && /saved copy/.test(hitTxt) && /no request/.test(hitTxt), hitTxt.trim().slice(0, 120));
  await page.click(pt('from', '.hits button'));

  // ---- 3. save, at a 30 km setting
  await page.$eval('#routeKm', el => { el.value = 30; el.dispatchEvent(new Event('input')); });
  await listReady();
  const at30 = await clubNames();
  await page.fill('#routeName', 'Leonberg → München');
  await page.click('#routeSave');
  await page.waitForFunction(() => /saved .*made no request/.test(document.getElementById('routeOut').textContent), null, {timeout: 5000});
  const [rec] = await idbRoutes();
  const keys = rec ? Object.keys(rec).sort().join(',') : '';
  check('saved: name, line, ends, options, length, time, dates - and no club list',
    rec && keys === 'approximate,distanceKm,durationSec,from,hasFerry,hasToll,id,line,lineAt,name,options,savedAt,to' && rec.line === SHAPE &&
    rec.options.withinKm === 30 && rec.distanceKm === 268.4 && rec.durationSec === 9720, keys);
  const lineEnd = LINE[LINE.length - 1];
  check('a searched end is kept as the typed words and the LINE\'s end point, never the search answer',
    rec.from.kind === 'search' && rec.from.label === 'Leonberg' && rec.from.lat === LINE[0][0] && rec.from.lon === LINE[0][1] &&
    rec.to.label === 'München' && rec.to.lat === lineEnd[0] && rec.to.lon === lineEnd[1] && !JSON.stringify(rec).includes('Baden-Württemberg'),
    JSON.stringify([rec.from, rec.to]));

  const rowTxt = () => page.$eval('#savedRoutes .sroute', e => e.textContent);
  await page.waitForFunction(() => /at current settings/.test(document.querySelector('#savedRoutes .sroute')?.textContent || ''), null, {timeout: 5000});
  check('saved route: the same range, labelled "at current settings"', /about €34 to €41 at current settings/.test(await rowTxt()), await rowTxt());
  await page.fill('#costPrice', '1.5');
  await page.waitForFunction(() => /€25 to €31/.test(document.querySelector('#savedRoutes .sroute')?.textContent || ''), null, {timeout: 5000});
  check('saved route: the range follows the settings', /about €25 to €31 at current settings/.test(await rowTxt()), await rowTxt());
  await page.fill('#costPrice', '');

  // ---- 4. reload, then open it: no request, the club list worked out again
  await page.reload(); await loaded();
  await openPanel();
  await page.click('#savedRoutes summary');
  const listed = await page.$$eval('#savedRoutes .sroute', els => els.map(e => e.textContent));
  check('after a reload the saved route is listed', listed.length === 1 && /Leonberg → München/.test(listed[0]), listed.join(' | '));
  const before = {...count};
  await page.click('#savedRoutes [data-act="open"]'); await listReady();
  const reopened = await clubNames();
  const txt = await routeText();
  check('opening a saved route makes no Stadia request', count.route === before.route && count.search === before.search, JSON.stringify(count));
  check('...and lists the same clubs, at its saved 30 km', JSON.stringify(reopened) === JSON.stringify(at30) &&
    (await page.inputValue('#routeKm')) === '30', `${reopened.length} vs ${at30.length}`);
  check('...shows its saved date and a Refresh route button costing about 20 credits',
    /saved \w{3}, \d+ \w{3} \d{4}/.test(txt) && /Refresh route/.test(txt) && /about 20 credits/.test(txt), txt.slice(0, 200));
  check('the route panel does not scroll the page sideways', await noSideScroll());

  // ---- 4b. a saved route with the new cost shown, and an older one with no distance
  const opened = await routeText();
  check('opened saved route shows its range and carries its distance', /about €34 to €41/.test(opened) && /268 km/.test(opened), opened.slice(0, 160));
  await page.evaluate(rec => new Promise((res, rej) => {
    const old = {...rec, id: 'old-no-distance', name: 'Older route', savedAt: '2026-01-01T10:00:00.000Z'};
    delete old.distanceKm; delete old.durationSec; delete old.hasToll; delete old.hasFerry;
    const r = indexedDB.open('football-planner-device');
    r.onsuccess = () => { const t = r.result.transaction('routes', 'readwrite'); t.objectStore('routes').put(old);
      t.oncomplete = () => res(); t.onerror = () => rej(t.error); };
  }), (await idbRoutes())[0]);
  await page.reload(); await loaded(); await openPanel();
  await page.click('#savedRoutes summary');
  const rows = await page.$$eval('#savedRoutes .sroute', els => els.map(e => e.textContent));
  const oldRow = rows.find(t => /Older route/.test(t)), newRow = rows.find(t => /Leonberg → München/.test(t));
  const rb = {...count};
  check('older saved route (no distance): no cost and no NaN in its row', oldRow && !/fuel estimate|NaN|diesel/.test(oldRow), oldRow);
  check('...while the route saved with a distance still shows its range', /about €34 to €41 at current settings/.test(newRow || ''), newRow);
  await page.click('#savedRoutes .sroute:has-text("Older route") [data-act="open"]');
  await page.waitForFunction(() => /No distance is kept/.test(document.getElementById('routeOut').textContent), null, {timeout: 5000});
  const oldTxt = await routeText();
  check('...opening it shows no cost, no NaN, and asks Stadia for nothing', !/fuel estimate: about|NaN/.test(oldTxt) && count.route === rb.route && count.search === rb.search, oldTxt.slice(0, 160));
  check('...and the page still does not scroll sideways', await noSideScroll());
  await page.evaluate(() => new Promise((res, rej) => { const r = indexedDB.open('football-planner-device');
    r.onsuccess = () => { const t = r.result.transaction('routes', 'readwrite'); t.objectStore('routes').delete('old-no-distance');
      t.oncomplete = () => res(); t.onerror = () => rej(t.error); }; }));
  await page.reload(); await loaded(); await openPanel();
  await page.click('#savedRoutes summary');
  await page.click('#savedRoutes [data-act="open"]'); await listReady();

  // ---- 5. rename
  await page.click('#savedRoutes [data-act="rename"]');
  await page.fill('#savedRoutes .sroute input', 'Away day to Munich');
  await page.click('#savedRoutes [data-act="ok"]');
  await page.waitForFunction(() => /Away day to Munich/.test(document.getElementById('savedRoutes').textContent));
  check('rename is stored', (await idbRoutes())[0].name === 'Away day to Munich');

  // ---- 6. route back
  const b6 = {...count};
  await page.click('#routeBack'); await listReady();
  const back = await clubNames();
  const btxt = await routeText();
  // Clubs beyond an end of the line all sit at that end's distance along it, so the
  // order among them is by distance from the road both ways: only near-reverse.
  check('route back: no request, labelled approximate, the same clubs, the far end first',
    count.route === b6.route && /approximate/.test(btxt) && JSON.stringify([...back].sort()) === JSON.stringify([...reopened].sort()) &&
    reopened.indexOf(back[0]) >= reopened.length * 2 / 3 && reopened.indexOf(back[back.length - 1]) < reopened.length / 3,
    `back: ${back[0]} ... ${back[back.length - 1]}; out: ${reopened[0]} ... ${reopened[reopened.length - 1]}`);

  // ---- 7. refresh: one request, new line date
  await page.click('#savedRoutes [data-act="open"]'); await listReady();
  const lineAt0 = (await idbRoutes())[0].lineAt;
  await page.waitForTimeout(20);
  await page.click('#routeRefresh'); await page.waitForFunction(() => !/Asking Stadia/.test(document.getElementById('routeOut').textContent));
  await listReady();
  const r7 = (await idbRoutes())[0];
  check('Refresh route: one request, the saved line date moves, the name stays', count.route === 2 && r7.lineAt > lineAt0 && r7.name === 'Away day to Munich',
    `${lineAt0} -> ${r7.lineAt}`);

  // ---- 8. the credit estimate: 2 routes, 2 searches
  const cr = await page.textContent('#routeCredits');
  check('credit estimate: 2 routes and 2 searches, about 80 credits, labelled an estimate without tiles',
    /about 80 credits/.test(cr) && /2 routes and 2 searches/.test(cr) && /Estimate/.test(cr) && /tiles/.test(cr), cr);

  // ---- 9. search cache expiry: a copy 8 days old is asked again
  await page.evaluate(() => new Promise(res => { const r = indexedDB.open('football-planner-device'); r.onsuccess = () => {
    const st = r.result.transaction('searches', 'readwrite').objectStore('searches');
    st.getAll().onsuccess = e => { for(const row of e.target.result){ row.at = new Date(Date.now() - 8 * 864e5).toISOString(); st.put(row); } res(); }; }; }));
  await search('from', 'Leonberg');
  check('a saved search older than 7 days is not used: Stadia is asked again', count.search === 3 &&
    !/saved copy/.test(await page.textContent(pt('from', '.hits'))), JSON.stringify(count));

  // ---- 10. offline: open the saved route
  await page.click('#routeClose');
  offline = true; await ctx.setOffline(true);
  await page.reload(); await loaded();
  await openPanel(); await page.click('#savedRoutes summary');
  const b10 = {...count};
  await page.click('#savedRoutes [data-act="open"]'); await listReady();
  await page.waitForTimeout(600);
  const offList = await clubNames();
  const card = await page.evaluate(() => ({on: document.getElementById('mapOffline').getBoundingClientRect().height > 0,
    text: document.getElementById('mapOffline').textContent.replace(/\s+/g, ' ').trim()}));
  check('offline: the saved route opens and its club list works', offList.length === at30.length && count.route === b10.route, `${offList.length} clubs`);
  check('offline: the map shows its needs-a-connection card', card.on && /needs a connection/.test(card.text), card.text);
  await page.screenshot({path: path.join(TMP, 'routes-offline.png')});
  await page.click('#routeClose');
  offline = false; await ctx.setOffline(false);
  await page.reload(); await loaded();

  // ---- 11. export, delete, import
  await openPanel(); await page.click('#savedRoutes summary');
  const [dl] = await Promise.all([page.waitForEvent('download'), page.click('#routesExport')]);
  const file = path.join(TMP, 'routes-export.json');
  await dl.saveAs(file);
  const exp = JSON.parse(fs.readFileSync(file, 'utf8'));
  check('export writes a JSON file holding the route', exp.format === 'football-planner-saved-routes' && exp.routes.length === 1 &&
    exp.routes[0].name === 'Away day to Munich' && dl.suggestedFilename().endsWith('.json'), dl.suggestedFilename());
  await page.click('#savedRoutes [data-act="delete"]'); await page.click('#savedRoutes [data-act="yes"]');
  await page.waitForFunction(() => !document.querySelector('#savedRoutes .sroute'));
  check('delete removes it', (await idbRoutes()).length === 0);
  await page.setInputFiles('#routesFile', file);
  await page.waitForFunction(() => /Imported/.test(document.getElementById('routesMsg')?.textContent || ''));
  const im = await idbRoutes();
  check('import brings it back, line and all', im.length === 1 && im[0].line === exp.routes[0].line && im[0].name === 'Away day to Munich',
    await page.textContent('#routesMsg'));
  await page.setInputFiles('#routesFile', file);
  await page.waitForFunction(() => /already on this device/.test(document.getElementById('routesMsg').textContent) &&
    /Imported 0/.test(document.getElementById('routesMsg').textContent));
  check('importing the same file again leaves it alone', (await idbRoutes()).length === 1, await page.textContent('#routesMsg'));
  const bad = path.join(TMP, 'routes-bad.json');
  fs.writeFileSync(bad, JSON.stringify({format: 'football-planner-saved-routes', version: 1,
    routes: [{...exp.routes[0], id: 'other', line: ''}, {id: 'x'}]}));
  await page.setInputFiles('#routesFile', bad);
  await page.waitForFunction(() => /not imported/.test(document.getElementById('routesMsg').textContent));
  const badMsg = await page.textContent('#routesMsg');
  check('a file with broken routes: each named with its reason, none kept', (await idbRoutes()).length === 1 && /no route line/.test(badMsg) && /2 not imported/.test(badMsg), badMsg);
  fs.writeFileSync(bad, '{"hello": 1}');
  await page.setInputFiles('#routesFile', bad);
  await page.waitForFunction(() => /not a saved-routes export/.test(document.getElementById('routesMsg').textContent));
  check('a JSON file that is not an export is refused', true);

  // ---- 11b. tolls and ferries: Stadia's has_toll is true, the estimate says it is not in the cost
  TOLL = true;
  if(await page.$eval('#routePanel', e => e.hidden)) await openPanel();
  await page.evaluate(() => { setEnd('from', 48.8003, 9.0167, 'Start point', 'tap'); setEnd('to', 48.1351, 11.582, 'End point', 'tap'); });
  await page.click('#routeGo'); await listReady();
  await page.waitForFunction(() => /fuel estimate/.test(document.getElementById('costResult').textContent), null, {timeout: 8000});
  const tollTxt = await page.textContent('#costResult');
  check('cost: has_toll from Stadia shows "Route includes tolls/ferries, not in this cost", range unchanged',
    /Route includes tolls\/ferries, not in this cost/.test(tollTxt) && /about €34 to €41/.test(tollTxt), tollTxt);
  check('cost: the tolls line does not scroll the page sideways', await noSideScroll());
  TOLL = false;

  // ---- 12. a second tab in the same browser profile
  const tab2 = await ctx.newPage();
  tab2.on('pageerror', e => errors.push('tab2: ' + e.message));
  await tab2.goto(BASE);
  await tab2.waitForFunction(() => typeof CLUBS !== 'undefined' && CLUBS.length > 400);
  await tab2.click('#routeChip'); await tab2.waitForSelector('#savedRoutes summary');
  const t2 = await tab2.textContent('#savedRoutes');
  check('a second tab in the same profile sees the same saved routes', /Away day to Munich/.test(t2) && /\(1\)/.test(t2), t2.slice(0, 80));
  await tab2.close();

  check('no script errors', errors.length === 0, errors.join(' | '));
  await ctx.close();
  server.closeAllConnections(); server.close();
  const failed = results.filter(r => !r).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
