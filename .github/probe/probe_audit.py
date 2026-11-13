#!/usr/bin/env python3
"""TEMPORARY - grounds and coordinates audit, phase 1e. Removed before the merge.

Reads Wikipedia season articles (grounds tables), OpenStreetMap (Overpass, then Nominatim)
and a few club pages; posts compact tables as pull-request comments. Commits nothing.
Wikimedia: one request per second, maxlag=5, never raised; on a lag refusal the probe
waits and retries. Overpass and Nominatim: descriptive User-Agent, at most one request per second.
Other hosts: robots.txt, then the root page and the terms page it links, then content.
"""
import html, json, os, re, sys, threading, time, unicodedata
import urllib.error, urllib.parse, urllib.request, urllib.robotparser
from concurrent.futures import ThreadPoolExecutor

UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
RUN = os.environ.get("PROBE_RUN", "?")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
PR = os.environ.get("PR_NUMBER", "")
TOKEN = os.environ.get("GH_TOKEN", "")
HERE = os.path.dirname(os.path.abspath(__file__))
T0 = time.time()
DEADLINE = T0 + 80 * 60
LOG, LAST, NREQ = [], {}, {}
LOCK = threading.Lock()
LANGS = {"DE": ["de"], "AT": ["de"], "CH": ["de", "fr", "it"], "BE": ["nl", "fr"], "NL": ["nl"],
         "FR": ["fr"], "ES": ["es"], "IT": ["it"], "RO": ["ro"], "RS": ["sr"], "GR": ["el"], "GB": ["en"]}
SDB = {"DE": "ger", "RO": "rou", "FR": "fra", "IT": "ita", "CH": "sui", "AT": "aut", "RS": "ser",
       "GR": "gre", "ES": "esp", "GB": "eng", "NL": "ned", "BE": "bel"}
LEAGUES = {"IT": ["https://www.legaseriea.it/", "https://www.legab.it/"], "CH": ["https://sfl.ch/"],
           "ES": ["https://www.laliga.com/"], "FR": ["https://ligue1.com/"],
           "NL": ["https://eredivisie.nl/", "https://keukenkampioendivisie.nl/"],
           "BE": ["https://www.proleague.be/"], "GR": ["https://www.slgr.gr/"],
           "RO": ["https://lpf.ro/"], "AT": ["https://www.bundesliga.at/"]}
KEY = (r"capacit|kapazit|kapacit|pl[aä]tze|zuschauer|capien|posti|spettator|aforo|espectador|localidades|"
       r"toeschouwer|plaatsen|\bplaces\b|χωρητικ|θέσε|θεατ|капацитет|места|mesta|locuri|lugares|lotaç|"
       r"\bseats\b|seater|all-seat|seating")
NUM = r"\d{1,3}(?:[.,   '’]\d{3})+|\d{3,6}"
SKIPHOST = re.compile(r"transfermarkt|soccerway|worldfootball|weltfussball|footballdatabase|facebook|twitter|"
                      r"//x\.com|instagram|youtube|google|openstreetmap|geohack|wikimedia|wikipedia|wikidata|"
                      r"toolforge|archive\.|tiktok|linkedin|flickr|bing\.com|booking|tripadvisor|"
                      r"superliga\.rs|mhscfoot|fcbotosani\.ro|onlinebettingacademy|germanfootballgrounds|"
                      r"racingstub|numero-diez|pressonline", re.I)
STADWORD = re.compile(r"stadi|stade|estadi|arena|ground|campo|sportpark|capac|infrastr|venue|anlage|terrain|"
                      r"gipedo|γήπεδο|facilit|impianto|veld", re.I)
TERMS = re.compile(r"terms|conditions|legal|nutzungsbedingungen|agb|mentions|aviso|condizioni|note-legali|"
                   r"voorwaarden|disclaimer|oroi|uslovi|termeni|impressum|condiciones|rechtlich", re.I)
BAN = re.compile(r"[^.]{0,120}(automated (?:means|access|quer|system)|robots?,? spiders?|scrap(?:e|ing)|"
                 r"crawl(?:er|ing)|data[- ]mining|automatisiert\w* (?:abruf|zugriff|abfrage)|"
                 r"moyens? automatis|medios automatizados|mezzi automatizzati|geautomatiseerd\w* (?:middel|toegang))"
                 r"[^.]{0,120}", re.I)
ANTHROPIC = ["claudebot", "anthropic-ai", "claude-web", "claude-user", "claude-searchbot"]


def log(msg):
    with LOCK:
        LOG.append(f"{int(time.time() - T0):5d}s {msg}")
    print(msg, flush=True)


