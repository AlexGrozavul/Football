// Headless Chromium test of the layout problems seen on a real phone, at 390x844.
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright          (anywhere; it is not a dependency of this repo)
//   node tools/test_layout.js .     (serves the checkout itself; it changes no file)
//
// What it checks, all with the real data files:
//  1. The Ticket info tab and the Bucket list tab, every card opened, are no wider than the
//     screen: no sideways scroll, every card and every tag inside the screen, and every warning
//     of a ticket event or bucket entry in football-rules.json - the longest is Inter's - on a tag
//     that wraps inside its card on the Bucket list tab.
//  2. The club sheet sits against the bottom bar and scrolls inside itself: the map pane cannot
//     be scrolled, by a swipe past the end of a sheet or by script; a long sheet scrolls its own
//     body. Checked on a Regionalliga Bayern and a Regionalliga Südwest club and on Bayern.
//  3. The club's Wikidata id is not on the distance note; it is on a separate "Details" line at
//     the bottom of the sheet, a link labelled "Wikidata".
//  4. The Fixtures and Ticket info sections name no file, path or internal source (OpenLigaDB,
//     football-data.org) in their visible text; that detail is only under a collapsed "Why?" or
//     "Source" line. A club with no fixtures is told which leagues are covered.
//  5. (since 2026-10-07) no sheet has a "Next window" line: sale dates are the Bucket list's only. It said "No window recorded" when neither source records one for the club,
//     "No upcoming window recorded" when what is recorded is all past, and never "none ahead".
//  6. For every club with any ticket information, the sheet, with every section opened, is no
//     wider than the screen.
//  7. (since 2026-10-11) Every sheet and panel - found by looking for class "sheet" in the page, then
//     opened with its real trigger - expands to full by dragging its handle up (real touch events),
//     returns to half by tapping the handle or dragging down, scrolls its content in full, closes from
//     full and reopens at half; the map does not move during a drag; nothing overflows sideways. At
//     390 and 360 px wide, in both themes and both languages. A sheet with no trigger below fails.
// Stadia's tiles are stubbed. CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8772, BASE = `http://localhost:${PORT}/Football/`;
const W = 390, H = 844;
const TYPES = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.csv':'text/csv; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
const results = [];
const check = (name, ok, detail='') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ' :: ' + detail : '')); };

