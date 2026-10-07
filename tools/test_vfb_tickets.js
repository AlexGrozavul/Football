// Headless Chromium test of VfB Stuttgart's ticket information, at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page or the ticket files; by hand:
//
//   npm install playwright              (anywhere; it is not a dependency of this repo)
//   node tools/test_vfb_tickets.js .    (serves the checkout itself; it changes no file)
//
// Added 2026-10-07, with the first researched VfB rows. Checked against the files:
//  - the Ticket info tab lists VfB under Clubs; its entry opens with "Country rules: Germany" holding every DE row of
//    data/country-ticket-rules.csv (or "No national rules researched for Germany" if there are none), ABOVE
//    "Researched rules", which is above "Your notes" (football-rules.json's vfb entry, through football-rules-links.csv);
//  - every VfB rule, window (its label) and phase is in that entry, and its Prices and Sell-out record
//    sections hold exactly as many rows as the files - no row dropped;
//  - no inferred (or disputed) date is shown to the day, in the entry, on the club sheet or in the vfb-regular card;
//  - the club sheet shows the same order and the same rows, and neither it nor the entry shows a sale date (no Next window, no "Typically opens");
//  - the Bucket list's vfb-regular entry shows VfB with Germany's rules above its researched rules and its notes;
//  - no sideways scroll, no script error.
// Stadia's tiles are stubbed. CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8782, BASE = `http://localhost:${PORT}/Football/`;
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