def http(url, key, gap, timeout=30, maxbytes=4_000_000):
    with LOCK:
        now = time.time()
        at = max(now, LAST.get(key, 0) + gap)
        LAST[key] = at
        NREQ[key] = NREQ.get(key, 0) + 1
    if at > now:
        time.sleep(at - now)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en,*;q=0.5"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.headers, r.read(maxbytes), r.geturl()


WAITED = {}


def wm(host, params, budget=None):
    """Wikimedia API call, maxlag=5 always. On a lag refusal: wait and retry inside the run."""
    back = 10
    budget = budget or (int(os.environ.get("WD_BUDGET", "1500")) if "wikidata" in host else 1500)
    for attempt in range(400):
        p = dict(params)
        p.update(format="json", maxlag="5", formatversion="2")
        url = f"https://{host}/w/api.php?" + urllib.parse.urlencode(p)
        try:
            _, hdr, body, _ = http(url, "wikimedia", 1.0, timeout=60, maxbytes=40_000_000)
            data = json.loads(body)
            err = data.get("error", {}) if isinstance(data, dict) else {}
            if err.get("code") == "maxlag":
                ra = hdr.get("Retry-After") or ""
                w = max(int(ra) if ra.isdigit() else 0, back)
                back = min(back * 2, 300)
                if WAITED.get(host, 0) + w > budget or time.time() + w > DEADLINE:
                    log(f"LAG {host}: waited {WAITED.get(host, 0)} s in all, still refused ({str(err.get('info'))[:90]}); this call is given up, maxlag stays 5")
                    return None
                WAITED[host] = WAITED.get(host, 0) + w
                log(f"LAG {host}: {str(err.get('info'))[:90]} retry-after={ra or '-'}; waiting {w} s")
                time.sleep(w)
                continue
            if err:
                log(f"ERR {host} api {err.get('code')}: {str(err.get('info'))[:140]}")
                return None
            return data
        except urllib.error.HTTPError as e:
            ra = e.headers.get("Retry-After") or ""
            log(f"HTTP {e.code} {host} retry-after={ra or '-'} try {attempt}")
            if e.code in (429, 503) and attempt < 8:
                w = max(int(ra) if ra.isdigit() else 0, back)
                back = min(back * 2, 300)
                WAITED[host] = WAITED.get(host, 0) + w
                time.sleep(w)
                continue
            return None
        except Exception as e:
            log(f"ERR {host} {type(e).__name__} {str(e)[:100]}")
            if attempt >= 3:
                return None
            time.sleep(5)
    return None


def post(body):
    body = body[:64500]
    if not (TOKEN and PR):
        print(body[:1500])
        return
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{PR}/comments",
        data=json.dumps({"body": body}).encode(), method="POST",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
                 "User-Agent": UA, "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=60).read()
    except Exception as e:
        print("COMMENT FAILED", e)
    time.sleep(1.5)


def post_chunks(title, lines, limit=60000):
    part, buf, size = 1, [], 0
    for ln in lines:
        ln = ln[:limit - 200]
        if size + len(ln) + 1 > limit and buf:
            post(f"{title} part {part}\n```\n" + "\n".join(buf) + "\n```")
            part, buf, size = part + 1, [], 0
        buf.append(ln)
        size += len(ln) + 1
    if buf:
        post(f"{title} part {part} LAST\n```\n" + "\n".join(buf) + "\n```")


def fold(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9α-ωа-я]+", " ", s).strip()


# ---------- Wikidata: the ground of each club and its articles ----------


def page_text(body):
    t = body.decode("utf-8", "replace")
    title = re.search(r"<title[^>]*>(.*?)</title>", t, re.S | re.I)
    links = re.findall(r"<a\s[^>]*?href\s*=\s*[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", t, re.S | re.I)
    t = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    return (html.unescape(title.group(1)).strip()[:90] if title else ""), t, links




def rendered(url):
    """A page that needs a browser: Chromium through Playwright, the same User-Agent, no clicks."""
    import subprocess
    with LOCK:
        NREQ["rendered"] = NREQ.get("rendered", 0) + 1
    try:
        r = subprocess.run(["node", os.path.join(HERE, "render.js"), url], capture_output=True, text=True, timeout=150)
        d = json.loads(r.stdout.strip().split("\n")[-1])
        return d.get("status") or "no status", d.get("final") or url, d.get("title", "")[:90], re.sub(r"\s+", " ", d.get("text", "")), d.get("links", [])
    except Exception as e:
        return f"render {type(e).__name__}", url, "", "", []




# ====================== phase 1e ======================
import math
from html.parser import HTMLParser

