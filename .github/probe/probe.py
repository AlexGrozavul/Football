"""Temporary probe, phase 5b session 3. Reads Wikipedia pages through the MediaWiki parse API
and posts, per pair, only the sentences naming both clubs and their section heading; reads the
grounds' places (club P115 -> venue P131) from Wikidata. Removed before merge."""
import json, os, re, sys, time, urllib.parse, urllib.request
from html.parser import HTMLParser
UA = 'FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)'
NREQ = 0
def get(url):
    global NREQ
    for attempt in range(6):
        NREQ += 1
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
        except Exception as e:
            print('fetch error', url, e); time.sleep(10 * (attempt + 1)); continue
        if d.get('error', {}).get('code') == 'maxlag':
            time.sleep(10 * (attempt + 1)); continue
        time.sleep(1.5)
        return d
    return None
SKIP = {'style', 'script', 'sup', 'math'}
BLOCK = {'p', 'li', 'tr', 'dd', 'dt', 'caption', 'blockquote', 'th'}
VOID = {'br', 'img', 'hr', 'meta', 'link', 'input', 'wbr', 'area', 'col', 'source'}
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.stack = []; s.skip_at = None; s.head = 'Lead'; s.inh = False; s.buf = []; s.hb = []; s.out = []
    def handle_starttag(s, t, a):
        if t in VOID:
            if t == 'br' and s.skip_at is None: s.buf.append(' ')
            return
        s.stack.append(t)
        if s.skip_at is not None: return
        cls = dict(a).get('class') or ''
        if t in SKIP or any(k in cls for k in ('navbox', 'reflist', 'mw-references', 'mw-editsection', 'metadata', 'infobox', 'shortdescription')):
            s.skip_at = len(s.stack); return
        if t in ('h2', 'h3', 'h4'): s.flush(); s.inh = True; s.hb = []
        elif t in BLOCK: s.flush()
        elif t == 'td': s.buf.append(' | ')
    def handle_endtag(s, t):
        if t in VOID or t not in s.stack: return
        while s.stack:
            if s.stack.pop() == t: break
        if s.skip_at is not None:
            if len(s.stack) < s.skip_at: s.skip_at = None
            return
        if t in ('h2', 'h3', 'h4') and s.inh:
            s.inh = False; s.head = ' '.join(''.join(s.hb).split())
        elif t in BLOCK: s.flush()
    def handle_data(s, d):
        if s.skip_at is not None: return
        (s.hb if s.inh else s.buf).append(d)
    def flush(s):
        txt = ' '.join(''.join(s.buf).split()); s.buf = []
        if txt: s.out.append((s.head, txt))
def blocks(html):
    p = P(); p.feed(html); p.flush(); return p.out
CLASSW = re.compile(r'local derby|Lokalderby|Stadtderby|city derby|cross-?town|derby cittadino|della città|stadsderby|derby local|main rival|biggest rival|arch-?(?:rival|nemes|enem)|principal|fiercest|greatest rival|same city|both (?:based|from|located|hailing)|neighbou?r', re.I)
def sentences(txt):
    return re.split(r'(?<=[.!?])\s+(?=[A-Z"“(])', txt)
def page(url):
    title = urllib.parse.unquote(url.split('/wiki/')[1].split('#')[0])
    api = 'https://en.wikipedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'parse', 'page': title, 'prop': 'text', 'format': 'json', 'formatversion': 2, 'redirects': 1, 'maxlag': 5})
    d = get(api)
    if not d or 'parse' not in d: return None, (d or {}).get('error', {}).get('info', 'no response')
    return blocks(d['parse']['text']), d['parse']['title']
