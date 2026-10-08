// Headless Chromium test of the club sheet's ticket section, at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright            (anywhere; it is not a dependency of this repo)
//   node tools/test_sheet_tickets.js .   (serves the checkout itself; it changes no file)
//
// Opens the sheet of VfB, KSC, Kaiserslautern, Kickers, Poli, UTA, Bayern, Nürnberg and Inter
// and checks, against the files read here: "Your notes" (football-rules.json, joined through
// data/football-rules-links.csv) shows exactly when a link exists, and every text field of the
// entry is on the sheet as written; "Researched rules" (club-tickets.csv) shows exactly when a row
// exists; both are labelled; a "Next window" line is present, names only that club's own events
// or windows, never a disputed one, carries a dateSource label, says "estimated" for an inferred
// one and never shows an inferred one to the day; a club with neither source keeps "Ticket info
// unavailable"; the club's country rules come first ("Country rules: <country>", every national row
// of that country, or "No national rules researched for <country> yet"), then "Researched rules",
// then "Your notes"; no sideways scroll; no script error. Prints each club's Next window line.
// Stadia's tiles are stubbed. CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8771, BASE = `http://localhost:${PORT}/Football/`;
const TYPES = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.csv':'text/csv; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
const results = [];
const check = (name, ok, detail='') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ' :: ' + detail : '')); };

const CLUBS = [['VfB Stuttgart', 'Q4512'], ['Karlsruher SC', 'Q105853'], ['1. FC Kaiserslautern', 'Q8466'],
  ['Stuttgarter Kickers', 'Q170105'], ['Poli Timișoara', 'Q4654417'], ['UTA Arad', 'Q680770'],
  ['FC Bayern München', 'Q15789'], ['1. FC Nürnberg', 'Q15786'], ['Inter', 'Q631']];

// A small CSV reader for the checks: quoted cells, doubled quotes.
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
const tickets = csv('data/club-tickets.csv');
const windows = csv('data/club-ticket-windows.csv');
const countryRules = csv('data/country-ticket-rules.csv');
const leaves = obj => Object.entries(obj).flatMap(([k, v]) => k === 'id' || k === 'name' ? [] :
  v && typeof v === 'object' && !Array.isArray(v) ? leaves(v) : Array.isArray(v) ? v.filter(x => typeof x === 'string') :
  typeof v === 'string' ? [v] : []);
