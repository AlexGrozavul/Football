// Headless Chromium test of the club sheet's ticket section, at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright            (anywhere; it is not a dependency of this repo)
//   node tools/test_sheet_tickets.js .   (serves the checkout itself; it changes no file)
//
// Opens the sheet of VfB, KSC, Kaiserslautern, Kickers, Poli, UTA, Bayern, Nürnberg, Inter, Frankfurt and Elversberg
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
// One duration line per section, so a slow section is visible in the job log.
const T_START = Date.now();
let tMark = T_START;
const tick = name => { const now = Date.now(); console.log(`TIME ${name}: ${((now - tMark) / 1000).toFixed(1)} s`); tMark = now; };

const CLUBS = [['VfB Stuttgart', 'Q4512'], ['Karlsruher SC', 'Q105853'], ['1. FC Kaiserslautern', 'Q8466'],
  ['Stuttgarter Kickers', 'Q170105'], ['Poli Timișoara', 'Q4654417'], ['UTA Arad', 'Q680770'],
  ['FC Bayern München', 'Q15789'], ['1. FC Nürnberg', 'Q15786'], ['Inter', 'Q631'], ['Eintracht Frankfurt', 'Q38245'],
  ['SV Elversberg', 'Q692691']];
// Clubs whose every researched row is checked on the sheet, text against the files (2026-10-11;
// SV Elversberg added 2026-10-22).
const FULL_ROWS = ['Q38245', 'Q692691'];

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
const clubRules = csv('data/club-ticket-rules.csv'), phases = csv('data/club-ticket-phases.csv'), demand = csv('data/club-ticket-demand.csv');
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
    if(FULL_ROWS.includes(qid)){
      const flat = norm(S.text), mine = r => r.clubQid === qid && (r.team || 'men') === 'men';
      const miss = [...clubRules.filter(mine).filter(r => !flat.includes(norm(r.rule))).map(r => `rule ${r.topic}`),
        ...windows.filter(mine).filter(r => !flat.includes(norm(r.label))).map(r => `window ${r.window}`),
        ...phases.filter(mine).filter(r => !flat.includes(norm(r.buyers))).map(r => `phase ${r.window}/${r.phase}`)];
      check(`${label}: every rule, window label and phase in the files is on the sheet`, !miss.length, miss.join(' | '));
      const nd = await page.evaluate(() => { const d = [...document.querySelectorAll('#sheetTix details')]
        .find(x => x.querySelector(':scope > summary')?.textContent.startsWith('Sell-out record'));
        return d ? d.querySelectorAll(':scope > .item').length : -1; });
      const want = demand.filter(mine).length;
      check(`${label}: Sell-out record holds all ${want} rows of the file`, want ? nd === want : nd === -1, `shown ${nd}`);
    }
    // Sale dates are shown only on the Bucket list: no Next window line, no window date line.
    check(`${label}: no sale date on the sheet - no Next window line, no "Typically opens"`,
      S.next === null && !/Next window|Typically opens/.test(S.text));
    check(`${label}: no sideways scroll`, await noSideScroll());
    if(label === 'Inter') await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', 'sheet-inter.png')});
  }

  tick('page load + ticket info per club');
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


  tick('club with neither source');
  // ---- Rivalries section: read from the data files, no club name or count written here.
  const riv = csv('data/club-rivalries.csv'), rivSrc = csv('data/club-culture-sources.csv');
  const bucketLines = csv('data/bucket-links-manual.csv').filter(r => !r.ticketEventId);
  const RANK = {main: 0, local: 1, other: 2}, LABEL = {main: 'Main rival', local: 'Local rival', other: 'Other rivalry'};
  const expectOrder = rows => [...rows].sort((a, b) => RANK[a.class] - RANK[b.class] || a.rivalName.localeCompare(b.rivalName));
  const clubNames = await page.evaluate(() => Object.fromEntries(CLUBS.map(c => [c.id, c.name])));
  const RIV_NONE = 'No rivalry recorded for this club yet.', RIV_MIRROR = n => `Stated on ${n}'s page only`;
  // What a club's Rivalries section holds (2026-10-18), worked out from the rows alone: its own rows (class order, then name), then every
  // row that names this club in rivalQ when this club has no row of its own for the club that states it, shown as that club (no class),
  // labelled, alphabetical. A row with no rivalQ is never mirrored.
  const rivValid = r => RANK[r.class] !== undefined && rivSrc.some(x => x.sourceId === r.sourceId);
  const expRiv = (q, rows = riv) => {
    const ok = rows.filter(rivValid);
    const own = expectOrder(ok.filter(r => r.clubQ === q)).map(r => ({...r, mirror: ''}));
    const ownFor = new Set(own.map(r => r.rivalQ).filter(Boolean));
    const mir = ok.filter(r => r.rivalQ === q && r.clubQ && r.clubQ !== q && !ownFor.has(r.clubQ) && clubNames[r.clubQ])
      .map(r => ({...r, rivalQ: r.clubQ, rivalName: clubNames[r.clubQ], mirror: r.clubQ, class: ''}))
      .sort((a, b) => a.rivalName.localeCompare(b.rivalName));
    return [...own, ...mir];
  };
  const rivalSheet = async (pg, qid) => {
    await pg.evaluate(q => openSheet(CLUBS.find(c => c.id === q)), qid);
    await pg.waitForFunction(() => !/Loading/.test(document.getElementById('sheetTix').textContent), null, {timeout: 10000});
    await pg.waitForTimeout(200);
    return pg.evaluate(() => {
      const b = document.getElementById('sheetBody'), sb = document.querySelector('#sheet .sbody');
      return {h4: [...b.querySelectorAll('h4')].map(h => h.textContent),
        none: b.querySelector('.rivnone')?.textContent || '',
        rows: [...b.querySelectorAll('.riv')].map(r => ({name: r.querySelector('.rvname').textContent,
          mirror: r.querySelector('.rvmirror')?.textContent || '', dataMirror: r.dataset.mirror === '1', dataClass: r.dataset.class || '',
          cls: r.querySelector('.rvclass')?.textContent || '', tap: r.querySelector('.rvname').tagName === 'BUTTON',
          rivalId: r.querySelector('.rvname').dataset.id || '', href: r.querySelector('a')?.href || '',
          sub: r.querySelector('.sub:not(.frquote)').textContent, quote: r.querySelector('.frquote')?.textContent || '',
          quoteLabel: r.querySelector('.frquote > span:first-child')?.textContent || '', quoteIsData: r.querySelector('.frquote > span[data-content]')?.textContent || '',
          sourceSays: /Source says/.test(r.textContent), bucket: [...r.querySelectorAll('.rvbucket')].map(x => x.dataset.bucket),
          wide: r.scrollWidth > r.clientWidth + 1, shown: !r.hidden})),
        more: b.querySelector('.rvmore')?.textContent || '',
        parent: (p => p && {text: p.textContent, id: p.querySelector('button.rvname')?.dataset.id || '', tap: !!p.querySelector('button.rvname'),
          btnText: p.querySelector('button.rvname')?.textContent || '', inRivs: !!p.closest('.rivs'),
          last: ![...b.querySelectorAll('.riv, .rvmore')].some(x => x.compareDocumentPosition(p) & Node.DOCUMENT_POSITION_PRECEDING),
          wide: p.scrollWidth > p.clientWidth + 1})(b.querySelector('.rvparent')),
        sideways: sb.scrollWidth > sb.clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1};
    });
  };
  const onMap = await page.evaluate(() => CLUBS.map(c => c.id));
  const ownClubs = [...new Set(riv.map(r => r.clubQ))].filter(q => onMap.includes(q));
  const withRows = onMap.filter(q => expRiv(q).length > 0);          // own rows or mirrored ones
  // data/club-parents.csv (2026-10-19): a reserve side whose first team is on the map. Read here from the file; the sentence it
  // makes the sheet show is worked out from the row alone.
  const parentsCsv = csv('data/club-parents.csv');
  const parentOf = Object.fromEntries(parentsCsv.filter(r => onMap.includes(r.clubQ) && onMap.includes(r.parentQ)).map(r => [r.clubQ, r.parentQ]));
  const PARENT_SENTENCE = pn => `Reserve side of ${pn}. Its rivals are listed on the first team's sheet.`;
  const noRows = onMap.filter(q => expRiv(q).length === 0 && !parentOf[q]);   // the neutral line only on a club that is no reserve side here
  const mirTotal = withRows.reduce((n, q) => n + expRiv(q).filter(w => w.mirror).length, 0);
  const rivGainedRows = withRows.filter(q => ownClubs.includes(q) && expRiv(q).some(w => w.mirror)), rivGainedSection = withRows.filter(q => !ownClubs.includes(q));
  console.log(`  rivalry rows mirrored in total: ${mirTotal}; clubs with own rows gaining mirrored rows: ${rivGainedRows.length}; clubs gaining the section: ${rivGainedSection.length}; clubs on the map with the neutral line: ${noRows.length} of ${onMap.length}`);
  check('at least one club has rivalry rows, and one has mirrored rows', ownClubs.length > 0 && mirTotal > 0, `${withRows.length} clubs, ${mirTotal} mirrored`);
  let sectionOk = true, orderOk = true, linkOk = true, widthOk = true, bucketOk = true, mirrorOk = true, neutralOk = true, parentOk = true, nParents = 0, nParentRows = 0, bad = [];
  for(const q of onMap){
    const want = expRiv(q);
    const R = await rivalSheet(page, q);
    const name = clubNames[q];
    if(R.h4.filter(h => h === 'Rivalries').length !== 1) { sectionOk = false; bad.push(`${name}: section`); }
    const pq = parentOf[q];                                  // a reserve side listed in club-parents.csv, with its first team on the map
    if(pq){
      nParents++;
      if(!R.parent || R.parent.text !== PARENT_SENTENCE(clubNames[pq]) || R.parent.id !== pq || !R.parent.tap || R.parent.btnText !== clubNames[pq] || !R.parent.inRivs || !R.parent.last || R.parent.wide){
        parentOk = false; bad.push(`${name}: reserve-side sentence ${JSON.stringify(R.parent)}`); }
      if(want.length) nParentRows++;
    } else if(R.parent !== null){ parentOk = false; bad.push(`${name}: a sentence on a club with no row in club-parents.csv`); }
    if(!want.length){                                       // nothing own, nothing mirrored
      if(pq){                                               // a reserve side: the sentence instead of the neutral line, and no row
        if(R.none || R.rows.length || R.more) { neutralOk = false; bad.push(`${name}: neutral line or rows on a reserve side with no rows`); }
      } else if(R.none !== RIV_NONE || R.rows.length || R.more) { neutralOk = false; bad.push(`${name}: neutral line`); }
      continue;
    }
    if(R.none) { neutralOk = false; bad.push(`${name}: neutral line on a club with rows`); }
    if(JSON.stringify(R.rows.map(r => r.name)) !== JSON.stringify(want.map(r => r.rivalName)) ||
       JSON.stringify(R.rows.map(r => r.cls)) !== JSON.stringify(want.map(r => r.mirror ? '' : LABEL[r.class]))){ orderOk = false; bad.push(`${name}: order`); }
    const wo = want.filter(w => !w.mirror);
    if(wo.length && RANK[wo[0].class] !== Math.min(...wo.map(r => RANK[r.class]))){ orderOk = false; bad.push(`${name}: biggest not first`); }
    if(want.findIndex(w => w.mirror) >= 0 && want.slice(want.findIndex(w => w.mirror)).some(w => !w.mirror)){ orderOk = false; bad.push(`${name}: a mirrored row before an own one`); }
    R.rows.forEach((r, i) => {
      const w = want[i];
      if(r.mirror !== (w.mirror ? RIV_MIRROR(clubNames[w.mirror]) : '') || r.dataMirror !== !!w.mirror || (w.mirror && (r.cls || r.dataClass)) || (!w.mirror && r.dataClass !== w.class)){ mirrorOk = false; bad.push(`${name}: label or class tag of ${r.name}`); }
      if(w.mirror && (w.quote ? r.quote !== `Source says: «${w.quote}»` : r.quote !== '')){ mirrorOk = false; bad.push(`${name}: quote of mirrored ${r.name}`); }
      if(w.mirror && r.rivalId !== w.mirror){ mirrorOk = false; bad.push(`${name}: mirrored ${r.name} not tappable to its club`); }
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
  check('every club on the map shows one Rivalries section', sectionOk, bad.join(' | '));
  check('rivals in class order, main then local then other, alphabetical within a class, biggest first; mirrored rows after the club\'s own, alphabetical', orderOk, bad.join(' | '));
  check(`every row with a rivalQ shows on the rival's sheet: its own row, or mirrored with "Stated on <club>'s page only", no class tag, the stating club's quote and a tap to it (${mirTotal} mirrored rows)`, mirrorOk && mirTotal === riv.filter(r => rivValid(r) && r.rivalQ && r.clubQ !== r.rivalQ && onMap.includes(r.rivalQ) && onMap.includes(r.clubQ) && !riv.some(o => rivValid(o) && o.clubQ === r.rivalQ && o.rivalQ === r.clubQ)).length, bad.join(' | '));
  check(`a club with no own row and no mirrored row shows "${RIV_NONE}" and no row; a club with rows does not (${noRows.length} clubs)`, neutralOk && noRows.length > 0, bad.join(' | '));
  check('each row has its class label, a source link and "Checked on", and taps only when the rival is on the map', linkOk, bad.join(' | '));
  check('a bucket link shows exactly when a bucket entry names both clubs by Wikidata id', bucketOk, bad.join(' | '));
  check('the Rivalries section fits 390 px, no sideways scroll', widthOk, bad.join(' | '));
  console.log(`  reserve sides in club-parents.csv: ${parentsCsv.length} rows, ${nParents} with both clubs on the map, ${nParentRows} of them with rivalry rows of their own or mirrored`);
  check(`every reserve side in club-parents.csv (${nParents}) shows "Reserve side of <parent>. Its rivals are listed on the first team's sheet." with the parent tappable, below any rivalry rows, no neutral line; every other club shows no such sentence`,
    parentOk && nParents > 0 && nParents === parentsCsv.length, bad.join(' | ') + ` (${nParents} of ${parentsCsv.length} rows)`);

  const without = await page.evaluate(have => { const c = CLUBS.find(c => !have.includes(c.id)); return c && {id: c.id, name: c.name}; }, [...withRows, ...Object.keys(parentOf)]);
  const W = await rivalSheet(page, without.id);
  check(`a club without rows (${without.name}) shows the Rivalries heading with the neutral line, no rows and no Show all`, W.h4.includes('Rivalries') && W.none === RIV_NONE && !W.rows.length && !W.more && !W.sideways);

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
  const many = ownClubs.sort((a, b) => riv.filter(r => r.clubQ === b).length - riv.filter(r => r.clubQ === a).length)[0];
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
  const Mriv = await rivalSheet(pg2, many);
  const mwant = expRiv(many, csvText(mixed));        // the club's own rows, then any mirrored ones
  const mrows = mwant;
  check('mixed classes: main first, then local, then other, alphabetical within a class',
    new Set(mrows.filter(r => !r.mirror).map(r => r.class)).size > 1 && JSON.stringify(Mriv.rows.map(r => r.name)) === JSON.stringify(mwant.map(r => r.rivalName)) &&
    JSON.stringify(Mriv.rows.map(r => r.cls)) === JSON.stringify(mwant.map(r => r.mirror ? '' : LABEL[r.class])) && Mriv.rows[0].cls === LABEL[mwant[0].class],
    Mriv.rows.map(r => `${r.name}:${r.cls}`).join(' | '));
  // More than 5 rows: the first 5 show, the rest wait behind "Show all (n)".
  check(`more than 5 rows (${mrows.length}): 5 shown, "Show all (${mrows.length})" present`,
    mrows.length > 5 && Mriv.rows.filter(r => r.shown).length === 5 && Mriv.more === `Show all (${mrows.length})`, `${Mriv.rows.filter(r => r.shown).length} shown, "${Mriv.more}"`);
  await pg2.click('#sheetBody .rvmore');
  const opened = await pg2.evaluate(() => ({shown: [...document.querySelectorAll('#sheetBody .riv')].filter(r => !r.hidden).length,
    expanded: document.querySelector('#sheetBody .rvmore').getAttribute('aria-expanded'),
    sideways: document.getElementById('sheetBody').scrollWidth > document.getElementById('sheetBody').clientWidth + 1}));
  check('"Show all" reveals every row, no sideways scroll', opened.shown === mrows.length && opened.expanded === 'true' && !opened.sideways, JSON.stringify(opened));

  // ---- Rivalry quotes (2026-10-17): a row with a quote shows "Source says: «…»" under it, the quote marked as data, using
  // the Fan friendships quote's renderer and string; a row without one looks as before. Expected values come from the files.
  const qSrc = rivSrc[0].sourceId;
  const RQ = 'Erbitterte Rivalität zwischen den beiden Vereinen';
  const rivQCsv = fs.readFileSync(path.join(ROOT, 'data/club-rivalries.csv'), 'utf8').replace(/\n?$/, '\n') +
    `${without.id},,Quote Test FC,other,${qSrc},2026-10-03,"${RQ}, «so»"\n${without.id},,Noquote Test FC,other,${qSrc},2026-10-03\n`;
  const RQT = `${RQ}, «so»`;
  const pgQ = await ctx.newPage();
  await pgQ.route('**/data/club-rivalries.csv', r => r.fulfill({status: 200, contentType: 'text/csv', body: rivQCsv}));
  pgQ.on('pageerror', e => errors.push(e.message));
  await pgQ.goto(BASE);
  await pgQ.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  const QS = await rivalSheet(pgQ, without.id);
  const qRow = QS.rows.find(r => r.name === 'Quote Test FC'), nRow = QS.rows.find(r => r.name === 'Noquote Test FC');
  check('rivalry quote: an injected row with a quote shows "Source says: «…»", the quote in the data-content element',
    !!qRow && qRow.quote === `Source says: «${RQT}»` && qRow.quoteLabel === 'Source says:' && qRow.quoteIsData === `«${RQT}»` && /Checked on /.test(qRow.sub), JSON.stringify(qRow));
  check('rivalry quote: an injected row without a quote shows no "Source says" and keeps its source line',
    !!nRow && nRow.quote === '' && !nRow.sourceSays && /Checked on /.test(nRow.sub) && !QS.sideways && QS.rows.every(r => !r.wide), JSON.stringify(nRow));
  await pgQ.close();
  const quoted = riv.filter(r => r.quote);
  const quotedClubs = withRows.filter(c => expRiv(c).some(w => w.quote));      // own quoted rows and mirrored ones
  let quotedBad = [];
  for(const c of quotedClubs){
    const R = await rivalSheet(page, c), want = expRiv(c);
    want.forEach((w, i) => { if(w.quote ? R.rows[i].quote !== `Source says: «${w.quote}»` || R.rows[i].quoteIsData !== `«${w.quote}»` : R.rows[i].sourceSays) quotedBad.push(`${c}/${w.rivalName}`); });
  }
  check(`rivalry quote: every real row with a quote (${quoted.length} rows on ${quotedClubs.length} clubs) shows it, and rows without one show none`, quotedBad.length === 0 && quoted.every(r => r.quote.split(/\s+/).length <= 15), quotedBad.join(' | '));

  {
  // ---- Mirrored rivalries and the neutral line, with injected rows (2026-10-18): Y is a club with nothing; X1..X6 each state a rivalry
  // with Y (X1 and Y also state one with each other, so Y shows its own row for X1 and no label), X7 states one with Y2 only (a club whose
  // only row is mirrored), and Z states one with a name equal to Y3's but no rivalQ (Y3 must stay empty). Expected values come from expRiv().
  const [Y, X1, X2, X3, X4, X5, X6, Y2, X7, Z, Y3] = noRows;
  const injS = rivSrc[0].sourceId;
  const inj = [
    {clubQ: X1, rivalQ: Y, rivalName: clubNames[Y], class: 'main', quote: 'Quote from X1 about Y'},
    {clubQ: Y, rivalQ: X1, rivalName: clubNames[X1], class: 'local', quote: 'Quote from Y about X1'},
    {clubQ: X2, rivalQ: Y, rivalName: clubNames[Y], class: 'main', quote: ''},
    {clubQ: X3, rivalQ: Y, rivalName: clubNames[Y], class: 'local', quote: 'Quote from X3'},
    {clubQ: X4, rivalQ: Y, rivalName: clubNames[Y], class: 'other', quote: 'Quote from X4'},
    {clubQ: X5, rivalQ: Y, rivalName: clubNames[Y], class: 'other', quote: ''},
    {clubQ: X6, rivalQ: Y, rivalName: clubNames[Y], class: 'main', quote: 'Quote from X6'},
    {clubQ: X7, rivalQ: Y2, rivalName: clubNames[Y2], class: 'local', quote: 'Quote from X7 about Y2'},
    {clubQ: Z, rivalQ: '', rivalName: clubNames[Y3], class: 'main', quote: 'Name only quote'},
  ].map(r => ({...r, sourceId: injS, checkedOn: '2026-10-03'}));
  const RH = 'clubQ,rivalQ,rivalName,class,sourceId,checkedOn,quote';
  const qv = v => /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  const injCsv = fs.readFileSync(path.join(ROOT, 'data/club-rivalries.csv'), 'utf8').replace(/\n?$/, '\n') + inj.map(r => RH.split(',').map(k => qv(r[k] || '')).join(',')).join('\n') + '\n';
  const injRows = [...riv, ...inj];
  const injPage = async lang => {
    const pg = await ctx.newPage();
    await pg.addInitScript(l => { try { localStorage.setItem('football-planner-lang', l); } catch(e){} }, lang);
    await pg.route('**/data/club-rivalries.csv', r => r.fulfill({status: 200, contentType: 'text/csv', body: injCsv}));
    pg.on('pageerror', e => errors.push(e.message));
    await pg.goto(BASE);
    await pg.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
    return pg;
  };
  const sameRiv = (S, want, lbl) => S.rows.length === want.length && want.every((w, i) => {
    const r = S.rows[i];
    return r.name === w.rivalName && r.cls === (w.mirror ? '' : LABEL[w.class]) && r.mirror === (w.mirror ? lbl(clubNames[w.mirror]) : '') &&
      (w.quote ? r.quote === `Source says: «${w.quote}»` : r.quote === '') && r.tap && r.rivalId === w.rivalQ;
  });
  const pgI = await injPage('en');
  const IY = await rivalSheet(pgI, Y), IYw = expRiv(Y, injRows);
  check(`mirror: ${clubNames[Y]} (nothing before) shows its own row for ${clubNames[X1]} (class tag, no label) first, then the five mirrored rows alphabetically, each with its label, no class tag and the stating club's quote`,
    IYw.length === 6 && IYw[0].mirror === '' && IYw.slice(1).every(w => w.mirror) && IY.none === '' && sameRiv(IY, IYw, RIV_MIRROR), JSON.stringify(IY.rows.map(r => [r.name, r.cls, r.mirror])));
  check('mirror: mirrored rows count in the first 5 and "Show all (6)"', IY.rows.filter(r => r.shown).length === 5 && IY.more === 'Show all (6)', `${IY.rows.filter(r => r.shown).length} shown, "${IY.more}"`);
  await pgI.click('#sheetBody .rvmore');
  const IYo = await pgI.evaluate(() => ({shown: [...document.querySelectorAll('#sheetBody .riv')].filter(r => !r.hidden).length, wide: [...document.querySelectorAll('#sheetBody .riv')].some(r => r.scrollWidth > r.clientWidth + 1),
    sideways: document.querySelector('#sheet .sbody').scrollWidth > document.querySelector('#sheet .sbody').clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1}));
  check('mirror: "Show all" reveals all 6 rows and nothing overflows at 390 px', IYo.shown === 6 && !IYo.wide && !IYo.sideways, JSON.stringify(IYo));
  const IX1 = await rivalSheet(pgI, X1), IX1w = expRiv(X1, injRows);
  check(`mirror: a two-sided pair (${clubNames[X1]} and ${clubNames[Y]}) shows once on each sheet, as each club's own row, with no label`,
    IX1w.length === 1 && !IX1w[0].mirror && sameRiv(IX1, IX1w, RIV_MIRROR) && IX1.rows[0].cls === 'Main rival' && IY.rows.filter(r => r.rivalId === X1).length === 1 && !IY.rows[0].mirror, JSON.stringify(IX1.rows.map(r => [r.name, r.cls, r.mirror])));
  const IY2 = await rivalSheet(pgI, Y2), IY2w = expRiv(Y2, injRows);
  check(`mirror: a club whose only row is mirrored (${clubNames[Y2]}) gets the section with that row, labelled, no class tag, and no neutral line`,
    IY2w.length === 1 && IY2w[0].mirror === X7 && IY2.h4.includes('Rivalries') && IY2.none === '' && sameRiv(IY2, IY2w, RIV_MIRROR), JSON.stringify(IY2.rows.map(r => [r.name, r.cls, r.mirror])));
  const IY3 = await rivalSheet(pgI, Y3), IZ = await rivalSheet(pgI, Z);
  check(`mirror: a row with no rivalQ shows only on its own club's sheet (${clubNames[Z]}); ${clubNames[Y3]}, whose name it carries, stays empty with the neutral line`,
    expRiv(Y3, injRows).length === 0 && IY3.none === RIV_NONE && !IY3.rows.length && IZ.rows.length === 1 && IZ.rows[0].name === clubNames[Y3] && !IZ.rows[0].mirror && IZ.rows[0].cls === 'Main rival' && IZ.none === '', JSON.stringify([IY3.none, IZ.rows.map(r => r.name)]));
  const IX7 = await rivalSheet(pgI, X7);
  check('mirror: the stating club keeps only its own row (nothing is mirrored back onto it)', IX7.rows.length === 1 && !IX7.rows[0].mirror && IX7.rows[0].name === clubNames[Y2], JSON.stringify(IX7.rows.map(r => [r.name, r.mirror])));
  await rivalSheet(pgI, Y2);
  await pgI.click(`#sheetBody .rivs .rvname[data-id="${X7}"]`);
  await pgI.waitForFunction(id => SHEET_FOR === id, X7, {timeout: 8000}).catch(() => {});
  check('mirror: tapping the club shown on a mirrored row opens that club\'s sheet', await pgI.evaluate(() => SHEET_FOR) === X7);
  await pgI.close();
  // Romanian: the label and the neutral line are Romanian, from the page's own dictionary (unchecked by the user), and the club name is filled in
  const pgIr = await injPage('ro');
  const roLbl = await pgIr.evaluate(([n]) => ({mirror: t('riv.mirror', {club: n}), none: t('riv.none'), mirrorEn: I18N.en['riv.mirror'], noneEn: I18N.en['riv.none']}), [clubNames[X7]]);
  const IYr = await rivalSheet(pgIr, Y2), IY3r = await rivalSheet(pgIr, Y3);
  check('mirror (Romanian): the label reads "Menționat doar pe pagina <club>" and the neutral line is Romanian, both different from the English, with the club name filled in',
    IYr.rows.length === 1 && IYr.rows[0].mirror === `Menționat doar pe pagina ${clubNames[X7]}` && roLbl.mirror === IYr.rows[0].mirror && IY3r.none === roLbl.none && roLbl.none !== roLbl.noneEn && roLbl.none.length > 10 && !IYr.sideways, JSON.stringify([IYr.rows.map(r => r.mirror), IY3r.none]));
  await pgIr.evaluate(() => { try { localStorage.setItem('football-planner-lang', 'en'); } catch(e){} });   // the context shares its localStorage: later pages are English
  await pgIr.close();
  }
  tick('rivalries');
  // ---- Reserve sides (2026-10-19): data/club-parents.csv. Expected values come from the file and from expRiv(); the real data has
  // no reserve side with rows of its own that is checked below unless it exists, so the "both" and "mirrored" cases are also injected.
  {
    const resList = Object.keys(parentOf);
    const resA = resList.find(q => expRiv(q).length === 0), resB = resList.find(q => q !== resA && expRiv(q).length === 0), srcId = rivSrc[0].sourceId;
    const sentenceEn = pn => PARENT_SENTENCE(pn);
    const parentPage = async (lang, extra) => {
      const pg = await ctx.newPage();
      await pg.addInitScript(l => { try { localStorage.setItem('football-planner-lang', l); } catch(e){} }, lang);
      if(extra) await pg.route('**/data/club-rivalries.csv', r => r.fulfill({status: 200, contentType: 'text/csv', body: extra}));
      pg.on('pageerror', e => errors.push(e.message));
      await pg.goto(BASE);
      await pg.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
      return pg;
    };
    const baseRivCsv = fs.readFileSync(path.join(ROOT, 'data/club-rivalries.csv'), 'utf8').replace(/\n?$/, '\n');
    // (1) tapping the parent opens its sheet
    const TA = await rivalSheet(page, resA);
    await page.click(`#sheetBody .rivs .rvparent button.rvname[data-id="${parentOf[resA]}"]`);
    await page.waitForFunction(id => SHEET_FOR === id, parentOf[resA], {timeout: 8000}).catch(() => {});
    check(`reserve side: ${clubNames[resA]} shows "${sentenceEn(clubNames[parentOf[resA]])}" and tapping ${clubNames[parentOf[resA]]} opens its sheet`,
      !!TA.parent && TA.parent.text === sentenceEn(clubNames[parentOf[resA]]) && await page.evaluate(() => SHEET_FOR) === parentOf[resA]);
    // (2) own rows and the sentence: an injected own row on resA, an injected mirrored row on resB (stated by a club with no rows)
    const stater = noRows[0];
    const injCsv2 = baseRivCsv + `${resA},,Scratch Rival FC,other,${srcId},2026-10-03,Scratch quote\n` + `${stater},${resB},${clubNames[resB]},local,${srcId},2026-10-03,\n`;
    const pgP = await parentPage('en', injCsv2);
    const PA = await rivalSheet(pgP, resA);
    const PA1 = await pgP.evaluate(() => ({w: document.querySelector('#sheetBody .rvparent').getBoundingClientRect().right, sw: document.querySelector('#sheet').getBoundingClientRect().right}));
    const PB = await rivalSheet(pgP, resB), PC = await rivalSheet(pgP, stater);
    check(`reserve side with a row of its own (${clubNames[resA]}): the row is shown as before and the sentence comes under it, no neutral line`,
      PA.rows.length === 1 && PA.rows[0].name === 'Scratch Rival FC' && PA.rows[0].cls === 'Other rivalry' && PA.none === '' && !!PA.parent && PA.parent.last && PA.parent.text === sentenceEn(clubNames[parentOf[resA]]) && !PA.sideways, JSON.stringify([PA.rows.map(r => r.name), PA.parent]));
    check(`reserve side with a mirrored row (${clubNames[resB]}, stated by ${clubNames[stater]}): the mirrored row (label, no class) and the sentence under it`,
      PB.rows.length === 1 && PB.rows[0].mirror === RIV_MIRROR(clubNames[stater]) && PB.rows[0].cls === '' && PB.none === '' && !!PB.parent && PB.parent.last && PB.parent.id === parentOf[resB], JSON.stringify([PB.rows.map(r => [r.name, r.mirror]), PB.parent]));
    check('a club with no row in club-parents.csv is unchanged: the same rows, no sentence', PC.parent === null && PC.rows.length === 1 && !PC.rows[0].mirror && PC.rows[0].name === clubNames[resB]);
    check('the sentence stays inside the sheet at 390 px', PA1.w <= PA1.sw + 1, JSON.stringify(PA1));
    await pgP.close();
    // (3) Romanian: the sentence is Romanian from the page's own dictionary, the club name is filled in, no English words of the sentence remain
    const pgRo2 = await parentPage('ro');
    const roSentence = await pgRo2.evaluate(n => t('riv.parent', {club: n}), clubNames[parentOf[resA]]);
    const enSentence = await pgRo2.evaluate(n => I18N.en['riv.parent'].split('{club}').join(n), clubNames[parentOf[resA]]);
    const RA = await rivalSheet(pgRo2, resA);
    check('reserve side (Romanian): the sentence is the Romanian one from the dictionary with the parent filled in, not the English, parent still tappable, nothing overflows',
      !!RA.parent && RA.parent.text === roSentence && roSentence !== enSentence && roSentence.includes(clubNames[parentOf[resA]]) && RA.parent.tap && RA.parent.id === parentOf[resA] && !RA.sideways && !RA.parent.wide, JSON.stringify([roSentence, RA.parent]));
    await pgRo2.evaluate(() => { try { localStorage.setItem('football-planner-lang', 'en'); } catch(e){} });
    await pgRo2.close();
  }
  tick('reserve sides');
  // ---- The "When the atmosphere is best" section was removed (2026-10-10): the sheet has Rivalries and Fan
  // friendships only. The page must not ask for the old file or draw any atmosphere element, on the two clubs
  // that used to have rows (Borussia Dortmund and 1. FC Union Berlin) or on any other.
  const pg3 = await ctx.newPage();
  const atmRequests = [];
  pg3.on('request', rq => { if(/club-atmosphere/.test(rq.url())) atmRequests.push(rq.url()); });
  pg3.on('pageerror', e => errors.push(e.message));
  await pg3.goto(BASE);
  await pg3.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
  const sheetOf = async (pg, qid) => {
    await pg.evaluate(q => openSheet(CLUBS.find(c => c.id === q)), qid);
    await pg.waitForFunction(() => !/Loading/.test(document.getElementById('sheetTix').textContent), null, {timeout: 10000});
    await pg.waitForTimeout(200);
    return pg.evaluate(() => {
      const b = document.getElementById('sheetBody'), sb = document.querySelector('#sheet .sbody');
      return {h4: [...b.querySelectorAll('h4')].map(h => h.textContent),
        atmElements: b.querySelectorAll('details.atm, .atmrow, .atmnote, #sheetAtm').length,
        sideways: sb.scrollWidth > sb.clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1};
    });
  };
  const realFri = csv('data/club-friendships.csv');
  // What a club's Fan friendships section holds, worked out from the rows alone: the club's own rows, plus every
  // row that names this club in friendQ when this club has no row of its own for the club that states it (shown
  // as that club, labelled). A row with no friendQ is never mirrored.
  const FR0 = {active: 0, unclear: 1, ended: 2};
  const friShown = (qid, rows) => {
    const own = rows.filter(r => r.clubQ === qid).map(r => ({...r, mirror: ''}));
    const ownFor = new Set(own.map(r => r.friendQ).filter(Boolean));
    const mir = rows.filter(r => r.friendQ === qid && r.clubQ && !ownFor.has(r.clubQ) && clubNames[r.clubQ])
      .map(r => ({...r, friendQ: r.clubQ, friendName: clubNames[r.clubQ], mirror: r.clubQ}));
    return [...own, ...mir].sort((a, b) => FR0[a.status] - FR0[b.status] || a.friendName.localeCompare(b.friendName));
  };
  // The sections that exist for a club are Rivalries (always, since 2026-10-18: with the neutral line when the club has no row)
  // and Fan friendships, Fan friendships directly after Rivalries when both exist. Clubs are picked from the data: one with
  // both, one with Rivalries only.
  const SECTIONS = [['Rivalries', riv], ['Fan friendships', realFri]];
  const present = q => SECTIONS.filter(([h, rows]) => h === 'Fan friendships' ? friShown(q, rows).length > 0 : true).map(([h]) => h);
  const fileClubs = onMap.filter(q => present(q).length > 0);
  const bothAt = fileClubs.find(q => present(q).length === 2);
  const oneOnly = fileClubs.find(q => present(q).length === 1);
  for(const [kind, q] of [['both sections', bothAt], ['only the Rivalries section', oneOnly]]){
    if(!q){ check(`section order: a club with ${kind} exists in the data`, false, 'none found'); continue; }
    const S = await sheetOf(page, q), want = present(q);
    const got = S.h4.filter(h => SECTIONS.some(([s]) => s === h));
    const idx = want.map(h => S.h4.indexOf(h));
    const consecutive = idx.every((x, i) => x >= 0 && (i === 0 || x === idx[i - 1] + 1));
    check(`section order, club with ${kind} (${q}): exactly [${want.join(', ') || 'none'}], each directly after the previous that exists`,
      JSON.stringify(got) === JSON.stringify(want) && consecutive, S.h4.join(' | '));
    check(`atmosphere removed (${q}): no atmosphere heading or element on the sheet`, !S.h4.includes('When the atmosphere is best') && !S.atmElements, S.h4.join(' | '));
  }
  // The two clubs that used to have atmosphere rows still show whatever Rivalries / Fan friendships rows they have.
  for(const q of ['Q41420', 'Q141971']){
    if(!onMap.includes(q)){ check(`atmosphere removed: ${q} is on the map`, false, 'not on the map'); continue; }
    const S = await sheetOf(pg3, q), want = present(q);
    check(`atmosphere removed (${q}, a club that used to have rows): no atmosphere section, and exactly [${want.join(', ') || 'none'}] still show`,
      !S.h4.includes('When the atmosphere is best') && !S.atmElements && JSON.stringify(S.h4.filter(h => SECTIONS.some(([s]) => s === h))) === JSON.stringify(want) &&
      !S.sideways, S.h4.join(' | '));
  }
  check('atmosphere removed: the page never asked for data/club-atmosphere.csv', !atmRequests.length, atmRequests.join(' '));
  const srcRow = rivSrc.find(r => r.sourceId === srcId);
  await pg3.close();
  await pg2.close();

  tick('atmosphere removed');
  // ---- "Fan friendships": temporary rows injected here only (the real file is header-only and stays so).
  // A German club and a non-German one, the order, the labels, "Show all", a tap on a friend on the map,
  // a club without rows, and 390 px in English and Romanian.
  const nonDE = await page.evaluate(m => { const c = CLUBS.find(c => c.country && c.country !== 'DE' && c.id !== m); return c && c.id; }, many);
  const friendOnMap = await page.evaluate(([a, b]) => { const c = CLUBS.find(c => c.id !== a && c.id !== b); return {id: c.id, name: c.name}; }, [many, nonDE]);
  const q = v => /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  const FH = 'clubQ,friendQ,friendName,scope,status,groupsText,sourceId,checkedOn,quote';
  const LONGQ = 'Averyverylongquotewithoutanybreakshere' + 'y'.repeat(120);
  const LONG = 'Averyveryverylongfangroupnamewithoutanybreakshere' + 'x'.repeat(120);
  const spare = await page.evaluate(ids => CLUBS.filter(c => !ids.includes(c.id)).slice(0, 8).map(c => c.id), [many, nonDE, friendOnMap.id]);
  const [M, X1, X2, X3, X4, X5, X6] = spare;
  const frRows = [
    {clubQ: many, friendQ: '', friendName: 'Zulu Test', scope: 'clubs', status: 'ended', groupsText: '', quote: 'Zu Zeiten der Teilung gab es eine Fanfreundschaft'},
    {clubQ: many, friendQ: '', friendName: 'Alpha Test', scope: 'fan-groups', status: 'active', groupsText: 'Group One, Group Two', quote: 'Une amitié, « très forte », entre „supporters“'},
    {clubQ: many, friendQ: '', friendName: 'Mike Test', scope: 'unclear', status: 'unclear', groupsText: ''},
    {clubQ: many, friendQ: '', friendName: 'Bravo Test', scope: 'clubs', status: 'active', groupsText: '', quote: 'Suporterii au o legătură strânsă de prietenie'},
    {clubQ: many, friendQ: '', friendName: 'Echo Test', scope: 'fan-groups', status: 'ended', groupsText: LONG, quote: LONGQ},
    {clubQ: many, friendQ: '', friendName: 'Delta Test', scope: 'clubs', status: 'unclear', groupsText: ''},
    {clubQ: many, friendQ: friendOnMap.id, friendName: friendOnMap.name, scope: 'fan-groups', status: 'unclear', groupsText: '', quote: 'ein freundschaftliches Verhältnis'},
    {clubQ: nonDE, friendQ: '', friendName: 'Foreign Beta', scope: 'clubs', status: 'ended', groupsText: ''},
    {clubQ: nonDE, friendQ: '', friendName: 'Foreign Alpha', scope: 'fan-groups', status: 'active', groupsText: 'Some Fans'},
    // mirror tests: six clubs state a friendship with M (one two-sided: M also has its own row for X2), X3 also has a
    // name-only row, and M has a name-only row of its own
    {clubQ: X1, friendQ: M, friendName: clubNames[M], scope: 'clubs', status: 'ended', groupsText: '', quote: 'Quote from X1'},
    {clubQ: X2, friendQ: M, friendName: clubNames[M], scope: 'fan-groups', status: 'active', groupsText: 'X2 Fans', quote: 'Quote from X2 about M'},
    {clubQ: M, friendQ: X2, friendName: clubNames[X2], scope: 'clubs', status: 'active', groupsText: '', quote: 'Quote from M about X2'},
    {clubQ: X3, friendQ: M, friendName: clubNames[M], scope: 'unclear', status: 'unclear', groupsText: '', quote: 'Quote from X3'},
    {clubQ: X3, friendQ: '', friendName: 'Name Only FC', scope: 'clubs', status: 'active', groupsText: '', quote: 'Name only quote'},
    {clubQ: X4, friendQ: M, friendName: clubNames[M], scope: 'clubs', status: 'active', groupsText: '', quote: 'Quote from X4'},
    {clubQ: X5, friendQ: M, friendName: clubNames[M], scope: 'fan-groups', status: 'unclear', groupsText: 'X5 Fans', quote: 'Quote from X5'},
    {clubQ: X6, friendQ: M, friendName: clubNames[M], scope: 'clubs', status: 'ended', groupsText: '', quote: 'Quote from X6'},
    {clubQ: M, friendQ: '', friendName: 'Own Name Only', scope: 'clubs', status: 'unclear', groupsText: ''},
  ].map(r => ({...r, sourceId: srcId, checkedOn: '2026-10-03'}));
  const frCsv = FH + '\n' + frRows.map(r => FH.split(',').map(k => q(r[k] || '')).join(',')).join('\n') + '\n';
  const rivExtra = `${nonDE},,Test Rival,main,${srcId},2026-10-03`;
  const FRI_RANK = {active: 0, unclear: 1, ended: 2};
  const wantFri = id => frRows.filter(r => r.clubQ === id).sort((a, b) => FRI_RANK[a.status] - FRI_RANK[b.status] || a.friendName.localeCompare(b.friendName));
  const friPage = async lang => {
    const pg = await ctx.newPage();
    if(lang) await pg.addInitScript(l => { try { localStorage.setItem('football-planner-lang', l); } catch(e){} }, lang);
    await pg.route('**/data/club-friendships.csv', r => r.fulfill({status: 200, contentType: 'text/csv', body: frCsv}));
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
          groups: r.querySelector('.frgroups')?.textContent || '', quote: r.querySelector('.frquote')?.textContent || '',
          quoteLabel: r.querySelector('.frquote > span:first-child')?.textContent || '', quoteIsData: r.querySelector('.frquote > span[data-content]')?.textContent || '', href: r.querySelector('.frsrc a')?.href || '', src: r.querySelector('.frsrc').textContent,
          shown: !r.hidden, mirror: r.querySelector('.frmirror')?.textContent || '', wide: r.scrollWidth > r.clientWidth + 1})),
        more: b.querySelector('.frmore')?.textContent || '', sections: b.querySelectorAll('.fris').length,
        rivs: b.querySelectorAll('.riv').length, atm: b.querySelectorAll('details.atm, .atmrow, .atmnote, #sheetAtm').length,
        sideways: sb.scrollWidth > sb.clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1};
    });
  };
  const SC = {'fan-groups': 'Between fan groups', clubs: 'Between clubs', unclear: 'Not specified'}, ST = {active: 'Active', ended: 'Ended', unclear: 'Not clear'};
  const pg4 = await friPage(null);
  const F = await friSheet(pg4, many), fw = wantFri(many);
  check('friendships: "Fan friendships" sits directly below Rivalries, with its note, and no atmosphere section follows',
    F.h4.indexOf('Fan friendships') === F.h4.indexOf('Rivalries') + 1 && !F.h4.includes('When the atmosphere is best') && !F.atm &&
    F.note === 'As stated by the cited source. Fan friendships change and can end.', F.h4.join(' | '));
  check('friendships: active, then not clear, then ended, alphabetical within each',
    JSON.stringify(F.rows.map(r => r.name)) === JSON.stringify(fw.map(r => r.friendName)) && F.rows.length === fw.length, F.rows.map(r => r.name).join(' | '));
  check('friendships: every row has its scope label, status label, groups (only when the source names them) and a source with "Checked on"',
    F.rows.every((r, i) => r.scope === SC[fw[i].scope] && r.status === ST[fw[i].status] &&
      (fw[i].groupsText ? r.groups === `Groups: ${fw[i].groupsText}` : r.groups === '') &&
      r.href === srcRow.url && /Checked on /.test(r.src) && r.src.includes(srcRow.title)), JSON.stringify(F.rows.map(r => [r.scope, r.status, r.groups.slice(0, 30)])));
  check('friendships: a row with a quote shows "Source says: «…»" in the original wording (the quote itself marked as data, not translated); a row without one shows no quote line',
    F.rows.every((r, i) => fw[i].quote ? r.quote === `Source says: «${fw[i].quote}»` && r.quoteLabel === 'Source says:' && r.quoteIsData === `«${fw[i].quote}»` : r.quote === ''),
    JSON.stringify(F.rows.map(r => r.quote.slice(0, 40))));
  const stRank = {Active: 0, 'Not clear': 1, Ended: 2};
  check('friendships: an ended row sorts last (every Ended row comes after every other row), and the last row shown is an ended one',
    F.rows.length > 1 && F.rows[F.rows.length - 1].status === 'Ended' && F.rows.every((r, i) => i === 0 || stRank[r.status] >= stRank[F.rows[i - 1].status]),
    F.rows.map(r => r.status).join(', '));
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
  const NF = await friSheet(pg4, (await pg4.evaluate(([a, b, c, sp]) => CLUBS.find(x => ![a, b, c, ...sp].includes(x.id)).id, [many, nonDE, friendOnMap.id, spare])));
  check('friendships: a club without rows shows no Fan friendships section', !NF.h4.includes('Fan friendships') && !NF.sections && !NF.rows.length && !NF.note);
  const FD = await friSheet(pg4, nonDE), fd = wantFri(nonDE);
  check(`friendships: a non-German club (${nonDE}) shows Rivalries and Fan friendships, in that order, and no atmosphere section`,
    FD.h4.indexOf('Fan friendships') === FD.h4.indexOf('Rivalries') + 1 && !FD.h4.includes('When the atmosphere is best') &&
    FD.rivs === expRiv(nonDE, csvText(mixed + rivExtra + '\n')).length && FD.atm === 0 && JSON.stringify(FD.rows.map(r => r.name)) === JSON.stringify(fd.map(r => r.friendName)) && !FD.sideways, FD.h4.join(' | '));
  tick('friendships, injected rows');
  // ---- Mirrored rows (injected): a friendship stated on one club's page only also shows on the friend's sheet.
  const LBL = n => `Stated on ${n}'s page only`;
  const sameRows = (S, want, lbl) => S.rows.length === want.length && want.every((w, i) => {
    const r = S.rows[i];
    return r.name === w.friendName && r.scope === SC[w.scope] && r.status === ST[w.status] &&
      (w.groupsText ? r.groups === `Groups: ${w.groupsText}` : r.groups === '') &&
      (w.quote ? r.quote === `Source says: «${w.quote}»` : r.quote === '') &&
      r.mirror === (w.mirror ? lbl(clubNames[w.mirror]) : '') && r.tap === !!w.friendQ && r.fid === (w.friendQ || '');
  });
  const mirT = await friSheet(pg4, friendOnMap.id), mirTw = friShown(friendOnMap.id, frRows);
  check(`mirror: a club whose only rows are mirrored (${friendOnMap.id}) gets the section, with the friend shown as the club that states it (tappable), the row exactly as stated and the label`,
    mirTw.length === 1 && mirTw[0].mirror === many && mirT.h4.includes('Fan friendships') && mirT.note === 'As stated by the cited source. Fan friendships change and can end.' && sameRows(mirT, mirTw, LBL),
    JSON.stringify(mirT.rows.map(r => [r.name, r.mirror, r.quote])));
  const mirM = await friSheet(pg4, M), mirMw = friShown(M, frRows);
  check(`mirror: ${M} shows its own rows and the mirrored ones, sorted active / not clear / ended and alphabetically by the friend shown, each mirrored row with its label`,
    sameRows(mirM, mirMw, LBL) && mirM.rows.map(r => r.status).every((x, i, a) => i === 0 || stRank[x] >= stRank[a[i - 1]]), JSON.stringify(mirM.rows.map(r => [r.name, r.status, r.mirror ? 'mirror' : 'own'])));
  check(`mirror: ${M} has ${mirMw.length} rows, 5 shown and "Show all (${mirMw.length})" - mirrored rows count`, mirMw.length === 7 && mirM.rows.filter(r => r.shown).length === 5 && mirM.more === `Show all (${mirMw.length})`,
    `${mirM.rows.filter(r => r.shown).length} shown, "${mirM.more}"`);
  const x2On = mirM.rows.filter(r => r.fid === X2);
  const mirX2 = await friSheet(pg4, X2);
  check(`mirror: a two-sided pair (${X2} and ${M}) shows once on each sheet, with its own row only and no label`,
    x2On.length === 1 && !x2On[0].mirror && x2On[0].quote === 'Source says: «Quote from M about X2»' && mirX2.rows.filter(r => r.fid === M).length === 1 &&
    !mirX2.rows.find(r => r.fid === M).mirror && mirX2.rows.find(r => r.fid === M).quote === 'Source says: «Quote from X2 about M»', JSON.stringify(mirX2.rows.map(r => [r.name, r.mirror])));
  const mirX3 = await friSheet(pg4, X3);
  const everyoneElse = [];
  for(const c of [M, X1, X2, X4, friendOnMap.id]){ const S = await friSheet(pg4, c); if(S.rows.some(r => /Name Only FC|Own Name Only/.test(r.name) && c !== X3 && c !== M)) everyoneElse.push(c); }
  check('mirror: a row with no friendQ shows only on its own club\'s sheet (X3\'s "Name Only FC" and M\'s "Own Name Only" are on no other)',
    mirX3.rows.some(r => r.name === 'Name Only FC' && !r.mirror) && mirM.rows.filter(r => r.name === 'Own Name Only').length === 1 && !everyoneElse.length &&
    sameRows(mirX3, friShown(X3, frRows), LBL), everyoneElse.join(', '));
  const mirOver = await pg4.evaluate(() => ({wide: [...document.querySelectorAll('#sheetBody .fri')].some(r => r.scrollWidth > r.clientWidth + 1),
    sideways: document.querySelector('#sheet .sbody').scrollWidth > document.querySelector('#sheet .sbody').clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1}));
  await friSheet(pg4, M);
  await pg4.click('#sheetBody .frmore');
  const mirOpen = await pg4.evaluate(() => ({shown: [...document.querySelectorAll('#sheetBody .fri')].filter(r => !r.hidden).length, wide: [...document.querySelectorAll('#sheetBody .fri')].some(r => r.scrollWidth > r.clientWidth + 1),
    sideways: document.querySelector('#sheet .sbody').scrollWidth > document.querySelector('#sheet .sbody').clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1}));
  check('mirror (English): every row open, label included, nothing overflows at 390 px', mirOpen.shown === 7 && !mirOpen.wide && !mirOpen.sideways && !mirOver.sideways, JSON.stringify(mirOpen));
  await pg4.click(`#sheetBody .fris .frname[data-id="${X1}"]`);
  await pg4.waitForFunction(id => SHEET_FOR === id, X1, {timeout: 8000}).catch(() => {});
  check('mirror: tapping the club shown on a mirrored row opens that club\'s sheet', await pg4.evaluate(() => SHEET_FOR) === X1);
  const pg5 = await friPage('ro');
  const RO = await friSheet(pg5, many);
  const SCro = {'fan-groups': 'Între grupurile de suporteri', clubs: 'Între cluburi', unclear: 'Nespecificat'}, STro = {active: 'Activă', ended: 'Încheiată', unclear: 'Neclară'};
  check('friendships (Romanian): heading, note, labels and "Arată tot" are Romanian and the order is the same',
    RO.h4.includes('Prietenii între suporteri') && RO.note.startsWith('Așa cum le arată sursa citată') && RO.more === `Arată tot (${fw.length})` &&
    RO.rows.every((r, i) => r.scope === SCro[fw[i].scope] && r.status === STro[fw[i].status] && r.name === fw[i].friendName), RO.h4.join(' | '));
  check('friendships (Romanian): the label reads "Sursa spune:" and the quote stays in its original language',
    RO.rows.every((r, i) => fw[i].quote ? r.quote === `Sursa spune: «${fw[i].quote}»` && r.quoteLabel === 'Sursa spune:' && r.quoteIsData === `«${fw[i].quote}»` : r.quote === ''),
    JSON.stringify(RO.rows.map(r => r.quote.slice(0, 40))));
  await pg5.click('#sheetBody .frmore');
  const ROo = await pg5.evaluate(() => ({wide: [...document.querySelectorAll('#sheetBody .fri')].some(r => r.scrollWidth > r.clientWidth + 1),
    sideways: document.querySelector('#sheet .sbody').scrollWidth > document.querySelector('#sheet .sbody').clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1}));
  check('friendships (Romanian): nothing overflows at 390 px with every row open', !ROo.wide && !ROo.sideways && !RO.sideways, JSON.stringify(ROo));
  const LBLro = n => `Menționat doar pe pagina ${n}`;
  const roM = await friSheet(pg5, M);
  await pg5.click('#sheetBody .frmore');
  const roMo = await pg5.evaluate(() => ({wide: [...document.querySelectorAll('#sheetBody .fri')].some(r => r.scrollWidth > r.clientWidth + 1),
    sideways: document.querySelector('#sheet .sbody').scrollWidth > document.querySelector('#sheet .sbody').clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1}));
  const roMw = friShown(M, frRows);
  check('mirror (Romanian): the label reads "Menționat doar pe pagina <club>" on every mirrored row and only there, the quote stays in its original language, nothing overflows at 390 px',
    roM.rows.length === roMw.length && roMw.every((w, i) => roM.rows[i].mirror === (w.mirror ? LBLro(clubNames[w.mirror]) : '') && (w.quote ? roM.rows[i].quote === `Sursa spune: «${w.quote}»` : true)) &&
    roMw.some(w => w.mirror) && roM.more === `Arată tot (${roMw.length})` && !roMo.wide && !roMo.sideways, JSON.stringify(roM.rows.map(r => r.mirror)));
  await pg4.close(); await pg5.close();

  tick('mirrored rows, injected');
  // ---- Real data: every row of data/club-friendships.csv shows its quote on its club's sheet, and the sheet
  // lists the active rows first and the ended ones last; nothing overflows at 390 px in English or Romanian.
  const realByClub = {};
  for(const r of realFri) (realByClub[r.clubQ] = realByClub[r.clubQ] || []).push(r);
  check('real data: every club with friendship rows is on the map', Object.keys(realByClub).every(c => onMap.includes(c)) && Object.keys(realByClub).length > 0,
    Object.keys(realByClub).filter(c => !onMap.includes(c)).join(', '));
  // Every club whose sheet should hold rows: its own, and the ones mirrored onto it.
  const realExp = {};
  for(const c of onMap){ const e = friShown(c, realFri); if(e.length) realExp[c] = e; }
  const realClubs = Object.keys(realExp);
  const mirroredTotal = Object.values(realExp).reduce((n, e) => n + e.filter(r => r.mirror).length, 0);
  const gained = Object.keys(realExp).filter(c => realExp[c].some(r => r.mirror));
  const gainedSection = gained.filter(c => !realByClub[c]);
  console.log(`  mirrored rows shown in total: ${mirroredTotal}; clubs with mirrored rows: ${gained.length} (${gainedSection.length} only mirrored, i.e. gained the section)`);
  const realPage = async lang => {
    const pg = await ctx.newPage();
    if(lang) await pg.addInitScript(l => { try { localStorage.setItem('football-planner-lang', l); } catch(e){} }, lang);
    pg.on('pageerror', e => errors.push(e.message));
    await pg.goto(BASE);
    await pg.waitForFunction(() => / z\d+/.test(document.getElementById('zoomChip').textContent), null, {timeout: 30000});
    return pg;
  };
  const pgR = await realPage('en');   // pinned: the Romanian page above left its language in the shared localStorage
  const lacking = [], badOrder = [], overflowR = [], seen = {};
  for(const c of realClubs){
    const S = await friSheet(pgR, c); seen[c] = S;
    const exp = realExp[c];
    if(S.rows.length !== exp.length) lacking.push(`${c}: ${S.rows.length} rows shown, ${exp.length} expected`);
    if(!S.h4.includes('Fan friendships')) lacking.push(`${c}: no Fan friendships section`);
    if(!realByClub[c] && !exp.every(r => r.mirror)) lacking.push(`${c}: expected only mirrored rows`);
    for(const r of exp){
      const row = S.rows.find(x => x.name === r.friendName && !!x.mirror === !!r.mirror);
      if(!row) lacking.push(`${c}/${r.friendName}: row missing`);
      else {
        if(r.quote ? row.quote !== `Source says: «${r.quote}»` : row.quote !== '') lacking.push(`${c}/${r.friendName}: quote`);
        if(row.scope !== SC[r.scope] || row.status !== ST[r.status] || (r.groupsText ? row.groups !== `Groups: ${r.groupsText}` : row.groups !== '')) lacking.push(`${c}/${r.friendName}: scope, status or groups`);
        if(row.mirror !== (r.mirror ? `Stated on ${clubNames[r.mirror]}'s page only` : '')) lacking.push(`${c}/${r.friendName}: label "${row.mirror}"`);
        if(r.mirror && (!row.tap || row.fid !== r.mirror)) lacking.push(`${c}/${r.friendName}: not tappable to ${r.mirror}`);
      }
    }
    const shown = S.rows.filter(r => r.shown).length;
    if(shown !== Math.min(5, exp.length) || S.more !== (exp.length > 5 ? `Show all (${exp.length})` : '')) lacking.push(`${c}: ${shown} shown, "${S.more}" for ${exp.length} rows`);
    if(!S.rows.every((r, i) => i === 0 || stRank[r.status] >= stRank[S.rows[i - 1].status])) badOrder.push(c);
    // click only when the button exists: a missing one made click() wait its 30 s default for 61 of 72 clubs
    const moreBtn = await pgR.$('#sheetBody .frmore'); if(moreBtn) await moreBtn.click();
    const w = await pgR.evaluate(() => ({wide: [...document.querySelectorAll('#sheetBody .fri')].some(r => r.scrollWidth > r.clientWidth + 1),
      sideways: document.querySelector('#sheet .sbody').scrollWidth > document.querySelector('#sheet .sbody').clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1}));
    if(w.wide || w.sideways) overflowR.push(c);
  }
  check(`real data: ${realClubs.length} clubs show their rows - own, plus ${mirroredTotal} mirrored ones on ${gained.length} clubs - each with its quote as "Source says: «…»", scope, status, groups, the label on mirrored rows only, and "Show all (n)" counting all of them`, !lacking.length, lacking.slice(0, 5).join(' | '));
  check('real data: every row of the file with a friendQ shows on its own club\'s sheet and, unless the friend has its own row for that club, on the friend\'s sheet with the label; a two-sided pair shows once per sheet with no label',
    realFri.every(r => {
      const own = (seen[r.clubQ]?.rows || []).filter(x => !x.mirror && x.quote === (r.quote ? `Source says: «${r.quote}»` : '') && x.name === r.friendName);
      if(!own.length) return false;
      if(!r.friendQ) return true;
      const twoSided = realFri.some(f => f.clubQ === r.friendQ && f.friendQ === r.clubQ);
      const onFriend = (seen[r.friendQ]?.rows || []).filter(x => x.fid === r.clubQ);
      return onFriend.length === 1 && (twoSided ? !onFriend[0].mirror : onFriend[0].mirror === `Stated on ${clubNames[r.clubQ]}'s page only` && onFriend[0].quote === (r.quote ? `Source says: «${r.quote}»` : ''));
    }), '');
  check('real data: a row with no friendQ is on its own club\'s sheet only',
    realFri.filter(r => !r.friendQ).every(r => Object.entries(seen).every(([c, S]) => (c === r.clubQ) === S.rows.some(x => x.quote === `Source says: «${r.quote}»` && x.name === r.friendName && !x.mirror)) ||
      !r.quote), '');
  check('real data: active rows first, then not clear, then ended, on every sheet', !badOrder.length, badOrder.join(', '));
  check('real data (English): nothing overflows at 390 px with every row open', !overflowR.length, overflowR.join(', '));
  const bigClub = [...realClubs].filter(c => realExp[c].some(r => r.mirror)).sort((a, b) => realExp[b].length - realExp[a].length)[0];
  const pgRo = await realPage('ro');
  const SRo = await friSheet(pgRo, bigClub);
  const moreBtnRo = await pgRo.$('#sheetBody .frmore'); if(moreBtnRo) await moreBtnRo.click();
  const wRo = await pgRo.evaluate(() => ({wide: [...document.querySelectorAll('#sheetBody .fri')].some(r => r.scrollWidth > r.clientWidth + 1),
    sideways: document.querySelector('#sheet .sbody').scrollWidth > document.querySelector('#sheet .sbody').clientWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1}));
  check(`real data (Romanian, ${bigClub}, ${realExp[bigClub].length} rows, ${realExp[bigClub].filter(r => r.mirror).length} mirrored): labels "Sursa spune:" and "Menționat doar pe pagina …", quote unchanged, nothing overflows at 390 px`,
    SRo.rows.length === realExp[bigClub].length && realExp[bigClub].every(r => { const row = SRo.rows.find(x => x.name === r.friendName && !!x.mirror === !!r.mirror);
      return row && (r.quote ? row.quote === `Sursa spune: «${r.quote}»` : row.quote === '') && row.mirror === (r.mirror ? `Menționat doar pe pagina ${clubNames[r.mirror]}` : ''); }) &&
    !wRo.wide && !wRo.sideways, JSON.stringify(wRo));
  await pgR.close(); await pgRo.close();

  tick('real friendship data');
  // ---- The checker (tools/check_club_culture.py) on a scratch copy of the data: a pair in both the friendships
  // and the rivalries file exits 1 unless the friendship has ended; a quote over 15 words exits 1; no quote warns.
  const cp = require('child_process'), os = require('os');
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'culture-'));
  fs.mkdirSync(path.join(scratch, 'tools')); fs.mkdirSync(path.join(scratch, 'data', 'clubs'), {recursive: true});
  fs.copyFileSync(path.join(ROOT, 'tools/check_club_culture.py'), path.join(scratch, 'tools/check_club_culture.py'));
  for(const f of fs.readdirSync(path.join(ROOT, 'data/clubs'))) if(/^[A-Z]{2}\.json$/.test(f)) fs.copyFileSync(path.join(ROOT, 'data/clubs', f), path.join(scratch, 'data/clubs', f));
  for(const f of ['club-rivalries.csv', 'club-friendships.csv', 'club-culture-sources.csv', 'club-parents.csv']) fs.copyFileSync(path.join(ROOT, 'data', f), path.join(scratch, 'data', f));
  const runChecker = () => cp.spawnSync('python3', [path.join(scratch, 'tools/check_club_culture.py')], {encoding: 'utf8'});
  const friFile = path.join(scratch, 'data/club-friendships.csv'), baseFri = fs.readFileSync(friFile, 'utf8').replace(/\n?$/, '\n');
  const withRow = row => { fs.writeFileSync(friFile, baseFri + FH.split(',').map(k => q(row[k] || '')).join(',') + '\n'); return runChecker(); };
  const B0 = runChecker();
  check('checker: the real data passes (exit 0) and prints each quote', B0.status === 0 && /quote: «/.test(B0.stdout) && !/PROBLEM/.test(B0.stdout), (B0.stdout + B0.stderr).slice(-300));
  // club-parents.csv: unknown parentQ, repeated clubQ, own parent and a parent that is itself a reserve side exit 1; a missing checkedOn only warns.
  const parFile = path.join(scratch, 'data/club-parents.csv'), baseParents = fs.readFileSync(parFile, 'utf8').replace(/\n?$/, '\n');
  const withParent = lines => { fs.writeFileSync(parFile, baseParents + lines.join('\n') + '\n'); const r = runChecker(); fs.writeFileSync(parFile, baseParents); return r; };
  const p0 = parentsCsv[0], freeClub = noRows[0], freeClub2 = noRows[1];
  check(`checker: the real club-parents.csv passes and is read back (${parentsCsv.length} rows)`, B0.status === 0 && new RegExp(`club-parents\\.csv: ${parentsCsv.length} accepted rows`).test(B0.stdout), B0.stdout.slice(-200));
  const BP = withParent([`${freeClub},Q0,https://example.org/x,2026-10-19`]);
  check('checker: a parentQ on no club file exits 1 and names the cell', BP.status === 1 && /club-parents\.csv line \d+: parentQ "Q0" is on no club file/.test(BP.stdout), (BP.stdout + BP.stderr).slice(-250));
  const BC = withParent([`Q0,${p0.parentQ},https://example.org/x,2026-10-19`]);
  check('checker: a clubQ on no club file exits 1', BC.status === 1 && /clubQ "Q0" is on no club file/.test(BC.stdout), (BC.stdout + BC.stderr).slice(-250));
  const BD = withParent([`${p0.clubQ},${p0.parentQ},https://example.org/x,2026-10-19`]);
  check('checker: a repeated clubQ exits 1', BD.status === 1 && /is entered twice/.test(BD.stdout), (BD.stdout + BD.stderr).slice(-250));
  const BS = withParent([`${freeClub},${freeClub},https://example.org/x,2026-10-19`]);
  check('checker: a club that is its own parent exits 1', BS.status === 1 && /a club cannot be its own parent/.test(BS.stdout), (BS.stdout + BS.stderr).slice(-250));
  const BR = withParent([`${p0.parentQ},${freeClub2},https://example.org/x,2026-10-19`]);
  check('checker: a parent that is itself a reserve side exits 1', BR.status === 1 && /which is itself a reserve side/.test(BR.stdout), (BR.stdout + BR.stderr).slice(-250));
  const BW = withParent([`${freeClub},${freeClub2},https://example.org/x,`]);
  check('checker: a row with no checkedOn only warns (exit 0)', BW.status === 0 && /club-parents\.csv line \d+: no checkedOn/.test(BW.stdout), (BW.stdout + BW.stderr).slice(-250));
  const pairRiv = riv.find(r => r.rivalQ && !realFri.some(f => (f.clubQ === r.clubQ && f.friendQ === r.rivalQ) || (f.clubQ === r.rivalQ && f.friendQ === r.clubQ)));
  const base = {scope: 'fan-groups', groupsText: '', sourceId: realFri[0].sourceId, checkedOn: realFri[0].checkedOn, quote: 'a short quote'};
  const rowOf = st => ({...base, clubQ: pairRiv.clubQ, friendQ: pairRiv.rivalQ, friendName: pairRiv.rivalName, status: st});
  const PAIR = /a pair may be in both only when the friendship has ended/;
  for(const st of ['active', 'unclear']){
    const R = withRow(rowOf(st));
    check(`checker: a pair that is in both files (${pairRiv.clubQ} / ${pairRiv.rivalQ}) with status ${st} exits 1`, R.status === 1 && PAIR.test(R.stdout), (R.stdout + R.stderr).slice(-300));
  }
  const clubName = await page.evaluate(id => CLUBS.find(c => c.id === id).name, pairRiv.clubQ);
  const Rrev = withRow({...rowOf('active'), clubQ: pairRiv.rivalQ, friendQ: pairRiv.clubQ, friendName: clubName});
  check('checker: the same pair entered the other way round, active, exits 1', Rrev.status === 1 && PAIR.test(Rrev.stdout), (Rrev.stdout + Rrev.stderr).slice(-300));
  const nameOnly = riv.find(r => !r.rivalQ);
  const Rnm = nameOnly ? withRow({...base, clubQ: nameOnly.clubQ, friendQ: '', friendName: nameOnly.rivalName, status: 'active'}) : null;
  check('checker: a pair joined by name only (the rival is not on the map), active, exits 1', !!Rnm && Rnm.status === 1 && PAIR.test(Rnm.stdout), Rnm ? (Rnm.stdout + Rnm.stderr).slice(-300) : 'no rivalry row without a Q-id');
  const Rend = withRow(rowOf('ended'));
  check('checker: the same pair with status ended is allowed (exit 0)', Rend.status === 0 && !/PROBLEM/.test(Rend.stdout), (Rend.stdout + Rend.stderr).slice(-300));
  const other = {...base, clubQ: pairRiv.clubQ, friendQ: '', friendName: 'Scratch Friend FC', status: 'active'};
  const words = n => Array.from({length: n}, (_, i) => 'w' + i).join(' ');
  const R15 = withRow({...other, quote: words(15)}), R16 = withRow({...other, quote: words(16)}), R0 = withRow({...other, quote: ''});
  check('checker: a quote of 15 words passes, of 16 words exits 1', R15.status === 0 && R16.status === 1 && /16 words; 15 at most/.test(R16.stdout), (R16.stdout + R16.stderr).slice(-200));
  check('checker: a row with no quote only warns (exit 0)', R0.status === 0 && /has no quote/.test(R0.stdout), (R0.stdout + R0.stderr).slice(-200));
  const rivFile = path.join(scratch, 'data/club-rivalries.csv'), baseRiv = fs.readFileSync(rivFile, 'utf8').replace(/\n?$/, '\n');
  const withRiv = quote => { fs.writeFileSync(rivFile, baseRiv + `${pairRiv.clubQ},,Scratch Rival FC,other,${rivSrc[0].sourceId},2026-10-03,${quote}\n`); return runChecker(); };
  const RV15 = withRiv(words(15)), RV16 = withRiv(words(16)), RV0 = withRiv('');
  check('checker: a rivalry quote of 15 words passes, of 16 words exits 1', RV15.status === 0 && RV16.status === 1 && /club-rivalries\.csv line \d+: the quote is 16 words; 15 at most/.test(RV16.stdout), (RV16.stdout + RV16.stderr).slice(-200));
  const noQ = (RV0.stdout.match(/^WARNING: club-rivalries\.csv: \d+ rows have no quote/gm) || []);
  check('checker: rivalry rows with no quote give one warning with a count, no row listed, exit 0',
    RV0.status === 0 && noQ.length === 1 && !/Scratch Rival FC.*no quote/.test(RV0.stdout) && Number(noQ[0].match(/: (\d+) rows/)[1]) === riv.filter(r => !r.quote).length + 1, (RV0.stdout + RV0.stderr).slice(-200));
  fs.rmSync(scratch, {recursive: true, force: true});
  function csvText(t){ const f = '__tmp'; return t.split('\n').slice(1).filter(Boolean).map(l => { const c = l.split(','); return {clubQ: c[0], rivalQ: c[1], rivalName: c[2], class: c[3], sourceId: c[4]}; }); }

  tick('checker on scratch data');
  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  console.log(`TIME total: ${((Date.now() - T_START) / 1000).toFixed(1)} s`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