def main():
    rows = [l.rstrip('\n').split('\t') for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
    cache = {}; out = []
    for r in rows:
        ids, url, ra, rb = r[:4]; one = len(r) > 4 and r[4] in ('one', 'line'); line = len(r) > 4 and r[4] == 'line'
        u = url.split('#')[0]
        if u not in cache: cache[u] = page(u)
        bl, title = cache[u]
        if bl is None: out.append(f'## {ids}: CANNOT READ {u} ({title})'); continue
        A, B = re.compile(ra), re.compile(rb); hits = []
        for head, txt in bl:
            for snt in ([txt] if line else sentences(txt)):
                if A.search(snt) and (one or B.search(snt)): hits.append((0 if CLASSW.search(snt) else (2 if ' | ' in snt else 1), head, snt))
        hits_sorted = sorted(enumerate(hits), key=lambda x: (x[1][0], x[0]))[:6]
        out.append(f'## {ids} [{title}] {len(hits)} sentences name both')
        for _, (c, head, snt) in sorted(hits_sorted):
            out.append(f'- ({head}) {snt[:260]}')
    # grounds' places
    qids = [l.strip() for l in open(os.path.join(os.path.dirname(sys.argv[1]), 'qids.txt')) if l.strip()] if os.path.exists(os.path.join(os.path.dirname(sys.argv[1]), 'qids.txt')) else []
    def ents(ids, props):
        res = {}
        for i in range(0, len(ids), 50):
            d = get('https://www.wikidata.org/w/api.php?' + urllib.parse.urlencode({'action': 'wbgetentities', 'ids': '|'.join(ids[i:i + 50]), 'props': props, 'languages': 'en', 'format': 'json', 'maxlag': 5}))
            res.update((d or {}).get('entities', {}))
        return res
    def claim(e, p):
        v = []
        for c in e.get('claims', {}).get(p, []):
            if c.get('rank') == 'deprecated': continue
            try: v.append((c['rank'], c['mainsnak']['datavalue']['value']['id']))
            except KeyError: pass
        pref = [x for r, x in v if r == 'preferred']
        return pref or [x for r, x in v]
    if not qids:
        qids = []
    clubs = ents(qids, 'claims|labels') if qids else {}; ven = {q: claim(clubs.get(q, {}), 'P115') for q in qids}
    vids = sorted({v for vs in ven.values() for v in vs}); venues = ents(vids, 'claims|labels')
    pl = {v: claim(venues.get(v, {}), 'P131') for v in vids}; pids = sorted({p for ps in pl.values() for p in ps})
    places = ents(pids, 'labels')
    lab = lambda d, q: d.get(q, {}).get('labels', {}).get('en', {}).get('value', q)
    if qids: out.append('## Grounds (club P115 venue -> P131)')
    for q in qids:
        out.append(f'- {q} {lab(clubs, q)}: ' + '; '.join(f'{lab(venues, v)} -> ' + ', '.join(lab(places, p) for p in pl.get(v, [])) for v in ven[q]))
    lp = os.path.join(os.path.dirname(sys.argv[1]), 'labels.txt')
    if os.path.exists(lp):
        ids = [l.strip() for l in open(lp) if l.strip()]
        out.append('## Labels')
        for q0 in ids:
          d = get('https://www.wikidata.org/w/api.php?' + urllib.parse.urlencode({'action': 'wbgetentities', 'ids': q0, 'props': 'labels|descriptions', 'languages': 'en|nl|es|de', 'format': 'json', 'maxlag': 5}))
          if d and 'error' in d: out.append(f"- {q0}: error {d['error'].get('code')}")
          for q, e in ((d or {}).get('entities') or {}).items():
            out.append(f"- {q}: " + '; '.join(f"{k}={v['value']}" for k, v in e.get('labels', {}).items()) + ' / ' + '; '.join(f"{k}={v['value']}" for k, v in e.get('descriptions', {}).items()))
    out.append(f'requests: {NREQ}')
    body = '\n'.join(out); print(body[:3000])
    label = os.environ.get('RUN_LABEL', 'run')
    chunks, cur = [], ''
    for line in body.split('\n'):
        if len(cur) + len(line) > 60000: chunks.append(cur); cur = ''
        cur += line + '\n'
    chunks.append(cur)
    for n, c in enumerate(chunks):
        req = urllib.request.Request(f"https://api.github.com/repos/{os.environ['REPO']}/issues/{os.environ['PR']}/comments", data=json.dumps({'body': f'Probe {label} part {n + 1}/{len(chunks)}\n\n' + c}).encode(), headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'], 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'})
        urllib.request.urlopen(req)
main()