OSM_UA = "football-fixture-planner/1.0 (personal project; https://github.com/AlexGrozavul/Football)"
OVERPASS = "https://overpass-api.de/api/interpreter"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
STAGES = os.environ.get("PROBE_STAGES", "A,B,C").split(",")
NS = re.compile(r"^(File|Datei|Fișier|Fichier|Bestand|Image|Bild|Category|Kategorie|Categorie|Special|Spezial|"
                r"Help|Hilfe|Wikipedia|Template|Vorlage|Portal|Format|Talk|Diskussion|Benutzer|User|Imagine):", re.I)
GENERIC = set("stadion stadionul stadium arena sportpark sportplatz sportanlage platz am an der im in auf dem den "
              "des die das zur zum the ground stade stadio de la du".split())


class TP(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.stack, self.skip, self.spans = [], [], 0, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("style", "script", "sup"):
            self.skip += 1
            return
        if tag == "span":
            hid = "display:none" in (a.get("style") or "").replace(" ", "")
            self.spans.append(hid)
            if hid:
                self.skip += 1
            return
        if tag == "table":
            self.stack.append({"cls": a.get("class") or "", "rows": [], "row": None, "cell": None})
            return
        if not self.stack:
            return
        t = self.stack[-1]
        if tag == "tr":
            t["row"] = []
            t["rows"].append(t["row"])
            t["cell"] = None
        elif tag in ("td", "th"):
            if t["row"] is None:
                t["row"] = []
                t["rows"].append(t["row"])

            def n(v):
                m = re.match(r"\d+", v or "")
                return max(1, min(int(m.group()), 60)) if m else 1
            t["cell"] = {"th": tag == "th", "text": [], "links": [], "cs": n(a.get("colspan")), "rs": n(a.get("rowspan"))}
            t["row"].append(t["cell"])
        elif tag == "a" and t["cell"] is not None:
            h = a.get("href") or ""
            if h.startswith("/wiki/"):
                title = urllib.parse.unquote(h[6:]).split("#")[0].replace("_", " ")
                if title and not NS.match(title):
                    t["cell"]["links"].append(title)
        elif tag == "br" and t["cell"] is not None:
            t["cell"]["text"].append(" ")

    def handle_endtag(self, tag):
        if tag in ("style", "script", "sup"):
            self.skip = max(0, self.skip - 1)
            return
        if tag == "span":
            if self.spans and self.spans.pop():
                self.skip = max(0, self.skip - 1)
            return
        if not self.stack:
            return
        t = self.stack[-1]
        if tag == "table":
            self.tables.append(self.stack.pop())
        elif tag in ("td", "th"):
            t["cell"] = None
        elif tag == "tr":
            t["row"] = None

    def handle_data(self, data):
        if self.skip or not self.stack:
            return
        c = self.stack[-1]["cell"]
        if c is not None:
            c["text"].append(data)


def ctext(c):
    return re.sub(r"\s+", " ", "".join(c["text"])).strip()


def grid(rows):
    out, carry = [], {}
    for r in rows:
        line, ci, cells = [], 0, list(r)
        while cells or ci in carry:
            if ci in carry:
                cell, left = carry[ci]
                line.append(cell)
                if left > 1:
                    carry[ci] = (cell, left - 1)
                else:
                    del carry[ci]
                ci += 1
                continue
            c = cells.pop(0)
            for _ in range(c["cs"]):
                line.append(c)
                if c["rs"] > 1:
                    carry[ci] = (c, c["rs"] - 1)
                ci += 1
        out.append(line)
    return out


def columns(header):
    idx = {}
    for i, h in enumerate(header):
        if re.search(r"kapaz|capac|platze|zuschau|schnitt|attend|locuri", h):
            idx.setdefault("cap", i)
        elif re.search(r"stadi|spielst|ground|arena|venue|heimst|teren|sportst|\bstade\b|baza", h):
            idx.setdefault("stad", i)
        elif re.search(r"verein|mannschaft|team|club|echip|klub|^nume$|denumire", h):
            idx.setdefault("club", i)
        elif re.search(r"\bort\b|location|stadt|city|localit|oras|sitz|town|judet|county|spielort|\bville\b|plaats", h):
            idx.setdefault("loc", i)
    return idx


def tables_of(page_html):
    p = TP()
    try:
        p.feed(page_html)
    except Exception as e:
        log(f"PARSE {type(e).__name__} {str(e)[:80]}")
    out = []
    for t in p.tables:
        g = grid(t["rows"])
        hi = next((i for i, r in enumerate(g) if len(r) >= 2 and sum(1 for c in r if c["th"]) * 2 >= len(r)), None)
        if hi is None or len(g) - hi < 3:
            continue
        header = [fold(ctext(c)) for c in g[hi]]
        out.append({"header": header, "rows": [r for r in g[hi + 1:] if any(not c["th"] for c in r)], "cols": columns(header)})
    return out


def qids_for(host, titles):
    """title -> Q-id through pageprops, redirects followed."""
    res, titles = {}, sorted(set(titles))
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        d = wm(host, {"action": "query", "prop": "pageprops", "ppprop": "wikibase_item", "redirects": "1", "titles": "|".join(batch)})
        if not d:
            continue
        q = d.get("query", {})
        norm = {x["from"]: x["to"] for x in q.get("normalized", [])}
        red = {x["from"]: x["to"] for x in q.get("redirects", [])}
        item = {pg["title"]: (pg.get("pageprops") or {}).get("wikibase_item") for pg in q.get("pages", [])}
        for t in batch:
            t2 = norm.get(t, t)
            t3 = red.get(t2, t2)
            if item.get(t3):
                res[t] = item[t3]
    return res


def nname(s):
    s = re.sub(r"\([^)]*\)", " ", s or "")
    s = fold(s)
    s = re.sub(r"\b(u ?23|u ?21|u ?19|2)$", "ii", s)
    return s.strip()


def name_match(a, b):
    a, b = nname(a), nname(b)
    if not a or not b:
        return False
    if a == b:
        return True
    ta, tb = set(a.split()), set(b.split())
    if ("ii" in ta) != ("ii" in tb) or ("b" in ta) != ("b" in tb):
        return False
    small, big = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    return small <= big and len([x for x in small if len(x) >= 3 and x != "ii"]) >= 2


def gtok(s):
    s = fold(re.sub(r"\([^)]*\)", " ", s or ""))
    t = set(s.split())
    return (t - GENERIC) or t


def gscore(a, b):
    ta, tb = gtok(a), gtok(b)
    if not ta or not tb:
        return 0
    if ta == tb:
        return 3 if fold(a) == fold(b) else 2.5
    if ta <= tb or tb <= ta:
        return 2
    j = len(ta & tb) / len(ta | tb)
    return 1 if j >= 0.5 else 0


def read_article(lang, title):
    host = f"{lang}.wikipedia.org"
    d = wm(host, {"action": "parse", "page": title, "prop": "text|wikitext", "redirects": "1"})
    if not d or "parse" not in d:
        return None
    pr = d["parse"]
    wt = pr.get("wikitext") or ""
    wd = len(re.findall(r"\{\{\s*#(?:property|statements|invoke:\s*(?:Wikidata|Wd))|\{\{\s*(?:Wikidata|Wd|Wdib)\s*\|", wt, re.I))
    tabs = tables_of(pr.get("text") or "")
    titles = set()
    for t in tabs:
        for r in t["rows"]:
            for c in r:
                titles.update(c["links"])
    qm = qids_for(host, titles)
    return {"lang": lang, "title": pr.get("title") or title, "tabs": tabs, "qm": qm, "wd": wd, "len": len(wt)}


def search_titles(lang, q):
    d = wm(f"{lang}.wikipedia.org", {"action": "query", "list": "search", "srsearch": q, "srlimit": "8"})
    return [x["title"] for x in (d or {}).get("query", {}).get("search", [])]


def cut(s, n):
    s = re.sub(r"\s+", " ", s or "")
    return s if len(s) <= n else s[:n - 1] + "~"


def stage_a(scope):
    arts = {"DE": [("de", "3. Fußball-Liga 2026/27"), ("de", "Fußball-Regionalliga 2026/27"),
                   ("de", "Fußball-Regionalliga Bayern 2026/27"), ("de", "Fußball-Regionalliga Nord 2026/27"),
                   ("de", "Fußball-Regionalliga Nordost 2026/27"), ("de", "Fußball-Regionalliga Südwest 2026/27"),
                   ("de", "Fußball-Regionalliga West 2026/27"), ("en", "2026–27 3. Liga"), ("en", "2026–27 Regionalliga")],
            "RO": [("ro", "Liga a III-a 2026-2027"), ("ro", "Liga III 2026-2027"), ("en", "2026–27 Liga III")]}
    lines, n = [], 0
    for cc, lst in arts.items():
        clubs = [c for c in scope if c["cc"] == cc]
        byq = {c["q"]: c for c in clubs}
        got_local = False
        for lang, title in lst:
            n += 1
            a = read_article(lang, title)
            if not a:
                lines.append(f"ART {n} {lang}:{title} NOT READ")
                if lang == "ro" and title.startswith("Liga III"):
                    lines.append("  ro search: " + " ; ".join(search_titles("ro", "Liga a III-a 2026-2027")))
                continue
            gt = [t for t in a["tabs"] if "stad" in t["cols"]]
            lines.append(f"ART {n} {lang}:{a['title']} wikitext {a['len']} ch, wikitables {len(a['tabs'])}, grounds tables {len(gt)} "
                         f"({sum(len(t['rows']) for t in gt)} rows), wikidata calls in wikitext {a['wd']}")
            for t in a["tabs"]:
                isg = "stad" in t["cols"]
                sig = cut("/".join(h for h in t["header"] if h)[:60], 60)
                ccol = t["cols"].get("club", 0)
                for r in t["rows"]:
                    cells = [r[ccol]] if (isg and ccol < len(r)) else r
                    qs = {a["qm"].get(l) for c in cells for l in c["links"]} - {None}
                    hit = [byq[q] for q in qs if q in byq]
                    how = "Q"
                    if not hit and isg and ccol < len(r):
                        nm = ctext(r[ccol])
                        hit = [c for c in clubs if name_match(c["n"], nm)]
                        how = "~" + cut(nm, 30)
                    elif not hit and not isg:
                        for c in r[:3]:
                            nm = ctext(c)
                            if 3 < len(nm) < 45:
                                hit += [x for x in clubs if nname(x["n"]) == nname(nm)]
                        how = "~"
                    for c in hit:
                        if isg:
                            sc = r[t["cols"]["stad"]] if t["cols"]["stad"] < len(r) else None
                            lc = r[t["cols"]["loc"]] if t["cols"].get("loc", 99) < len(r) else None
                            c.setdefault("G", []).append({"art": n, "lang": lang, "how": how, "ground": ctext(sc) if sc else "",
                                                           "glink": (sc["links"][:1] or [""])[0] if sc else "", "loc": ctext(lc) if lc else ""})
                        else:
                            c.setdefault("T", {}).setdefault(n, set()).add(sig[:34])
    post_chunks(f"RUN {RUN} A0 articles", lines)
    rows, cnt = [], {}
    for c in scope:
        loc = [g for g in c.get("G", []) if g["lang"] != "en"]
        en = [g for g in c.get("G", []) if g["lang"] == "en"]

        def verdict(gs):
            if not gs:
                return None
            best = max(gs, key=lambda g: gscore(c["v"], g["ground"]))
            best["s"] = gscore(c["v"], best["ground"])
            return best
        bl, be = verdict(loc), verdict(en)
        c["bl"], c["be"] = bl, be
        ref = bl or be
        if ref:
            st = "AGREE" if ref["s"] >= 2 else "DIFF"
            if bl and be and (bl["s"] >= 2) != (be["s"] >= 2):
                st += "(wikis split)"
        else:
            st = "NOT-IN-TABLE" if c.get("T") else "ABSENT"
        c["A"] = st
        cnt[st] = cnt.get(st, 0) + 1

        def show(g):
            if not g:
                return "-"
            gl = f" [{cut(g['glink'], 34)}]" if g["glink"] and fold(g["glink"]) != fold(g["ground"]) else ""
            return f"#{g['art']}{'' if g['how'] == 'Q' else g['how']} {cut(g['ground'], 44)}{gl} @{cut(g['loc'], 22)} s{g['s']}"
        if st == "AGREE" and (not be or be["s"] >= 2):
            rows.append(f"{c['q']}|{cut(c['n'], 26)}|{c['t']}|AGREE|{cut(c['v'], 34)}|{'#%d' % ref['art']}{'' if ref['how'] == 'Q' else '~'} s{ref['s']}{'' if ref['s'] >= 3 else ' ' + cut(ref['ground'], 40)}")
        else:
            tabs = "; ".join(f"#{k}:{'+'.join(sorted(v))}" for k, v in sorted(c.get("T", {}).items()))
            rows.append(f"{c['q']}|{cut(c['n'], 26)}|{c['t']}|{st}|{cut(c['v'], 40)}|L {show(bl)}|EN {show(be)}" + (f"|other tables {cut(tabs, 150)}" if not ref else ""))
    rows.sort(key=lambda r: (r.split("|")[3].startswith("AGREE"), r.split("|")[3]))
    post_chunks(f"RUN {RUN} A1 grounds {json.dumps(cnt)}", rows)


def osm_http(url, data=None, key="osm"):
    for attempt in range(5):
        with LOCK:
            now = time.time()
            at = max(now, LAST.get(key, 0) + 1.25)
            LAST[key] = at
            NREQ[key] = NREQ.get(key, 0) + 1
        if at > now:
            time.sleep(at - now)
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": OSM_UA, "Accept-Language": "en"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read(30_000_000))
        except urllib.error.HTTPError as e:
            log(f"OSM HTTP {e.code} {key} try {attempt}")
            if e.code in (429, 502, 503, 504) and attempt < 4:
                time.sleep(20 * (2 ** attempt))
                continue
            return None
        except Exception as e:
            log(f"OSM ERR {key} {type(e).__name__} {str(e)[:80]}")
            if attempt >= 2:
                return None
            time.sleep(15)
    return None


def hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(x))


