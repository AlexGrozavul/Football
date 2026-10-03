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
// unavailable"; no sideways scroll; no script error. Prints each club's Next window line.
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
      return {text: t.innerText, notes: !!document.getElementById('tixNotes'), researched: !!document.getElementById('tixResearched'),
        notesLabel: document.getElementById('tixNotes')?.textContent, resLabel: document.getElementById('tixResearched')?.textContent,
        next: nw ? [...nw.querySelectorAll('.nw')].map(e => ({name: e.querySelector('b').textContent, text: e.textContent,
          tags: [...e.querySelectorAll('.tag')].map(x => x.textContent)})) : null,
        nextText: nw ? nw.innerText.replace(/\s+/g, ' ') : null, unavailable: /Ticket info unavailable/.test(t.textContent)};
    });
  };

  for(const [label, qid] of CLUBS){
    const ids = links.filter(l => l.clubQid === qid).map(l => l.rulesId);
    const entries = rules.clubs.filter(c => ids.includes(c.id));
    const row = tickets.find(t => t.clubQid === qid && t.team === 'men');
    const S = await open(qid);
    console.log(`    ${label}: ${S.nextText}`);
    if(!entries.length && !row){ check(`${label}: no ticket information, so "Ticket info unavailable"`, S.unavailable); continue; }
    check(`${label}: "Your notes" ${entries.length ? 'shown' : 'absent, and says so'}`, S.notes && /^Your notes/.test(S.notesLabel) &&
      (entries.length ? !/None of your notes are about this club/.test(S.text) : /None of your notes are about this club/.test(S.text)));
    check(`${label}: "Researched rules" ${row ? 'shown' : 'absent, and says so'}`, S.researched && /^Researched rules/.test(S.resLabel) &&
      (row ? /Who may buy/.test(S.text) : /Not researched yet/.test(S.text)));
    if(entries.length){
      const flat = norm(S.text);
      const missing = entries.flatMap(leaves).filter(v => !flat.includes(norm(v)));
      check(`${label}: every text field of the football-rules.json entry is on the sheet, as written`, !missing.length, missing.join(' | '));
    }
    // Next window
    check(`${label}: a Next window line`, S.next !== null);
    const own = new Set([...rules.ticketEvents.filter(e => ids.includes(e.club)).map(e => e.title || e.id),
      ...windows.filter(w => w.clubQid === qid).map(w => w.label || w.window)]);
    const disputed = rules.ticketEvents.filter(e => ids.includes(e.club) && e.dateSource === 'disputed').map(e => e.title || e.id);
    for(const n of S.next || []){
      check(`${label}: next window "${n.name}" is this club's own event or window`, own.has(n.name));
      check(`${label}: "${n.name}" carries a dateSource label`, n.tags.some(t => /^(confirmed|estimated|no date source)$/.test(t)), n.tags.join(','));
      check(`${label}: "${n.name}" is never a disputed entry`, !disputed.includes(n.name));
      if(n.tags.includes('estimated')){
        check(`${label}: "${n.name}" is estimated, so worded as an estimate and never to the day`,
          /estimated/.test(n.text.replace(n.tags.join(''), '')) && !DAY.test(n.text), n.text);
      }
    }
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
    check(`a club with neither source (${plain}) keeps "Ticket info unavailable"`, S.unavailable && S.next === null);
  }

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
