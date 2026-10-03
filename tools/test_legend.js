// Headless Chromium test of the map's collapsible tier legend, added 2026-10-03.
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright          (anywhere; it is not a dependency of this repo)
//   node tools/test_legend.js .     (serves the checkout itself; it changes no file)
//
// What it checks, at 390x700 and 390x500 (and 390x300 for the scrolling fallback):
//  1. The legend starts closed on a first visit: only "Leagues shown" and an arrow are visible,
//     and the tier rows and the shared-ground row are not.
//  2. The header is a real button with aria-expanded, at least 44 px tall.
//  3. A tap opens it and a second tap closes it; the arrow rotates (its transform changes).
//  4. Open, "Leagues shown" is a header above every tier row and the shared-ground row, the rows
//     are the ones the page defines (TIER_NAME) and the zoom dimming still follows zoomForTier.
//  5. Open, the legend never overlaps the attribution bar or the bottom navigation, and does not
//     reach the top row, at both heights - including when the attribution wraps to several lines
//     and when the window shrinks while it is open. Every row is fully visible, or, on a screen
//     too short for them, the legend scrolls inside itself with its header kept in view and the
//     last row reachable.
//  6. The choice survives a reload, open or closed; and with storage blocked the legend still
//     works for the visit, starting closed, with no script error.
// Stadia's tiles are stubbed. CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8773, BASE = `http://localhost:${PORT}/Football/`;
const W = 390;
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

  const newPage = async (height, {blockStorage = false, ctx = null} = {}) => {
    ctx = ctx || await browser.newContext({viewport: {width: W, height}, isMobile: true, hasTouch: true,
      deviceScaleFactor: 2, serviceWorkers: 'block'});
    await ctx.route('https://tiles.stadiamaps.com/**', r => r.fulfill({status:200, contentType:'image/png', headers: {'Access-Control-Allow-Origin': '*'}, body: PNG}));
    await ctx.route('https://api.stadiamaps.com/**', r => r.abort());
    if(blockStorage) await ctx.addInitScript(() => {
      Object.defineProperty(window, 'localStorage', {get(){ throw new DOMException('blocked', 'SecurityError'); }});
    });
    const page = await ctx.newPage();
    page.errors = [];
    page.on('pageerror', e => page.errors.push(e.message));
    await page.goto(BASE);
    await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
    await page.waitForTimeout(400);
    return page;
  };

  /* What is on screen: the legend's own text as the user sees it, its header, and the rectangles
     the overlap checks compare. visibility counts: a hidden body has no height. */
  const state = page => page.evaluate(() => {
    const R = el => { const r = el.getBoundingClientRect(); return {top: r.top, bottom: r.bottom, left: r.left, right: r.right, h: r.height}; };
    const q = s => document.querySelector(s);
    const head = q('#legendToggle'), body = q('#legendBody');
    const rows = [...document.querySelectorAll('#legend .lbody div')];
    return {
      text: q('#legend').innerText.replace(/\s+/g, ' ').trim(),
      tag: head.tagName, expanded: head.getAttribute('aria-expanded'), headText: head.textContent.trim(),
      arrow: getComputedStyle(head.querySelector('.larr')).transform,
      bodyHidden: body.hidden, bodyVisible: body.getBoundingClientRect().height > 0,
      legend: R(q('#legend')), head: R(head), body: R(body),
      attr: q('.leaflet-control-attribution') ? R(q('.leaflet-control-attribution')) : null,
      nav: R(q('nav')), bar: R(q('.bar')), pane: R(q('#pane-map')),
      rows: rows.map(r => ({text: r.textContent.trim(), tier: r.dataset.tier || null, shared: r.classList.contains('shared'),
        off: r.classList.contains('off'), ...R(r)})),
      body_scroll: {sh: body.scrollHeight, ch: body.clientHeight},
      zoom: MAP.getZoom(),
      expectOff: Object.keys(TIER_COLOUR).map(t => [t, MAP.getZoom() < zoomForTier(Number(t))]),
      tierNames: Object.keys(TIER_COLOUR).map(t => TIER_NAME[t]),
      stored: (() => { try{ return localStorage.getItem('football-planner-legend-open'); }catch(e){ return 'blocked'; } })(),
    };
  });
  const overlaps = (a, b) => a && b && a.top < b.bottom - 0.5 && a.bottom > b.top + 0.5 && a.left < b.right - 0.5 && a.right > b.left + 0.5;
  const tapToggle = async page => { await page.tap('#legendToggle'); await page.waitForTimeout(300); };

  // ---- 1-4. First visit, toggle, structure, at 390x700
  let page = await newPage(700);
  let s = await state(page);
  check('1. first visit: the legend starts closed', s.expanded === 'false' && s.bodyHidden && !s.bodyVisible, `aria-expanded=${s.expanded}`);
  check('1. closed, the visible legend text is only "Leagues shown"', s.text === 'Leagues shown', JSON.stringify(s.text));
  check('1. nothing was stored by just visiting', s.stored === null, String(s.stored));
  check('2. the header is a real <button> with aria-expanded', s.tag === 'BUTTON' && (s.expanded === 'true' || s.expanded === 'false'), s.tag);
  check('2. the header says "Leagues shown"', s.headText === 'Leagues shown', s.headText);
  check(`2. the header is at least 44 px tall (${s.head.h.toFixed(1)})`, s.head.h >= 44);
  const closedArrow = s.arrow;

  await tapToggle(page);
  s = await state(page);
  check('3. a tap opens it', s.expanded === 'true' && !s.bodyHidden && s.bodyVisible, `aria-expanded=${s.expanded}`);
  check('3. the arrow rotates when it opens', s.arrow !== closedArrow, `${closedArrow} -> ${s.arrow}`);
  const openArrow = s.arrow;
  check('3. the choice is stored on the device', s.stored === '1', String(s.stored));

  const tierRows = s.rows.filter(r => r.tier), sharedRow = s.rows.find(r => r.shared);
  check(`4. the legend holds ${s.tierNames.length} tier rows and the shared-ground row`,
    tierRows.length === s.tierNames.length && !!sharedRow && s.rows.length === tierRows.length + 1, `${tierRows.length} tier rows`);
  check('4. the tier rows are the page\'s own tier names, in order', JSON.stringify(tierRows.map(r => r.text)) === JSON.stringify(s.tierNames),
    tierRows.map(r => r.text).join(' | '));
  check('4. the shared-ground row reads "Shared ground, tap for the list"', !!sharedRow && /^2\s*Shared ground\s.+\stap for the list$/.test(sharedRow.text.replace(/\s+/g, ' ')), sharedRow && sharedRow.text);
  check('4. "Leagues shown" is a header above every tier row and the shared-ground row',
    s.rows.every(r => s.head.bottom <= r.top + 0.5), `header bottom ${s.head.bottom.toFixed(1)}, first row top ${Math.min(...s.rows.map(r => r.top)).toFixed(1)}`);
  check('4. the rows run in order, tier 1 first and the shared-ground row last',
    s.rows.every((r, i) => i === 0 || r.top >= s.rows[i - 1].top) && s.rows[s.rows.length - 1].shared);
  const dimWrong = s.expectOff.filter(([t, off]) => tierRows.find(r => r.tier === t).off !== off).map(([t]) => t);
  check(`4. the zoom dimming still follows zoomForTier at z${s.zoom} (tiers dimmed: ${s.expectOff.filter(e => e[1]).map(e => e[0]).join(',') || 'none'})`, !dimWrong.length, dimWrong.join(','));
  await page.evaluate(() => MAP.setZoom(9, {animate: false}));
  await page.waitForTimeout(400);
  s = await state(page);
  check('4. at z9 no tier row is dimmed', !s.rows.filter(r => r.tier && r.off).length, s.rows.filter(r => r.off).map(r => r.tier).join(','));
  await page.evaluate(() => MAP.setZoom(8, {animate: false}));
  await page.waitForTimeout(300);

  await tapToggle(page);
  s = await state(page);
  check('3. a second tap closes it', s.expanded === 'false' && s.bodyHidden && s.text === 'Leagues shown', `aria-expanded=${s.expanded}`);
  check('3. the arrow rotates back when it closes', s.arrow === closedArrow && s.arrow !== openArrow);
  check('3. the closed choice is stored too', s.stored === '0', String(s.stored));
  check('no script error (toggle)', !page.errors.length, page.errors.join(' | '));
  await page.context().close();

  // ---- 5. Clear of the attribution bar and the bottom navigation, at both heights
  for(const H of [700, 500]){
    page = await newPage(H);
    await tapToggle(page);
    s = await state(page);
    const where = `390x${H}`;
    check(`5. ${where}: the open legend does not overlap the attribution bar`, !overlaps(s.legend, s.attr),
      `legend ${s.legend.top.toFixed(0)}..${s.legend.bottom.toFixed(0)}, attribution ${s.attr && s.attr.top.toFixed(0)}..${s.attr && s.attr.bottom.toFixed(0)}`);
    check(`5. ${where}: it does not overlap the bottom navigation`, !overlaps(s.legend, s.nav) && s.legend.bottom <= s.nav.top + 0.5,
      `legend bottom ${s.legend.bottom.toFixed(0)}, navigation top ${s.nav.top.toFixed(0)}`);
    check(`5. ${where}: it does not reach the top row`, s.legend.top >= s.bar.bottom - 0.5, `legend top ${s.legend.top.toFixed(0)}, top row bottom ${s.bar.bottom.toFixed(0)}`);
    const last = s.rows[s.rows.length - 1];
    check(`5. ${where}: the last row, "Shared ground", is fully visible inside the legend`,
      last.bottom <= s.legend.bottom + 0.5 && last.top >= s.head.bottom - 0.5 && s.body_scroll.sh <= s.body_scroll.ch + 1,
      `row ${last.top.toFixed(0)}..${last.bottom.toFixed(0)}, legend bottom ${s.legend.bottom.toFixed(0)}, body ${s.body_scroll.sh}/${s.body_scroll.ch}`);

    // The attribution wraps to several lines on some phones: force it to, and check again.
    await page.addStyleTag({content: '.leaflet-control-attribution{max-width:150px!important;white-space:normal!important}'});
    await page.waitForTimeout(400);
    s = await state(page);
    check(`5. ${where}: with the attribution wrapped to ${Math.round(s.attr.h)} px, the legend still clears it`,
      s.attr.h > 30 && !overlaps(s.legend, s.attr) && s.legend.bottom <= s.attr.top + 0.5,
      `legend bottom ${s.legend.bottom.toFixed(0)}, attribution top ${s.attr.top.toFixed(0)} (${s.attr.h.toFixed(0)} px tall)`);
    check(`5. ${where}: and it still clears the top row and the bottom navigation`,
      s.legend.top >= s.bar.bottom - 0.5 && s.legend.bottom <= s.nav.top + 0.5);

    // Shrinking the window while open (the phone's keyboard does this).
    const shrink = Math.max(300, H - 160);
    await page.setViewportSize({width: W, height: shrink});
    await page.waitForTimeout(500);
    s = await state(page);
    check(`5. ${where}: after the window shrinks to ${shrink} px the legend still clears the attribution bar, the top row and the navigation`,
      !overlaps(s.legend, s.attr) && s.legend.bottom <= s.nav.top + 0.5 && s.legend.top >= s.bar.bottom - 0.5,
      `legend ${s.legend.top.toFixed(0)}..${s.legend.bottom.toFixed(0)}, top row bottom ${s.bar.bottom.toFixed(0)}, attribution top ${s.attr.top.toFixed(0)}`);
    check(`5. ${where}: no script error`, !page.errors.length, page.errors.join(' | '));
    await page.context().close();
  }

  // ---- 5. A screen too short for every row: the legend scrolls inside itself
  page = await newPage(300);
  await tapToggle(page);
  s = await state(page);
  check('5. 390x300: too short for every row, so the legend caps its height and scrolls inside itself',
    s.body_scroll.sh > s.body_scroll.ch + 1 && s.legend.top >= s.bar.bottom - 0.5 && !overlaps(s.legend, s.attr) && s.legend.bottom <= s.nav.top + 0.5,
    `body ${s.body_scroll.sh}/${s.body_scroll.ch}, legend ${s.legend.top.toFixed(0)}..${s.legend.bottom.toFixed(0)}`);
  check('5. 390x300: the header stays in view', s.head.top >= s.legend.top - 0.5 && s.head.bottom <= s.legend.bottom + 0.5);
  await page.evaluate(() => { const b = document.getElementById('legendBody'); b.scrollTop = b.scrollHeight; });
  await page.waitForTimeout(150);
  s = await state(page);
  const lastShort = s.rows[s.rows.length - 1];
  check('5. 390x300: scrolled to the end, the last row is fully visible inside the legend',
    lastShort.bottom <= s.body.bottom + 0.5 && lastShort.top >= s.body.top - 0.5 && s.head.top >= s.legend.top - 0.5,
    `row ${lastShort.top.toFixed(0)}..${lastShort.bottom.toFixed(0)}, body ${s.body.top.toFixed(0)}..${s.body.bottom.toFixed(0)}`);
  check('5. 390x300: the map pane did not scroll', await page.evaluate(() => document.getElementById('pane-map').scrollTop === 0));
  await page.context().close();

  // ---- 6. The choice survives a reload; blocked storage does not break the legend
  page = await newPage(700);
  await tapToggle(page);                                   // open
  await page.reload();
  await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await page.waitForTimeout(400);
  s = await state(page);
  check('6. opened, then reloaded: it is still open', s.expanded === 'true' && s.bodyVisible, `aria-expanded=${s.expanded}`);
  check('6. and still clear of the attribution bar after the reload', !overlaps(s.legend, s.attr) && s.legend.bottom <= s.nav.top + 0.5);
  await tapToggle(page);                                   // close
  await page.reload();
  await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  await page.waitForTimeout(400);
  s = await state(page);
  check('6. closed, then reloaded: it is still closed', s.expanded === 'false' && s.bodyHidden && s.text === 'Leagues shown', `aria-expanded=${s.expanded}`);
  check('6. no script error (reloads)', !page.errors.length, page.errors.join(' | '));
  await page.context().close();

  page = await newPage(700, {blockStorage: true});
  s = await state(page);
  check('6. storage blocked: the legend starts closed', s.expanded === 'false' && s.bodyHidden && s.text === 'Leagues shown');
  await tapToggle(page);
  s = await state(page);
  check('6. storage blocked: a tap still opens it', s.expanded === 'true' && s.bodyVisible && s.rows.length === s.tierNames.length + 1);
  await tapToggle(page);
  s = await state(page);
  check('6. storage blocked: a second tap still closes it', s.expanded === 'false' && s.bodyHidden);
  check('6. storage blocked: no script error', !page.errors.length, page.errors.join(' | '));
  await page.context().close();

  await browser.close();
  server.close();
  const failed = results.filter(r => !r).length;
  console.log(`\n${results.length - failed} of ${results.length} checks passed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
