// Headless Chromium test of Karlsruher SC's ticket information, at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page or the ticket files; by hand:
//
//   npm install playwright              (anywhere; it is not a dependency of this repo)
//   node tools/test_ksc_tickets.js .    (serves the checkout itself; it changes no file)
//
// Added 2026-10-06, with the first researched KSC rows and the first German national rows. Checked against the files:
//  - the Ticket info tab lists KSC under Clubs; its entry opens with "Country rules: Germany" holding every DE row of
//    data/country-ticket-rules.csv (or "No national rules researched for Germany" if there are none), ABOVE
//    "Researched rules", which is above "Your notes";
//  - every KSC rule of data/club-ticket-rules.csv and every KSC window of data/club-ticket-windows.csv is in that entry;
//  - no inferred (or disputed) date is shown to the day, in the entry, on the club sheet or in the Südwestderby card;
//  - the club sheet shows the same order, and neither shows a sale date (no Next window, no "Typically opens");
//  - the Bucket list's Südwestderby entry shows KSC (host) with its researched rules, Germany's rules above them, and
//    1. FC Kaiserslautern as not researched ("Researched rules - Not researched yet", since its notes exist);
//  - no sideways scroll, no script error.
// Stadia's tiles are stubbed. CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8781, BASE = `http://localhost:${PORT}/Football/`;
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
const nat = csv('data/country-ticket-rules.csv');
const rulesLinks = csv('data/football-rules-links.csv').filter(l => rules.clubs.some(c => c.id === l.rulesId));
const bucketLinks = csv('data/bucket-links-manual.csv');
const ticketQids = new Set(['club-tickets', 'club-ticket-windows', 'club-ticket-phases', 'club-ticket-rules',
  'club-ticket-demand', 'club-ticket-prices'].flatMap(f => csv(`data/${f}.csv`).filter(r => (r.team || 'men') === 'men').map(r => r.clubQid)));
rulesLinks.forEach(l => ticketQids.add(l.clubQid));
const norm = s => String(s).replace(/\s+/g, ' ').trim();
// A date to the day, in any form the page could print one.
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

