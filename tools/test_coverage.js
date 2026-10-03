// Headless Chromium test of the coverage panel (the club-count chip), at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright            (anywhere; it is not a dependency of this repo)
//   node tools/test_coverage.js .     (serves the checkout itself; it changes no file)
//
// Counts the club files here, independently of the page, and checks the panel against them:
// tapping the chip opens it; the total clubs and total leagues are the files' own counts (a
// league is a competition name the club data records, counted per country and tier); the
// per-tier lines add up to both totals; every league in the list is a name the data holds,
// and clubs with none sit under "league not recorded (tier N)", never under a made-up name;
// the tier and country filters narrow the list correctly; a league lists exactly its clubs;
// tapping a club flies to it at a zoom where it is drawn and opens its sheet above the panel;
// the panel shares one layer with Route and Derbies; no sideways scroll; no script error.
// Stadia's tiles are stubbed. CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8770, BASE = `http://localhost:${PORT}/Football/`;
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

// The files' own counts.
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const listed = JSON.parse(html.match(/const COUNTRY_FILES = (\[[^\]]*\])/)[1].replace(/'/g, '"'));
const files = {clubs: 0, leagues: new Set(), names: new Set(), unrecorded: 0, byTier: {}, byCountry: {}};
for(const f of listed){
  const d = JSON.parse(fs.readFileSync(path.join(ROOT, f), 'utf8'));
  for(const c of d.clubs || []){
    if(c.lat == null || c.lon == null || c.tier == null) continue;
    files.clubs++;
    const t = files.byTier[c.tier] ||= {clubs: 0, leagues: new Set()};
    t.clubs++;
    files.byCountry[d.country] = (files.byCountry[d.country] || 0) + 1;
    if(c.competition){ const k = `${d.country}|${c.tier}|${c.competition}`; files.leagues.add(k); t.leagues.add(k); files.names.add(c.competition); }
    else files.unrecorded++;
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
  const noSideScroll = () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);

  // ---- open it
  await page.tap('#zoomChip');
  await page.waitForSelector('#covClubs');
  await page.waitForTimeout(400);
  const P = await page.evaluate(() => ({
    visible: document.getElementById('coveragePanel').getBoundingClientRect().top < innerHeight - 100,
    clubs: Number(document.getElementById('covClubs').textContent),
    leagues: Number(document.getElementById('covLeagues').textContent),
    bigClubs: parseFloat(getComputedStyle(document.getElementById('covClubs')).fontSize),
    tierFont: parseFloat(getComputedStyle(document.querySelector('.covtiers')).fontSize),
    clubsLeft: document.getElementById('covClubs').getBoundingClientRect().left,
    leaguesRight: document.getElementById('covLeagues').getBoundingClientRect().right,
    tiers: [...document.querySelectorAll('.covtiers tr')].map(tr => ({tier: tr.dataset.tier,
      clubs: Number(tr.children[1].textContent.match(/\d+/)[0]),
      leagues: Number((tr.children[2].textContent.match(/^(\d+) league/) || [0, 0])[1])})),
    rows: [...document.querySelectorAll('#covList .covl')].map(b => ({name: b.querySelector('.rn').firstChild.textContent,
      n: Number(b.querySelector('em').textContent.match(/\d+/)[0])}))}));
  console.log(`    panel: ${P.clubs} clubs, ${P.leagues} leagues; files: ${files.clubs} clubs, ${files.leagues.size} leagues, ` +
    `${files.unrecorded} with no league recorded`);
  console.log('    per tier:', P.tiers.map(t => `tier ${t.tier} ${t.clubs}/${t.leagues}`).join(', '));
  check('tapping the club-count chip opens the panel, on screen', P.visible);
  check('total clubs is the files\' count', P.clubs === files.clubs, `${P.clubs} against ${files.clubs}`);
  check('total leagues is the files\' count of recorded competitions', P.leagues === files.leagues.size, `${P.leagues} against ${files.leagues.size}`);
  check('clubs on the left, leagues on the right, both large', P.clubsLeft < 60 && P.leaguesRight > 330 && P.bigClubs >= 2 * P.tierFont,
    `${P.bigClubs}px against ${P.tierFont}px`);
  check('the per-tier lines match the files', P.tiers.every(t => files.byTier[t.tier] && files.byTier[t.tier].clubs === t.clubs &&
    files.byTier[t.tier].leagues.size === t.leagues) && P.tiers.length === Object.keys(files.byTier).length);
  check('the per-tier clubs add up to the total', P.tiers.reduce((a, t) => a + t.clubs, 0) === P.clubs);
  check('the per-tier leagues add up to the total', P.tiers.reduce((a, t) => a + t.leagues, 0) === P.leagues);
  check('the list holds every club once', P.rows.reduce((a, r) => a + r.n, 0) === files.clubs);
  const named = P.rows.filter(r => !/^league not recorded \(tier \d+\)$/.test(r.name));
  check('every league in the list is a competition the data names, none made up',
    named.every(r => files.names.has(r.name)) && named.length === files.leagues.size,
    named.filter(r => !files.names.has(r.name)).map(r => r.name).join(', '));
  const unnamed = P.rows.filter(r => /^league not recorded/.test(r.name));
  check('clubs with no recorded competition are under "league not recorded (tier N)"',
    unnamed.reduce((a, r) => a + r.n, 0) === files.unrecorded, unnamed.map(r => `${r.name} ${r.n}`).join('; '));
  check('no sideways scroll on the panel', await noSideScroll());
  await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', 'coverage-phone.png')});

  // ---- filters
  const listNow = () => page.evaluate(() => ({
    heads: [...document.querySelectorAll('#covList .covc')].map(h => h.textContent),
    rows: [...document.querySelectorAll('#covList .covl')].map(b => ({name: b.querySelector('.rn').firstChild.textContent,
      tier: b.querySelector('.rd').textContent, n: Number(b.querySelector('em').textContent.match(/\d+/)[0])}))}));
  await page.selectOption('#covTier', '3');
  let F = await listNow();
  check('the tier filter shows tier 3 only', F.rows.length > 0 && F.rows.every(r => r.tier === 'Tier 3'),
    F.rows.map(r => r.name).join('; '));
  check('tier 3 holds every tier-3 club', F.rows.reduce((a, r) => a + r.n, 0) === files.byTier[3].clubs);
  await page.selectOption('#covTier', '');
  await page.selectOption('#covCountry', 'RO');
  F = await listNow();
  check('the country filter shows one country', F.heads.length === 1 && /^Romania/i.test(F.heads[0]) &&
    F.rows.reduce((a, r) => a + r.n, 0) === files.byCountry.RO, F.heads.join(' | '));
  await page.selectOption('#covCountry', 'DE');
  await page.selectOption('#covTier', '4');
  F = await listNow();
  check('both filters together: German tier 4, "league not recorded (tier 4)" among them',
    F.rows.every(r => r.tier === 'Tier 4') && F.rows.some(r => r.name === 'league not recorded (tier 4)'),
    F.rows.map(r => `${r.name} ${r.n}`).join('; '));

  // ---- a league, then a club
  const league = F.rows.find(r => r.name !== 'league not recorded (tier 4)');
  await page.$$eval('#covList .covl', (bs, name) => bs.find(b => b.querySelector('.rn').firstChild.textContent === name).click(), league.name);
  await page.waitForSelector('#covClubsList');
  const L = await page.evaluate(() => ({title: document.getElementById('covTitle').textContent,
    clubs: [...document.querySelectorAll('#covClubsList .rclub .rn')].map(e => e.firstChild.textContent)}));
  const inData = await page.evaluate(name => CLUBS.filter(c => c.competition === name && c.country === 'DE').map(c => c.name).sort(), league.name);
  check(`tapping ${league.name} lists exactly its clubs`, L.title === league.name &&
    JSON.stringify(L.clubs.slice().sort()) === JSON.stringify(inData), `${L.clubs.length} listed, ${inData.length} in the data`);
  await page.tap('#covClubsList .rclub');
  await page.waitForFunction(n => !document.getElementById('sheet').hidden && document.querySelector('#sheetHead h3').textContent === n,
    L.clubs[0], {timeout: 8000}).catch(() => {});
  await page.waitForTimeout(400);
  const S = await page.evaluate(n => {
    const c = CLUBS.find(c => c.name === n);
    let drawn = false;
    LAYER.eachLayer(l => { const ll = l.getLatLng(); if(ll.lat === c.lat && ll.lng === c.lon) drawn = true; });
    const s = document.getElementById('sheet').getBoundingClientRect();
    const el = document.elementFromPoint(s.left + s.width / 2, s.top + 20);
    return {title: document.querySelector('#sheetHead h3').textContent, zoom: MAP.getZoom(), need: zoomForTier(c.tier), drawn,
      onTop: document.getElementById('sheet').contains(el)};
  }, L.clubs[0]);
  check(`tapping ${L.clubs[0]} flies to it and opens its sheet`, S.title === L.clubs[0] && S.zoom >= S.need && S.drawn, JSON.stringify(S));
  check('the sheet sits on top of the panel', S.onTop);
  await page.tap('#sheetClose');
  await page.tap('#covBack');
  check('back returns to the list, filters kept', await page.evaluate(() =>
    !!document.getElementById('covList') && document.getElementById('covTier').value === '4' &&
    document.getElementById('covCountry').value === 'DE'));

  // ---- one layer with Route and Near me
  await page.tap('#routeChip');
  let st = await page.evaluate(() => ['coveragePanel', 'routePanel', 'nearPanel'].map(id => document.getElementById(id).hidden));
  check('opening Route closes the coverage panel', st[0] && !st[1], JSON.stringify(st));
  await page.tap('#zoomChip');
  st = await page.evaluate(() => ['coveragePanel', 'routePanel', 'nearPanel'].map(id => document.getElementById(id).hidden));
  check('opening the coverage panel closes Route', !st[0] && st[1], JSON.stringify(st));
  await page.tap('#nearChip');
  st = await page.evaluate(() => ['coveragePanel', 'routePanel', 'nearPanel'].map(id => document.getElementById(id).hidden));
  check('opening Near me closes the coverage panel', st[0] && !st[2], JSON.stringify(st));

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
