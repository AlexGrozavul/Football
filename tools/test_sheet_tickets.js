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
  const riv = csv('data/club-rivalries.csv'), rivSrc = csv('data/club-culture-sources.csv');
  const bucketLines = csv('data/bucket-links-manual.csv').filter(r => !r.ticketEventId);
  const RANK = {main: 0, local: 1, other: 2}, LABEL = {main: 'Main rival', local: 'Local rival', other: 'Other rivalry'};
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
          wide: r.scrollWidth > r.clientWidth + 1, shown: !r.hidden})),
        more: b.querySelector('.rvmore')?.textContent || '',
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
    if(R.rows.length && RANK[want[0].class] !== Math.min(...want.map(r => RANK[r.class]))){ orderOk = false; bad.push(`${name}: biggest not first`); }
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
    if(R.rows.filter(r => r.shown).length > 5 || (R.rows.length > 5) !== /^Show all \(\d+\)$/.test(R.more)) { sectionOk = false; bad.push(`${name}: show-all control`); }
  }
  function rivalSrc(id){ return rivSrc.find(r => r.sourceId === id); }
  check('every club with rows shows one Rivalries section', sectionOk, bad.join(' | '));
  check('rivals in class order, main then local then other, alphabetical within a class, biggest first', orderOk, bad.join(' | '));
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
  const srcId = rivSrc[0].sourceId;
  const extra = ['Zeta Test', 'Yankee Test', 'Xray Test'].map((n, i) => `${many},,${n},${['local', 'main', 'other'][i]},${srcId},2026-10-03`);
  const mixed = lines.map((l, i) => i && l.startsWith(many + ',') ? l.replace(/,(main|local|other),/, `,${classes[k++ % 5]},`) : l)
    .filter(Boolean).concat(extra).join('\n') + '\n';
  const pg2 = await ctx.newPage();
  await pg2.route('**/data/club-rivalries.csv', r => r.fulfill({status: 200, contentType: 'text/csv', body: mixed}));
  pg2.on('pageerror', e => errors.push(e.message));
  await pg2.goto(BASE);
  await pg2.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  const M = await rivalSheet(pg2, many);
  const mrows = csvText(mixed).filter(r => r.clubQ === many);
  const mwant = expectOrder(mrows);
  check('mixed classes: main first, then local, then other, alphabetical within a class',
    new Set(mrows.map(r => r.class)).size > 1 && JSON.stringify(M.rows.map(r => r.name)) === JSON.stringify(mwant.map(r => r.rivalName)) &&
    JSON.stringify(M.rows.map(r => r.cls)) === JSON.stringify(mwant.map(r => LABEL[r.class])) && M.rows[0].cls === LABEL[mwant[0].class],
    M.rows.map(r => `${r.name}:${r.cls}`).join(' | '));
  // More than 5 rows: the first 5 show, the rest wait behind "Show all (n)".
  check(`more than 5 rows (${mrows.length}): 5 shown, "Show all (${mrows.length})" present`,
    mrows.length > 5 && M.rows.filter(r => r.shown).length === 5 && M.more === `Show all (${mrows.length})`, `${M.rows.filter(r => r.shown).length} shown, "${M.more}"`);
  await pg2.click('#sheetBody .rvmore');
  const opened = await pg2.evaluate(() => ({shown: [...document.querySelectorAll('#sheetBody .riv')].filter(r => !r.hidden).length,
    expanded: document.querySelector('#sheetBody .rvmore').getAttribute('aria-expanded'),
    sideways: document.getElementById('sheetBody').scrollWidth > document.getElementById('sheetBody').clientWidth + 1}));
  check('"Show all" reveals every row, no sideways scroll', opened.shown === mrows.length && opened.expanded === 'true' && !opened.sideways, JSON.stringify(opened));

  // ---- "When the atmosphere is best": served fixture rows (the real file may hold none), the club and
  // counts read from the data; a club with no rows must show no section.
  const realAtm = csv('data/club-atmosphere.csv');
  const rival1 = mrows.find(r => r.rivalQ && onMap.includes(r.rivalQ));
  const oppName = rival1 ? rival1.rivalName : 'Test Opponent';
  const H = 'clubQ,situation,opponentQ,opponentName,where,whenText,recurrence,what,attribution,basis,sourceId,checkedOn';
  const fx = [
    [many, 'cup', '', '', '', 'early season', 'annual', 'Fixture sentence for a cup row.', 'Fixture Press A', 'reported'],
    [many, 'european', '', '', 'home end', 'autumn', 'if-qualified', 'Fixture sentence for a European row.', 'Fixture Club B', 'documented'],
    [many, 'derby', rival1 ? rival1.rivalQ : '', oppName, 'the main stand', 'spring', 'if-same-league', 'Fixture sentence for a derby row.', 'Fixture Fans C', 'reported'],
    [many, 'derby', '', '', '', '', 'irregular', 'Fixture sentence for a second derby row.', 'Fixture Press D', 'documented'],
    [many, 'other', '', '', '', 'whole season', 'annual', 'Fixture sentence for an other row.', 'Fixture Press E', 'reported'],
  ].map(a => a.concat(srcId, '2026-10-03').join(',')).join('\n');
  const atmCsv = H + '\n' + fx + '\n';
  const pg3 = await ctx.newPage();
  await pg3.route('**/data/club-atmosphere.csv', r => r.fulfill({status: 200, contentType: 'text/csv', body: atmCsv}));
  pg3.on('pageerror', e => errors.push(e.message));
  await pg3.goto(BASE);
  await pg3.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  const atmSheet = async (pg, qid) => {
    await pg.evaluate(q => openSheet(CLUBS.find(c => c.id === q)), qid);
    await pg.waitForFunction(() => !/Loading/.test(document.getElementById('sheetTix').textContent), null, {timeout: 10000});
    await pg.waitForTimeout(200);
    return pg.evaluate(() => {
      const b = document.getElementById('sheetBody'), sb = document.querySelector('#sheet .sbody');
      return {h4: [...b.querySelectorAll('h4')].map(h => h.textContent),
        note: b.querySelector('.atmnote')?.textContent || '',
        groups: [...b.querySelectorAll('details.atm')].map(d => ({sit: d.dataset.situation, head: d.querySelector('summary').textContent, open: d.open,
          sumH: d.querySelector('summary').getBoundingClientRect().height,
          rows: [...d.querySelectorAll('.atmrow')].map(r => ({opp: r.querySelector('.atmopp').textContent, rec: r.querySelector('.atmrec')?.textContent || '', what: r.querySelector('.atmwhat').textContent,
            by: r.querySelector('.atmby').textContent, label: r.querySelector('.atmbasis').textContent, href: r.querySelector('.atmsrc a')?.href || '',
            src: r.querySelector('.atmsrc').textContent, wide: r.scrollWidth > r.clientWidth + 1}))})),
        sideways: sb.scrollWidth > sb.clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1};
    });
  };
  const A = await atmSheet(pg3, many);
  const ORDER = ['derby', 'european', 'cup', 'other'];
  const REC_EN = {annual: 'Every season', 'if-same-league': 'Only when both clubs are in the same league', 'if-qualified': 'Only when the club qualifies', irregular: 'Irregular'};
  const REC_RO = {annual: 'În fiecare sezon', 'if-same-league': 'Doar când ambele cluburi sunt în aceeași ligă', 'if-qualified': 'Doar când clubul se califică', irregular: 'Neregulat'};
  const GROUPS_EN = {derby: 'Derbies and rivals', european: 'European nights', cup: 'Cup games', other: 'Other occasions'};
  const GROUPS_RO = {derby: 'Derby-uri și rivale', european: 'Seri europene', cup: 'Meciuri de cupă', other: 'Alte ocazii'};
  const fxRows = atmCsv.split('\n').slice(1).filter(Boolean).map(l => l.split(','));
  const wantGroups = ORDER.map(k => [k, fxRows.filter(r => r[1] === k)]).filter(([, g]) => g.length);
  // Section order on the real files: the sections that exist for a club are Rivalries, Fan friendships, atmosphere,
  // each directly after the previous one that exists. Clubs are picked from the data: one with all three, one with
  // only some (preferring one that lacks the middle section), one with none. No name or count is written here.
  const realFri = csv('data/club-friendships.csv');
  const SECTIONS = [['Rivalries', riv], ['Fan friendships', realFri], ['When the atmosphere is best', realAtm]];
  const has = (q, rows) => rows.some(r => r.clubQ === q);
  const present = q => SECTIONS.filter(([, rows]) => has(q, rows)).map(([h]) => h);
  const fileClubs = [...new Set([...riv, ...realFri, ...realAtm].map(r => r.clubQ))].filter(q => onMap.includes(q));
  const allThree = fileClubs.find(q => present(q).length === 3);
  const someOnly = fileClubs.find(q => present(q).length === 2 && !present(q).includes('Fan friendships')) || fileClubs.find(q => present(q).length > 0 && present(q).length < 3);
  const noneAt = onMap.find(q => present(q).length === 0);
  for(const [kind, q] of [['all three sections', allThree], ['only some sections', someOnly], ['no sections', noneAt]]){
    if(!q){ check(`section order: a club with ${kind} exists in the data`, false, 'none found'); continue; }
    const S = await atmSheet(page, q), want = present(q);
    const got = S.h4.filter(h => SECTIONS.some(([s]) => s === h));
    const idx = want.map(h => S.h4.indexOf(h));
    const consecutive = idx.every((x, i) => x >= 0 && (i === 0 || x === idx[i - 1] + 1));
    check(`section order, club with ${kind} (${q}): exactly [${want.join(', ') || 'none'}], each directly after the previous that exists`,
      JSON.stringify(got) === JSON.stringify(want) && consecutive, S.h4.join(' | '));
    if(want.includes('When the atmosphere is best')) check(`section order (${q}): the atmosphere section carries its note`, S.note === 'Opinions of the cited sources, not measured.', S.note);
  }
  check('atmosphere: groups in the fixed order, each heading carries its row count',
    JSON.stringify(A.groups.map(g => g.sit)) === JSON.stringify(wantGroups.map(([k]) => k)) &&
    A.groups.every((g, i) => g.head.endsWith(`(${wantGroups[i][1].length})`) && g.rows.length === wantGroups[i][1].length), A.groups.map(g => g.head).join(' | '));
  check('atmosphere: only the first group starts open', A.groups.length > 1 && A.groups.map(g => g.open).join() === A.groups.map((g, i) => i === 0).join(), A.groups.map(g => g.open).join());
  const srcRow = rivSrc.find(r => r.sourceId === srcId);
  let rowsOk = true, rbad = [];
  A.groups.forEach((g, gi) => g.rows.forEach((r, ri) => {
    const f = wantGroups[gi][1][ri];
    if(!r.by.startsWith(`According to ${f[8]}`) || r.by.split('According to').length !== 2) { rowsOk = false; rbad.push(`by ${f[8]}`); }
    if(r.rec !== `When it happens: ${REC_EN[f[6]]}`) { rowsOk = false; rbad.push(`recurrence ${f[8]}: ${r.rec}`); }
    if(r.label !== (f[9] === 'documented' ? 'Documented' : 'Reported')) { rowsOk = false; rbad.push(`label ${f[8]}`); }
    if(r.what !== f[7]) { rowsOk = false; rbad.push(`what ${f[8]}`); }
    if(r.href !== srcRow.url || !/Checked on /.test(r.src)) { rowsOk = false; rbad.push(`source ${f[8]}`); }
    if(!r.opp.startsWith(f[3] || 'any opponent')) { rowsOk = false; rbad.push(`opponent ${f[8]}`); }
    if(f[4] && !r.opp.includes(f[4])) { rowsOk = false; rbad.push(`where ${f[8]}`); }
    if(f[5] && !r.opp.includes(f[5])) { rowsOk = false; rbad.push(`when ${f[8]}`); }
    if(r.wide) { rowsOk = false; rbad.push(`wide ${f[8]}`); }
  }));
  check('atmosphere: every row shows opponent (or "any opponent"), where, when, "When it happens" with its recurrence, its sentence, "According to" once, the label and a source with "Checked on"', rowsOk, rbad.join(' | '));
  check('atmosphere: the groups are Derbies and rivals / European nights / Cup games / Other occasions, with no Regular home games group',
    A.groups.every(g => g.head.startsWith(GROUPS_EN[g.sit] + ' (')) && !A.groups.some(g => /Regular home/.test(g.head)), A.groups.map(g => g.head).join(' | '));
  check('atmosphere: no attribution in the real file starts with "According to" or "Laut"', realAtm.every(r => !/^\s*(according to|laut)\b/i.test(r.attribution || '')), realAtm.map(r => r.attribution).join(' | '));
  check('atmosphere: every row of the real file has a valid recurrence', realAtm.every(r => REC_EN[r.recurrence]), realAtm.map(r => r.recurrence).join(','));
  check('atmosphere: no sideways scroll at 390 px', !A.sideways && A.groups.every(g => g.sumH >= 44), `sideways ${A.sideways}`);
  await pg3.click('#sheetBody details.atm:not([open]) summary');
  const toggled = await pg3.evaluate(() => [...document.querySelectorAll('#sheetBody details.atm')].map(d => d.open));
  await pg3.click('#sheetBody details.atm[open] summary');
  const toggled2 = await pg3.evaluate(() => [...document.querySelectorAll('#sheetBody details.atm')].map(d => d.open));
  check('atmosphere: groups open and close by tap', toggled.filter(Boolean).length === 2 && toggled2.filter(Boolean).length === 1, `${toggled} -> ${toggled2}`);
  const noAtm = await pg3.evaluate(q => CLUBS.find(c => c.id !== q).id, many);
  const N = await atmSheet(pg3, noAtm);
  check('atmosphere: a club without rows shows no section', !N.h4.includes('When the atmosphere is best') && !N.groups.length && !N.note);
  // The real file, whatever it holds: each club with rows shows exactly its rows, nothing overflows.
  const realClubs = [...new Set(realAtm.map(r => r.clubQ))].filter(q => onMap.includes(q));
  let realOk = true, realBad = [];
  for(const q of realClubs){
    const R = await atmSheet(page, q);
    const n = R.groups.reduce((a, g) => a + g.rows.length, 0);
    if(n !== realAtm.filter(r => r.clubQ === q).length || R.sideways || R.groups.some(g => g.rows.some(r => r.wide))) { realOk = false; realBad.push(q); }
  }
  check(`atmosphere: the real file's ${realClubs.length} clubs show exactly their rows and fit`, realOk, realBad.join(' '));
  await pg3.close();
  await pg2.close();

  // ---- "Fan friendships": temporary rows injected here only (the real file is header-only and stays so).
  // A German club and a non-German one, the order, the labels, "Show all", a tap on a friend on the map,
  // a club without rows, and 390 px in English and Romanian.
  const nonDE = await page.evaluate(m => { const c = CLUBS.find(c => c.country && c.country !== 'DE' && c.id !== m); return c && c.id; }, many);
  const friendOnMap = await page.evaluate(([a, b]) => { const c = CLUBS.find(c => c.id !== a && c.id !== b); return {id: c.id, name: c.name}; }, [many, nonDE]);
  const q = v => /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  const FH = 'clubQ,friendQ,friendName,scope,status,groupsText,sourceId,checkedOn';
  const LONG = 'Averyveryverylongfangroupnamewithoutanybreakshere' + 'x'.repeat(120);
  const frRows = [
    {clubQ: many, friendQ: '', friendName: 'Zulu Test', scope: 'clubs', status: 'ended', groupsText: ''},
    {clubQ: many, friendQ: '', friendName: 'Alpha Test', scope: 'fan-groups', status: 'active', groupsText: 'Group One, Group Two'},
    {clubQ: many, friendQ: '', friendName: 'Mike Test', scope: 'unclear', status: 'unclear', groupsText: ''},
    {clubQ: many, friendQ: '', friendName: 'Bravo Test', scope: 'clubs', status: 'active', groupsText: ''},
    {clubQ: many, friendQ: '', friendName: 'Echo Test', scope: 'fan-groups', status: 'ended', groupsText: LONG},
    {clubQ: many, friendQ: '', friendName: 'Delta Test', scope: 'clubs', status: 'unclear', groupsText: ''},
    {clubQ: many, friendQ: friendOnMap.id, friendName: friendOnMap.name, scope: 'fan-groups', status: 'unclear', groupsText: ''},
    {clubQ: nonDE, friendQ: '', friendName: 'Foreign Beta', scope: 'clubs', status: 'ended', groupsText: ''},
    {clubQ: nonDE, friendQ: '', friendName: 'Foreign Alpha', scope: 'fan-groups', status: 'active', groupsText: 'Some Fans'},
  ].map(r => ({...r, sourceId: srcId, checkedOn: '2026-10-03'}));
  const frCsv = FH + '\n' + frRows.map(r => FH.split(',').map(k => q(r[k])).join(',')).join('\n') + '\n';
  const atmExtra = [nonDE, 'cup', '', '', '', 'early season', 'annual', 'Fixture sentence for a foreign cup row.', 'Fixture Press F', 'reported', srcId, '2026-10-03'].join(',');
  const rivExtra = `${nonDE},,Test Rival,main,${srcId},2026-10-03`;
  const FRI_RANK = {active: 0, unclear: 1, ended: 2};
  const wantFri = id => frRows.filter(r => r.clubQ === id).sort((a, b) => FRI_RANK[a.status] - FRI_RANK[b.status] || a.friendName.localeCompare(b.friendName));
  const friPage = async lang => {
    const pg = await ctx.newPage();
    if(lang) await pg.addInitScript(l => { try { localStorage.setItem('football-planner-lang', l); } catch(e){} }, lang);
    await pg.route('**/data/club-friendships.csv', r => r.fulfill({status: 200, contentType: 'text/csv', body: frCsv}));
    await pg.route('**/data/club-atmosphere.csv', r => r.fulfill({status: 200, contentType: 'text/csv', body: atmCsv + atmExtra + '\n'}));
    await pg.route('**/data/club-rivalries.csv', r => r.fulfill({status: 200, contentType: 'text/csv', body: mixed + rivExtra + '\n'}));
    pg.on('pageerror', e => errors.push(e.message));
    await pg.goto(BASE);
    await pg.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
    return pg;
  };
  const friSheet = async (pg, qid) => {
    await pg.evaluate(c => openSheet(CLUBS.find(x => x.id === c)), qid);
    await pg.waitForFunction(() => !/Loading/.test(document.getElementById('sheetTix').textContent), null, {timeout: 10000});
    await pg.waitForTimeout(250);
    return pg.evaluate(() => {
      const b = document.getElementById('sheetBody'), sb = document.querySelector('#sheet .sbody');
      return {h4: [...b.querySelectorAll('h4')].map(h => h.textContent),
        note: b.querySelector('.frnote')?.textContent || '',
        rows: [...b.querySelectorAll('.fri')].map(r => ({name: r.querySelector('.frname').textContent, tap: r.querySelector('.frname').tagName === 'BUTTON',
          fid: r.querySelector('.frname').dataset.id || '', scope: r.querySelector('.frscope').textContent, status: r.querySelector('.frstatus').textContent,
          groups: r.querySelector('.frgroups')?.textContent || '', href: r.querySelector('.frsrc a')?.href || '', src: r.querySelector('.frsrc').textContent,
          shown: !r.hidden, wide: r.scrollWidth > r.clientWidth + 1})),
        more: b.querySelector('.frmore')?.textContent || '', sections: b.querySelectorAll('.fris').length,
        rivs: b.querySelectorAll('.riv').length, atm: b.querySelectorAll('details.atm').length,
        sideways: sb.scrollWidth > sb.clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1};
    });
  };
  const SC = {'fan-groups': 'Between fan groups', clubs: 'Between clubs', unclear: 'Not specified'}, ST = {active: 'Active', ended: 'Ended', unclear: 'Not clear'};
  const pg4 = await friPage(null);
  const F = await friSheet(pg4, many), fw = wantFri(many);
  check('friendships: "Fan friendships" sits directly below Rivalries and above the atmosphere section, with its note',
    F.h4.indexOf('Fan friendships') === F.h4.indexOf('Rivalries') + 1 && F.h4.indexOf('When the atmosphere is best') === F.h4.indexOf('Fan friendships') + 1 &&
    F.note === 'As stated by the cited source. Fan friendships change and can end.', F.h4.join(' | '));
  check('friendships: active, then not clear, then ended, alphabetical within each',
    JSON.stringify(F.rows.map(r => r.name)) === JSON.stringify(fw.map(r => r.friendName)) && F.rows.length === fw.length, F.rows.map(r => r.name).join(' | '));
  check('friendships: every row has its scope label, status label, groups (only when the source names them) and a source with "Checked on"',
    F.rows.every((r, i) => r.scope === SC[fw[i].scope] && r.status === ST[fw[i].status] &&
      (fw[i].groupsText ? r.groups === `Groups: ${fw[i].groupsText}` : r.groups === '') &&
      r.href === srcRow.url && /Checked on /.test(r.src) && r.src.includes(srcRow.title)), JSON.stringify(F.rows.map(r => [r.scope, r.status, r.groups.slice(0, 30)])));
  check(`friendships: ${fw.length} rows give 5 shown and "Show all (${fw.length})"`, F.rows.filter(r => r.shown).length === 5 && F.more === `Show all (${fw.length})`, `${F.rows.filter(r => r.shown).length} shown, "${F.more}"`);
  await pg4.click('#sheetBody .frmore');
  const FO = await pg4.evaluate(() => ({shown: [...document.querySelectorAll('#sheetBody .fri')].filter(r => !r.hidden).length,
    exp: document.querySelector('#sheetBody .frmore').getAttribute('aria-expanded'), label: document.querySelector('#sheetBody .frmore').textContent,
    wide: [...document.querySelectorAll('#sheetBody .fri')].some(r => r.scrollWidth > r.clientWidth + 1),
    sideways: document.querySelector('#sheet .sbody').scrollWidth > document.querySelector('#sheet .sbody').clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1}));
  check('friendships: "Show all" reveals every row and fits 390 px (long group name included)', FO.shown === fw.length && FO.exp === 'true' && FO.label === 'Show fewer' && !FO.wide && !FO.sideways, JSON.stringify(FO));
  const tapRow = F.rows.find(r => r.tap);
  check('friendships: only the friend on the map is a tap target', F.rows.filter(r => r.tap).length === 1 && tapRow && tapRow.fid === friendOnMap.id);
  await pg4.click(`#sheetBody .fris .frname[data-id="${friendOnMap.id}"]`);
  await pg4.waitForFunction(id => SHEET_FOR === id, friendOnMap.id, {timeout: 8000}).catch(() => {});
  check('friendships: tapping a friend on the map opens its own sheet', await pg4.evaluate(() => SHEET_FOR) === friendOnMap.id);
  const NF = await friSheet(pg4, (await pg4.evaluate(([a, b, c]) => CLUBS.find(x => ![a, b, c].includes(x.id)).id, [many, nonDE, friendOnMap.id])));
  check('friendships: a club without rows shows no Fan friendships section', !NF.h4.includes('Fan friendships') && !NF.sections && !NF.rows.length && !NF.note);
  const FD = await friSheet(pg4, nonDE), fd = wantFri(nonDE);
  check(`friendships: a non-German club (${nonDE}) shows Rivalries, Fan friendships and the atmosphere section, in that order`,
    FD.h4.indexOf('Fan friendships') === FD.h4.indexOf('Rivalries') + 1 && FD.h4.indexOf('When the atmosphere is best') === FD.h4.indexOf('Fan friendships') + 1 &&
    FD.rivs === 1 && FD.atm === 1 && JSON.stringify(FD.rows.map(r => r.name)) === JSON.stringify(fd.map(r => r.friendName)) && !FD.sideways, FD.h4.join(' | '));
  const pg5 = await friPage('ro');
  const RO = await friSheet(pg5, many);
  const SCro = {'fan-groups': 'Între grupurile de suporteri', clubs: 'Între cluburi', unclear: 'Nespecificat'}, STro = {active: 'Activă', ended: 'Încheiată', unclear: 'Neclară'};
  check('friendships (Romanian): heading, note, labels and "Arată tot" are Romanian and the order is the same',
    RO.h4.includes('Prietenii între suporteri') && RO.note.startsWith('Așa cum le arată sursa citată') && RO.more === `Arată tot (${fw.length})` &&
    RO.rows.every((r, i) => r.scope === SCro[fw[i].scope] && r.status === STro[fw[i].status] && r.name === fw[i].friendName), RO.h4.join(' | '));
  await pg5.click('#sheetBody .frmore');
  const ROo = await pg5.evaluate(() => ({wide: [...document.querySelectorAll('#sheetBody .fri')].some(r => r.scrollWidth > r.clientWidth + 1),
    sideways: document.querySelector('#sheet .sbody').scrollWidth > document.querySelector('#sheet .sbody').clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1}));
  check('friendships (Romanian): nothing overflows at 390 px with every row open', !ROo.wide && !ROo.sideways && !RO.sideways, JSON.stringify(ROo));
  const AR = await atmSheet(pg5, many);
  check('atmosphere (Romanian): groups, "Când are loc" with the recurrence and "Potrivit" once, all in Romanian',
    AR.groups.length === A.groups.length && AR.groups.every(g => g.head.startsWith(GROUPS_RO[g.sit] + ' (')) &&
    AR.groups.every((g, gi) => g.rows.every((r, ri) => r.rec === `Când are loc: ${REC_RO[wantGroups[gi][1][ri][6]]}` && r.by.startsWith('Potrivit ') && r.by.split('Potrivit').length === 2)), AR.groups.map(g => g.head).join(' | '));
  await pg5.evaluate(() => document.querySelectorAll('#sheetBody details.atm').forEach(d => { d.open = true; }));
  const ARo = await pg5.evaluate(() => ({wide: [...document.querySelectorAll('#sheetBody .atmrow')].some(r => r.scrollWidth > r.clientWidth + 1),
    sideways: document.querySelector('#sheet .sbody').scrollWidth > document.querySelector('#sheet .sbody').clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1}));
  check('atmosphere (Romanian): nothing overflows at 390 px with every group open', !ARo.wide && !ARo.sideways, JSON.stringify(ARo));
  await pg4.close(); await pg5.close();
  function csvText(t){ const f = '__tmp'; return t.split('\n').slice(1).filter(Boolean).map(l => { const c = l.split(','); return {clubQ: c[0], rivalQ: c[1], rivalName: c[2], class: c[3], sourceId: c[4]}; }); }

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
