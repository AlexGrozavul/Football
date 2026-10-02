// Headless Chromium test of the installable app (manifest, sw.js), at phone width.
// Not run by any workflow: run it by hand after changing index.html, sw.js or the manifest.
//
//   npm install playwright            (anywhere; it is not a dependency of this repo)
//   mkdir -p /tmp/site && cp -r . /tmp/site/Football     (a COPY: the test edits files in it)
//   node tools/test_pwa.js /tmp/site /tmp
//
// It serves the copy at http://localhost:8765/Football/ with GitHub Pages' own
// Cache-Control: max-age=600, stubs Stadia's tiles, and checks: Chrome's own
// installability errors (none), a second load offline with the banner, an online
// load after a data change showing the new data, and a new deploy replacing the
// shell (with and without a change to sw.js). Exits 1 on any failure.
// CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path'), crypto = require('crypto');
const ROOT = process.argv[2];            // directory that contains Football/
const SITE = path.join(ROOT, 'Football');
const PORT = 8765, BASE = `http://localhost:${PORT}/Football/`;
const TYPES = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.csv':'text/csv; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
let server = null, requests = [];
function up(){ return new Promise(r => {
  server = http.createServer((req, res) => {
    let p = decodeURIComponent(req.url.split('?')[0]);
    requests.push(p);
    if(p === '/Football'){ res.writeHead(301, {Location: '/Football/'}); return res.end(); }
    if(!p.startsWith('/Football/')){ res.writeHead(404); return res.end(); }
    let f = path.join(ROOT, p); if(p.endsWith('/')) f = path.join(f, 'index.html');
    fs.stat(f, (e, st) => {
      if(e || !st.isFile()){ res.writeHead(404); return res.end('nf'); }
      const etag = '"' + crypto.createHash('md5').update(fs.readFileSync(f)).digest('hex') + '"';
      // GitHub Pages' own caching headers
      const h = {'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream', 'Cache-Control':'max-age=600', ETag: etag};
      if(req.headers['if-none-match'] === etag){ res.writeHead(304, h); return res.end(); }
      res.writeHead(200, h); fs.createReadStream(f).pipe(res);
    });
  }).listen(PORT, r);
});}
function down(){ return new Promise(r => { server.closeAllConnections(); server.close(r); }); }
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
let netOff = false;
const results = [];
const check = (name, ok, detail='') => { results.push([ok, name, detail]); console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ' :: ' + detail : '')); };