def rx_tokens(names):
    toks = []
    for nm in names:
        ws = [w for w in re.split(r"[^\w]+", re.sub(r"\([^)]*\)", " ", nm or "")) if len(w) >= 4 and fold(w) not in GENERIC and not w.isdigit()]
        ws.sort(key=len, reverse=True)
        for w in ws[:2]:
            t = "".join(ch if (ch.isascii() and ch.isalnum()) else "." for ch in w)
            if t not in toks:
                toks.append(t)
    return "|".join(toks[:4])


def overpass_club(c, names):
    lat, lon = c["lat"], c["lon"]
    rx = rx_tokens(names)
    q = f'[out:json][timeout:60];(nwr["leisure"~"^(stadium|pitch)$"]["name"](around:3000,{lat},{lon});'
    if rx:
        q += f'nwr["leisure"]["name"~"{rx}",i](around:3000,{lat},{lon});nwr["building"]["name"~"{rx}",i](around:3000,{lat},{lon});'
    q += ");out tags center 1500;"
    d = osm_http(OVERPASS, data=urllib.parse.urlencode({"data": q}).encode(), key="overpass")
    if d is None:
        return None
    out = []
    for e in d.get("elements", []):
        tg = e.get("tags") or {}
        la = e.get("lat", (e.get("center") or {}).get("lat"))
        lo = e.get("lon", (e.get("center") or {}).get("lon"))
        if la is None:
            continue
        nms = []
        for k in ("name", "alt_name", "official_name", "short_name", "old_name", "loc_name", "name:de", "name:ro", "name:en"):
            nms += [x.strip() for x in (tg.get(k) or "").split(";") if x.strip()]
        kind = tg.get("leisure") or ("building=" + tg.get("building", "?"))
        rank = 3 if tg.get("leisure") == "stadium" else 2 if (tg.get("leisure") in ("sports_centre", "track") or "building" in tg) else 1
        out.append({"id": f"{e['type']}/{e['id']}", "names": nms, "kind": kind, "rank": rank, "lat": la, "lon": lo,
                    "d": hav(lat, lon, la, lo), "sport": tg.get("sport", "")})
    return out