const KSC = 'Q105853', FCK = 'Q8466';
const deRows = nat.filter(r => r.country === 'DE');
const kscRules = csv('data/club-ticket-rules.csv').filter(r => r.clubQid === KSC);
const kscWindows = csv('data/club-ticket-windows.csv').filter(r => r.clubQid === KSC);

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

  check('the files hold KSC rows to test', kscRules.length > 0 && kscWindows.length > 0, `${kscRules.length} rules, ${kscWindows.length} windows`);

  const openAll = async pane => {
    await page.click(`nav button[data-pane=${pane}]`);
    await page.waitForFunction(p => document.querySelector(`#pane-${p} details.card`), pane, {timeout: 15000});
    await page.$$eval(`#pane-${pane} details.card`, ds => ds.forEach(d => d.open = true));
    await page.waitForFunction(p => ![...document.querySelectorAll(`#pane-${p} details.card > .tix`)]
      .some(t => /Loading…/.test(t.textContent)), pane, {timeout: 60000});
    await page.$$eval(`#pane-${pane} details`, ds => ds.forEach(d => d.open = true));
    await page.waitForTimeout(250);
  };
  const dayLevelIn = sel => page.evaluate(([s, re]) => {
    const DAY = new RegExp(re);
    return [...document.querySelectorAll(`${s} [data-ds="inferred"], ${s} [data-ds="disputed"]`)]
      .map(e => ({ds: e.dataset.ds, text: e.innerText.replace(/\s+/g, ' ')})).filter(x => DAY.test(x.text));
  }, [sel, DAY.source]);
  const noSideways = () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);
  const germanyOk = text => deRows.length ? deRows.every(r => norm(text).includes(norm(r.rule)))
    : /No national rules researched for Germany \(DE\) yet\./.test(text);
  const germanyMissing = text => deRows.filter(r => !norm(text).includes(norm(r.rule))).map(r => r.topic).join(', ');

  // ---------------------------------------------------------------- Ticket info, Clubs
  await openAll('tickets');
  const K = await page.evaluate(q => {
    const d = document.querySelector(`details.tclub[data-qid="${q}"]`);
    if(!d) return null;
    const heads = [...d.querySelectorAll('h5.srch')];
    const idx = c => heads.findIndex(h => h.classList.contains(c));
    const clubsH2 = [...document.querySelectorAll('#ticketBody h2')].find(h => /^Clubs/.test(h.textContent));
    return {text: d.innerText, country: d.querySelector('.tix-country')?.textContent || '',
      order: [idx('tix-country'), idx('tix-researched'), idx('tix-notes')],
      underClubs: !!clubsH2 && !!(clubsH2.compareDocumentPosition(d) & Node.DOCUMENT_POSITION_FOLLOWING)};
  }, KSC);
  check('Ticket info: KSC has a row under Clubs', !!K && K.underClubs);
  check(`KSC: "Country rules: Germany" ${deRows.length ? `holds all ${deRows.length} German national rules` : 'says none are researched'}`,
    !!K && /^Country rules: Germany/.test(K.country) && germanyOk(K.text), K ? germanyMissing(K.text) || K.country : 'no KSC row');
  check('KSC: country rules above researched rules, researched rules above your notes',
    !!K && K.order[0] === 0 && K.order[1] > K.order[0] && K.order[2] > K.order[1], K ? K.order.join(',') : '');
  const missingRules = K ? kscRules.filter(r => !norm(K.text).includes(norm(r.rule))) : kscRules;
  check(`KSC: every one of its ${kscRules.length} researched rules is in the entry`, !missingRules.length,
    missingRules.map(r => `${r.scope}/${r.topic}`).join(', '));
  const missingWin = K ? kscWindows.filter(w => !norm(K.text).includes(norm(w.label))) : kscWindows;
  check(`KSC: every one of its ${kscWindows.length} sales windows is in the entry, by its label (no sale date)`, !missingWin.length,
    missingWin.map(w => w.window).join(', '));
  let days = await dayLevelIn(`details.tclub[data-qid="${KSC}"]`);
  check('KSC (Ticket info): no inferred or disputed date shown to the day', !days.length, JSON.stringify(days).slice(0, 300));
  check('Ticket info: no sideways scroll with every card open', await noSideways());

  // ---------------------------------------------------------------- the club sheet
  await page.evaluate(q => openSheet(CLUBS.find(c => c.id === q)), KSC);
  await page.waitForFunction(() => !/Loading/.test(document.getElementById('sheetTix').textContent), null, {timeout: 15000});
  await page.waitForTimeout(300);
  await page.$$eval('#sheetTix details', ds => ds.forEach(d => d.open = true));
  const S = await page.evaluate(() => {
    const t = document.getElementById('sheetTix'), nw = document.getElementById('nextWindow');
    const heads = [...t.querySelectorAll('h5.srch')].map(h => h.className);
    return {text: t.innerText, country: t.querySelector('.tix-country')?.textContent || '',
      order: ['tix-country', 'tix-researched', 'tix-notes'].map(c => heads.findIndex(h => h.includes(c))),
      hasNext: !!nw};
  });
  check('KSC sheet: "Country rules: Germany" first, then researched rules, then your notes',
    /^Country rules: Germany/.test(S.country) && germanyOk(S.text) && S.order[0] === 0 && S.order[1] > 0 && S.order[2] > S.order[1],
    `${S.order.join(',')} ${germanyMissing(S.text)}`);
  check('KSC sheet: its researched derby rules are shown', kscRules.filter(r => r.scope === 'derby-home').every(r => norm(S.text).includes(norm(r.rule))));
  // Sale dates are shown only on the Bucket list: the sheet has no Next window line and no window date line.
  check('KSC sheet: no sale date - no Next window line, no "Typically opens"', !S.hasNext && !/Next window|Typically opens/.test(S.text), S.text.slice(0, 120));
  days = await dayLevelIn('#sheetTix');
  check('KSC sheet: no inferred or disputed date shown to the day', !days.length, JSON.stringify(days).slice(0, 300));
  check('KSC sheet: no sideways scroll', await noSideways());
  await page.evaluate(() => typeof closeSheet === 'function' && closeSheet());

  // ---------------------------------------------------------------- the Südwestderby bucket entry
  await openAll('bucket');
  const B = await page.evaluate(() => {
    const d = document.querySelector('details.bucket[data-id="sudwest-derby"]');
    return d ? {clubs: [...d.querySelectorAll('.bclub')].map(c => ({qid: c.dataset.qid, head: c.querySelector('.bclubh').innerText, text: c.innerText})),
      text: d.innerText} : null;
  });
  check('Südwestderby: KSC (host) first, then Kaiserslautern', !!B && B.clubs.map(c => c.qid).join() === `${KSC},${FCK}` && /host/.test(B.clubs[0].head),
    B ? B.clubs.map(c => c.head).join(' | ') : 'no card');
  const k = B?.clubs[0]?.text || '', f = B?.clubs[1]?.text || '';
  check("Südwestderby: KSC's researched rules are shown", /Researched rules/.test(k) && kscRules.filter(r => r.scope === 'derby-home').every(r => norm(k).includes(norm(r.rule))));
  check("Südwestderby: Germany's national rules above KSC's researched rules",
    k.indexOf(deRows.length ? 'Country rules: Germany' : 'No national rules researched for Germany') >= 0 &&
    k.indexOf(deRows.length ? 'Country rules: Germany' : 'No national rules researched for Germany') < k.indexOf('Researched rules') && germanyOk(k));
  // Kaiserslautern has hand-written notes (football-rules.json's fck), so its block says "Researched rules - Not researched
  // yet" rather than "No ticket rules researched for ... yet", which is the line for a club with neither source.
  check('Südwestderby: Kaiserslautern "not researched"', /Researched rules[\s\S]*Not researched yet\./.test(f) ||
    /No ticket rules researched for 1\. FC Kaiserslautern yet\./.test(f), f.slice(0, 200));
  days = await dayLevelIn('details.bucket[data-id="sudwest-derby"]');
  check('Südwestderby: no inferred or disputed date shown to the day', !days.length, JSON.stringify(days).slice(0, 300));
  check('Bucket list: no sideways scroll with every card open', await noSideways());
  await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', 'ksc-tickets.png')});

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