(async () => {
  await up();
  // A persistent profile, because Chrome never offers to install from an incognito window.
  const prof = fs.mkdtempSync(path.join(process.argv[3], 'profile-'));
  const ctx = await chromium.launchPersistentContext(prof, { executablePath: process.env.CHROMIUM_PATH || undefined, headless: true,
    viewport: {width:390, height:844}, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const browser = ctx;
  await ctx.route('https://tiles.stadiamaps.com/**', route => netOff ? route.abort('internetdisconnected') : route.fulfill({status:200, contentType:'image/png', body: PNG}));
  const page = ctx.pages()[0] || await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const clubsShown = () => page.evaluate(() => CLUBS.length);
  const state = () => page.evaluate(() => ({
    // what is on screen, not the attribute: a CSS display rule can override [hidden]
    banner: document.getElementById('offlineBanner').getBoundingClientRect().height > 0, bannerText: document.getElementById('offlineText').textContent,
    mapOff: document.getElementById('mapOffline').getBoundingClientRect().height > 0, mapOffText: document.getElementById('mapOffline').textContent.trim(),
    clubs: CLUBS.length, chip: document.getElementById('zoomChip').textContent,
    bucket: document.getElementById('bucketBody').textContent.length, title: document.title,
    deployMeta: document.querySelector('meta[name=deploy-test]')?.content || null,
    controlled: !!navigator.serviceWorker.controller }));
  const cacheKeys = () => page.evaluate(async () => {
    const out = {}; for(const n of await caches.keys()){ const c = await caches.open(n); out[n] = (await c.keys()).map(r => new URL(r.url).pathname); } return out; });
  const waitLoaded = () => page.waitForFunction(() => typeof CLUBS !== 'undefined' && CLUBS.length > 0 && document.getElementById('bucketBody').textContent.length > 0, null, {timeout: 30000});

  // ---- 1. first visit, online
  await page.goto(BASE); await waitLoaded();
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.waitForFunction(() => !!navigator.serviceWorker.controller, null, {timeout: 15000});
  const poll = async (fn, ms) => { const t0 = Date.now(); while(Date.now() - t0 < ms){ if(await fn()) return true; await new Promise(r => setTimeout(r, 300)); } return false; };
  const warmed = await poll(async () => { const k = (await cacheKeys())['football-data-v1'] || [];
     return k.includes('/Football/data/football-rules.json') && k.filter(u => /data\/clubs\/[A-Z]{2}\.json$/.test(u)).length === 12; }, 20000);
  check('first visit: files loaded before the worker took over are saved for offline', warmed, JSON.stringify((await cacheKeys())['football-data-v1']));
  const s1 = await state();
  check('first visit loads, online, no banner, no map card', s1.clubs > 400 && !s1.banner && !s1.mapOff, JSON.stringify({clubs:s1.clubs, banner:s1.banner, mapOff:s1.mapOff}));
  const cdp = await ctx.newCDPSession(page);
  const inst = await cdp.send('Page.getInstallabilityErrors');
  check('Chrome installability errors: none', inst.installabilityErrors.length === 0, JSON.stringify(inst.installabilityErrors));
  const man = await cdp.send('Page.getAppManifest');
  check('manifest parsed without errors', man.errors.length === 0, man.url + ' ' + JSON.stringify(man.errors));
  let parsed = null;
  try { parsed = (await cdp.send('Page.getAppManifest', {})).parsed || null; } catch(e) {}
  const m = JSON.parse(man.data);
  const startUrl = new URL(m.start_url, man.url).href, scope = new URL(m.scope, man.url).href;
  check('start_url and scope resolve to the /Football/ subpath', startUrl === BASE && scope === BASE, `start_url=${startUrl} scope=${scope}`);
  const reg = await page.evaluate(async () => { const r = await navigator.serviceWorker.getRegistration(); return {scope: r.scope, script: r.active.scriptURL}; });
  check('service worker registered at /Football/sw.js with scope /Football/', reg.scope === BASE && reg.script === BASE + 'sw.js', JSON.stringify(reg));
  console.log('caches after first visit:', JSON.stringify(Object.fromEntries(Object.entries(await cacheKeys()).map(([k,v]) => [k, v.length]))));

  // tiles and Stadia never in any cache
  const allKeys = Object.values(await cacheKeys()).flat();
  check('nothing outside the site is cached (no tiles, no Stadia)', allKeys.every(p => p.startsWith('/Football/')), allKeys.filter(p => !p.startsWith('/Football/')).join(','));

  // ---- 2. second load, offline. One file is taken out of the saved copies first,
  // to check that a file never saved is named rather than silently missing.
  const grCount = await page.evaluate(() => CLUBS.filter(c => c.country === 'GR').length);
  await page.evaluate(async () => { const c = await caches.open('football-data-v1'); await c.delete(new URL('data/clubs/GR.json', location.href).href); });
  await down(); netOff = true; await ctx.setOffline(true);
  await page.reload(); await waitLoaded();
  await page.waitForTimeout(800);
  const s2 = await state();
  check('second load works offline: clubs drawn, bucket list rendered', s2.clubs === s1.clubs - grCount && grCount > 0 && s2.bucket > 0, `clubs=${s2.clubs} of ${s1.clubs}, GR ${grCount} removed on purpose`);
  check('offline: a file never saved is named in the banner', /missing: clubs\/GR\.json/.test(s2.bannerText), s2.bannerText);
  check('offline: data banner shows with a saved-on date', s2.banner && /^Offline\. Showing data saved on .*\d{4}/.test(s2.bannerText), s2.bannerText);
  check('offline: map shows "needs a connection" card', s2.mapOff && /needs a connection/.test(s2.mapOffText), s2.mapOffText);
  await page.screenshot({ path: process.argv[3] + '/offline.png' });
  // route search offline says so
  await page.click('#routeChip');
  await page.fill('#routeBody .pt[data-end="from"] input', 'Munich');
  await page.click('#routeBody .pt[data-end="from"] button[data-act="find"]');
  await page.waitForTimeout(500);
  const hitTxt = await page.textContent('#routeBody .pt[data-end="from"] .hits');
  check('offline: place search says it needs a connection', /offline/.test(hitTxt), hitTxt.trim());
  await page.click('#routeClose');

  // ---- 3. online again, after a data change
  const de = path.join(SITE, 'data/clubs/DE.json');
  const orig = fs.readFileSync(de, 'utf8');
  const j = JSON.parse(orig); const oldName = j.clubs[0].name; j.clubs[0].name = 'PWA TEST CHANGED NAME';
  fs.writeFileSync(de, JSON.stringify(j));
  await up(); netOff = false; await ctx.setOffline(false);
  requests = [];
  await page.reload(); await waitLoaded();
  const s3 = await state();
  const names = await page.evaluate(() => CLUBS.map(c => c.name));
  check('online load after a data change shows the NEW data', names.includes('PWA TEST CHANGED NAME') && !names.includes(oldName) , `old="${oldName}"`);
  check('online: no banner, no map card', !s3.banner && !s3.mapOff);
  check('online: DE.json actually requested from the server', requests.includes('/Football/data/clubs/DE.json'));
  await page.waitForTimeout(500);
  const savedName = await page.evaluate(async () => { const c = await caches.open('football-data-v1'); const r = await c.match(new URL('data/clubs/DE.json', location.href).href); return (await r.json()).clubs[0].name; });
  check('the saved copy was replaced by the new data', savedName === 'PWA TEST CHANGED NAME', savedName);
  fs.writeFileSync(de, orig);

  // ---- 4a. new deploy of index.html, sw.js untouched
  const idx = path.join(SITE, 'index.html'); const idxOrig = fs.readFileSync(idx, 'utf8');
  fs.writeFileSync(idx, idxOrig.replace('<title>', '<meta name="deploy-test" content="deploy-2">\n<title>'));
  await page.reload(); await waitLoaded();
  check('new index.html reaches the page on the next online load (sw.js unchanged)', (await state()).deployMeta === 'deploy-2');
  await down(); netOff = true; await ctx.setOffline(true);
  await page.reload(); await waitLoaded();
  check('...and the offline shell is that new index.html, not the old one', (await state()).deployMeta === 'deploy-2');
  await up(); netOff = false; await ctx.setOffline(false);

  // ---- 4b. new deploy that changes sw.js (SHELL_VERSION v1 -> v2)
  const swf = path.join(SITE, 'sw.js'); const swOrig = fs.readFileSync(swf, 'utf8');
  fs.writeFileSync(swf, swOrig.replace("const SHELL_VERSION = 'v1';", "const SHELL_VERSION = 'v2';"));
  fs.writeFileSync(idx, idxOrig.replace('<title>', '<meta name="deploy-test" content="deploy-3">\n<title>'));
  await page.reload(); await waitLoaded();
  await poll(async () => { const k = Object.keys(await cacheKeys()); return k.includes('football-shell-v2') && !k.includes('football-shell-v1'); }, 20000);
  const keys4 = Object.keys(await cacheKeys());
  check('changed sw.js installs: shell-v2 created, shell-v1 deleted, data cache kept', keys4.includes('football-shell-v2') && !keys4.includes('football-shell-v1') && keys4.includes('football-data-v1'), keys4.join(','));
  const v2meta = await page.evaluate(async () => { const c = await caches.open('football-shell-v2'); const r = await c.match(new URL('./', location.href).href); return (await r.text()).includes('deploy-3'); });
  check('the v2 shell cache holds the new index.html', v2meta);
  await down(); netOff = true; await ctx.setOffline(true);
  await page.reload(); await waitLoaded();
  const s4 = await state();
  check('offline after the sw.js update: opens, new shell, banner shows', s4.deployMeta === 'deploy-3' && s4.banner && s4.clubs > 400, JSON.stringify({meta:s4.deployMeta, banner:s4.banner}));
  fs.writeFileSync(swf, swOrig); fs.writeFileSync(idx, idxOrig);

  check('no script errors on any load', errors.length === 0, errors.join(' | '));
  await browser.close();
  await new Promise(r => server.listening ? down().then(r) : r());
  const failed = results.filter(r => !r[0]).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