def best_match(els, name):
    best = None
    for e in els:
        s = max((gscore(name, n) for n in e["names"]), default=0)
        if s <= 0:
            continue
        key = (s, e["rank"], -e["d"])
        if best is None or key > best[0]:
            best = (key, e, s)
    if not best:
        return None
    same = sum(1 for e in els if max((gscore(name, n) for n in e["names"]), default=0) == best[2])
    e = dict(best[1])
    e["s"], e["same"] = best[2], same
    return e


def nominatim(q, cc, lat, lon):
    url = NOMINATIM + "?" + urllib.parse.urlencode({"q": q, "format": "jsonv2", "limit": "5", "countrycodes": cc.lower()})
    d = osm_http(url, key="nominatim")
    if d is None:
        return "nominatim failed"
    if not d:
        return "nominatim: nothing"
    r = min(d, key=lambda x: hav(lat, lon, float(x["lat"]), float(x["lon"])))
    return (f"nominatim({len(d)}) {r.get('osm_type')}/{r.get('osm_id')} {r.get('category')}={r.get('type')} "
            f"\"{cut(r.get('display_name'), 70)}\" {float(r['lat']):.6f},{float(r['lon']):.6f} {hav(lat, lon, float(r['lat']), float(r['lon'])):.0f}m")


def fmt(e):
    return f"{e['id']} {e['kind']} \"{cut(e['names'][0] if e['names'] else '', 44)}\" s{e['s']}x{e['same']} {e['lat']:.6f},{e['lon']:.6f} {e['d']:.0f}m"


