// TEMPORARY probe, removed before merge. Runs on a GitHub runner (the sandbox cannot reach Stadia).
//  1. Headers Stadia sends on tiles, place search and routing, from the real domain and a refused one
//     (CORS on a refused tile decides how item 2 can read the refusal; Cache-Control decides how long
//     a search result may be kept under Stadia's terms (c)).
//  2. The terms page, re-read: the paragraphs on caching and storage.
//  3. The checkout's index.html in headless Chromium, served AS IF from https://alexgrozavul.github.io/Football/
//     and from a refused made-up domain, every Stadia request real: tiles, a place search, a route.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const MODE = process.argv[3] || 'all';
const TILE = 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/8/134/89.png';
const GOOD = 'https://alexgrozavul.github.io', BAD = 'https://fbplanner-q7x2k-test.net';
const H = r => Object.fromEntries(['access-control-allow-origin','cache-control','expires','content-type','content-length','vary','age','etag','last-modified']
  .map(k => [k, r.headers.get(k)]).filter(([, v]) => v != null));

async function headers(){
  for(const [name, origin] of [['real domain', GOOD], ['refused domain', BAD], ['no origin', null]]){
    const hdr = origin ? {Origin: origin, Referer: origin + '/Football/'} : {};
    const t = await fetch(TILE, {headers: hdr});
    const tb = Buffer.from(await t.arrayBuffer());
    console.log(`TILE ${name}: ${t.status} ${JSON.stringify(H(t))} bytes=${tb.length} png=${tb.slice(1,4).toString()}`);
    const g = await fetch('https://api.stadiamaps.com/geocoding/v1/search?text=Leonberg&size=1', {headers: hdr});
    const gt = await g.text();
    console.log(`SEARCH ${name}: ${g.status} ${JSON.stringify(H(g))} body=${gt.slice(0, 160).replace(/\s+/g, ' ')}`);
    if(origin !== BAD){
      const r = await fetch('https://api.stadiamaps.com/route/v1', {method: 'POST', headers: {...hdr, 'Content-Type': 'application/json'},
        body: JSON.stringify({locations: [{lat: 48.8003, lon: 9.0167}, {lat: 48.7758, lon: 9.1829}], costing: 'auto', units: 'kilometers', directions_type: 'none'})});
      const rj = await r.json().catch(() => null);
      console.log(`ROUTE ${name}: ${r.status} ${JSON.stringify(H(r))} legs=${rj?.trip?.legs?.length} shapeChars=${rj?.trip?.legs?.[0]?.shape?.length} km=${rj?.trip?.summary?.length}`);
    }
  }
  // CORS preflight-free GET of a tile from a refused origin, as a browser fetch would see it
  const pre = await fetch(TILE, {method: 'OPTIONS', headers: {Origin: BAD, 'Access-Control-Request-Method': 'GET'}});
  console.log(`TILE OPTIONS refused origin: ${pre.status} ${JSON.stringify(H(pre))}`);
}

