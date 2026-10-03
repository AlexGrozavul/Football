// Headless Chromium test of the map tab's Derbies panel, at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page; by hand after changing data/derbies.csv:
//
//   npm install playwright            (anywhere; it is not a dependency of this repo)
//   node tools/test_derbies.js .      (serves the checkout itself; it changes no file)
//
// Serves the repo at http://localhost:8766/Football/, stubs Stadia's tiles, and checks:
// the Near me chip, then its Derbies tab, opens a list at the 100 km default, nearest first, every row with
// both clubs on the map and inside the distance; the slider widens it; tapping a derby
// shows both clubs and a next-meeting section that says one of the four honest
// answers; a club sheet opens from it above the panel; the page never scrolls
// sideways; no script error. Exits 1 on any failure.
// CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8766, BASE = `http://localhost:${PORT}/Football/`;
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
  await page.waitForFunction(() => typeof CLUBS !== 'undefined' && CLUBS.length > 0 && HOME, null, {timeout: 30000});

  const csvRows = fs.readFileSync(path.join(ROOT, 'data/derbies.csv'), 'utf8').trim().split('\n').length - 1;
  const noSideScroll = () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);

  // ---- 1. the list at the default distance
  // Since 2026-10-03 the derbies are the second tab of the Near me panel.
  await page.tap('#nearChip');
  await page.waitForSelector('#nearBody h4');
  await page.tap('#tabDerbies');
  await page.waitForSelector('#derbyBody h4');
  await page.waitForTimeout(500);                // the panel slides up for 0.22 s
  const list = async () => page.evaluate(() => {
    const head = document.querySelector('#derbyBody h4').textContent;
    const rows = [...document.querySelectorAll('#derbyBody .rclub')].map(b => {
      const t = b.querySelectorAll('.rd')[1].textContent;
      return {name: b.querySelector('.rn').firstChild.textContent, near: Number(t.match(/≈ (\d+) km/)[1]),
              other: Number(t.match(/· ≈ (\d+) km/)[1])};
    });
    return {head, rows, foot: [...document.querySelectorAll('#derbyBody .sub')].map(s => s.textContent).join(' | '),
            visible: document.getElementById('nearPanel').getBoundingClientRect().top < innerHeight - 100 &&
              !document.getElementById('derbyBody').hidden && document.getElementById('nearBody').hidden};
  });
  let L = await list();
  console.log('    100 km:', L.head, '-', L.rows.map(r => `${r.name} ${r.near}/${r.other}`).join('; '));
  check('Near me, then the Derbies tab, opens the derby list on screen', L.visible);
  check('default distance is 100 km', /within 100 km/.test(L.head), L.head);
  check('every listed derby is within 100 km of home', L.rows.every(r => r.near <= 100));
  check('nearest first', L.rows.every((r, i) => !i || L.rows[i-1].near <= r.near));
  check('each row shows both grounds, the nearer first', L.rows.every(r => r.near <= r.other));
  const expected = await page.evaluate(async () => {
    const D = await loadDerbies();
    return {both: D.shown.length, off: D.offMap.length, bad: D.malformed.length,
      within: D.shown.filter(d => Math.min(roadEstimate(d.a.lat, d.a.lon), roadEstimate(d.b.lat, d.b.lon)) <= 100).length};
  });
  check('the list holds exactly the derbies with both clubs on the map within 100 km', L.rows.length === expected.within,
    JSON.stringify(expected));
  check('every row of the file is accounted for (shown, off the map, or malformed)',
    expected.both + expected.off + expected.bad === csvRows, `${csvRows} rows in the file`);
  check('no sideways scroll on the list', await noSideScroll());

  // ---- 2. the slider widens the list
  await page.$eval('#derbyKm', el => { el.value = '1500'; el.dispatchEvent(new Event('input')); el.dispatchEvent(new Event('change')); });
  await page.waitForFunction(() => /within 1500 km/.test(document.querySelector('#derbyBody h4').textContent));
  const W = await list();
  check('the slider widens the list', W.rows.length >= L.rows.length && W.rows.length > 0, `${W.rows.length} at 1500 km`);
  check('slider value survives a redraw', await page.$eval('#derbyKm', el => el.value) === '1500');

  // ---- 3. every derby's detail says one of the honest answers
  const answers = {};
  for(let i = 0; i < W.rows.length; i++){
    await page.$$eval('#derbyBody .rclub', (bs, i) => bs[i].click(), i);
    await page.waitForFunction(() => document.querySelector('#derbyNext') &&
      !/Loading/.test(document.querySelector('#derbyNext').textContent), null, {timeout: 20000});
    const d = await page.evaluate(() => ({
      title: document.getElementById('derbyTitle').textContent,
      clubs: document.querySelectorAll('#derbyBody .dclub').length,
      next: document.getElementById('derbyNext').textContent,
      cup: /different divisions/.test(document.getElementById('derbyBody').textContent),
      probably: /Probably not played this season/.test(document.getElementById('derbyBody').textContent),
      src: document.querySelectorAll('#derbyBody a[href^="http"]').length}));
    const kind = /has no fixture source/.test(d.next) ? 'no source'
      : /different fixture sources/.test(d.next) ? 'different sources'
      : /No meeting in the fixture data/.test(d.next) ? 'no meeting'
      : /German time/.test(d.next) ? 'meeting' : 'OTHER';
    (answers[kind] ||= []).push(d.title);
    if(kind === 'OTHER' || d.clubs !== 2 || !d.src || d.cup !== d.probably)
      check(`detail of ${d.title}`, false, JSON.stringify(d));
    if(i === 0) check('no sideways scroll on a detail', await noSideScroll());
    await page.tap('#derbyBack');
    await page.waitForSelector('#derbyBody .rclub');
  }
  for(const [k, v] of Object.entries(answers)) console.log(`    ${k} (${v.length}): ${v.join('; ')}`);
  check('every detail shows two clubs, a source, and a known next-meeting answer', !answers.OTHER);

  // ---- 4. a meeting row uses the sheet's date handling; a club sheet opens above the panel
  const withMeeting = (answers.meeting || [])[0];
  if(withMeeting){
    const i = W.rows.findIndex(r => r.name === withMeeting);
    await page.$$eval('#derbyBody .rclub', (bs, i) => bs[i].click(), i);
    await page.waitForFunction(() => /German time/.test(document.getElementById('derbyNext').textContent));
    const when = await page.$eval('#derbyNext .fx .when', el => el.textContent);
    check(`next meeting of ${withMeeting} has a date (and "time not set" where the time is a placeholder)`,
      /\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b/.test(when) && (/\d\d:\d\d/.test(when) || /time not set/.test(when)), when);
    await page.tap('#derbyBody .dclub button');
    await page.waitForFunction(() => !document.getElementById('sheet').hidden);
    await page.waitForTimeout(500);              // the sheet slides up for 0.22 s
    const top = await page.evaluate(() => {
      const s = document.getElementById('sheet').getBoundingClientRect();
      const el = document.elementFromPoint(s.left + s.width / 2, s.top + 20);
      return document.getElementById('sheet').contains(el) || (el ? el.id || el.className : 'nothing');
    });
    check('a club sheet opened from a derby sits on top of the panel', top === true, String(top));
    await page.tap('#sheetClose');
  }else check('at least one derby with a meeting in the fixture data, to test the date handling', false);

  // ---- 5. the route chip closes the derby panel
  await page.tap('#routeChip');
  const both = await page.evaluate(() => [document.getElementById('nearPanel').hidden, document.getElementById('routePanel').hidden]);
  check('opening Route closes the Near me panel', both[0] === true && both[1] === false, JSON.stringify(both));

  check('no script error', !errors.length, errors.join(' | '));
  await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', 'derbies-phone.png')});
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