def stage_b(scope, only=None):
    rows, cnt = [], {}
    for c in scope:
        if only is not None and c["q"] not in only:
            continue
        if time.time() > DEADLINE:
            rows.append(f"{c['q']}|{c['n']}|NOT REACHED (time)")
            continue
        ref = c.get("bl") or c.get("be")
        alt = ref["ground"] if (ref and ref.get("s", 3) < 2 and ref["ground"]) else (c.get("alt") or "")
        town = (ref or {}).get("loc") or c.get("town") or ""
        els = overpass_club(c, [c["v"]] + ([alt] if alt else []))
        if els is None:
            cnt["OVERPASS-FAILED"] = cnt.get("OVERPASS-FAILED", 0) + 1
            rows.append(f"{c['q']}|{cut(c['n'], 26)}|OVERPASS-FAILED|{cut(c['v'], 40)}")
            continue
        m = best_match(els, c["v"])
        extra = ""
        if m and m["s"] >= 2:
            st = "WITHIN" if m["d"] < 500 else "DIFFERS"
            extra = fmt(m)
        else:
            st = "NOTFOUND"
            extra = (("weak " + fmt(m) + " ; ") if m else "") + f"{len(els)} named els ; " + nominatim(f"{c['v']}, {town}" if town else c["v"], c["cc"], c["lat"], c["lon"])
        if alt:
            ma = best_match(els, alt)
            extra += " || ALT \"" + cut(alt, 40) + "\": " + (fmt(ma) if ma and ma["s"] >= 2 else ("none in 3 km ; " + nominatim(f"{alt}, {town}" if town else alt, c["cc"], c["lat"], c["lon"])))
        cnt[st] = cnt.get(st, 0) + 1
        rows.append(f"{c['q']}|{cut(c['n'], 26)}|{st}|{cut(c['v'], 40)}|{extra}")
    rows.sort(key=lambda r: {"WITHIN": 9}.get(r.split("|")[2], 0))
    post_chunks(f"RUN {RUN} B coordinates {json.dumps(cnt)}", rows)