function csv(file){
  const text = fs.readFileSync(path.join(ROOT, file), 'utf8');
  const rows = []; let row = [], cell = '', q = false;
  for(let i = 0; i < text.length; i++){
    const ch = text[i];
    if(q){ if(ch === '"' && text[i+1] === '"'){ cell += '"'; i++; } else if(ch === '"') q = false; else cell += ch; }
    else if(ch === '"') q = true; else if(ch === ','){ row.push(cell); cell = ''; }
    else if(ch === '\n' || ch === '\r'){ if(ch === '\r' && text[i+1] === '\n') i++; row.push(cell); rows.push(row); row = []; cell = ''; }
    else cell += ch;
  }
  if(cell || row.length){ row.push(cell); rows.push(row); }
  const head = rows.shift();
  return rows.filter(r => r.some(c => c.trim())).map(r => Object.fromEntries(head.map((h, i) => [h.trim(), (r[i] || '').trim()])));
}
const rules = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/football-rules.json'), 'utf8'));
const links = csv('data/football-rules-links.csv');
const tickets = csv('data/club-tickets.csv').filter(t => t.team === 'men');
const windows = csv('data/club-ticket-windows.csv').filter(w => (w.team || 'men') === 'men');
// A file name, a path or an internal source name, as the sheet must not show them outside "Why?".
const INTERNAL = /[\w-]+\.(csv|json)\b|\bdata\/|OpenLigaDB|football-data/i;

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
  const ctx = await browser.newContext({viewport: {width: W, height: H}, isMobile: true, hasTouch: true,
    deviceScaleFactor: 2, serviceWorkers: 'block'});
  await ctx.route('https://tiles.stadiamaps.com/**', r => r.fulfill({status:200, contentType:'image/png', headers: {'Access-Control-Allow-Origin': '*'}, body: PNG}));
  await ctx.route('https://api.stadiamaps.com/**', r => r.abort());
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(BASE);
  await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});

  /* Everything inside `sel` that reaches past the screen's edges, as "text :: left..right". */
  const overflowing = sel => page.evaluate(sel => [...document.querySelectorAll(sel + ' *')].filter(el => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && (r.right > innerWidth + 1 || r.left < -1);
    }).map(el => `${el.tagName.toLowerCase()}.${el.className} "${el.textContent.trim().slice(0, 50)}" ${Math.round(el.getBoundingClientRect().left)}..${Math.round(el.getBoundingClientRect().right)}`), sel);

  // ---- 1. The Ticket info and Bucket list tabs
  for(const [pane, label] of [['tickets', 'Ticket info'], ['bucket', 'Bucket list']]){
    await page.click(`nav button[data-pane=${pane}]`);
    await page.waitForTimeout(250);
    // Every card opened, and everything inside it, so the widest content is on screen.
    await page.$$eval(`#pane-${pane} details.card`, ds => ds.forEach(d => d.open = true));
    await page.waitForFunction(p => ![...document.querySelectorAll(`#pane-${p} details.card > .tix`)]
      .some(t => /Loading…/.test(t.textContent)), pane, {timeout: 30000});
    await page.$$eval(`#pane-${pane} details`, ds => ds.forEach(d => d.open = true));
    await page.waitForTimeout(250);
    const t = await page.evaluate(id => {
      const p = document.getElementById(id);
      return {scrollW: p.scrollWidth, clientW: p.clientWidth, docW: document.documentElement.scrollWidth,
        cards: [...p.querySelectorAll('.card')].map(c => ({title: c.querySelector('h3')?.textContent,
          sw: c.scrollWidth, cw: c.clientWidth})),
        bad: [...p.querySelectorAll('.tag.bad')].map(x => {
          const r = x.getBoundingClientRect(), c = x.closest('.card').getBoundingClientRect();
          return {text: x.textContent, inCard: r.left >= c.left - 0.5 && r.right <= c.right + 0.5, h: r.height};
        })};
    }, 'pane-' + pane);
    check(`${label} tab: no sideways scroll (${t.scrollW} wide in ${t.clientW})`, t.scrollW <= t.clientW + 1 && t.docW <= W + 1);
    const over = await overflowing('#pane-' + pane);
    check(`${label} tab: nothing reaches past the screen edges`, !over.length, over.slice(0, 5).join(' | '));
    const wide = t.cards.filter(c => c.sw > c.cw + 1);
    check(`${label} tab: every one of ${t.cards.length} cards holds its content`, !wide.length, wide.map(c => c.title).join(' | '));
    // A bucket entry's warning is a tag in its card on the Bucket list tab. Ticket events are not drawn since the
    // Reminders came out (2026-10-08), so their warnings are on no tab. The Ticket info tab holds rules only; a
    // club entry's own "warning" field is a row of its notes there.
    const warnings = pane === 'tickets' ? [] : rules.bucketList.filter(b => b.warning);
    for(const w of warnings.sort((a, b) => b.warning.length - a.warning.length)){
      const tag = t.bad.find(b => b.text === w.warning);
      check(`${label} tab: ${w.id}'s warning (${w.warning.length} characters) is on a tag inside its card` +
        (tag && tag.h > 20 ? ', wrapped' : ''), !!tag && tag.inCard, tag ? '' : 'tag not found');
    }
  }
  await page.click('nav button[data-pane=map]');
  await page.waitForTimeout(300);

  const open = async (qid, allDetails = false) => {
    await page.evaluate(q => openSheet(CLUBS.find(c => c.id === q)), qid);
    await page.waitForFunction(() => !/Loading/.test(document.getElementById('sheetFix').textContent) &&
      !/Loading/.test(document.getElementById('sheetTix').textContent), null, {timeout: 10000});
    await page.waitForTimeout(250);   // the sheet's slide-up
    await page.$$eval('#sheetBody details', (ds, all) => ds.forEach(d => d.open = all || !d.classList.contains('why')), allDetails);
  };
  const geometry = () => page.evaluate(() => {
    const sheet = document.getElementById('sheet'), body = document.getElementById('sheetBody');
    const pane = document.getElementById('pane-map');
    return {bottom: sheet.getBoundingClientRect().bottom, top: sheet.getBoundingClientRect().top,
      navTop: document.querySelector('nav').getBoundingClientRect().top, paneScroll: pane.scrollTop,
      paneH: pane.clientHeight, sheetH: sheet.offsetHeight, bodyScroll: body.scrollTop,
      bodyScrollH: body.scrollHeight, bodyClientH: body.clientHeight};
  });
  const swipePastEnd = async () => {
    const box = await page.locator('#sheetBody').boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + Math.min(80, box.height / 2));
    for(let i = 0; i < 12; i++){ await page.mouse.wheel(0, 500); await page.waitForTimeout(60); }
    await page.waitForTimeout(250);
  };

  // ---- 2. The sheet sits against the bottom bar and scrolls inside itself
  const pick = await page.evaluate(() => ({
    bayern: CLUBS.find(c => c.tier === 4 && /Regionalliga Bayern/.test(c.competition || '')),
    suedwest: CLUBS.find(c => c.tier === 4 && /Regionalliga S(ü|ue)dwest/.test(c.competition || ''))}));
  const cases = [[pick.bayern, 'Regionalliga Bayern club'], [pick.suedwest, 'Regionalliga Südwest club'],
    [{id: 'Q15789', name: 'FC Bayern München'}, 'a long sheet']];
  for(const [club, what] of cases){
    check(`a ${what} exists to test`, !!club);
    if(!club) continue;
    await open(club.id);
    const g0 = await geometry();
    check(`${club.name} (${what}): the sheet sits against the bottom bar when opened`, Math.abs(g0.bottom - g0.navTop) <= 1,
      `sheet bottom ${g0.bottom}, bar top ${g0.navTop}`);
    await swipePastEnd();
    const g1 = await geometry();
    check(`${club.name}: after scrolling past the end, the sheet still sits against the bottom bar and the map pane has not moved`,
      Math.abs(g1.bottom - g1.navTop) <= 1 && g1.paneScroll === 0, `sheet bottom ${g1.bottom}, bar top ${g1.navTop}, map pane scrolled ${g1.paneScroll}`);
    check(`${club.name}: the sheet is at most 74% of the map pane's height`, g1.sheetH <= g1.paneH * 0.74 + 1, `${g1.sheetH} of ${g1.paneH}`);
    if(what === 'a long sheet'){
      check(`${club.name}: a long sheet scrolls inside itself`, g1.bodyScrollH > g1.bodyClientH && g1.bodyScroll > 0,
        `body ${g1.bodyScrollH} tall in ${g1.bodyClientH}, scrolled ${g1.bodyScroll}`);
    }
  }
  const forced = await page.evaluate(() => { const p = document.getElementById('pane-map'); p.scrollTop = 500; return p.scrollTop; });
  check('the map pane cannot be scrolled by script either', forced === 0, `scrollTop ${forced}`);
  await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', 'layout-long-sheet.png')});

  // ---- 3, 4 and 6 for every club with ticket information, and one club per country and tier
  const ticketClubs = [...new Set([...links.map(l => l.clubQid), ...tickets.map(t => t.clubQid)])];
  const sample = await page.evaluate(() => {
    const seen = new Map();
    for(const c of CLUBS) if(!seen.has(c.country + c.tier)) seen.set(c.country + c.tier, c.id);
    return [...seen.values()];
  });
  const onMap = await page.evaluate(ids => ids.filter(id => CLUBS.some(c => c.id === id)), ticketClubs);
  const offMap = ticketClubs.filter(id => !onMap.includes(id));
  if(offMap.length) console.log(`    not on the map, so no sheet to open: ${offMap.join(', ')}`);
  const all = [...new Set([...onMap, pick.bayern?.id, pick.suedwest?.id, ...sample].filter(Boolean))];
  let fixturesUnavailable = 0;
  for(const qid of all){
    await open(qid);
    const S = await page.evaluate(() => {
      const body = document.getElementById('sheetBody');
      const clubPart = [];
      for(const el of body.children){ if(el.tagName === 'H4' && el.textContent === 'Fixtures') break; clubPart.push(el.innerText); }
      const det = document.getElementById('sheetDetails'), a = det?.querySelector('a');
      return {name: document.querySelector('#sheetHead h3').textContent, club: clubPart.join(' '),
        fix: document.getElementById('sheetFix').innerText, tix: document.getElementById('sheetTix').innerText,
        fixUnavail: /Fixtures unavailable/.test(document.getElementById('sheetFix').textContent),
        fixWhy: !!document.querySelector('#sheetFix details.why'),
        tixUnavail: /Ticket info unavailable/.test(document.getElementById('sheetTix').textContent),
        tixWhy: !!document.querySelector('#sheetTix details.why'),
        details: det ? {last: det === body.lastElementChild, text: det.innerText, link: a?.textContent, href: a?.href} : null};
    });
    const label = `${S.name} (${qid})`;
    // 3
    check(`${label}: no Wikidata id on the club section or its distance note`, !/\bQ\d+\b/.test(S.club), S.club.match(/\bQ\d+\b/)?.[0]);
    check(`${label}: a separate Details line at the bottom, linked "Wikidata"`, !!S.details && S.details.last &&
      S.details.link === 'Wikidata' && S.details.href === `https://www.wikidata.org/wiki/${qid}`, JSON.stringify(S.details));
    // 4
    check(`${label}: Fixtures names no file or internal source`, !INTERNAL.test(S.fix), S.fix.match(INTERNAL)?.[0]);
    check(`${label}: Ticket info names no file or internal source`, !INTERNAL.test(S.tix), S.tix.match(INTERNAL)?.[0]);
    if(S.fixUnavail){
      fixturesUnavailable++;
      check(`${label}: no fixtures, so it says which leagues are covered, with a Why? line`,
        /Fixtures are fetched for: .*Bundesliga/.test(S.fix) && S.fixWhy);
    }
    if(S.tixUnavail) check(`${label}: no ticket information, said in plain words, with a Why? line`,
      /No ticket information recorded for this club yet\. Only a few clubs have been researched\./.test(S.tix) && S.tixWhy);
    // 6, with every section and every Why? line opened
    if(ticketClubs.includes(qid)){
      await page.$$eval('#sheetBody details', ds => ds.forEach(d => d.open = true));
      const w = await page.evaluate(() => { const s = document.getElementById('sheet'), b = document.getElementById('sheetBody');
        return {sheet: s.getBoundingClientRect().width, sw: b.scrollWidth, cw: b.clientWidth, doc: document.documentElement.scrollWidth}; });
      const over = await overflowing('#sheet');
      check(`${label}: the sheet, every section open, is no wider than the screen`,
        w.sheet <= W + 0.5 && w.sw <= w.cw + 1 && w.doc <= W + 1 && !over.length,
        `sheet ${w.sheet}, body ${w.sw} in ${w.cw}` + (over.length ? '; ' + over.slice(0, 3).join(' | ') : ''));
    }
  }
  check('at least one sheet with no fixtures was checked', fixturesUnavailable > 0, String(fixturesUnavailable));

  // ---- 5. No sale date on any sheet: the Next window line is gone (sale dates are the Bucket list's only)
  const withNext = [];
  for(const qid of onMap){
    await open(qid);
    if(await page.evaluate(() => !!document.getElementById('nextWindow') || /Next window|Typically opens/.test(document.getElementById('sheetTix')?.innerText || '')))
      withNext.push(qid);
  }
  check(`no sheet shows a Next window line or a "Typically opens" line (${onMap.length} checked)`, !withNext.length, withNext.join(','));

  // ---- 7. Every sheet and panel expands to full by dragging, and comes back
  const cdp = await ctx.newCDPSession(page);
  const touch = (type, x, y) => cdp.send('Input.dispatchTouchEvent', {type, touchPoints: type === 'touchEnd' ? [] : [{x, y}]});
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const dragBy = async (x, y0, y1, {steps = 8, gap = 16, mid = null} = {}) => {
    await touch('touchStart', x, y0);
    for(let i = 1; i <= steps; i++){
      await touch('touchMove', x, y0 + (y1 - y0) * i / steps);
      if(gap) await sleep(gap);
      if(mid && i === Math.floor(steps / 2)) await mid();
    }
    await touch('touchEnd');
  };
  const mapState = () => page.evaluate(() => { const c = MAP.getCenter(); return [c.lat, c.lng, MAP.getZoom()]; });
  const mapStill = async () => {                     // wait until a fly-to has ended
    let a = await mapState();
    for(let i = 0; i < 20; i++){ await sleep(250); const b = await mapState(); if(JSON.stringify(a) === JSON.stringify(b)) return b; a = b; }
    return a;
  };
  const goPane = async pane => { await page.click(`nav button[data-pane=${pane}]`); await page.waitForTimeout(250); };
  // How each sheet is really opened. A sheet found in the page with no entry here fails the test.
  const TRIGGER = {
    sheet: async () => { await goPane('map'); await page.fill('#searchInput', 'Bayern'); await page.click('#searchHits button'); },
    routePanel: async () => { await goPane('map'); await page.click('#routeChip'); },
    nearPanel: async () => { await goPane('map'); await page.click('#nearChip'); },
    coveragePanel: async () => { await goPane('map'); await page.click('#zoomChip'); },
    bsheet: async () => {
      await goPane('bucket'); await page.click('#tabCal');
      for(let i = 0; i < 16 && !(await page.$('#calBody .calitem')); i++){ await page.click('#calBody [data-cal=next]'); await page.waitForTimeout(120); }
      await page.click('#calBody .calitem');
    },
    asheet: async () => { await goPane('me'); await page.click('#meTabMatches'); await page.waitForSelector('#meMatches .acard'); await page.click('#meMatches .acard'); },
    csheet: async () => { await goPane('competitions'); await page.waitForSelector('#compBody .comprow'); await page.click('#compBody .comprow'); },
    filterPanel: async () => { await goPane('bucket'); await page.click('#bfChip'); },
    ssheet: async () => { await goPane('me'); await page.click('#settingsBtn'); },
  };
  const LABEL = {en: ['Expand', 'Collapse'], ro: ['Extinde', 'Restrânge']};
  const sheetIds = await page.evaluate(() => [...document.querySelectorAll('.sheet')].map(e => e.id));
  console.log('    sheets and panels found (class "sheet"): ' + sheetIds.join(', '));
  check('every sheet and panel has a trigger in this test', sheetIds.every(id => TRIGGER[id]), sheetIds.filter(id => !TRIGGER[id]).join(','));
  check('every one of the sheets is wired for expanding (a handle with role=button)',
    await page.evaluate(() => [...document.querySelectorAll('.sheet')].every(s => s.dataset.sd && s.querySelector(':scope > .grip[role="button"]'))));
  let scrolled = 0;
  const combos = [[390, 'dark', 'en'], [390, 'light', 'ro'], [360, 'dark', 'ro'], [360, 'light', 'en'],
                  [390, 'dark', 'ro'], [390, 'light', 'en'], [360, 'dark', 'en'], [360, 'light', 'ro']];
  for(const [vw, theme, lang] of combos){
    await page.setViewportSize({width: vw, height: H});
    await page.evaluate(([th, lg]) => { setTheme(th); setLang(lg); }, [theme, lang]);
    await page.waitForTimeout(300);
    for(const id of sheetIds.filter(i => TRIGGER[i])){
      const tag = `${vw}px ${theme} ${lang} #${id}`;
      const geo = () => page.evaluate(id => {
        const s = document.getElementById(id), r = s.getBoundingClientRect(), g = s.querySelector(':scope > .grip');
        return {hidden: s.hidden, size: s.dataset.size, h: r.height, top: r.top, bottom: r.bottom, left: r.left, right: r.right,
          navTop: document.querySelector('nav').getBoundingClientRect().top, navH: document.querySelector('nav').getBoundingClientRect().height,
          label: g && g.getAttribute('aria-label'), docW: document.documentElement.scrollWidth, vh: innerHeight, vw: innerWidth};
      }, id);
      const box = sel => page.locator(sel).first().boundingBox();
      const open = async () => {
        await TRIGGER[id]();
        await page.waitForFunction(id => { const s = document.getElementById(id); return !s.hidden && !/Loading|Se încarcă/.test(s.innerText); }, id, {timeout: 30000});
        await page.waitForTimeout(400);
        if(['sheet', 'routePanel', 'nearPanel', 'coveragePanel'].includes(id)) await mapStill();
      };
      const isFull = g => Math.abs(g.h - (g.vh - g.navH)) <= 1.5 && Math.abs(g.bottom - g.navTop) <= 1.5 && g.top <= 1.5;
      const grip = async () => { const b = await box(`#${id} > .grip`); return [b.x + b.width / 2, b.y + b.height / 2]; };
      await open();
      const g0 = await geo();
      check(`${tag}: opens at half, handle labelled "${LABEL[lang][0]}"`, g0.size === 'half' && g0.label === LABEL[lang][0] && !isFull(g0), JSON.stringify(g0));
      const travel = (g0.vh - g0.navH) - g0.h;
      check(`${tag}: there is room to expand (${Math.round(travel)} px)`, travel > 30, String(travel));
      const m0 = await mapState();
      // Dragging the handle up, partway: the sheet follows the finger, the map stays put, release past a third snaps to full.
      let [gx, gy] = await grip();
      let midH = 0, midMap = null;
      await dragBy(gx, gy, gy - travel * 0.55, {mid: async () => { midH = (await geo()).h; midMap = await mapState(); }});
      await page.waitForTimeout(380);
      let g1 = await geo();
      check(`${tag}: the sheet followed the finger during the drag`, midH > g0.h + 5 && midH < g1.h + 1, `${g0.h} -> ${midH} -> ${g1.h}`);
      check(`${tag}: dragging the handle up reaches full (${Math.round(g1.h)} of ${g1.vh - g1.navH}, bottom bar visible)`, g1.size === 'full' && isFull(g1), JSON.stringify(g1));
      check(`${tag}: handle now labelled "${LABEL[lang][1]}"`, g1.label === LABEL[lang][1], String(g1.label));
      check(`${tag}: the map centre and zoom did not change during or after the drag`,
        JSON.stringify(midMap) === JSON.stringify(m0) && JSON.stringify(await mapState()) === JSON.stringify(m0), `${m0} / ${midMap}`);
      check(`${tag}: the bottom bar is still visible and tappable in full`, await page.evaluate(() => {
        const b = document.querySelector('nav button[data-pane=bucket]').getBoundingClientRect();
        const el = document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2);
        return !!el && !!el.closest('nav'); }));
      const over = await overflowing('#' + id);
      check(`${tag}: in full, nothing overflows sideways`, g1.docW <= g1.vw + 1 && g1.left >= -1 && g1.right <= g1.vw + 1 && !over.length, over.slice(0, 3).join(' | '));
      // Content still scrolls in full, by touch, and a scroll does not resize the sheet.
      const bd = await page.evaluate(id => { const b = [...document.getElementById(id).querySelectorAll(':scope > .sbody')].find(x => !x.hidden);
        const r = b.getBoundingClientRect(); return {sel: '#' + id + ' > .sbody:not([hidden])', can: b.scrollHeight > b.clientHeight + 6, x: r.x + r.width / 2, y: r.y + r.height * 0.75, h: r.height, ob: getComputedStyle(b).overscrollBehaviorY}; }, id);
      check(`${tag}: the content area has overscroll-behavior: contain`, bd.ob === 'contain', bd.ob);
      if(bd.can){
        scrolled++;
        await dragBy(bd.x, bd.y, bd.y - Math.min(140, bd.h * 0.6), {steps: 8, gap: 16});
        await page.waitForTimeout(250);
        const sc = await page.evaluate(sel => document.querySelector(sel).scrollTop, bd.sel);
        const g2 = await geo();
        check(`${tag}: content scrolls in full, and the sheet keeps its size`, sc > 0 && g2.size === 'full' && Math.abs(g2.h - g1.h) <= 1, `scrollTop ${sc}, height ${g1.h} -> ${g2.h}`);
        await page.evaluate(sel => { document.querySelector(sel).scrollTop = 0; }, bd.sel);
      }
      // Title row stays at the top in full.
      const hd = await page.evaluate(id => { const h = document.getElementById(id).querySelector(':scope > .shead').getBoundingClientRect(); return {top: h.top, bottom: h.bottom}; }, id);
      const sc0 = await geo();
      check(`${tag}: in full the title row is at the top of the sheet`, hd.top >= sc0.top - 0.5 && hd.top - sc0.top < 40, `${hd.top} vs ${sc0.top}`);
      // Tap the handle: back to half.
      [gx, gy] = await grip();
      await page.touchscreen.tap(gx, gy);
      await page.waitForTimeout(380);
      let g3 = await geo();
      check(`${tag}: tapping the handle returns to half (${Math.round(g3.h)} against ${Math.round(g0.h)})`, g3.size === 'half' && Math.abs(g3.h - g0.h) <= 1.5 && g3.label === LABEL[lang][0], JSON.stringify(g3));
      // Tap again to expand, then drag the title row down.
      [gx, gy] = await grip();
      await page.touchscreen.tap(gx, gy);
      await page.waitForTimeout(380);
      g1 = await geo();
      check(`${tag}: tapping the handle at half goes to full`, g1.size === 'full' && isFull(g1), JSON.stringify(g1));
      const hb = await box(`#${id} > .shead`);
      await dragBy(hb.x + 20, hb.y + hb.height / 2, hb.y + hb.height / 2 + travel * 0.6);
      await page.waitForTimeout(380);
      g3 = await geo();
      check(`${tag}: dragging the title row down from full returns to half, not closed`, g3.size === 'half' && !g3.hidden && Math.abs(g3.h - g0.h) <= 1.5, JSON.stringify(g3));
      // A short, fast flick up goes to full; a short slow drag does not.
      [gx, gy] = await grip();
      await dragBy(gx, gy, gy - 14, {steps: 4, gap: 0});
      await page.waitForTimeout(380);
      g3 = await geo();
      check(`${tag}: a short slow drag (14 px) does not expand`, g3.size === 'half' && Math.abs(g3.h - g0.h) <= 1.5, JSON.stringify(g3));
      await dragBy(gx, gy, gy - 60, {steps: 3, gap: 2});
      await page.waitForTimeout(380);
      g3 = await geo();
      check(`${tag}: a flick up goes to full`, g3.size === 'full' && isFull(g3), JSON.stringify(g3));
      // Dragging down from full a small way springs back to full.
      [gx, gy] = await grip();
      await dragBy(gx, gy, gy + 10, {steps: 4, gap: 16});
      await page.waitForTimeout(380);
      g3 = await geo();
      check(`${tag}: a small drag down from full springs back to full`, g3.size === 'full' && isFull(g3), JSON.stringify(g3));
      // Close from full, reopen: half.
      await page.click(`#${id} .shead .x`, {timeout: 4000}).catch(() => {});
      await page.waitForTimeout(350);
      check(`${tag}: Close works from full`, (await geo()).hidden);
      await open();
      const g4 = await geo();
      check(`${tag}: reopens at half, never at full`, g4.size === 'half' && !isFull(g4) && Math.abs(g4.h - g0.h) <= 1.5, JSON.stringify(g4));
      // A drag that starts in the content never resizes the sheet.
      const bd2 = await page.evaluate(id => { const b = [...document.getElementById(id).querySelectorAll(':scope > .sbody')].find(x => !x.hidden); const r = b.getBoundingClientRect();
        return {x: r.x + r.width / 2, y: r.y + r.height * 0.8, h: r.height}; }, id);
      await dragBy(bd2.x, bd2.y, bd2.y - Math.min(120, bd2.h * 0.7));
      await page.waitForTimeout(300);
      const g5 = await geo();
      check(`${tag}: dragging in the content area does not resize the sheet`, g5.size === 'half' && Math.abs(g5.h - g0.h) <= 1.5, JSON.stringify(g5));
      // Reduced motion: the size changes at once, with no animation.
      if(vw === 390 && theme === 'dark' && lang === 'en'){
        await page.emulateMedia({reducedMotion: 'reduce'});
        const rm = await page.evaluate(id => { const s = document.getElementById(id); s.querySelector(':scope > .grip').click();
          const a = [s.dataset.size, s.style.transition, s.style.height]; s.querySelector(':scope > .grip').click(); return [...a, s.dataset.size]; }, id);
        await page.emulateMedia({reducedMotion: 'no-preference'});
        check(`${tag}: with reduced motion the size changes at once, without a transition`, rm[0] === 'full' && rm[1] === '' && rm[2] === '' && rm[3] === 'half', rm.join('|'));
      }
      // Keyboard: Enter on the handle toggles.
      await page.evaluate(id => document.getElementById(id).querySelector(':scope > .grip')
        .dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true, cancelable: true})), id);
      await page.waitForTimeout(380);
      check(`${tag}: Enter on the handle expands`, (await geo()).size === 'full');
      await page.click(`#${id} .shead .x`, {timeout: 4000}).catch(() => {});
      await page.waitForTimeout(350);
    }
  }
  check('content was scrolled in full on at least three sheets (the others fit in full)', scrolled >= 3, String(scrolled));
  await page.setViewportSize({width: W, height: H});

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
