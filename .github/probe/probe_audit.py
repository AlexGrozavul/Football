#!/usr/bin/env python3
"""TEMPORARY - capacity audit, phase 1d. Removed before the merge. Commits nothing.

Reads, for the clubs in targets.json: the ground's Wikipedia article (local wiki and
English; it.wikipedia for every Italian club), the references cited on the capacity
line, StadiumDB's country tables, and pages a link list names (the ground's external
links, the league's own club pages found from the league site's root).
Wikimedia: one request per second, maxlag=5, never raised; on a lag refusal the probe
waits (the larger of Retry-After and 10 s doubling up to 5 minutes) and retries.
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

def wikidata(clubs):
    ids = [c["q"] for c in clubs]
    ent = {}
    for i in range(0, len(ids), 50):
        d = wm("www.wikidata.org", {"action": "wbgetentities", "ids": "|".join(ids[i:i + 50]), "props": "claims"})
        if d is None:
            return False
        ent.update(d.get("entities", {}))
    venues = {}
    for c in clubs:
        c["p115"] = []
        for st in ent.get(c["q"], {}).get("claims", {}).get("P115", []):
            v = st.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
            if v:
                c["p115"].append((v, st.get("rank"), "P582" in st.get("qualifiers", {})))
                venues[v] = None
    vids = sorted(venues)
    for i in range(0, len(vids), 50):
        d = wm("www.wikidata.org", {"action": "wbgetentities", "ids": "|".join(vids[i:i + 50]),
                                    "props": "labels|aliases|sitelinks|claims"})
        if d is None:
            return False
        venues.update(d.get("entities", {}))
    for c in clubs:
        want, pick, how = fold(c["venue"]), None, ""
        for v, rank, ended in c["p115"]:
            e = venues.get(v) or {}
            names = [x["value"] for x in e.get("labels", {}).values()]
            names += [a["value"] for al in e.get("aliases", {}).values() for a in al]
            if want and want in {fold(n) for n in names}:
                pick, how = v, "label"
                break
        if not pick and len(c["p115"]) == 1:
            pick, how = c["p115"][0][0], "only P115"
        if not pick and c["p115"]:
            live = [x for x in c["p115"] if not x[2] and x[1] != "deprecated"]
            pref = [x for x in live if x[1] == "preferred"] or live or c["p115"]
            pick, how = pref[0][0], f"first of {len(c['p115'])} (no label match)"
        c["wd"] = {"venueQ": pick, "how": how, "n115": len(c["p115"])}
        del c["p115"]
        if pick:
            e = venues.get(pick) or {}
            c["titles"] = {k[:-4].replace("_", "-"): v["title"] for k, v in e.get("sitelinks", {}).items()
                           if k.endswith("wiki") and k not in ("commonswiki", "specieswiki")}
            caps = []
            for st in e.get("claims", {}).get("P1083", []):
                amt = st.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("amount", "")
                when = [q.get("datavalue", {}).get("value", {}).get("time", "")[1:5]
                        for q in st.get("qualifiers", {}).get("P585", [])]
                caps.append(f"{amt.lstrip('+')}/{st.get('rank', '')[:4]}/{','.join(when)}")
            c["wd"]["P1083"] = caps
    return True


def by_name(clubs):
    """Fallback when Wikidata stayed lagged: the ground's English article by its name, and its language links."""
    for c in clubs:
        if c.get("titles") or not c.get("venue"):
            continue
        d = wm("en.wikipedia.org", {"action": "query", "titles": c["venue"], "redirects": "1",
                                    "prop": "langlinks", "lllimit": "500"})
        pages = (d or {}).get("query", {}).get("pages", [])
        if pages and not pages[0].get("missing"):
            c["titles"] = {"en": pages[0]["title"]}
            for ll in pages[0].get("langlinks", []):
                c["titles"][ll["lang"]] = ll["title"]
            c["wd"] = {"how": "by name on en.wikipedia (Wikidata lagged)"}
        else:
            c["wd"] = {"how": "not found by name (Wikidata lagged)"}


