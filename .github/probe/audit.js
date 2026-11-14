// TEMPORARY (ticket data audit, phase 2a). Reads robots.txt and the legal notice of each host, then the
// source pages named in targets.json, and posts text extracts as PR comments. Removed before the merge.
const { execFileSync } = require('child_process');
const fs = require('fs');
const { chromium } = require('/tmp/pw/node_modules/playwright');
const T = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const UA = 'FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)';
const FORBIDDEN = /acheter|panier|connexion|se-connecter|mon-compte|inscription|commande|acquista|carrello|accedi|registrati|ticketone|vivaticket|eventim|kaufen|buy|bestellen|warenkorb|cart|checkout|login|signin|sign-in|anmelden|register|queue|warteraum|saalplan|seatmap|\/sso|auth\b|account|konto/i;
const ALLOW = new Set(T.pages.map(p => p.url));
const isForbidden = u => FORBIDDEN.test(u) && !ALLOW.has(u);
const BOTS = /\b(bots?|robots?|crawl\w*|spider\w*|scrap\w*|automatisiert\w*|automated|automatically|automatis\w+|data[- ]?mining|maschinell\w*|harvest\w*|künstliche\w* intelligenz|artificial intelligence|automatizzat\w*|automatique\w*|robotis\w*|44b)\b/i;
const CHALLENGE = /just a moment|attention required|access denied|verify you are human|checking your browser|are you a robot|are you human|bot protection|sicherheitsüberprüfung|pardon our interruption|request blocked/i;
const NOTICE = /impressum|imprint|legal[- ]?notice|mentions[- ]l[ée]gales|note[- ]legali|nutzungsbedingungen|terms[- ]of[- ]use|terms[- ]and[- ]conditions|conditions[- ]g[ée]n[ée]rales d.utilisation|\bcgu\b|termini/i;
const SEASON = /20(2[3-7])\s?[\/\-–|]\s?(20)?2\d|\b2[3-7]\s?\/\s?2[4-7]\b|Stand:?\s*\d{1,2}\.\s?\d{1,2}\.\s?\d{2,4}|Stand:?\s+\d{0,2}\.?\s?[A-ZÄa-zä]+\s+20\d\d|Geltungszeitraum[^\n]{0,40}|gültig ab[^\n]{0,30}|version[^\n]{0,30}20\d\d|aggiornat[^\n]{0,30}20\d\d/gi;
const bare = h => h.replace(/^www\./, '');
const sleep = ms => new Promise(r => setTimeout(r, ms));
let n = 0;
function post(body) {
  const f = `/tmp/c${++n}.md`; fs.writeFileSync(f, body.slice(0, 64000));
  for (const wait of [0, 20000, 60000]) {
    if (wait) execFileSync('sleep', [String(wait / 1000)]);
    try { execFileSync('gh', ['api', `repos/${process.env.REPO}/issues/${process.env.PR}/comments`, '-F', `body=@${f}`], { stdio: ['ignore', 'ignore', 'inherit'] }); return; } catch (e) {}
  }
  console.log('POST FAILED', body.slice(0, 200));
}
const robots = {}, gate = {};
async function fetchRobots(host) {
  let status, text = '';
  for (const limit of [30000, 60000]) {
    await sleep(1000);
    try { const r = await fetch(`https://${host}/robots.txt`, { headers: { 'User-Agent': UA }, signal: AbortSignal.timeout(limit) }); status = r.status; text = await r.text(); break; }
    catch (e) { status = `error: ${e.message}`; }
  }
  const html = /<html|<!doctype/i.test(text.slice(0, 500));
  const groups = []; let cur = null, lastUA = false;
  if (!html) for (const raw of text.split('\n')) {
    const m = raw.replace(/#.*/, '').trim().match(/^([^:]+):\s*(.*)$/); if (!m) continue;
    const k = m[1].toLowerCase(), v = m[2].trim();
    if (k === 'user-agent') { if (!lastUA) { cur = { agents: [], rules: [] }; groups.push(cur); } cur.agents.push(v.toLowerCase()); lastUA = true; }
    else { lastUA = false; if (cur && (k === 'allow' || k === 'disallow')) cur.rules.push([k, v]); }
  }
  const ANTH = ['claudebot', 'anthropic-ai', 'claude-web', 'claude-user', 'claude-searchbot', 'footballplannerbot'];
  const own = groups.filter(g => g.agents.some(a => a !== '*' && ANTH.some(x => x.startsWith(a) || a.startsWith(x))));
  const rules = (own.length ? own : groups.filter(g => g.agents.includes('*'))).flatMap(g => g.rules);
  const blocked = [401, 403, 429, 503].includes(status) || typeof status !== 'number';
  const named = own.map(g => g.agents.join(',') + ' -> ' + g.rules.map(r => r.join(': ')).join('; ')).join(' | ');
  robots[host] = { status, rules, blocked, html, named, head: text.slice(0, 700) };
}
function allowed(host, path) {
  const rb = robots[host];
  if (!rb) return [false, 'robots.txt of this host was not read'];
  if (rb.blocked) return [false, `robots.txt answered ${rb.status}`];
  let best = null;
  for (const [k, v] of rb.rules) {
    if (!v) continue;
    const re = new RegExp('^' + v.split('*').map(s => s.replace(/[.+?^${}()|[\]\\]/g, '\\$&')).join('.*').replace(/\\\$$/, '$'));
    if (re.test(path) && (!best || v.length > best[1].length || (v.length === best[1].length && k === 'allow'))) best = [k, v];
  }
  return best && best[0] === 'disallow' ? [false, `Disallow: ${best[1]}`] : [true, best ? `${best[0]}: ${best[1]}` : 'no matching rule'];
}
// Opens one page. Returns {stop} or {status, final, title, text, blocks, links}.
async function open(browser, url) {
  const u = new URL(url);
  if (isForbidden(url)) return { stop: 'address holds a shop, cart, login or queue word; not opened' };
  const [ok, why] = allowed(u.host, u.pathname + u.search);
  if (!ok) return { stop: `robots.txt: ${why}; not opened` };
  const ctx = await browser.newContext({ userAgent: UA, locale: T.locale?.[u.host] || 'de-DE' });
  const killer = setTimeout(() => ctx.close().catch(() => {}), 150000);
  try {
    const page = await ctx.newPage();
    await page.route('**/*', r => (r.request().isNavigationRequest() && isForbidden(r.request().url())) ? r.abort() : r.continue());
    await sleep(1000);
    let resp;
    try { resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }); } catch (e) { return { stop: `FAILED: ${e.message.split('\n')[0]}` }; }
    try { await page.waitForLoadState('networkidle', { timeout: 15000 }); } catch {}
    await sleep(1500);
    try { await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)); await sleep(1500); } catch {}
    const status = resp ? resp.status() : 0, final = page.url();
    if (isForbidden(final)) return { stop: 'redirected to a login, checkout or queue address; nothing recorded' };
    if (bare(new URL(final).host) !== bare(u.host)) return { stop: `redirected to another host (${new URL(final).host}); nothing recorded` };
    const title = await page.title().catch(() => '');
    const d = await page.evaluate(() => {
      // Consent overlays are removed from this copy of the page; nothing is clicked or accepted.
      document.querySelectorAll('#CybotCookiebotDialog,#CybotCookiebotDialogBodyUnderlay,#usercentrics-root,#usercentrics-cmp-ui,#cmpbox,#cmpbox2,#onetrust-consent-sdk,#didomi-host,#axeptio_overlay,#tarteaucitronRoot,#sd-cmp,.cmp-root,[id^="sp_message_container"],#ccm-widget,.ccm-root,#cookiescript_injected_wrapper,.cky-consent-container,.cky-overlay,#BorlabsCookieBox,.borlabs-cookie').forEach(e => e.remove());
      const text = document.body ? document.body.innerText : '';
      const blocks = Array.from(document.querySelectorAll('p,li,tr,h1,h2,h3,h4,h5,dt,dd,summary,blockquote,figcaption')).map(e => (e.textContent || '').replace(/\s+/g, ' ').trim()).filter(x => x.length > 2 && x.length < 3000);
      const links = Array.from(document.querySelectorAll('a[href]')).map(a => [(a.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 70), a.href]);
      const main = document.querySelector('main'); const mt = main ? main.innerText : '';
      return { text, blocks, links, mt };
    });
    return { status, final, title, ...d };
  } catch (e) { return { stop: `FAILED: ${String(e.message).split('\n')[0]}` }; }
  finally { clearTimeout(killer); await ctx.close().catch(() => {}); }
}
const challenged = r => [403, 429, 503].includes(r.status) || CHALLENGE.test(r.title || '') || CHALLENGE.test((r.text || '').slice(0, 600));
function hits(lines, kws, ctxN, cap) {
  const res = kws.map(k => new RegExp(k, 'i')); const keep = new Set();
  lines.forEach((l, i) => { if (res.some(r => r.test(l))) for (let j = i - ctxN; j <= i + ctxN; j++) if (j >= 0 && j < lines.length) keep.add(j); });
  let out = '', last = -2;
  for (const i of [...keep].sort((a, b) => a - b)) { if (i !== last + 1) out += '\n[...]\n'; out += lines[i].slice(0, 700) + '\n'; last = i; if (out.length > cap) { out += '\n[cut at the cap]'; break; } }
  return out;
}
const seasons = t => [...new Set((t.match(SEASON) || []).map(x => x.replace(/\s+/g, ' ').trim()))].slice(0, 14).join(' ; ') || 'none found';
async function gateHost(browser, host) {
  const cfg = T.hosts[host] || {}; const rb = robots[host];
  let body = `### HOST ${host} (run ${T.run})\nrobots.txt: HTTP ${rb.status}${rb.html ? ' (an HTML page, read as no rules)' : ''}; groups naming this reader or Anthropic's agents: ${rb.named || 'none'}\n\n\`\`\`\n${rb.html ? '' : rb.head}\n\`\`\`\n`;
  if (rb.blocked) { gate[host] = [false, `robots.txt answered ${rb.status}`]; post(body + `\nGATE: CLOSED (${gate[host][1]})`); return; }
  if (rb.named && rb.rules.some(([k, v]) => k === 'disallow' && v === '/')) { gate[host] = [false, 'robots.txt bars this reader or Anthropic\'s agents']; post(body + `\nGATE: CLOSED (${gate[host][1]})`); return; }
  const mode = cfg.gate || 'discover';
  if (mode === 'open') { gate[host] = [true, cfg.why || 'judged open after an earlier run']; post(body + `\nGATE: open (${gate[host][1]})`); return; }
  if (mode === 'closed') { gate[host] = [false, cfg.why || 'judged closed']; post(body + `\nGATE: CLOSED (${gate[host][1]})`); return; }
  if (mode === 'robots' || mode === 'self') { gate[host] = [true, mode === 'self' ? 'the page asked for is the host\'s own terms; checked for bot wording when read' : cfg.why || 'robots.txt only']; post(body + `\nGATE: open (${gate[host][1]})`); return; }
  if (mode.startsWith('via:')) { gate[host] = ['via', mode.slice(4)]; post(body + `\nGATE: document host, follows ${mode.slice(4)}`); return; }
  if (mode === 'hold') { gate[host] = [false, 'held: no notice read yet']; post(body + '\nGATE: HELD (robots.txt only in this run)'); return; }
  let notices = cfg.notice || [];
  if (!notices.length) {
    const r = await open(browser, cfg.landing || `https://${host}/`);
    if (r.stop) { gate[host] = [false, `landing page: ${r.stop}`]; post(body + `\nLanding page: ${r.stop}\nGATE: HELD`); return; }
    if (challenged(r)) { gate[host] = [false, `landing page HTTP ${r.status}, title "${r.title}" (challenge or refusal)`]; post(body + `\nGATE: CLOSED (${gate[host][1]}); text length ${r.text.length}, unread`); return; }
    const cand = r.links.filter(([t, h]) => { try { return bare(new URL(h).host) === bare(host) && NOTICE.test(t + ' ' + decodeURIComponent(new URL(h).pathname)) && !isForbidden(h); } catch { return false; } });
    const seen = new Set(); notices = [];
    for (const [t, h] of cand) { const k = h.split('#')[0]; if (!seen.has(k)) { seen.add(k); notices.push(k); } }
    notices.sort((a, b) => (/impressum|imprint|legal|mentions|note/i.test(b) ? 1 : 0) - (/impressum|imprint|legal|mentions|note/i.test(a) ? 1 : 0));
    body += `\nLanding page ${r.final}: HTTP ${r.status}, title "${r.title}", ${r.text.length} characters. Notice links found: ${notices.slice(0, 6).join(' , ') || 'NONE'}\n`;
    notices = notices.slice(0, 3);
  }
  if (!notices.length) { gate[host] = [false, 'no legal notice link found on the landing page']; post(body + '\nGATE: HELD (no notice found)'); return; }
  let okN = 0, flagged = '';
  for (const nu of notices) {
    const r = await open(browser, nu);
    if (r.stop) { body += `\nNotice ${nu}: ${r.stop}\n`; continue; }
    if (challenged(r)) { body += `\nNotice ${nu}: HTTP ${r.status}, title "${r.title}" (challenge or refusal), unread\n`; continue; }
    const t = (r.mt && r.mt.length > 500) ? r.mt : r.text; const ls = t.split('\n').map(x => x.trim()).filter(Boolean);
    const fl = ls.filter(l => BOTS.test(l));
    body += `\nNotice ${r.final}: HTTP ${r.status}, title "${r.title}", ${t.length} characters. Lines with bot or automated-access wording: ${fl.length}\n`;
    if (fl.length) { flagged += fl.map(l => '> ' + l.slice(0, 600)).join('\n') + '\n'; body += fl.slice(0, 8).map(l => '> ' + l.slice(0, 600)).join('\n') + '\n'; }
    if (t.length >= 300) okN++;
  }
  if (!okN) gate[host] = [false, 'no notice text of 300 characters or more was read'];
  else if (flagged) gate[host] = [false, 'a notice has bot or automated-access wording: a person judges'];
  else gate[host] = [true, 'robots.txt read, notice read, no bot or automated-access wording'];
  post(body + `\nGATE: ${gate[host][0] ? 'open' : 'HELD'} (${gate[host][1]})`);
}
function isOpen(host) { let g = gate[host]; if (g && g[0] === 'via') g = gate[g[1]] || [false, `${g[1]} was not gated in this run`]; return g || [false, 'host not gated']; }
async function readPdf(p) {
  const u = new URL(p.url); const [ok, why] = allowed(u.host, u.pathname + u.search);
  if (!ok) return { stop: `robots.txt: ${why}; not opened` };
  await sleep(1000);
  let r; try { r = await fetch(p.url, { headers: { 'User-Agent': UA }, signal: AbortSignal.timeout(90000), redirect: 'follow' }); } catch (e) { return { stop: `FAILED: ${e.message}` }; }
  if (bare(new URL(r.url).host) !== bare(u.host)) return { stop: `redirected to another host (${new URL(r.url).host}); nothing recorded` };
  const ct = r.headers.get('content-type') || ''; const buf = Buffer.from(await r.arrayBuffer());
  if (r.status !== 200) return { stop: `HTTP ${r.status} (${ct}), ${buf.length} bytes; unread` };
  if (!/pdf/i.test(ct) && buf.slice(0, 5).toString() !== '%PDF-') return { notpdf: ct, bytes: buf.length, status: r.status };
  const f = `/tmp/d${n}_${Math.random().toString(36).slice(2)}.pdf`; fs.writeFileSync(f, buf);
  let lay = '', raw = '', info = '';
  try { lay = execFileSync('pdftotext', ['-layout', f, '-'], { maxBuffer: 1 << 26 }).toString(); raw = execFileSync('pdftotext', ['-raw', f, '-'], { maxBuffer: 1 << 26 }).toString(); info = execFileSync('pdfinfo', [f]).toString(); } catch (e) { return { stop: `pdftotext failed: ${e.message.split('\n')[0]}` }; }
  return { status: 200, final: r.url, title: (info.match(/Title:\s*(.*)/) || [])[1] || '', info: (info.match(/(CreationDate|ModDate|Pages):.*/g) || []).join(' ; '), text: lay, raw, bytes: buf.length };
}
async function readPage(browser, p) {
  const host = new URL(p.url).host; const g = isOpen(host);
  const head = `### PAGE ${p.id} (run ${T.run}) ${p.url}\nrows: ${p.rows.join(', ')}\n`;
  if (!g[0]) { post(head + `SKIPPED: host gate not open (${g[1]}); not opened.`); return; }
  let r = p.type === 'pdf' ? await readPdf(p) : await open(browser, p.url);
  if (r.notpdf) r = await open(browser, p.url);
  if (r.stop && /Download is starting|net::ERR_ABORTED/.test(r.stop)) r = await readPdf(p);
  if (r.notpdf) { post(head + `STOPPED: neither a PDF nor a page (content type ${r.notpdf}, ${r.bytes} bytes): a picture or another file, unread.`); return; }
  if (r.stop) { post(head + `STOPPED: ${r.stop}`); return; }
  if (r.raw === undefined && challenged(r)) { post(head + `STOPPED: HTTP ${r.status}, title "${r.title}" (challenge or refusal); text length ${r.text.length}, unread.`); return; }
  const isPdf = r.raw !== undefined;
  const full = isPdf ? r.text : ((r.mt && r.mt.length > 500 && r.text.length > 12000) ? r.mt : r.text);
  if ((T.hosts[host] || {}).gate === 'self' && BOTS.test(r.text)) {
    const fl = r.text.split('\n').filter(l => BOTS.test(l)).slice(0, 8).map(l => '> ' + l.trim().slice(0, 500)).join('\n');
    post(head + `HELD: this page is the host's own terms and has bot or automated-access wording; only those lines are posted, a person judges.\n${fl}`); return;
  }
  const lines = full.split('\n').map(x => x.replace(/\s+$/, '')).filter(x => x.trim());
  let kwText = hits(lines, p.kw, isPdf ? 2 : 1, 11000);
  if (isPdf) { const k2 = hits(r.raw.split('\n').filter(x => x.trim()), p.kw, 1, 5000); kwText += `\n--- same file, pdftotext -raw ---\n${k2}`; }
  else { const shown = new Set(lines.map(l => l.trim())); const hidden = (r.blocks || []).filter(b => !shown.has(b) && !full.includes(b.slice(0, 60))); const k2 = hits(hidden, p.kw, 0, 5000); if (k2.trim()) kwText += `\n--- in the page's HTML but not displayed (collapsed sections) ---\n${k2}`; }
  let body = head + `HTTP ${r.status}; final address ${r.final}; title "${r.title}"; ${isPdf ? `PDF, ${r.bytes} bytes, ${r.info}; ` : ''}text ${r.text.length} characters${(!isPdf && full !== r.text) ? ` (posted from <main>, ${full.length})` : ''}\nSeason or date marks in the text: ${seasons(r.text)}\nKey words: ${p.kw.join(' | ')}\n\n#### First 3000 characters\n\`\`\`\n${p.nofirst ? '(not posted for this page: press text, key-word paragraphs only)' : full.slice(0, 3000)}\n\`\`\`\n#### Paragraphs with a key word\n\`\`\`\n${kwText}\n\`\`\`\n`;
  if (p.links && r.links) {
    const seen = new Set(); const ls = r.links.filter(([t, h]) => { if (seen.has(h) || !/^https?:/.test(h)) return false; seen.add(h); return new RegExp(p.links === true ? '.' : p.links, 'i').test(t + ' ' + h); }).slice(0, 120);
    body += `#### Links (${ls.length})\n` + ls.map(([t, h]) => `- ${t} : ${h}`).join('\n') + '\n';
  }
  post(body);
  if (p.follow && r.links) {
    const fr = new RegExp(p.follow.re, 'i'); const seen = new Set(); let k = 0;
    for (const [tx, h] of r.links) {
      if (k >= (p.follow.max || 2)) break;
      if (seen.has(h) || !fr.test(tx + ' ' + h) || isForbidden(h)) continue; seen.add(h);
      let hh; try { hh = new URL(h).host; } catch { continue; }
      if (!robots[hh]) { post(`### PAGE ${p.id}-f${k + 1} (run ${T.run}) ${h}\nSKIPPED: linked from ${p.id}, but its host ${hh} was not gated in this run.`); k++; continue; }
      await readPage(browser, { id: `${p.id}-f${++k}`, url: h, rows: p.rows, kw: p.follow.kw || p.kw, type: 'pdf' });
    }
  }
}
(async () => {
  const browser = await chromium.launch();
  const hosts = [...new Set([...Object.keys(T.hosts), ...T.pages.map(p => new URL(p.url).host)])];
  const order = hosts.filter(h => !String((T.hosts[h] || {}).gate || '').startsWith('via:')).concat(hosts.filter(h => String((T.hosts[h] || {}).gate || '').startsWith('via:')));
  const byHost = {}; for (const p of T.pages) (byHost[new URL(p.url).host] ||= []).push(p);
  // Phase 1: robots.txt and the notice of every host, four hosts at a time. Phase 2: pages, host by host.
  let i = 0; const worker = async () => { while (i < order.length) { const h = order[i++]; try { await fetchRobots(h); await gateHost(browser, h); } catch (e) { gate[h] = [false, 'gate error ' + e.message]; post(`### HOST ${h}\nGATE ERROR ${e.message}`); } } };
  await Promise.all([1, 2, 3, 4].map(worker));
  let j = 0; const hs = Object.keys(byHost); const w2 = async () => { while (j < hs.length) { const h = hs[j++]; for (const p of byHost[h]) { try { await readPage(browser, p); } catch (e) { post(`### PAGE ${p.id} ${p.url}\nFAILED: ${e.message}`); } } } };
  await Promise.all([1, 2, 3, 4].map(w2));
  await browser.close();
  post(`### RUN ${T.run} finished: ${hosts.length} hosts, ${T.pages.length} pages, ${n} comments.\n` + hosts.map(h => `- ${h}: ${JSON.stringify(isOpen(h))}`).join('\n'));
})().catch(e => { console.error(e); post('### RUN FAILED ' + e.message); process.exit(1); });
