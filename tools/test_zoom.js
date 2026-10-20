// Headless Chromium test of the map's zoom rule, at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright            (anywhere; it is not a dependency of this repo)
//   node tools/test_zoom.js .         (serves the checkout itself; it changes no file)
//
// The guaranteed property (CLAUDE.md, "Tier zoom bands"): at the tier-3 threshold, z9,
// EVERY club inside the visible bounds plus 50% padding is drawn, whatever its tier, and no
// ground outside that padding is (drawClubs() culls, since 2026-10-19). The expected set is
// worked out from the club files and the live map's bounds; this test fails loudly, naming
// each club, if one is missing. A club far outside is not drawn, and is drawn after the map
// flew to it from a search suggestion. The chip still counts every club and shared ground at
// the zoom, drawn or not. It also checks: tiers 1 and 2 keep their thresholds (z0, z7);
// minZoom is 3; zoomDelta and zoomSnap are 1 (read from the live map, and the + button
// moves exactly one level); every club file in data/clubs/ is in COUNTRY_FILES; every club
// in those files with a position and a tier is on the map; the legend shows no tier as off
// at z9; no script error.
//
// It then MEASURES (and does not judge) the redraw at z9 over the densest areas - the
// Ruhr, northern Italy, Bucharest, at z7, z8 and z9 - with the CPU slowed 4x through the
// DevTools protocol, beside the old draw-everything behaviour, and prints the numbers. No threshold: a runner's speed varies, so a timing limit here
// would fail on the machine, not on the page.
// Stadia's tiles are stubbed. CHROMIUM_PATH points it at a Chromium other than Playwright's.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8768, BASE = `http://localhost:${PORT}/Football/`;
const TYPES = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.csv':'text/csv; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
const THRESHOLD = 9;          // the zoom tier 3 used before the merge, now shared by tier 3 and deeper
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

