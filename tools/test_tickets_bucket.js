// Headless Chromium test of the Ticket info and Bucket list tabs, at phone width (390x844).
// Run by .github/workflows/test-pages.yml on any change to the page; by hand:
//
//   npm install playwright                 (anywhere; it is not a dependency of this repo)
//   node tools/test_tickets_bucket.js .    (serves the checkout itself; it changes no file)
//
// Added 2026-10-04, when the Ticket info tab became rules only and dated reminders moved to the
// Bucket list tab. Checked against the files read here, with every card opened:
//  - neither tab scrolls sideways or has anything past the screen's edges;
//  - Ticket info lists every country with a row in data/country-ticket-rules.csv and every club
//    with ticket information (the club-ticket files, or a line in football-rules-links.csv);
//    Italy opens to each of its rules, with "Applies to" never blank and never "all" where the
//    row says unknown; Inter shows "Country rules: Italy" above its researched rules and its
//    notes, with Italy's rules in it; Nürnberg shows Germany's national rules (or says none are researched, if the
//    file has none);
//    Inter's notes carry the "unverified" marking football-rules.json gives them;
//  - Ticket info has no upcoming-dates section: no ticket window, no Next window, no heading but
//    Countries and Clubs; since 2026-10-07 neither it nor any club sheet shows a sale date at all, and the
//    Bucket list still does;
//  - the Bucket list shows every bucketList entry; every ticketEvents entry is reachable from it,
//    inside the entry data/bucket-links-manual.csv links it to or under Reminders, which holds
//    exactly the unlinked ones, soonest first and undated last;
//  - the Frankenderby entry shows Nürnberg (host) then Fürth, Fürth "not researched"; the Milan
//    derby entry shows AC Milan and Inter; every entry says event rules are not researched yet;
//  - no inferred (or disputed) date is shown at day level anywhere on either tab;
//  - no script error.
// Stadia's tiles are stubbed. CHROMIUM_PATH points it at a Chromium other than Playwright's own.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2] || '.');
const PORT = 8778, BASE = `http://localhost:${PORT}/Football/`;
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

  const openAll = async pane => {
    await page.click(`nav button[data-pane=${pane}]`);
    await page.waitForFunction(p => document.querySelector(`#pane-${p} details.card`), pane, {timeout: 15000});
    await page.$$eval(`#pane-${pane} details.card`, ds => ds.forEach(d => d.open = true));
    await page.waitForFunction(p => ![...document.querySelectorAll(`#pane-${p} details.card > .tix`)]
      .some(t => /Loading…/.test(t.textContent)), pane, {timeout: 60000});
    await page.$$eval(`#pane-${pane} details`, ds => ds.forEach(d => d.open = true));
    await page.waitForTimeout(250);
  };
  const sideways = pane => page.evaluate(p => {
    const el = document.getElementById('pane-' + p);
    const over = [...el.querySelectorAll('*')].filter(x => { const r = x.getBoundingClientRect(); return r.width > 0 && (r.right > innerWidth + 1 || r.left < -1); });
    return {sw: el.scrollWidth, cw: el.clientWidth, doc: document.documentElement.scrollWidth,
      over: over.slice(0, 5).map(x => `${x.tagName}.${x.className} "${x.textContent.trim().slice(0, 40)}"`)};
  }, pane);
  const dayLevel = pane => page.evaluate(([p, re]) => {
    const DAY = new RegExp(re);
    return [...document.querySelectorAll(`#pane-${p} [data-ds="inferred"], #pane-${p} [data-ds="disputed"]`)]
      .map(e => ({ds: e.dataset.ds, text: e.innerText.replace(/\s+/g, ' ')})).filter(x => DAY.test(x.text));
  }, [pane, DAY.source]);

  // ---------------------------------------------------------------- Ticket info
  await openAll('tickets');
  let s = await sideways('tickets');
  check(`Ticket info: no sideways scroll (${s.sw} wide in ${s.cw}), every card opened`, s.sw <= s.cw + 1 && s.doc <= W + 1);
  check('Ticket info: nothing reaches past the screen edges', !s.over.length, s.over.join(' | '));

  const T = await page.evaluate(() => {
    const body = document.getElementById('ticketBody');
    return {h2: [...body.querySelectorAll('h2')].map(h => h.textContent),
      countries: [...body.querySelectorAll('details.tcountry')].map(d => d.dataset.country),
      clubs: [...body.querySelectorAll('details.tclub')].map(d => d.dataset.qid),
      ev: body.querySelectorAll('.ev').length, next: body.querySelectorAll('.nextw, #nextWindow').length,
      reminders: /Ticket windows \(reminders\)|Reminders/.test(body.innerText)};
  });
  const wantCountries = [...new Set(nat.map(r => r.country))].sort();
  check(`Ticket info: one row per country with national rules (${wantCountries.join(', ')})`,
    JSON.stringify(T.countries) === JSON.stringify(wantCountries), T.countries.join(','));
  check(`Ticket info: one row per club with ticket information (${ticketQids.size})`,
    T.clubs.length === ticketQids.size && T.clubs.every(q => ticketQids.has(q)), T.clubs.join(','));
  check('Ticket info: no upcoming-dates section - only the Countries and Clubs headings, no ticket window, no Next window',
    T.h2.length === 2 && /^Countries/.test(T.h2[0]) && /^Clubs/.test(T.h2[1]) && !T.ev && !T.next && !T.reminders,
    `${T.h2.join(' / ')}; ${T.ev} windows; ${T.next} next-window lines`);

  // Sale dates are shown only on the Bucket list (CLAUDE.md, "Sale dates"): no Ticket info card and no club sheet
  // carries a "Next window" line or a window's "Typically opens" / past-cycle line - for every club that has a
  // sales-window row, which is where those lines used to come from.
  const windowQids = [...new Set(csv('data/club-ticket-windows.csv').filter(r => (r.team || 'men') === 'men').map(r => r.clubQid))];
  const noSaleDate = t => !/Next window|Typically opens|Past cycle, what happened/.test(t);
  const tickText = await page.evaluate(() => document.getElementById('ticketBody').innerText);
  const sheetsWith = [];
  for(const q of windowQids){
    if(!await page.evaluate(q2 => !!CLUBS.find(c => c.id === q2), q)) continue;
    await page.evaluate(q2 => openSheet(CLUBS.find(c => c.id === q2)), q);
    await page.waitForFunction(() => !/Loading/.test(document.getElementById('sheetTix').textContent), null, {timeout: 15000});
    await page.$$eval('#sheetTix details', ds => ds.forEach(d => d.open = true));
    sheetsWith.push(await page.evaluate(() => ({text: document.getElementById('sheetTix').innerText,
      next: !!document.getElementById('nextWindow')})));
    await page.evaluate(() => typeof closeSheet === 'function' && closeSheet());
  }
  check(`Ticket info and ${sheetsWith.length} club sheets (every club with a sales window) show no sale date: no Next window, no "Typically opens"`,
    sheetsWith.length > 0 && noSaleDate(tickText) && !T.next && sheetsWith.every(x => noSaleDate(x.text) && !x.next),
    `${sheetsWith.length} sheets`);

  // Italy, opened
  const IT = await page.evaluate(() => {
    const d = document.querySelector('details.tcountry[data-country="IT"]');
    return d ? {text: d.innerText, items: [...d.querySelectorAll('.crule')].map(i => ({text: i.innerText,
      applies: [...i.querySelectorAll('.row')].find(r => /^Applies to/.test(r.innerText))?.innerText.replace(/^Applies to\s*/, '') || ''}))} : null;
  });
  const itRows = nat.filter(r => r.country === 'IT');
  check('Italy opens and shows each of its national rules', !!IT && itRows.every(r => norm(IT.text).includes(norm(r.rule))),
    IT ? `${IT.items.length} shown, ${itRows.length} in the file` : 'no Italy row');
  for(const [i, r] of itRows.entries()){
    const a = IT?.items[i]?.applies || '';
    check(`Italy rule ${r.topic}: "Applies to" is said plainly, never blank or "all"`, !!a.trim() && !/^all\b/i.test(a.trim()) &&
      (r.appliesTo !== 'unknown' || /do not say which matches/.test(a)), a);
    check(`Italy rule ${r.topic}: its condition, authority, status and source are shown`,
      /Only when/.test(IT.items[i].text) && IT.items[i].text.includes(r.authority) && /confirmed|inferred|unverified/.test(IT.items[i].text) && /Source:/.test(IT.items[i].text));
  }
  const club = qid => page.evaluate(q => {
    const d = document.querySelector(`details.tclub[data-qid="${q}"]`);
    if(!d) return null;
    const heads = [...d.querySelectorAll('h5.srch')];
    const idx = c => heads.findIndex(h => h.classList.contains(c));
    return {text: d.innerText, country: d.querySelector('.tix-country')?.textContent || '',
      order: [idx('tix-country'), idx('tix-researched'), idx('tix-notes')],
      unv: [...d.querySelectorAll('.tix-notes ~ .meta.unv .tag.bad')].map(t => t.textContent)};
  }, qid);
  const inter = await club('Q631');
  check('Inter: "Country rules: Italy" comes above its researched rules and its notes',
    !!inter && /^Country rules: Italy/.test(inter.country) && inter.order[0] === 0 && inter.order[1] > 0 && inter.order[2] > inter.order[1],
    inter ? inter.order.join(',') : 'no Inter row');
  check("Inter: Italy's rules are inside Inter's entry", !!inter && itRows.every(r => norm(inter.text).includes(norm(r.rule))));
  check('Inter: its notes are visibly marked unverified, as football-rules.json marks them',
    !!inter && inter.unv.some(t => /unverified: Age rules/.test(t)), inter ? inter.unv.join(' | ') : '');
  const fcn = await club('Q15786');
  // Since 2026-10-04 Germany had no national rows and Nürnberg said so; since 2026-10-06 it has three (DFB, DFL), so the
  // check follows the file: every German rule inside Nürnberg's entry, under "Country rules: Germany", or the old line.
  const deRows = nat.filter(r => r.country === 'DE');
  check(deRows.length ? `Nürnberg: "Country rules: Germany" with all ${deRows.length} of Germany's national rules` : 'Nürnberg: says no national rules are researched for Germany',
    !!fcn && (deRows.length ? /^Country rules: Germany/.test(fcn.country) && deRows.every(r => norm(fcn.text).includes(norm(r.rule)))
      : /No national rules researched for Germany \(DE\) yet\./.test(fcn.text)), fcn ? fcn.country : 'no Nürnberg row');
  check('Nürnberg: country rules first', !!fcn && fcn.order[0] === 0 && fcn.order[1] > 0);
  check('Ticket info: no inferred or disputed date shown to the day', !(await dayLevel('tickets')).length,
    JSON.stringify(await dayLevel('tickets')).slice(0, 300));
  await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', 'ticket-info.png')});

  // ---------------------------------------------------------------- Bucket list
  await openAll('bucket');
  s = await sideways('bucket');
  check(`Bucket list: no sideways scroll (${s.sw} wide in ${s.cw}), every card opened`, s.sw <= s.cw + 1 && s.doc <= W + 1);
  check('Bucket list: nothing reaches past the screen edges', !s.over.length, s.over.join(' | '));

  const B = await page.evaluate(() => {
    const body = document.getElementById('bucketBody');
    const reminders = [];
    for(const el of body.children){ if(el.tagName === 'H2' && !/^Reminders/.test(el.textContent)) break;
      if(el.classList.contains('evcard')) reminders.push(el.querySelector('.ev').dataset.ev); }
    return {cards: [...body.querySelectorAll('details.bucket')].map(d => d.dataset.id),
      inside: [...body.querySelectorAll('details.bucket')].map(d => ({id: d.dataset.id,
        ev: [...d.querySelectorAll('.ev')].map(e => e.dataset.ev),
        clubs: [...d.querySelectorAll('.bclub')].map(c => ({qid: c.dataset.qid, head: c.querySelector('.bclubh').innerText, text: c.innerText})),
        eventRules: /Event-specific ticket rules not researched yet\./.test(d.innerText)})),
      reminders};
  });
  check(`Bucket list: every one of ${rules.bucketList.length} entries has a card`,
    rules.bucketList.every(b => B.cards.includes(b.id)) && B.cards.length === rules.bucketList.length);
  const evLinks = new Map(bucketLinks.filter(r => r.ticketEventId).map(r => [r.ticketEventId, r.bucketId]));
  const reachable = new Set([...B.reminders, ...B.inside.flatMap(c => c.ev)]);
  check(`Bucket list: every one of ${rules.ticketEvents.length} ticket events is reachable`,
    rules.ticketEvents.every(e => reachable.has(e.id)), rules.ticketEvents.filter(e => !reachable.has(e.id)).map(e => e.id).join(','));
  for(const e of rules.ticketEvents){
    const where = evLinks.get(e.id);
    check(`ticket event ${e.id}: ${where ? 'inside ' + where : 'under Reminders'}`,
      where ? (B.inside.find(c => c.id === where)?.ev || []).includes(e.id) && !B.reminders.includes(e.id) : B.reminders.includes(e.id));
  }
  const keyOf = id => { const e = rules.ticketEvents.find(x => x.id === id); const raw = e.recurring === 'annual' ? e.nextEstimate : (e.date || e.dateEstimate);
    return raw && /^\d{4}-\d{2}/.test(raw) ? raw.slice(0, 7) : '9999'; };
  check('Reminders: soonest first, undated last', B.reminders.every((id, i) => i === 0 || keyOf(B.reminders[i - 1]) <= keyOf(id)),
    B.reminders.map(id => `${id} ${keyOf(id)}`).join(', '));
  const frank = B.inside.find(c => c.id === 'frankenderby');
  check('Frankenderby: shows Nürnberg, host, first, then Fürth', !!frank && frank.clubs.map(c => c.qid).join() === 'Q15786,Q153539' &&
    /host/.test(frank.clubs[0].head), frank ? frank.clubs.map(c => c.head).join(' | ') : 'no card');
  check('Frankenderby: Fürth "not researched"', !!frank && /No ticket rules researched for SpVgg Greuther Fürth yet\./.test(frank.clubs[1]?.text || ''));
  check('Bucket list still shows its ticket window reminders: every ticket event is on a card or under Reminders, and a club block keeps "Typically opens"',
    rules.ticketEvents.length > 0 && B.reminders.length + B.inside.reduce((n, c) => n + c.ev.length, 0) === rules.ticketEvents.length &&
    !!frank && /Typically opens/.test(frank.clubs[0].text),
    `${B.reminders.length} under Reminders, ${B.inside.reduce((n, c) => n + c.ev.length, 0)} inside entries`);
  check("Frankenderby: Nürnberg's researched rules are shown, Germany's national line on top",
    !!frank && /Researched rules/.test(frank.clubs[0].text) &&
    (() => { const i = frank.clubs[0].text.indexOf(deRows.length ? 'Country rules: Germany' : 'No national rules researched for Germany');
      return i >= 0 && i < frank.clubs[0].text.indexOf('Researched rules'); })());
  const mad = B.inside.find(c => c.id === 'derby-madonnina');
  check('Milan derby: shows AC Milan and Inter', !!mad && ['Q1543', 'Q631'].every(q => mad.clubs.some(c => c.qid === q)),
    mad ? mad.clubs.map(c => c.head).join(' | ') : 'no card');
  check("Milan derby: Italy's national rules above each club's", !!mad && mad.clubs.every(c => /^.*\n?Country rules: Italy/.test(c.text) &&
    itRows.every(r => norm(c.text).includes(norm(r.rule)))));
  check('Every entry says event-specific ticket rules are not researched yet (the file is header only)',
    B.inside.every(c => c.eventRules), B.inside.filter(c => !c.eventRules).map(c => c.id).join(','));
  const days = await dayLevel('bucket');
  check('Bucket list: no inferred or disputed date shown to the day', !days.length, JSON.stringify(days).slice(0, 400));
  // Each inferred ticket event with a date shows its month instead.
  const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const evText = await page.evaluate(() => Object.fromEntries([...document.querySelectorAll('#bucketBody .ev')]
    .map(e => [e.dataset.ev, e.querySelector('[data-ds]').innerText.replace(/\s+/g, ' ')])));
  for(const e of rules.ticketEvents.filter(e => e.dateSource !== 'confirmed')){
    const raw = e.recurring === 'annual' ? e.nextEstimate : (e.date || e.dateEstimate);
    if(!raw) continue;
    const month = `${MONTHS[Number(raw.slice(5, 7)) - 1]} ${raw.slice(0, 4)}`;
    check(`${e.id} (${e.dateSource}): shown as ${month}, not to the day`, (evText[e.id] || '').includes(month) && !DAY.test(evText[e.id] || ''), evText[e.id]);
  }
  await page.screenshot({path: path.join(process.env.SHOT_DIR || '/tmp', 'bucket-list.png')});

  check('no script error', !errors.length, errors.join(' | '));
  await browser.close(); server.close();
  const failed = results.filter(x => !x).length;
  console.log(`\n${results.length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
