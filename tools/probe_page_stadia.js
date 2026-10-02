// THROWAWAY probe, removed in the same branch. Opens this checkout's index.html
// in headless Chromium AS IF served from a given origin (the page and its data
// are answered from disk; every Stadia request goes to the real network), then
// checks that tiles draw, a place search answers and a route is drawn.
//   node tools/probe_page_stadia.js https://alexgrozavul.github.io
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const ORIGIN = process.argv[2];
const BASE = ORIGIN + '/Football/';
const TYPES = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.csv':'text/csv; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
(async () => {
  const browser = await chromium.launch({headless: true});
  const ctx = await browser.newContext({viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true, serviceWorkers: 'block'});
  await ctx.route(ORIGIN + '/**', route => {
    let p = decodeURIComponent(new URL(route.request().url()).pathname);
    if(!p.startsWith('/Football/')) return route.fulfill({status: 404, body: 'nf'});
    let f = path.join(process.cwd(), p.slice('/Football/'.length)); if(p.endsWith('/')) f = path.join(f, 'index.html');
    if(!fs.existsSync(f) || !fs.statSync(f).isFile()) return route.fulfill({status: 404, body: 'nf'});
    route.fulfill({status: 200, contentType: TYPES[path.extname(f)] || 'application/octet-stream', body: fs.readFileSync(f)});
  });
  const page = await ctx.newPage();
  const errors = [], stadia = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('response', async r => {
    const u = r.url(); if(!/stadiamaps\.com/.test(u)) return;
    const h = await r.request().allHeaders();
    stadia.push({kind: /tiles\./.test(u) ? 'tile' : /geocoding/.test(u) ? 'search' : /route/.test(u) ? 'route' : 'other',
      method: r.request().method(), status: r.status(), key: /api_key=/.test(u), referer: h.referer || null, origin: h.origin || null});
  });
  page.on('requestfailed', r => { if(/stadiamaps\.com/.test(r.url())) stadia.push({kind: 'FAILED', method: r.request ? r.method() : '', status: r.failure()?.errorText}); });
  await page.goto(BASE);
  await page.waitForFunction(() => typeof CLUBS !== 'undefined' && CLUBS.length > 0, null, {timeout: 30000});
  await page.waitForTimeout(6000);
  const tiles = await page.evaluate(() => {
    const imgs = [...document.querySelectorAll('img.leaflet-tile')];
    return {total: imgs.length, loaded: imgs.filter(i => i.classList.contains('leaflet-tile-loaded') && i.naturalWidth > 1).length,
            mapCard: document.getElementById('mapOffline').getBoundingClientRect().height > 0, clubs: CLUBS.length};
  });
  console.log(`[${ORIGIN}] tiles on screen: ${JSON.stringify(tiles)}`);
  await page.click('#routeChip');
  const find = async (which, text) => {
    const box = `#routeBody .pt[data-end="${which}"]`;
    await page.fill(`${box} input`, text);
    await page.click(`${box} button[data-act="find"]`);
    await page.waitForFunction(b => !/Searching/.test(document.querySelector(b + ' .hits').textContent), box, {timeout: 20000});
    const hits = await page.textContent(`${box} .hits`);
    console.log(`[${ORIGIN}] search ${which} "${text}": ${hits.slice(0, 200)}`);
    const btn = await page.$(`${box} .hits button`);
    if(btn){ await btn.click(); console.log(`[${ORIGIN}]   chosen: ${await page.textContent(box + ' .chosen')}`); return true; }
    return false;
  };
  const a = await find('from', 'Leonberg'), b = await find('to', 'Augsburg');
  if(a && b){
    await page.click('#routeGo');
    await page.waitForFunction(() => /Length|No route|failed/.test(document.getElementById('routeOut').textContent), null, {timeout: 30000});
    const out = await page.textContent('#routeOut');
    const listed = await page.evaluate(() => document.querySelectorAll('#routeList button, #routeList li, #routeList .row').length);
    console.log(`[${ORIGIN}] route: ${out.slice(0, 160)} ... list entries: ${listed}`);
  } else console.log(`[${ORIGIN}] route: not attempted, a place search gave no result`);
  const by = {};
  for(const s of stadia){ const k = `${s.kind} ${s.method} HTTP ${s.status} key=${s.key} referer=${s.referer} origin=${s.origin}`; by[k] = (by[k] || 0) + 1; }
  console.log(`[${ORIGIN}] Stadia responses:`); for(const [k, n] of Object.entries(by)) console.log(`   ${n} x ${k}`);
  console.log(`[${ORIGIN}] any request carrying api_key: ${stadia.some(s => s.key)}`);
  console.log(`[${ORIGIN}] page errors: ${JSON.stringify(errors)}`);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