const VFB = 'Q4512';
const deRows = nat.filter(r => r.country === 'DE');
const mineOf = f => csv(`data/${f}.csv`).filter(r => r.clubQid === VFB && (r.team || 'men') === 'men');
const vRules = mineOf('club-ticket-rules'), vWindows = mineOf('club-ticket-windows'), vPhases = mineOf('club-ticket-phases');
const vPrices = mineOf('club-ticket-prices'), vDemand = mineOf('club-ticket-demand');
const linked = rulesLinks.some(l => l.rulesId === 'vfb' && l.clubQid === VFB);

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

  check('the files hold VfB rows to test', vRules.length > 0 && vWindows.length > 0 && vPhases.length > 0 && vPrices.length > 0 && vDemand.length > 0,
    `${vRules.length} rules, ${vWindows.length} windows, ${vPhases.length} phases, ${vPrices.length} prices, ${vDemand.length} demand`);
  check('football-rules-links.csv links the vfb entry to the same Q-id', linked);

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
  // How many rows a section of the researched rules actually holds: its own .item children, counted in the page.
  const countIn = (sel, title) => page.evaluate(([s, t]) => {
    const d = [...document.querySelectorAll(`${s} details`)].find(x => x.querySelector(':scope > summary')?.textContent.startsWith(t));
    return d ? d.querySelectorAll(':scope > .item').length : -1;
  }, [sel, title]);
  const everyRowIn = async (text, label, sel) => {
    const t = norm(text);
    const r = vRules.filter(x => !t.includes(norm(x.rule))).map(x => `rule ${x.topic}/${x.season}`);
    const w = vWindows.filter(x => !t.includes(norm(x.label))).map(x => `window ${x.window}`);
    const p = vPhases.filter(x => !t.includes(norm(x.buyers))).map(x => `phase ${x.window}/${x.phase}`);
    const missing = [...r, ...w, ...p];
    check(`${label}: every one of VfB's ${vRules.length} rules, ${vWindows.length} windows and ${vPhases.length} phases is shown`,
      !missing.length, missing.join(', '));
    const np = await countIn(sel, 'Prices'), nd = await countIn(sel, 'Sell-out record');
    check(`${label}: Prices holds all ${vPrices.length} VfB price rows`, np === vPrices.length, `shown ${np}`);
    check(`${label}: Sell-out record holds all ${vDemand.length} VfB rows`, nd === vDemand.length, `shown ${nd}`);
  };

  // ---------------------------------------------------------------- Ticket info, Clubs
  await openAll('tickets');
  const V = await page.evaluate(q => {
    const d = document.querySelector(`details.tclub[data-qid="${q}"]`);
    if(!d) return null;
    const heads = [...d.querySelectorAll('h5.srch')];
    const idx = c => heads.findIndex(h => h.classList.contains(c));
    const clubsH2 = [...document.querySelectorAll('#ticketBody h2')].find(h => /^Clubs/.test(h.textContent));
    return {text: d.innerText, country: d.querySelector('.tix-country')?.textContent || '',
      order: [idx('tix-country'), idx('tix-researched'), idx('tix-notes')],
      underClubs: !!clubsH2 && !!(clubsH2.compareDocumentPosition(d) & Node.DOCUMENT_POSITION_FOLLOWING)};
  }, VFB);
  check('Ticket info: VfB has a row under Clubs', !!V && V.underClubs);
  check(`VfB: "Country rules: Germany" ${deRows.length ? `holds all ${deRows.length} German national rules` : 'says none are researched'}`,
    !!V && /^Country rules: Germany/.test(V.country) && germanyOk(V.text), V ? germanyMissing(V.text) || V.country : 'no VfB row');
  check('VfB: country rules above researched rules, researched rules above your notes (both sources under one club)',
    !!V && V.order[0] === 0 && V.order[1] > V.order[0] && V.order[2] > V.order[1], V ? V.order.join(',') : '');
  check('VfB (Ticket info): no sale date - no "Typically opens"', !!V && !/Typically opens|Next window/.test(V.text));
  check("VfB: Your notes holds football-rules.json's vfb entry", !!V && norm(V.text).includes(norm(rules.clubs.find(c => c.id === 'vfb').procedure.home)));
  if(V) await everyRowIn(V.text, 'VfB (Ticket info)', `details.tclub[data-qid="${VFB}"]`);
  let days = await dayLevelIn(`details.tclub[data-qid="${VFB}"]`);
  check('VfB (Ticket info): no inferred or disputed date shown to the day', !days.length, JSON.stringify(days).slice(0, 300));
  check('Ticket info: no sideways scroll with every card open', await noSideways());

  // ---------------------------------------------------------------- the club sheet
  await page.evaluate(q => openSheet(CLUBS.find(c => c.id === q)), VFB);
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
  check('VfB sheet: "Country rules: Germany" first, then researched rules, then your notes',
    /^Country rules: Germany/.test(S.country) && germanyOk(S.text) && S.order[0] === 0 && S.order[1] > 0 && S.order[2] > S.order[1],
    `${S.order.join(',')} ${germanyMissing(S.text)}`);
  await everyRowIn(S.text, 'VfB sheet', '#sheetTix');
  // Sale dates are shown only on the Bucket list: the sheet has no Next window line and no window date line.
  check('VfB sheet: no sale date - no Next window line, no "Typically opens"', !S.hasNext && !/Next window|Typically opens/.test(S.text), S.text.slice(0, 120));
  days = await dayLevelIn('#sheetTix');
  check('VfB sheet: no inferred or disputed date shown to the day', !days.length, JSON.stringify(days).slice(0, 300));
  check('VfB sheet: no sideways scroll', await noSideways());
  await page.evaluate(() => typeof closeSheet === 'function' && closeSheet());

  // ---------------------------------------------------------------- the vfb-regular bucket entry
  await openAll('bucket');
  const B = await page.evaluate(() => {
    const d = document.querySelector('details.bucket[data-id="vfb-regular"]');
    return d ? {clubs: [...d.querySelectorAll('.bclub')].map(c => ({qid: c.dataset.qid, text: c.innerText})), text: d.innerText} : null;
  });
  const vb = B?.clubs.find(c => c.qid === VFB)?.text || '';
  check('vfb-regular: the card shows a VfB block', !!vb, B ? B.clubs.map(c => c.qid).join() : 'no card');
  check("vfb-regular: Germany's national rules above VfB's researched rules, both shown",
    germanyOk(vb) && vb.indexOf(deRows.length ? 'Country rules: Germany' : 'No national rules researched for Germany') >= 0 &&
    vb.indexOf(deRows.length ? 'Country rules: Germany' : 'No national rules researched for Germany') < vb.indexOf('Researched rules') &&
    vRules.every(r => norm(vb).includes(norm(r.rule))));
  days = await dayLevelIn('details.bucket[data-id="vfb-regular"]');
  check('vfb-regular: no inferred or disputed date shown to the day', !days.length, JSON.stringify(days).slice(0, 300));
  check('Bucket list: no sideways scroll with every card open', await noSideways());
  await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', 'vfb-tickets.png')});

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