// What the club files hold, read here independently of the page.
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const listed = JSON.parse(html.match(/const COUNTRY_FILES = (\[[^\]]*\])/)[1].replace(/'/g, '"'));
const onDisk = fs.readdirSync(path.join(ROOT, 'data/clubs')).filter(f => /^[A-Z]{2}\.json$/.test(f)).map(f => 'data/clubs/' + f);
const expected = [], fileClubs = [];
for(const f of listed){
  const d = JSON.parse(fs.readFileSync(path.join(ROOT, f), 'utf8'));
  for(const c of d.clubs || []) if(c.lat != null && c.lon != null && c.tier != null){
    expected.push(c.id + '@' + d.country);
    fileClubs.push({id: c.id, name: c.name, tier: c.tier, lat: c.lat, lon: c.lon});
  }
}

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

  // ---- the files and the map
  const missingFiles = onDisk.filter(f => !listed.includes(f));
  check('every club file in data/clubs/ is loaded by the page (COUNTRY_FILES)', !missingFiles.length, missingFiles.join(', '));
  const onMap = await page.evaluate(() => CLUBS.map(c => c.id + '@' + c.country));
  const lost = expected.filter(k => !onMap.includes(k));
  check('every club in the files with a position and a tier is on the map', !lost.length && onMap.length === expected.length,
    `${expected.length} in the files, ${onMap.length} on the map` + (lost.length ? '; missing: ' + lost.join(', ') : ''));

  // ---- zoom settings, read from the live map rather than assumed
  const opts = await page.evaluate(() => ({delta: MAP.options.zoomDelta, snap: MAP.options.zoomSnap,
    min: MAP.getMinZoom(), max: MAP.getMaxZoom()}));
  check('zoomDelta is 1', opts.delta === 1, JSON.stringify(opts));
  check('zoomSnap is 1 (the map always rests on a whole zoom)', opts.snap === 1);
  check('minZoom is 3', opts.min === 3);
  await page.evaluate(() => MAP.setZoom(1, {animate: false}));
  check('zooming out past 3 stops at 3', await page.evaluate(() => MAP.getZoom()) === 3);
  await page.evaluate(() => MAP.setView([51.45, 7.2], 8, {animate: false}));
  await page.tap('.leaflet-control-zoom-in');
  await page.waitForFunction(() => !MAP._animatingZoom && MAP.getZoom() !== 8, null, {timeout: 5000}).catch(() => {});
  await page.waitForTimeout(400);
  const afterTap = await page.evaluate(() => MAP.getZoom());
  check('the + button moves exactly one zoom level (8 to 9)', afterTap === 9, `now z${afterTap}`);

  // ---- thresholds
  const t = await page.evaluate(() => ({1: zoomForTier(1), 2: zoomForTier(2), 3: zoomForTier(3), 4: zoomForTier(4),
    5: zoomForTier(5), 8: zoomForTier(8), 12: zoomForTier(12), deep: DEEP_TIER_ZOOM}));
  check('tier 1 keeps its threshold, z0', t[1] === 0, JSON.stringify(t));
  check('tier 2 keeps its threshold, z7', t[2] === 7);
  check(`tier 3 and every deeper tier share z${THRESHOLD}`, [3, 4, 5, 8, 12].every(k => t[k] === THRESHOLD) && t.deep === THRESHOLD);

  // ---- the property: at z9 (and above) every club inside the padded bounds is drawn
  /* drawClubs() draws a ground only when it lies inside the visible bounds padded by 50% (since
     2026-10-19). The expected set is worked out HERE, from the club files and the bounds the live
     map reports, never by asking the page which clubs it meant to draw. Grounds within EPS of the
     padded edge are neither required nor forbidden, so rounding cannot fail a run. */
  const from = tier => tier === 1 ? 0 : tier === 2 ? 7 : THRESHOLD;
  const EPS = 1e-6;
  const snap = z => page.evaluate(z => {
    if(z != null) MAP.setZoom(z, {animate: false});
    const b = MAP.getBounds();
    const drawn = new Map();                     // coordinate -> how many clubs its marker carries
    LAYER.eachLayer(l => {
      const ll = l.getLatLng(), key = ll.lat + ',' + ll.lng;
      const n = l instanceof L.CircleMarker ? 1 : Number(l.options.icon.options.html.match(/>(\d+)<\/div>$/)[1]);
      drawn.set(key, (drawn.get(key) || 0) + n);
    });
    return {zoom: MAP.getZoom(), b: {s: b.getSouth(), n: b.getNorth(), w: b.getWest(), e: b.getEast()}, drawn: [...drawn],
      chip: document.getElementById('zoomChip').textContent,
      legendOff: [...document.querySelectorAll('#legend div[data-tier].off')].map(e => e.dataset.tier)};
  }, z);
  const expectAt = r => {                        // r: a snap()
    const padLat = (r.b.n - r.b.s) * 0.5, padLon = (r.b.e - r.b.w) * 0.5;
    const within = (c, e) => c.lat >= r.b.s - padLat - e && c.lat <= r.b.n + padLat + e &&
                             c.lon >= r.b.w - padLon - e && c.lon <= r.b.e + padLon + e;
    const groups = new Map();                    // every club the tier rule shows at this zoom, by exact coordinate
    for(const c of fileClubs){ if(r.zoom < from(c.tier)) continue;
      const key = c.lat + ',' + c.lon; (groups.get(key) || groups.set(key, []).get(key)).push(c); }
    const required = [], allowed = new Set();
    for(const [key, cs] of groups){ if(within(cs[0], -EPS)) required.push([key, cs]); if(within(cs[0], EPS)) allowed.add(key); }
    const shownClubs = [...groups.values()].reduce((a, cs) => a + cs.length, 0);
    return {groups, required, allowed, shownClubs, sharedGrounds: [...groups.values()].filter(cs => cs.length > 1).length};
  };
  const verdict = r => {
    const e = expectAt(r), drawn = new Map(r.drawn);
    const missing = e.required.filter(([key, cs]) => (drawn.get(key) || 0) !== cs.length).flatMap(([, cs]) => cs.map(c => `${c.name || c.id} (${c.id})`));
    const outside = [...drawn.keys()].filter(k => !e.allowed.has(k));
    const drawnClubs = [...drawn.values()].reduce((a, n) => a + n, 0);
    return {e, missing, outside, drawnClubs, chipOk: r.chip.startsWith(e.shownClubs + ' clubs') &&
      (e.sharedGrounds ? r.chip.includes(e.sharedGrounds + ' shared ground') : !/shared ground/.test(r.chip))};
  };
  const at9 = await snap(THRESHOLD);
  const v9 = verdict(at9);
  console.log(`    z${THRESHOLD}: ${v9.drawnClubs} of ${fileClubs.length} clubs drawn (${v9.e.required.length} grounds required inside the padded bounds); chip "${at9.chip}"`);
  check(`at z${THRESHOLD} every club inside the visible bounds plus 50% is drawn`, at9.zoom === THRESHOLD && !v9.missing.length,
    v9.missing.length ? 'NOT DRAWN: ' + v9.missing.join('; ') : `${v9.drawnClubs} drawn`);
  check(`at z${THRESHOLD} nothing outside the padded bounds is drawn`, !v9.outside.length, v9.outside.join('; '));
  check(`the chip counts all ${v9.e.shownClubs} clubs and ${v9.e.sharedGrounds} shared grounds at z${THRESHOLD}, drawn or not`, v9.chipOk, at9.chip);
  check(`the legend shows no tier as off at z${THRESHOLD}`, !at9.legendOff.length, at9.legendOff.join(','));
  check(`some club is outside the padded bounds at z${THRESHOLD}, so the test can tell drawing from not drawing`,
    v9.drawnClubs < v9.e.shownClubs, `${v9.drawnClubs} drawn of ${v9.e.shownClubs}`);

  // the farthest club from the view: not drawn; tapping its search suggestion flies there and draws it
  const centre = {lat: (at9.b.s + at9.b.n) / 2, lon: (at9.b.w + at9.b.e) / 2};
  const km = c => { const r = Math.PI / 180, dl = (c.lon - centre.lon) * r, a = c.lat * r, b = centre.lat * r;
    return 6371 * Math.acos(Math.min(1, Math.sin(a) * Math.sin(b) + Math.cos(a) * Math.cos(b) * Math.cos(dl))); };
  const far = fileClubs.filter(c => c.name).reduce((m, c) => km(c) > km(m) ? c : m);
  check(`the farthest club (${far.name}, ${Math.round(km(far))} km away) is not drawn`, !new Map(at9.drawn).has(far.lat + ',' + far.lon));
  await page.fill('#searchInput', far.name);
  await page.waitForSelector('#searchHits button');
  const idx = await page.evaluate(id => SEARCH_HITS.findIndex(c => c.id === id), far.id);
  check(`the search offers ${far.name}`, idx >= 0, `index ${idx}`);
  await page.tap(`#searchHits button[data-i="${Math.max(idx, 0)}"]`);
  await page.waitForFunction(n => !document.getElementById('sheet').hidden && document.querySelector('#sheetHead h3')?.textContent === n,
    far.name, {timeout: 8000}).catch(() => {});
  await page.waitForTimeout(500);
  const flown = await snap();
  const vf = verdict(flown);
  check(`after flying to ${far.name} (tap on its suggestion) its ground is drawn`, new Map(flown.drawn).has(far.lat + ',' + far.lon) && !vf.missing.length,
    `z${flown.zoom}; ` + (vf.missing.join('; ') || 'drawn'));
  check('...and nothing outside the new padded bounds is drawn', !vf.outside.length, vf.outside.join('; '));
  await page.tap('#sheetClose');
  await page.evaluate(() => MAP.setView([51.45, 7.2], 9, {animate: false}));

  let above = [];
  for(let z = THRESHOLD + 1; z <= 18; z++){ const r = await snap(z), v = verdict(r);
    if(v.missing.length || v.outside.length || !v.chipOk) above.push(`z${z}: ${v.missing.length} missing, ${v.outside.length} outside, chip ${v.chipOk}`); }
  check(`every club inside the padded bounds stays drawn at every zoom from ${THRESHOLD + 1} to 18`, !above.length, above.join('; '));

  /* Tiers 1 and 2 keep their thresholds: below z7 only tier 1, below z9 only tiers 1 and 2 (the chip counts every one of them). */
  const upTo = k => fileClubs.filter(c => c.tier <= k).length;
  const at8 = await snap(8), at7 = await snap(7), at6 = await snap(6), at3 = await snap(3);
  const v8 = verdict(at8), v7 = verdict(at7), v6 = verdict(at6), v3 = verdict(at3);
  check('at z8 exactly tiers 1 and 2 count, and the ones inside the padded bounds are drawn', v8.e.shownClubs === upTo(2) && !v8.missing.length && !v8.outside.length && v8.chipOk,
    `${v8.e.shownClubs} count, ${upTo(2)} at tiers 1-2, chip "${at8.chip}"`);
  check('at z7 tiers 1 and 2 count (tier 2 switches on at 7)', v7.e.shownClubs === upTo(2) && !v7.missing.length && !v7.outside.length && v7.chipOk);
  check('at z6 only tier 1 counts', v6.e.shownClubs === upTo(1) && !v6.missing.length && !v6.outside.length && v6.chipOk, `${v6.e.shownClubs} count, ${upTo(1)} at tier 1`);
  check('at z3 only tier 1 counts and the chip counts them all', v3.e.shownClubs === upTo(1) && !v3.missing.length && !v3.outside.length && v3.chipOk,
    `${v3.drawnClubs} drawn of ${v3.e.shownClubs}, chip "${at3.chip}"`);

  // ---- timing at z7, z8, z9 over the densest areas, CPU slowed 4x (reported, not judged)
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', {rate: 4});
  const AREAS = [['Ruhr', 51.47, 7.15], ['northern Italy (Milan)', 45.52, 9.25], ['Bucharest', 44.44, 26.10]];
  const measure = (lat, lon, z) => page.evaluate(async ([lat, lon, z]) => {
    const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    const med = a => a.slice().sort((x, y) => x - y)[a.length >> 1];
    MAP.setView([lat, lon], z, {animate: false}); await frame();
    const empty = [];
    for(let i = 0; i < 15; i++){ const t0 = performance.now(); await frame(); empty.push(performance.now() - t0); }
    const zoomIn = [], redraw = [], pan = [];
    for(let i = 0; i < 15; i++){
      MAP.setZoom(z - 1, {animate: false}); await frame();
      let t0 = performance.now(); MAP.setZoom(z, {animate: false}); await frame();
      zoomIn.push(performance.now() - t0);          // the zoomend redraw, through to the next painted frame
      t0 = performance.now(); drawClubs(); redraw.push(performance.now() - t0);   // drawClubs() alone
      await frame();
      t0 = performance.now(); MAP.panBy([120, 0], {animate: false}); await frame();
      pan.push(performance.now() - t0);
      MAP.panBy([-120, 0], {animate: false}); await frame();
    }
    let drawn = 0; LAYER.eachLayer(() => drawn++);
    return {markers: drawn, zoomIn: med(zoomIn) - med(empty), worst: Math.max(...zoomIn) - med(empty),
      redraw: med(redraw), pan: med(pan) - med(empty)};
  }, [lat, lon, z]);
  const line = m => `${String(m.markers).padStart(4)} markers; drawClubs() ${m.redraw.toFixed(1)} ms; ` +
    `zoom step to painted frame ${m.zoomIn.toFixed(1)} ms (worst ${m.worst.toFixed(1)}); one pan ${m.pan.toFixed(1)} ms`;
  console.log(`    TIMING, ${fileClubs.length} clubs, 390x844, CPU 4x slower, median of 15; the two-frame wait itself is subtracted:`);
  /* "Draw everything" is the old behaviour: the page asked for a whole-world view, so every ground is inside the bounds. */
  for(const z of [7, 8, 9]) for(const [name, lat, lon] of AREAS){
    console.log(`      z${z} ${name}, visible bounds + 50%: ${line(await measure(lat, lon, z))}`);
    await page.evaluate(() => { window._gb = MAP.getBounds; MAP.getBounds = () => L.latLngBounds([-85, -540], [85, 540]); });
    console.log(`      z${z} ${name}, every club (old):     ${line(await measure(lat, lon, z))}`);
    await page.evaluate(() => { MAP.getBounds = window._gb; drawClubs(); });
  }
  await cdp.send('Emulation.setCPUThrottlingRate', {rate: 1});

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