async function terms(){
  const r = await fetch('https://stadiamaps.com/terms-of-service/', {headers: {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36'}});
  const html = await r.text();
  const text = html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g, ' ').replace(/<[^>]+>/g, '\n').replace(/&nbsp;/g, ' ')
    .replace(/&#8217;|&rsquo;/g, "'").replace(/&#8220;|&#8221;|&ldquo;|&rdquo;/g, '"').replace(/&amp;/g, '&');
  const paras = text.split(/\n\s*\n|\n/).map(s => s.replace(/\s+/g, ' ').trim()).filter(Boolean);
  console.log(`TERMS HTTP ${r.status}, ${html.length} bytes`);
  for(const p of paras) if(/effective/i.test(p) && p.length < 200) console.log('TERMS> ' + p);
  for(const p of paras) if(/cach|permanent|stor(e|ing|age)|offline|mobile application/i.test(p)) console.log('TERMS> ' + p);
}

async function page(origin, label){
  const browser = await chromium.launch({headless: true});
  const ctx = await browser.newContext({viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true, serviceWorkers: 'block'});
  const reqs = [];
  ctx.on('request', r => { if(/stadiamaps/.test(r.url())) reqs.push(r); });
  await ctx.route(origin + '/Football/**', route => {
    let p = new URL(route.request().url()).pathname.replace(/^\/Football\//, '');
    if(!p) p = 'index.html';
    const f = path.join(ROOT, p);
    if(!fs.existsSync(f)) return route.fulfill({status: 404, body: 'nf'});
    const ext = path.extname(f);
    route.fulfill({status: 200, body: fs.readFileSync(f), contentType: {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.csv': 'text/csv', '.png': 'image/png', '.webmanifest': 'application/manifest+json'}[ext] || 'application/octet-stream'});
  });
  const pg = await ctx.newPage();
  const errors = []; pg.on('pageerror', e => errors.push(e.message));
  await pg.goto(origin + '/Football/');
  await pg.waitForFunction(() => typeof CLUBS !== 'undefined' && CLUBS.length > 0, null, {timeout: 60000});
  await pg.waitForTimeout(6000);
  const tiles = await pg.evaluate(() => {
    const imgs = [...document.querySelectorAll('.leaflet-tile')];
    return {n: imgs.length, loaded: imgs.filter(i => i.classList.contains('leaflet-tile-loaded')).length,
      card: document.getElementById('mapOffline').getBoundingClientRect().height > 0, cardText: document.getElementById('mapOffline').textContent.replace(/\s+/g, ' ').trim()};
  });
  const tileResp = [];
  for(const r of reqs.filter(r => /tiles\./.test(r.url())).slice(0, 4)){ const res = await r.response(); tileResp.push(res ? res.status() : 'none'); }
  console.log(`PAGE ${label}: tiles ${tiles.loaded}/${tiles.n} "loaded", tile HTTP ${tileResp.join(',')}, card ${tiles.card} "${tiles.cardText}"`);
  await pg.click('#routeChip');
  for(const [end, text] of [['from', 'Leonberg'], ['to', 'Augsburg']]){
    await pg.fill(`#routeBody .pt[data-end="${end}"] input`, text);
    await pg.click(`#routeBody .pt[data-end="${end}"] button[data-act="find"]`);
    await pg.waitForFunction(e => { const h = document.querySelector(`#routeBody .pt[data-end="${e}"] .hits`); return h.querySelector('button') || h.querySelector('.err'); }, end, {timeout: 30000}).catch(() => {});
    const hits = await pg.textContent(`#routeBody .pt[data-end="${end}"] .hits`);
    console.log(`PAGE ${label}: search "${text}" -> ${hits.replace(/\s+/g, ' ').trim().slice(0, 160)}`);
    const b = await pg.$(`#routeBody .pt[data-end="${end}"] .hits button`);
    if(b) await b.click();
  }
  if(!(await pg.$eval('#routeGo', b => b.disabled))){
    await pg.click('#routeGo');
    await pg.waitForFunction(() => !/Asking Stadia/.test(document.getElementById('routeOut').textContent), null, {timeout: 60000});
    await pg.waitForTimeout(1500);
    console.log(`PAGE ${label}: route -> ${(await pg.textContent('#routeOut')).replace(/\s+/g, ' ').trim().slice(0, 200)}`);
  }else console.log(`PAGE ${label}: route not attempted, ends not set`);
  if(await pg.$('#routeSave')){
    await pg.click('#routeSave'); await pg.waitForTimeout(500);
    const n0 = reqs.filter(r => /route\/v1/.test(r.url())).length;
    await pg.reload(); await pg.waitForFunction(() => typeof CLUBS !== 'undefined' && CLUBS.length > 0, null, {timeout: 60000});
    await pg.click('#routeChip'); await pg.waitForTimeout(500); await pg.click('#savedRoutes summary');
    await pg.click('#savedRoutes [data-act="open"]'); await pg.waitForTimeout(2000);
    const n1 = reqs.filter(r => /route\/v1/.test(r.url())).length;
    console.log(`PAGE ${label}: saved, reloaded, opened: route requests ${n0} -> ${n1}; ${(await pg.textContent('#routeOut')).replace(/\s+/g, ' ').slice(0, 160)}`);
    await pg.click('#routeChip'); await pg.click('#routeChip'); await pg.waitForTimeout(300);
    console.log(`PAGE ${label}: credits line: ${await pg.textContent('#routeCredits')}`);
  }
  const keyed = reqs.filter(r => /api_key=/.test(r.url()));
  const sample = reqs.slice(0, 1).map(r => r.headers());
  console.log(`PAGE ${label}: ${reqs.length} Stadia requests, ${keyed.length} carrying api_key; first request headers ${JSON.stringify(sample)}`);
  console.log(`PAGE ${label}: script errors: ${errors.length ? errors.join(' | ') : 'none'}`);
  await pg.screenshot({path: `/tmp/probe-${label}.png`});
  await browser.close();
}

(async () => {
  if(MODE === 'all' || MODE === 'headers') { try{ await headers(); }catch(e){ console.log('HEADERS FAILED ' + e.message); } }
  if(MODE === 'all' || MODE === 'terms') { try{ await terms(); }catch(e){ console.log('TERMS FAILED ' + e.message); } }
  if(MODE === 'all' || MODE === 'page'){
    try{ await page(GOOD, 'real-domain'); }catch(e){ console.log('PAGE real-domain FAILED ' + e.message); }
    try{ await page(BAD, 'refused-domain'); }catch(e){ console.log('PAGE refused-domain FAILED ' + e.message); }
  }
})();
