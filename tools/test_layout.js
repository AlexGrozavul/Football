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
//  5. "Next window" says "No window recorded" when neither source records one for the club,
//     "No upcoming window recorded" when what is recorded is all past, and never "none ahead".
//  6. For every club with any ticket information, the sheet, with every section opened, is no
//     wider than the screen.
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
    // Every warning in football-rules.json is a tag on the Bucket list tab since 2026-10-04: a
    // ticket event's inside its entry or under Reminders, a bucket entry's in its card. The Ticket
    // info tab holds rules only; a club entry's own "warning" field is a row of its notes there.
    const warnings = pane === 'tickets' ? [] : rules.ticketEvents.filter(e => e.warning).concat(rules.bucketList.filter(b => b.warning));
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

  // ---- 5. The Next window wording, against the files
  let saw = {none: 0, past: 0};
  for(const qid of onMap){
    await open(qid);
    const N = await page.evaluate(() => { const nw = document.getElementById('nextWindow');
      return nw ? {text: nw.innerText.replace(/\s+/g, ' '), entries: nw.querySelectorAll('.nw').length} : null; });
    const name = await page.evaluate(() => document.querySelector('#sheetHead h3').textContent);
    if(!N){ check(`${name}: has ticket information, so a Next window line`, false); continue; }
    const ids = links.filter(l => l.clubQid === qid).map(l => l.rulesId);
    const recorded = rules.ticketEvents.filter(e => ids.includes(e.club)).length + windows.filter(w => w.clubQid === qid).length;
    console.log(`    ${name}: ${recorded} recorded; "${N.text}"`);
    check(`${name}: Next window never says "none ahead" or "No window ahead"`, !/none ahead|No window ahead/i.test(N.text));
    if(N.entries) continue;
    if(!recorded){ saw.none++; check(`${name}: nothing recorded in either source, so "No window recorded"`, /\bNo window recorded\./.test(N.text), N.text); }
    else { saw.past++; check(`${name}: ${recorded} recorded and none ahead, so "No upcoming window ... recorded"`, /No upcoming window( with a date or month)? recorded\./.test(N.text), N.text); }
  }
  console.log(`    real data: ${saw.none} club(s) with nothing recorded, ${saw.past} with nothing ahead`);
  // The two wordings, from made-up inputs, so they stay tested whatever the files hold.
  const synth = await page.evaluate(() => {
    const txt = h => { const d = document.createElement('div'); d.innerHTML = h; return d.textContent.replace(/\s+/g, ' '); };
    return {
      none: txt(nextWindowHtml({entries: []}, {windows: []})),
      past: txt(nextWindowHtml({entries: [{events: [{title: 'Old sale', date: '2020-05-01', dateSource: 'confirmed'}]}]}, {windows: []})),
      pastWin: txt(nextWindowHtml({entries: []}, {windows: [{label: 'Old window', opensEstimate: 'late June', estimateFor: '2020-21', dateSource: 'inferred'}]})),
      disputed: txt(nextWindowHtml({entries: [{events: [{title: 'Doubtful', date: '2099-01-01', dateSource: 'disputed'}]}]}, {windows: []}))};
  });
  check('made-up: no window in either source reads "No window recorded."', /^Next window ?No window recorded\.$/.test(synth.none.trim()), synth.none);
  check('made-up: a past event only reads "No upcoming window recorded."', /No upcoming window recorded\./.test(synth.past), synth.past);
  check('made-up: a past window row only reads "No upcoming window recorded."', /No upcoming window recorded\./.test(synth.pastWin), synth.pastWin);
  check('made-up: a disputed event only is recorded but not ahead, "No upcoming window recorded."', /No upcoming window recorded\./.test(synth.disputed) && !/Doubtful/.test(synth.disputed), synth.disputed);

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