# ---------- Part C and later runs: season rows, wiki passages, club pages ----------

def season_rows(lang, title, pat):
    a = read_article(lang, title)
    if not a:
        return [f"{lang}:{title} NOT READ"]
    out = [f"{lang}:{a['title']} wikitables {len(a['tabs'])}, wikidata calls {a['wd']}"]
    for t in a["tabs"]:
        if "stad" not in t["cols"]:
            continue
        for r in t["rows"]:
            line = " | ".join(cut(ctext(x), 60) for i, x in enumerate(r) if i == 0 or x is not r[i - 1])
            if re.search(pat, line, re.I):
                out.append("  [" + cut("/".join(t["header"]), 70) + "] " + cut(line, 260))
    return out


def wiki_passages(lang, title, pat, cap=8):
    d = wm(f"{lang}.wikipedia.org", {"action": "parse", "page": title, "prop": "wikitext", "redirects": "1"})
    if not d or "parse" not in d:
        return [f"{lang}:{title} NOT READ"]
    wt = d["parse"].get("wikitext") or ""
    out, seen = [f"{lang}:{d['parse'].get('title')} ({len(wt)} ch)"], set()
    for m in re.finditer(pat, wt, re.I):
        s = re.sub(r"\s+", " ", wt[max(0, m.start() - 170):m.end() + 230])
        k = s[60:160]
        if k in seen:
            continue
        seen.add(k)
        out.append("  ..." + s + "...")
        if len(out) > cap:
            break
    return out


ROBOTS = {}


def allowed(url):
    p = urllib.parse.urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in ROBOTS:
        info = {"rp": None, "note": "", "stop": ""}
        try:
            st, _, body, _ = http(base + "/robots.txt", p.netloc, 1.0)
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(body.decode("utf-8", "replace").splitlines())
            info["rp"] = rp
            info["note"] = f"robots.txt {st}"
        except urllib.error.HTTPError as e:
            info["note"] = f"robots.txt {e.code}"
            if e.code in (401, 403):
                info["stop"] = f"robots.txt {e.code}"
        except Exception as e:
            info["note"] = f"robots.txt {type(e).__name__}"
            info["stop"] = info["note"]
        if not info["stop"]:
            try:
                st, _, body, final = http(base + "/", p.netloc, 1.0)
                _, _, links = page_text(body)
                tl = next((urllib.parse.urljoin(final, h) for h, x in links if TERMS.search(h) or TERMS.search(re.sub(r"<[^>]+>", " ", x))), None)
                if tl and urllib.parse.urlparse(tl).netloc == p.netloc and (not info["rp"] or info["rp"].can_fetch(UA, tl)):
                    st2, _, b2, _ = http(tl, p.netloc, 1.0)
                    _, t2, _ = page_text(b2)
                    ban = BAN.search(t2)
                    info["note"] += f"; terms {tl} read: " + (f"POSSIBLE BAN: {ban.group(0).strip()[:240]}" if ban else "no automated-access wording")
                    if ban:
                        info["stop"] = "terms"
                else:
                    info["note"] += "; no terms link on the root page"
            except Exception as e:
                info["note"] += f"; root {type(e).__name__} {str(e)[:50]}"
        ROBOTS[base] = info
    info = ROBOTS[base]
    if info["stop"]:
        return False, "STOP " + info["stop"] + " (" + info["note"] + ")"
    if info["rp"] and not info["rp"].can_fetch(UA, url):
        return False, "STOP robots.txt disallows (" + info["note"] + ")"
    return True, info["note"]


