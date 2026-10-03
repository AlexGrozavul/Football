// Headless Chromium test of the map's zoom rule, at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright            (anywhere; it is not a dependency of this repo)
//   node tools/test_zoom.js .         (serves the checkout itself; it changes no file)
//
// The guaranteed property (CLAUDE.md, "Tier zoom bands"): at the tier-3 threshold, z9,
// EVERY club on the map is drawn, whatever its tier. This test fails loudly, naming each
// club, if one is not. It also checks: tiers 1 and 2 keep their thresholds (z0, z7);
// minZoom is 3; zoomDelta and zoomSnap are 1 (read from the live map, and the + button
// moves exactly one level); every club file in data/clubs/ is in COUNTRY_FILES; every club
// in those files with a position and a tier is on the map; the legend shows no tier as off
// at z9; no script error.
//
// It then MEASURES (and does not judge) the redraw at z9 over the densest areas - the
// Ruhr, northern Italy, Bucharest - with the CPU slowed 4x through the DevTools protocol,
// and prints the numbers. No threshold: a runner's speed varies, so a timing limit here
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
const expected = [];
for(const f of listed){
  const d = JSON.parse(fs.readFileSync(path.join(ROOT, f), 'utf8'));
  for(const c of d.clubs || []) if(c.lat != null && c.lon != null && c.tier != null) expected.push(c.id + '@' + d.country);
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

  // ---- the property: at z9 (and above) every club on the map is drawn
  const drawnAt = z => page.evaluate(z => {
    MAP.setZoom(z, {animate: false});
    const drawn = new Map();                     // coordinate -> how many clubs its marker carries
    LAYER.eachLayer(l => {
      const ll = l.getLatLng(), key = ll.lat + ',' + ll.lng;
      const n = l instanceof L.CircleMarker ? 1 : Number(l.options.icon.options.html.match(/>(\d+)<\/div>$/)[1]);
      drawn.set(key, (drawn.get(key) || 0) + n);
    });
    const need = new Map();
    for(const c of CLUBS){ const key = c.lat + ',' + c.lon; (need.get(key) || need.set(key, []).get(key)).push(c); }
    const hidden = [];
    for(const [key, clubs] of need) if((drawn.get(key) || 0) < clubs.length) hidden.push(...clubs);
    return {zoom: MAP.getZoom(), total: CLUBS.length, drawnClubs: [...drawn.values()].reduce((a, b) => a + b, 0),
      hidden: hidden.map(c => `${c.name || c.id} (${c.id}, tier ${c.tier}, ${c.country})`),
      chip: document.getElementById('zoomChip').textContent,
      legendOff: [...document.querySelectorAll('#legend div[data-tier].off')].map(e => e.dataset.tier)};
  }, z);
  const at9 = await drawnAt(THRESHOLD);
  console.log(`    z${THRESHOLD}: ${at9.drawnClubs} of ${at9.total} clubs drawn; chip "${at9.chip}"`);
  check(`at z${THRESHOLD} every club on the map is drawn`, at9.zoom === THRESHOLD && !at9.hidden.length && at9.drawnClubs === at9.total,
    at9.hidden.length ? 'NOT DRAWN: ' + at9.hidden.join('; ') : `${at9.drawnClubs}/${at9.total}`);
  check(`the chip counts all ${at9.total} clubs at z${THRESHOLD}`, at9.chip.startsWith(at9.total + ' clubs'), at9.chip);
  check(`the legend shows no tier as off at z${THRESHOLD}`, !at9.legendOff.length, at9.legendOff.join(','));
  let above = [];
  for(let z = THRESHOLD + 1; z <= 18; z++){ const r = await drawnAt(z); if(r.hidden.length) above.push(`z${z}: ${r.hidden.length}`); }
  check(`every club stays drawn at every zoom from ${THRESHOLD + 1} to 18`, !above.length, above.join('; '));

  const tierCount = await page.evaluate(() => {
    const n = {}; CLUBS.forEach(c => n[c.tier] = (n[c.tier] || 0) + 1); return n; });
  const upTo = k => Object.entries(tierCount).filter(([tier]) => Number(tier) <= k).reduce((a, [, v]) => a + v, 0);
  const at8 = await drawnAt(8), at7 = await drawnAt(7), at6 = await drawnAt(6);
  check('at z8 exactly tiers 1 and 2 are drawn', at8.drawnClubs === upTo(2), `${at8.drawnClubs} drawn, ${upTo(2)} at tiers 1-2`);
  check('at z7 tiers 1 and 2 are drawn (tier 2 switches on at 7)', at7.drawnClubs === upTo(2));
  check('at z6 only tier 1 is drawn', at6.drawnClubs === upTo(1), `${at6.drawnClubs} drawn, ${upTo(1)} at tier 1`);

  // ---- timing at z9 over the densest areas, CPU slowed 4x (reported, not judged)
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', {rate: 4});
  const AREAS = [['Ruhr', 51.47, 7.15], ['northern Italy (Milan)', 45.52, 9.25], ['Bucharest', 44.44, 26.10]];
  const measure = (lat, lon) => page.evaluate(async ([lat, lon]) => {
    const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    const med = a => a.slice().sort((x, y) => x - y)[a.length >> 1];
    MAP.setView([lat, lon], 9, {animate: false}); await frame();
    const empty = [];
    for(let i = 0; i < 15; i++){ const t0 = performance.now(); await frame(); empty.push(performance.now() - t0); }
    const zoomIn = [], redraw = [], pan = [];
    for(let i = 0; i < 15; i++){
      MAP.setZoom(8, {animate: false}); await frame();
      let t0 = performance.now(); MAP.setZoom(9, {animate: false}); await frame();
      zoomIn.push(performance.now() - t0);          // the zoomend redraw, through to the next painted frame
      t0 = performance.now(); drawClubs(); redraw.push(performance.now() - t0);   // drawClubs() alone
      await frame();
      t0 = performance.now(); MAP.panBy([120, 0], {animate: false}); await frame();
      pan.push(performance.now() - t0);
      MAP.panBy([-120, 0], {animate: false}); await frame();
    }
    let drawn = 0; LAYER.eachLayer(() => drawn++);
    return {onScreen: CLUBS.filter(c => zoomForTier(c.tier) <= 9 && MAP.getBounds().contains([c.lat, c.lon])).length,
      markers: drawn, empty: med(empty), zoomIn: med(zoomIn) - med(empty), worst: Math.max(...zoomIn) - med(empty),
      redraw: med(redraw), pan: med(pan) - med(empty)};
  }, [lat, lon]);
  const line = m => `${m.onScreen} clubs on screen, ${m.markers} markers in the layer; drawClubs() ${m.redraw.toFixed(1)} ms; ` +
    `zoom 8->9 to painted frame ${m.zoomIn.toFixed(1)} ms (worst ${m.worst.toFixed(1)}); one pan ${m.pan.toFixed(1)} ms`;
  console.log(`    TIMING at z${THRESHOLD}, 390x844, CPU 4x slower, median of 15; the two-frame wait itself is subtracted:`);
  for(const [name, lat, lon] of AREAS) console.log(`      ${name}, this rule: ${line(await measure(lat, lon))}`);
  /* The same, with the rule this replaced (tier 4 and deeper from z11), for comparison. */
  await page.evaluate(() => { window._newRule = zoomForTier;
    zoomForTier = t => ({1: 0, 2: 7, 3: 9})[t] ?? (t >= 4 ? 11 : undefined); });
  for(const [name, lat, lon] of AREAS) console.log(`      ${name}, the old rule: ${line(await measure(lat, lon))}`);
  await page.evaluate(() => { zoomForTier = window._newRule; drawClubs(); });
  await cdp.send('Emulation.setCPUThrottlingRate', {rate: 1});

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