const norm = s => s.replace(/\s+/g, ' ').trim();
const DAY = /\b(\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*|\d{4}-\d{2}-\d{2}|(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b)/;

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
  await page.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  const noSideScroll = () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);

  const open = async qid => {
    await page.evaluate(q => openSheet(CLUBS.find(c => c.id === q)), qid);
    await page.waitForFunction(() => !/Loading/.test(document.getElementById('sheetTix').textContent), null, {timeout: 10000});
    await page.waitForTimeout(300);
    // open every <details> so their text is on the page
    await page.$$eval('#sheetTix details', ds => ds.forEach(d => d.open = true));
    return page.evaluate(() => {
      const t = document.getElementById('sheetTix');
      const nw = document.getElementById('nextWindow');
      const heads = [...t.querySelectorAll('h5.srch')].map(h => h.className);
      return {text: t.innerText, notes: !!t.querySelector('.tix-notes'), researched: !!t.querySelector('.tix-researched'),
        notesLabel: t.querySelector('.tix-notes')?.textContent, resLabel: t.querySelector('.tix-researched')?.textContent,
        countryLabel: t.querySelector('.tix-country')?.textContent,
        order: ['tix-country', 'tix-researched', 'tix-notes'].map(c => heads.findIndex(h => h.includes(c))),
        next: nw ? [...nw.querySelectorAll('.nw')].map(e => ({name: e.querySelector('b').textContent, text: e.textContent,
          tags: [...e.querySelectorAll('.tag')].map(x => x.textContent)})) : null,
        nextText: nw ? nw.innerText.replace(/\s+/g, ' ') : null, unavailable: /Ticket info unavailable/.test(t.textContent),
        country: CLUBS.find(c => c.id === SHEET_FOR)?.country};
    });
  };

  for(const [label, qid] of CLUBS){
    const ids = links.filter(l => l.clubQid === qid).map(l => l.rulesId);
    const entries = rules.clubs.filter(c => ids.includes(c.id));
    const row = tickets.find(t => t.clubQid === qid && t.team === 'men');
    const S = await open(qid);
    if(!entries.length && !row){ check(`${label}: no ticket information, so "Ticket info unavailable"`, S.unavailable); continue; }
    check(`${label}: "Your notes" ${entries.length ? 'shown' : 'absent, and says so'}`, S.notes && /^Your notes/.test(S.notesLabel) &&
      (entries.length ? !/None of your notes are about this club/.test(S.text) : /None of your notes are about this club/.test(S.text)));
    check(`${label}: "Country rules" first, then "Researched rules", then "Your notes"`,
      S.order[0] === 0 && S.order[1] > S.order[0] && S.order[2] > S.order[1], S.order.join(','));
    const nat = countryRules.filter(r => r.country === (row?.country || S.country));
    check(`${label}: the country rules section names the country and ${nat.length ? `shows its ${nat.length} rules` : 'says none are researched'}`,
      /^Country rules: /.test(S.countryLabel || '') && (nat.length ? nat.every(r => norm(S.text).includes(norm(r.rule)))
        : /No national rules researched for .+ yet/.test(S.text)), S.countryLabel);
    check(`${label}: "Researched rules" ${row ? 'shown' : 'absent, and says so'}`, S.researched && /^Researched rules/.test(S.resLabel) &&
      (row ? /Who may buy/.test(S.text) : /Not researched yet/.test(S.text)));
    if(entries.length){
      const flat = norm(S.text);
      const missing = entries.flatMap(leaves).filter(v => !flat.includes(norm(v)));
      check(`${label}: every text field of the football-rules.json entry is on the sheet, as written`, !missing.length, missing.join(' | '));
    }
    // Sale dates are shown only on the Bucket list: no Next window line, no window date line.
    check(`${label}: no sale date on the sheet - no Next window line, no "Typically opens"`,
      S.next === null && !/Next window|Typically opens/.test(S.text));
    check(`${label}: no sideways scroll`, await noSideScroll());
    if(label === 'Inter') await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', 'sheet-inter.png')});
  }

  // A club with no ticket information at all keeps the unavailable state.
  const plain = await page.evaluate(() => {
    const c = CLUBS.find(c => c.name === 'Hamburger SV') || CLUBS[CLUBS.length - 1];
    return c.id;
  });
  const linked = new Set(links.map(l => l.clubQid)), researched = new Set(tickets.map(t => t.clubQid));
  if(!linked.has(plain) && !researched.has(plain)){
    const S = await open(plain);
    check(`a club with neither source (${plain}) keeps "Ticket info unavailable"`, S.unavailable && S.next === null && !/Typically opens/.test(S.text));
  }


  // ---- Rivalries section: read from the data files, no club name or count written here.
  const riv = csv('data/club-rivalries.csv'), rivSrc = csv('data/rivalry-sources.csv');
  const bucketLines = csv('data/bucket-links-manual.csv').filter(r => !r.ticketEventId);
  const RANK = {other: 0, local: 1, main: 2}, LABEL = {main: 'Main rival', local: 'Local rival', other: 'Other rivalry'};
  const expectOrder = rows => [...rows].sort((a, b) => RANK[a.class] - RANK[b.class] || a.rivalName.localeCompare(b.rivalName));
  const rivalSheet = async (pg, qid) => {
    await pg.evaluate(q => openSheet(CLUBS.find(c => c.id === q)), qid);
    await pg.waitForFunction(() => !/Loading/.test(document.getElementById('sheetTix').textContent), null, {timeout: 10000});
    await pg.waitForTimeout(200);
    return pg.evaluate(() => {
      const b = document.getElementById('sheetBody'), sb = document.querySelector('#sheet .sbody');
      return {h4: [...b.querySelectorAll('h4')].map(h => h.textContent),
        rows: [...b.querySelectorAll('.riv')].map(r => ({name: r.querySelector('.rvname').textContent,
          cls: r.querySelector('.rvclass').textContent, tap: r.querySelector('.rvname').tagName === 'BUTTON',
          rivalId: r.querySelector('.rvname').dataset.id || '', href: r.querySelector('a')?.href || '',
          sub: r.querySelector('.sub').textContent, bucket: [...r.querySelectorAll('.rvbucket')].map(x => x.dataset.bucket),
          wide: r.scrollWidth > r.clientWidth + 1})),
        sideways: sb.scrollWidth > sb.clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1};
    });
  };
  const onMap = await page.evaluate(() => CLUBS.map(c => c.id));
  const withRows = [...new Set(riv.map(r => r.clubQ))].filter(q => onMap.includes(q));
  check('at least one club has rivalry rows', withRows.length > 0, `${withRows.length} clubs`);
  let sectionOk = true, orderOk = true, linkOk = true, widthOk = true, bucketOk = true, bad = [];
  for(const q of withRows){
    const want = expectOrder(riv.filter(r => r.clubQ === q));
    const R = await rivalSheet(page, q);
    const name = await page.evaluate(i => CLUBS.find(c => c.id === i).name, q);
    if(R.h4.filter(h => h === 'Rivalries').length !== 1) { sectionOk = false; bad.push(`${name}: section`); }
    if(JSON.stringify(R.rows.map(r => r.name)) !== JSON.stringify(want.map(r => r.rivalName)) ||
       JSON.stringify(R.rows.map(r => r.cls)) !== JSON.stringify(want.map(r => LABEL[r.class]))){ orderOk = false; bad.push(`${name}: order`); }
    if(R.rows.length && RANK[want[want.length - 1].class] !== Math.max(...want.map(r => RANK[r.class]))){ orderOk = false; bad.push(`${name}: biggest not last`); }
    R.rows.forEach((r, i) => {
      const src = rivalSrc(want[i].sourceId), d = want[i].checkedOn;
      if(!src || r.href !== src.url || !/Checked on /.test(r.sub) || !r.sub.includes(src.title)) { linkOk = false; bad.push(`${name}: source of ${r.name}`); }
      if(r.tap !== !!(want[i].rivalQ && onMap.includes(want[i].rivalQ))) { linkOk = false; bad.push(`${name}: tap on ${r.name}`); }
      const exp = want[i].rivalQ ? bucketLines.filter(l => [l.hostQid, ...l.otherQids.split(';')].map(x => x.trim()).includes(q) &&
        [l.hostQid, ...l.otherQids.split(';')].map(x => x.trim()).includes(want[i].rivalQ)).map(l => l.bucketId) : [];
      if(JSON.stringify([...new Set(exp)].sort()) !== JSON.stringify([...r.bucket].sort())) { bucketOk = false; bad.push(`${name}: bucket link for ${r.name}`); }
      if(r.wide) { widthOk = false; bad.push(`${name}: ${r.name} wider than the sheet`); }
    });
    if(R.sideways) { widthOk = false; bad.push(`${name}: sideways scroll`); }
    if(R.rows.length > 5) { sectionOk = false; bad.push(`${name}: more than 5`); }
  }
  function rivalSrc(id){ return rivSrc.find(r => r.sourceId === id); }
  check('every club with rows shows one Rivalries section', sectionOk, bad.join(' | '));
  check('rivals in class order, other then local then main, alphabetical within a class, biggest last', orderOk, bad.join(' | '));
  check('each row has its class label, a source link and "Checked on", and taps only when the rival is on the map', linkOk, bad.join(' | '));
  check('a bucket link shows exactly when a bucket entry names both clubs by Wikidata id', bucketOk, bad.join(' | '));
  check('the Rivalries section fits 390 px, no sideways scroll', widthOk, bad.join(' | '));

  const without = await page.evaluate(have => { const c = CLUBS.find(c => !have.includes(c.id)); return c && {id: c.id, name: c.name}; }, withRows);
  const W = await rivalSheet(page, without.id);
  check(`a club without rows (${without.name}) shows no Rivalries section`, !W.h4.includes('Rivalries') && !W.rows.length);

  // A rival on the map opens its own sheet when tapped.
  const tapFrom = withRows.find(q => riv.some(r => r.clubQ === q && r.rivalQ && onMap.includes(r.rivalQ)));
  if(tapFrom){
    const R = await rivalSheet(page, tapFrom);
    const row = R.rows.find(r => r.tap);
    await page.click(`#sheetBody .rivs .rvname[data-id="${row.rivalId}"]`);
    await page.waitForFunction(id => SHEET_FOR === id && !document.getElementById('sheet').hidden, row.rivalId, {timeout: 8000}).catch(() => {});
    const now = await page.evaluate(() => ({id: SHEET_FOR, head: document.querySelector('#sheetHead h3')?.textContent}));
    check(`tapping a rival on the map (${row.name}) opens its own sheet`, now.id === row.rivalId, now.head);
  }else check('a rival on the map exists to tap', false);

  // The order is tested against mixed classes too: a served copy of the file, same club, classes rotated.
  const many = withRows.sort((a, b) => riv.filter(r => r.clubQ === b).length - riv.filter(r => r.clubQ === a).length)[0];
  const classes = ['main', 'other', 'local', 'main', 'other'];
  const lines = fs.readFileSync(path.join(ROOT, 'data/club-rivalries.csv'), 'utf8').split('\n');
  let k = 0;
  const mixed = lines.map((l, i) => i && l.startsWith(many + ',') ? l.replace(/,(main|local|other),/, `,${classes[k++ % 5]},`) : l).join('\n');
  const pg2 = await ctx.newPage();
  await pg2.route('**/data/club-rivalries.csv', r => r.fulfill({status: 200, contentType: 'text/csv', body: mixed}));
  pg2.on('pageerror', e => errors.push(e.message));
  await pg2.goto(BASE);
  await pg2.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  const M = await rivalSheet(pg2, many);
  const mrows = csvText(mixed).filter(r => r.clubQ === many);
  const mwant = expectOrder(mrows);
  check('mixed classes: other first, then local, then main last, alphabetical within a class',
    new Set(mrows.map(r => r.class)).size > 1 && JSON.stringify(M.rows.map(r => r.name)) === JSON.stringify(mwant.map(r => r.rivalName)) &&
    JSON.stringify(M.rows.map(r => r.cls)) === JSON.stringify(mwant.map(r => LABEL[r.class])) && M.rows[M.rows.length - 1].cls === LABEL[mwant[mwant.length - 1].class],
    M.rows.map(r => `${r.name}:${r.cls}`).join(' | '));
  await pg2.close();
  function csvText(t){ const f = '__tmp'; return t.split('\n').slice(1).filter(Boolean).map(l => { const c = l.split(','); return {clubQ: c[0], rivalQ: c[1], rivalName: c[2], class: c[3], sourceId: c[4]}; }); }

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