def snips(text, pat, cap=6, w=110):
    out, seen = [], set()
    for m in re.finditer(pat, text, re.I):
        s = text[max(0, m.start() - w):m.end() + w].strip()
        k = s[w // 2:w // 2 + 60]
        if k in seen:
            continue
        seen.add(k)
        out.append("    ..." + s + "...")
        if len(out) >= cap:
            break
    return out


def read_page(url, pat, follow=None, cap=6, depth=1):
    """One page: robots and terms first, plain fetch, a browser when the plain text is thin. follow = regex on links to open next (same host)."""
    ok, note = allowed(url)
    out = [f"PAGE {url} :: {note}"]
    if not ok:
        return out
    host = urllib.parse.urlparse(url).netloc
    try:
        st, _, body, final = http(url, host, 1.0)
        title, text, links = page_text(body)
        links = [(urllib.parse.urljoin(final, h), re.sub(r"<[^>]+>|\s+", " ", x).strip()[:60]) for h, x in links]
    except urllib.error.HTTPError as e:
        st, final, title, text, links = e.code, url, "", "", []
    except Exception as e:
        st, final, title, text, links = type(e).__name__, url, "", "", []
    how = "plain"
    if st != 200 or len(text) < 600 or not re.search(pat, text, re.I):
        st2, final2, title2, text2, links2 = rendered(url)
        if str(st2) == "200" and len(text2) > len(text):
            st, final, title, text, links, how = st2, final2, title2, text2, [(a, b) for a, b in links2], "browser"
    hits = snips(text, pat, cap)
    out.append(f"  {st} {how} final={final} title=\"{title}\" text {len(text)} ch, hits {len(hits)}")
    out += hits
    if follow and depth > 0:
        nxt, seen = [], set()
        for h, x in links:
            if urllib.parse.urlparse(h).netloc != urllib.parse.urlparse(final).netloc or h.split("#")[0] in seen:
                continue
            if re.search(follow, h, re.I) or re.search(follow, x, re.I):
                seen.add(h.split("#")[0])
                nxt.append(h.split("#")[0])
        out.append(f"  links matching /{follow}/: {len(nxt)} " + " ".join(nxt[:8]))
        for h in nxt[:5]:
            if h.rstrip("/") != final.rstrip("/"):
                out += read_page(h, pat, None, cap, 0)
    return out


def websites(qids):
    d = wm("www.wikidata.org", {"action": "wbgetentities", "ids": "|".join(qids), "props": "claims"}) or {}
    res = {}
    for q, e in (d.get("entities") or {}).items():
        for cl in (e.get("claims") or {}).get("P856", []):
            v = ((cl.get("mainsnak") or {}).get("datavalue") or {}).get("value")
            if v and cl.get("rank") != "deprecated":
                res.setdefault(q, []).append(v)
    return res


def stage_c(T):
    lines = []
    for lang, title, pat in T.get("season_rows", []):
        lines += season_rows(lang, title, pat)
    for lang, title, pat in T.get("passages", []):
        lines += wiki_passages(lang, title, pat)
    sites = websites(T["site_of"]) if T.get("site_of") else {}
    for q, (pat, follow) in (T.get("site_of") or {}).items():
        lines.append(f"SITE {q}: P856 {sites.get(q)}")
        for u in (sites.get(q) or [])[:1]:
            lines += read_page(u, pat, follow)
    for url, pat, follow in T.get("pages", []):
        lines += read_page(url, pat, follow)
    for name, cc, lat, lon in T.get("nominatim", []):
        lines.append(f"NOMINATIM \"{name}\": " + nominatim(name, cc, lat, lon))
    post_chunks(f"RUN {RUN} C pages", [cut(x, 700) for x in lines])


def main():
    T = json.load(open(os.path.join(HERE, "targets.json"), encoding="utf-8"))
    scope = T["scope"]
    try:
        if "A" in STAGES:
            stage_a(scope)
        if "B" in STAGES:
            stage_b(scope, set(T["only_b"]) if T.get("only_b") else None)
        if "C" in STAGES:
            stage_c(T)
    except Exception as e:
        import traceback
        post(f"RUN {RUN} CRASH\n```\n{traceback.format_exc()[-3000:]}\n```")
        raise
    finally:
        post(f"RUN {RUN} DONE requests {json.dumps(NREQ)} lag waits {json.dumps(WAITED)} elapsed {int(time.time() - T0)} s\n```\n" + "\n".join(LOG[-40:])[:6000] + "\n```")


if __name__ == "__main__":
    main()