def via_club(c):
    """The ground's article from the ground link of the club's own English infobox, then its language links."""
    d = wm("en.wikipedia.org", {"action": "parse", "page": c["clubtitle"], "prop": "wikitext", "section": "0", "redirects": "1"})
    wt = (d or {}).get("parse", {}).get("wikitext", "")
    m = re.search(r"^\s*\|\s*(?:ground|stadium)\s*=\s*[^\n]*?\[\[([^\]|#]+)", wt, re.I | re.M)
    if not m:
        c["wd"] = {"how": f"no ground link in the infobox of en.wikipedia {c['clubtitle']}"}
        return
    d = wm("en.wikipedia.org", {"action": "query", "titles": m.group(1).strip(), "redirects": "1", "prop": "langlinks", "lllimit": "500"})
    pages = (d or {}).get("query", {}).get("pages", [])
    if pages and not pages[0].get("missing"):
        c["titles"] = {"en": pages[0]["title"]}
        for ll in pages[0].get("langlinks", []):
            c["titles"][ll["lang"]] = ll["title"]
        c["wd"] = {"how": f"ground link of the club's English infobox ({c['clubtitle']} -> {pages[0]['title']})"}
    else:
        c["wd"] = {"how": f"ground link {m.group(1)} has no article"}


# ---------- Wikipedia: the capacity line, the sentences, the references ----------

def first_url(s):
    m = re.search(r"(?<![a-z-])url\s*=\s*(https?://[^\s|\]}<\"]+)", s) or re.search(r"https?://[^\s|\]}<\"]+", s)
    a = re.search(r"archive-?url\s*=\s*(https?://[^\s|\]}<\"]+)", s)
    u = (m.group(1) if m and m.groups() else m.group(0)) if m else ""
    return u, (a.group(1) if a else "")


def mark_refs(wt, refs):
    named = {}
    for m in re.finditer(r"<ref\s+[^>/]*name\s*=\s*\"?([^\">/]+?)\"?\s*(?:group[^>]*)?>(.*?)</ref>", wt, re.S):
        named[m.group(1).strip()] = m.group(2)

    def rep(m, full=True):
        if full:
            body = m.group(1)
        else:
            nm = re.search(r"name\s*=\s*\"?([^\">/]+)", m.group(0))
            body = named.get(nm.group(1).strip(), "") if nm else ""
        u, a = first_url(body)
        txt = re.sub(r"\s+", " ", re.sub(r"[{}\[\]|]", " ", body))[:70]
        refs.append((u, a))
        return f" [REF{len(refs) - 1}: {u or txt}] "
    wt = re.sub(r"<ref\s[^>]*?/\s*>", lambda m: rep(m, False), wt)
    return re.sub(r"<ref(?:\s[^>]*)?>(.*?)</ref>", rep, wt, flags=re.S)


def tidy(s):
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{(?:formatnum|nts|nowrap|small|nobr)\s*[:|]\s*([^{}]*)\}\}", r"\1", s, flags=re.I)
    s = re.sub(r"'{2,}|<br\s*/?>|</?small>|&nbsp;", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def article(lang, title):
    d = wm(f"{lang}.wikipedia.org", {"action": "parse", "page": title, "prop": "wikitext|externallinks", "redirects": "1"})
    if not d or "parse" not in d:
        return None
    wt, refs = d["parse"]["wikitext"], []
    wt = mark_refs(re.sub(r"<!--.*?-->", "", wt, flags=re.S), refs)
    out = {"title": d["parse"]["title"], "lines": [], "body": [], "web": ""}
    head = wt[:60000]
    for m in re.finditer(r"^\s*\|\s*([^=|\n]{0,40}?(?:capac|kapaz|kapac|aforo|posti|capien|χωρητικ|капацитет|pl[aä]tze|lotaç|seating|zuschauer|toeschouw)[^=|\n]{0,30})=([^\n]*(?:\n(?!\s*[|}])[^\n]*){0,6})", head, re.I | re.M):
        val = tidy(m.group(2))
        if re.search(r"\d", val):
            out["lines"].append(f"{m.group(1).strip()} = {val[:520]}")
    if not out["lines"]:
        out["keys"] = [k.strip() for k in re.findall(r"^\s*\|\s*([^=|\n{}\[\]]{1,28})=", head, re.M)][:60]
    if lang == "it":
        h = wm("it.wikipedia.org", {"action": "parse", "page": title, "prop": "text", "section": "0", "redirects": "1"})
        htm = (h or {}).get("parse", {}).get("text", "")
        for th, td in re.findall(r"<tr[^>]*>\s*<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", htm, re.S):
            tht = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", th))).strip()
            if re.search(r"posti|capien|spettator", tht, re.I):
                tdt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<sup.*?</sup>", " ", td, flags=re.S)))).strip()
                out["lines"].append(f"RENDERED INFOBOX ROW {tht} = {tdt[:300]}")
    w = re.search(r"^\s*\|\s*(?:website|homepage|sito|site|web|url)[^=\n]{0,20}=\s*[^\n]*?(https?://[^\s|\]}<\"]+)", head, re.I | re.M)
    out["web"] = w.group(1) if w else ""
    wt2 = re.sub(r"\{\{\s*(?:formatnum|M|TA|nts|tutto attaccato|unité|nombre|esd|nowrap|val)\s*[:|]\s*([\d .,\u00a0]+)(?:\|[^{}]*)?\}\}", r"\1", wt, flags=re.I)
    text = tidy(re.sub(r"\{\{[^{}]*\}\}", " ", re.sub(r"\{\|.*?\|\}", " ", wt2, flags=re.S)))
    text = re.sub(r"(?<=\d)\.(?=\d{3}(?!\d))", "\u00a0", text)
    for m in re.finditer(rf"[^.!?|=]{{0,170}}(?:{KEY})[^.!?|=]{{0,170}}", text, re.I):
        s = m.group(0).strip()
        if re.search(NUM, s) and len(out["body"]) < 5 and not any(s[:40] == b[:40] for b in out["body"]):
            out["body"].append(s[:330])
    used = sorted({int(x) for ln in out["lines"] + out["body"] for x in re.findall(r"\[REF(\d+):", ln)})
    out["refs"] = {str(i): list(refs[i]) for i in used if refs[i][0] or refs[i][1]}
    out["lineref"] = [refs[int(x)] for ln in out["lines"] for x in re.findall(r"\[REF(\d+):", ln) if refs[int(x)][0] or refs[int(x)][1]]
    out["bodyref"] = [refs[int(x)] for ln in out["body"] for x in re.findall(r"\[REF(\d+):", ln) if refs[int(x)][0]]
    out["ext"] = [u for u in d["parse"].get("externallinks", []) if u.startswith("http")]
    return out


# ---------- other hosts ----------

def forms(n):
    s = str(n)
    if len(s) < 4:
        return [s]
    a, b = s[:-3], s[-3:]
    return [s] + [a + sep + b for sep in ".,   '’"]


def page_text(body):
    t = body.decode("utf-8", "replace")
    title = re.search(r"<title[^>]*>(.*?)</title>", t, re.S | re.I)
    links = re.findall(r"<a\s[^>]*?href\s*=\s*[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", t, re.S | re.I)
    t = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    return (html.unescape(title.group(1)).strip()[:90] if title else ""), t, links


def snippets(text, figs, cap=6):
    out = []

    def add(a, b, tag):
        s = text[max(0, a):b].strip()
        if len(out) < cap and not any(s[20:70] in o for o in out):
            out.append(tag + s)
    for f in figs:
        for fm in forms(f):
            for m in re.finditer(rf"(?<![\d.,]){re.escape(fm)}(?![\d])", text):
                add(m.start() - 110, m.end() + 80, f"<{f}> ")
                break
    for m in re.finditer(KEY, text, re.I):
        win = text[max(0, m.start() - 70):m.end() + 90]
        if re.search(NUM, win):
            add(m.start() - 90, m.end() + 120, "")
    return out


RENDER = set()


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


class Host:
    def __init__(self, host):
        self.host, self.stop, self.rp, self.txt, self.done = host, "", None, "", False
        self.rootlinks, self.terms = [], ""
        self.lock = threading.RLock()
        self.render = host.replace("www.", "") in RENDER

    def get(self, url):
        try:
            st, hdr, body, final = http(url, self.host, 1.0)
            return st, body, final, hdr.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            return e.code, b"", url, ""
        except Exception as e:
            return f"{type(e).__name__}", b"", url, ""

    def read(self, url):
        """status, final URL, title, text, links - by plain HTTP, or in a browser for the hosts that need one."""
        if self.render:
            with self.lock:
                time.sleep(1.0)
                return rendered(url)
        st, body, final, ctype = self.get(url)
        if st != 200:
            return st, final, "", "", []
        if "pdf" in ctype.lower() or body[:4] == b"%PDF":
            return "200 pdf (not read)", final, "", "", []
        title, text, links = page_text(body)
        return st, final, title, text, links

    def open(self, scheme):
        with self.lock:
            if not self.done:
                self._open(scheme)
                self.done = True

    def _open(self, scheme):
        """robots.txt, then the root page and the terms page it links."""
        st, body, _, _ = self.get(f"{scheme}://{self.host}/robots.txt")
        if st in (403, 429, 503) or (not isinstance(st, int)):
            self.stop = f"robots.txt {st}"
            return
        if st == 200 and b"<html" not in body[:400].lower():
            self.txt = body.decode("utf-8", "replace")
            self.rp = urllib.robotparser.RobotFileParser()
            self.rp.parse(self.txt.splitlines())
        root = f"{scheme}://{self.host}/"
        if not self.allowed(root):
            return
        st, final, title, text, links = self.read(root)
        if st in (403, 429, 503):
            self.stop = f"root {st}"
            return
        if st == 200:
            if re.search(r"just a moment|attention required|access denied|verify you are human|checking your browser", title + text[:600], re.I):
                self.stop = "bot challenge on root"
                return
            self.rootlinks = [(urllib.parse.urljoin(final, h), re.sub(r"<[^>]+>|\s+", " ", x).strip()[:60]) for h, x in links]
            for u, x in self.rootlinks:
                if urllib.parse.urlparse(u).netloc.endswith(self.host.replace("www.", "")) and TERMS.search(u + " " + x) and self.allowed(u):
                    s2, _, _, t2, _ = self.read(u)
                    if s2 == 200:
                        ban = BAN.search(t2)
                        self.terms = f"{u} read; " + (f"POSSIBLE BAN: {ban.group(0).strip()[:300]}" if ban else "no automated-access wording found")
                        if ban and self.host not in TERMSOK:
                            self.stop = "terms: " + self.terms[:380]
                    else:
                        self.terms = f"{u} {s2}"
                    break

    def allowed(self, url):
        if not self.rp:
            return True
        low = self.txt.lower()
        agents = ["FootballPlannerBot"] + [a for a in ANTHROPIC if a in low]
        return all(self.rp.can_fetch(a, url) for a in agents)

    def page(self, url, figs, want_links=False, cap=6):
        res = {"url": url}
        if self.stop:
            res["st"] = "STOP " + self.stop
            return res, []
        if not self.allowed(url):
            res["st"] = "STOP robots.txt disallows"
            return res, []
        st, final, title, text, links = self.read(url)
        res["st"] = st
        if st in (403, 429, 503):
            self.stop = f"HTTP {st}"
            return res, []
        if st != 200:
            return res, []
        if urllib.parse.urlparse(final).netloc != urllib.parse.urlparse(url).netloc:
            res["redirected"] = final[:140]
            if urllib.parse.urlparse(final).netloc.replace("www.", "") != self.host.replace("www.", ""):
                res["st"] = "STOP redirect to another host"
                return res, []
        if re.search(r"just a moment|attention required|verify you are human|checking your browser", title + text[:400], re.I):
            self.stop = "bot challenge"
            res["st"] = "STOP bot challenge"
            return res, []
        dm = DUMP.get(url) and re.search(DUMP[url], text, re.I)
        if dm:
            res["dump"] = text[dm.start():dm.start() + 1500]
        res.update(title=title, chars=len(text), snips=[s[:420 if cap > 6 else 330] for s in snippets(text, figs, cap)])
        if self.render:
            res["rendered"] = 1
        return res, ([(urllib.parse.urljoin(final, h), re.sub(r"<[^>]+>|\s+", " ", x).strip()[:60]) for h, x in links] if want_links else [])


HOSTS = {}
TERMSOK = set()
DUMP = {}


def host_of(url):
    p = urllib.parse.urlparse(url)
    with LOCK:
        if p.netloc not in HOSTS:
            HOSTS[p.netloc] = Host(p.netloc)
    return HOSTS[p.netloc], p.scheme or "https"


def tokens(name):
    drop = set("fc cf sc sv ac as us ss ud cd rc afc club calcio football de la le el fk vv kv krc k r f c the "
               "city united town sporting sport real royal athletic sad 1898 1907 1909 1911 1913 1929 2018 stade unione sportiva societa associazione hellas jong".split())
    return [t for t in fold(name).split() if t not in drop and len(t) >= 4]


def run_host(job):
    """One host: its pages in order, one request per second. job = (host key, [(club, url, why)])."""
    hostname, items = job
    for c, url, why in items:
        if time.time() > DEADLINE:
            c["pages"].append({"url": url, "why": why, "st": "not reached (time)"})
            continue
        h, scheme = host_of(url)
        h.open(scheme)
        res, _ = h.page(url, c["figs"], cap=14 if why.startswith("added by hand") else 6)
        res["why"] = why
        c["pages"].append(res)


def run_league(job):
    root, clubs = job
    h, scheme = host_of(root)
    h.open(scheme)
    info = {"root": root, "stop": h.stop, "terms": h.terms[:200], "rootlinks": len(h.rootlinks)}
    links = list(h.rootlinks)
    if root.rstrip("/").count("/") > 2 and not h.stop:
        _, links = h.page(root, [], want_links=True)
    if not h.stop:
        idx = [u for u, x in links if urllib.parse.urlparse(u).netloc.replace("www.", "") == h.host.replace("www.", "")
               and re.search(r"/(teams?|clubs?|clubes|equipos|squadre|cluburi|echipe|omades|vereine|klubs)/?$", urllib.parse.urlparse(u).path, re.I)]
        for u in list(dict.fromkeys(idx))[:3]:
            _, more = h.page(u, [], want_links=True)
            links += more
        info["index"] = list(dict.fromkeys(idx))[:3]
        info["links"] = len(links)
    for c in clubs:
        toks = c.get("tok") or tokens(c["name"])
        cand = []
        for u, x in links:
            p = urllib.parse.urlparse(u)
            if p.netloc.replace("www.", "") != h.host.replace("www.", "") or len(p.path) < 4:
                continue
            if re.search(r"news|ticket|shop|video|match|partite|calendar|/20\d\d", p.path, re.I):
                continue
            f = fold(urllib.parse.unquote(p.path)) + " | " + fold(x)
            if any(t in f for t in toks) and u not in cand:
                cand.append(u)
        for u in cand[:2]:
            if time.time() > DEADLINE:
                break
            res, sub = h.page(u, c["figs"], want_links=True)
            res["why"] = "league site, link on its root"
            c["pages"].append(res)
            for u2, x2 in sub:
                if u2.startswith(u.rstrip("/") + "/") and STADWORD.search(u2[len(u):] + " " + x2):
                    r2, _ = h.page(u2, c["figs"])
                    r2["why"] = "league site, stadium link on the club page"
                    c["pages"].append(r2)
                    break
    return info


def stadiumdb(clubs):
    h, scheme = host_of("https://stadiumdb.com/")
    h.open(scheme)
    rows = {}
    for cc in sorted({c["cc"] for c in clubs}):
        if cc not in SDB or h.stop:
            continue
        url = f"https://stadiumdb.com/stadiums/{SDB[cc]}"
        if not h.allowed(url):
            log("stadiumdb robots disallows " + url)
            continue
        st, body, _, _ = h.get(url)
        if st != 200:
            log(f"stadiumdb {url} {st}")
            continue
        t = body.decode("utf-8", "replace")
        rows[cc] = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
            cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", td))).strip() for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(cells) >= 4 and re.search(r"\d", cells[-1]):
                rows[cc].append(cells)
    for c in clubs:
        toks, vt = tokens(c["name"]), [t for t in fold(c["venue"] or "").split() if len(t) >= 5 and not STADWORD.match(t)]
        c["sdb"] = []
        for cells in rows.get(c["cc"], []):
            f = [fold(x) for x in cells]
            if any(t in f[2] for t in toks) or (vt and all(t in f[0] for t in vt)):
                c["sdb"].append(" | ".join(cells)[:150])
        c["sdb"] = c["sdb"][:4]
    return h.stop or f"{sum(len(v) for v in rows.values())} rows in {len(rows)} country tables"


def main():
    cfg = json.load(open(os.path.join(HERE, "targets.json"), encoding="utf-8"))
    clubs = cfg["clubs"]
    extra = cfg.get("extra", {})
    TERMSOK.update(cfg.get("termsok") or [])
    only = set(cfg.get("only") or [])
    if only:
        clubs = [c for c in clubs if c["q"] in only]
    log(f"run {RUN}: {len(clubs)} clubs")
    RENDER.update(cfg.get("render") or [])
    DUMP.update(cfg.get("dump") or {})
    for c in clubs:
        if c.get("titles"):
            c["wd"] = {"how": c.pop("titlesfrom", "titles given")}
    ask = [c for c in clubs if not c.get("titles")]
    ok = wikidata(ask) if ask else True
    log(f"wikidata asked for {len(ask)} clubs: {'answered' if ok else 'did NOT answer within the waiting budget'}; waited {WAITED.get('www.wikidata.org', 0)} s on lag")
    if not ok:
        for c in ask:
            c.pop("p115", None)
            if c.get("clubtitle"):
                via_club(c)
            elif c.get("titles2"):
                c["titles"], c["wd"] = c["titles2"], {"how": "by name on en.wikipedia in run 1 (Wikidata lagged)"}
        by_name(ask)
    for c in clubs:
        c.pop("titles2", None)
    for c in clubs:
        c["wp"], c["pages"], c["figs"] = {}, [], [c["map"]] if c.get("map") else []
        titles = c.get("titles") or {}
        langs = [l for l in LANGS.get(c["cc"], []) if l in titles][:1]
        langs += [l for l in ("en",) if l in titles and l not in langs]
        for l in langs:
            a = article(l, titles[l])
            if a:
                c["wp"][l] = a
                for ln in a["lines"]:
                    for n in re.findall(NUM, re.sub(r"\[REF\d+:[^\]]*\]", "", ln)):
                        v = int(re.sub(r"\D", "", n))
                        if 300 <= v <= 120000 and v not in c["figs"]:
                            c["figs"].append(v)
        c["figs"] = c["figs"][:8]
    log(f"wikipedia done; wikimedia requests {NREQ.get('wikimedia', 0)}, waited on lag {WAITED}")
    # which pages to open
    jobs = {}
    for c in clubs:
        m = c.get("map") or 0
        linenums = [int(re.sub(r"\D", "", n)) for a in c["wp"].values() for ln in a["lines"]
                    for n in re.findall(NUM, re.sub(r"\[REF\d+:[^\]]*\]", "", ln))]
        agrees = m and any(abs(v - m) <= 0.03 * m for v in linenums)
        c["auto"] = "a number on a capacity line is within 3 percent of the map" if agrees else "no number on the capacity lines within 3 percent"
        todo = [(u, "added by hand for this run") for u in extra.get(c["q"], [])]
        if c.get("force"):
            agrees = False
        if not (c["grp"] == "B" and agrees) and not c.get("only_extra"):
            for l, a in c["wp"].items():
                for u, arch in a["lineref"][:2]:
                    todo.append((u or arch, f"reference on the capacity line of {l}.wikipedia" + ("" if u else " (archive copy named by the reference)")))
                for u, arch in a["bodyref"][:1]:
                    todo.append((u, f"reference on a capacity sentence of {l}.wikipedia"))
            ext = [u for a in c["wp"].values() for u in a["ext"]]
            if c.get("allext"):
                c["extlist"] = [u[:110] for u in ext][:25]
            sd = [u for u in ext if re.search(r"stadiumdb\.com|stadiony\.net", u)][:1]
            todo += [(u, "StadiumDB page in the article's link list") for u in sd]
            web = [a["web"] for a in c["wp"].values() if a["web"]][:1]
            todo += [(u, "website field of the ground's infobox") for u in web]
            n = 0
            for u in ext:
                p = urllib.parse.urlparse(u)
                if n < (5 if c.get("allext") else 3) and not SKIPHOST.search(u) and (c.get("allext") or STADWORD.search(p.path + "?" + p.query)) and not re.search(r"\.(pdf|jpg|png)$", p.path, re.I) and u not in sd:
                    todo.append((u, "external link of the article"))
                    n += 1
        seen = set()
        for u, why in todo:
            if not u or u in seen or SKIPHOST.search(u):
                if u and u not in seen:
                    c["pages"].append({"url": u[:160], "why": why, "st": "not opened (closed, statistics, social or archive host)"})
                continue
            seen.add(u)
            jobs.setdefault(urllib.parse.urlparse(u).netloc, []).append((c, u, why))
            if len(seen) >= 8:
                break
    sdb = stadiumdb(clubs)
    log("stadiumdb: " + str(sdb))
    leagues = {}
    for c in clubs:
        if (c["grp"] == "B" and c["auto"].startswith("a number") and not c.get("force")) or c.get("noleague"):
            continue
        for root in LEAGUES.get(c["cc"], []):
            leagues.setdefault(root, []).append(c)
    linfo = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        f1 = [ex.submit(run_host, j) for j in jobs.items()]
        f2 = [ex.submit(run_league, j) for j in leagues.items()]
        for f in f1:
            try:
                f.result()
            except Exception as e:
                log(f"host job failed: {type(e).__name__} {e}")
        for f in f2:
            try:
                linfo.append(f.result())
            except Exception as e:
                log(f"league job failed: {type(e).__name__} {e}")
    # report
    lines = []
    for c in clubs:
        for a in c["wp"].values():
            a.pop("ext", None), a.pop("lineref", None), a.pop("bodyref", None)
        c.pop("titles", None)
        lines.append(json.dumps(c, ensure_ascii=False, separators=(",", ":")))
    post_chunks(f"PROBE1D run {RUN} DATA", lines)
    stops = sorted(f"{h.host}: {h.stop}" for h in HOSTS.values() if h.stop)
    nother = sum(v for k, v in NREQ.items() if k != "wikimedia")
    summary = [f"clubs {len(clubs)}; wikimedia requests {NREQ.get('wikimedia', 0)}; other requests {nother} on {len(HOSTS)} hosts; minutes {int((time.time() - T0) / 60)}",
               f"lag waits (seconds, maxlag 5 throughout): {WAITED}", "stadiumdb: " + str(sdb),
               "leagues: " + json.dumps(linfo, ensure_ascii=False)[:3000], "STOPS:"] + stops + ["TERMS:"] + sorted(f"{h.host}: {h.terms[:160]}" for h in HOSTS.values() if h.terms) + ["LOG:"] + LOG[-150:]
    post_chunks(f"PROBE1D run {RUN} SUMMARY", summary)


if __name__ == "__main__":
    main()
