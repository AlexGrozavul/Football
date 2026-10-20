# TEMPORARY probe, removed before merge.
import json, re, sys, time, urllib.parse, urllib.request, urllib.error
from html.parser import HTMLParser

UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
LAST = {}
OUT = []
def say(s): OUT.append(s); print(s, flush=True)

def get(url, data=None, headers=None, tries=4):
    host = urllib.parse.urlparse(url).netloc
    for attempt in range(tries):
        gap = 1.0 - (time.time() - LAST.get(host, 0))
        if gap > 0: time.sleep(gap)
        LAST[host] = time.time()
        req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code in (429, 503) and attempt < tries - 1:
                time.sleep(min(int(e.headers.get("Retry-After", "10") or 10), 60)); continue
            return e.code, body, dict(e.headers)
        except Exception as e:
            if attempt < tries - 1: time.sleep(10); continue
            return 0, str(e).encode(), {}
    return 0, b"", {}

def wiki(params, host="en.wikipedia.org"):
    p = {"format": "json", "formatversion": "2", "maxlag": "5", **params}
    s, b, _ = get(f"https://{host}/w/api.php?" + urllib.parse.urlencode(p))
    try: return json.loads(b)
    except Exception: return {"error": f"HTTP {s} {b[:200]!r}"}

def wd(params):
    return wiki(params, "www.wikidata.org")

def sparql(q):
    s, b, _ = get("https://query.wikidata.org/sparql", data=urllib.parse.urlencode({"query": q, "format": "json"}).encode(),
                  headers={"Accept": "application/sparql-results+json", "Content-Type": "application/x-www-form-urlencoded"})
    try: return json.loads(b)["results"]["bindings"]
    except Exception: return [{"error": {"value": f"HTTP {s} {b[:300]!r}"}}]

class Tables(HTMLParser):
    def __init__(s): super().__init__(); s.t = []; s.cur = None; s.row = None; s.cell = None; s.links = None
    def handle_starttag(s, tag, a):
        a = dict(a)
        if tag == "table" and "wikitable" in (a.get("class") or ""): s.cur = []
        elif s.cur is not None and tag == "tr": s.row = []
        elif s.row is not None and tag in ("td", "th"): s.cell = ""
        elif s.cell is not None and tag == "a" and a.get("title") and s.row is not None: s.row.append(("L", a["title"]))
    def handle_endtag(s, tag):
        if tag in ("td", "th") and s.cell is not None: s.row.append(("T", s.cell.strip())); s.cell = None
        elif tag == "tr" and s.row is not None and s.cur is not None: s.cur.append(s.row); s.row = None
        elif tag == "table" and s.cur is not None: s.t.append(s.cur); s.cur = None
    def handle_data(s, d):
        if s.cell is not None: s.cell += d

def article(title):
    j = wiki({"action": "parse", "page": title, "prop": "text|displaytitle", "redirects": "1", "disablelimitreport": "1"})
    if "parse" not in j: return None, j.get("error")
    p = Tables(); p.feed(j["parse"]["text"]); return j["parse"]["title"], p.t

def pageprops(titles, host="en.wikipedia.org"):
    j = wiki({"action": "query", "titles": "|".join(titles), "prop": "pageprops", "ppprop": "wikibase_item", "redirects": "1"}, host)
    res = {}
    for pg in j.get("query", {}).get("pages", []):
        res[pg["title"]] = (pg.get("pageprops") or {}).get("wikibase_item") if not pg.get("missing") else "MISSING"
    return res, j.get("query", {}).get("redirects", [])

def step_leagues():
    say("== season / league pages")
    for q in ["Primeira Liga", "Liga Portugal 2", "Segunda Liga", "2026–27 Primeira Liga", "2026–27 Liga Portugal 2", "2026–27 Segunda Liga", "2026-27 Liga Portugal 2"]:
        r, red = pageprops([q]); say(f"  {q!r}: {r} redirects={[(x['from'], x['to']) for x in red]}")
    j = wiki({"action": "query", "list": "search", "srsearch": "2026–27 Liga Portugal 2 season", "srlimit": 6})
    say("  search: " + str([x["title"] for x in j.get("query", {}).get("search", [])]))
    j = wiki({"action": "query", "list": "search", "srsearch": "2026–27 Primeira Liga", "srlimit": 6})
    say("  search: " + str([x["title"] for x in j.get("query", {}).get("search", [])]))
    for t in ["2026–27 Primeira Liga", "2026–27 Liga Portugal 2"]:
        title, tabs = article(t)
        say(f"== article {t!r} -> {title}")
        if title is None: say(f"  FAILED {tabs}"); continue
        for i, tb in enumerate(tabs):
            hdr = [c[1] for c in tb[0] if c[0] == "T"][:8] if tb else []
            say(f"  table {i}: rows={len(tb)} header={hdr}")
            if any(re.search(r"stadium|venue", h, re.I) for h in hdr):
                for row in tb[1:]:
                    links = [c[1] for c in row if c[0] == "L"][:2]; txt = [c[1] for c in row if c[0] == "T"]
                    say(f"     {txt[:5]} links={links}")
    # entity facts
    lq = {}
    for t in ["Primeira Liga", "Liga Portugal 2"]:
        r, _ = pageprops([t]); lq[t] = list(r.values())[0]
    say(f"== league Q-ids {lq}")
    for t, q in lq.items():
        j = wd({"action": "wbgetentities", "ids": q, "props": "labels|claims|sitelinks|descriptions", "languages": "en|pt"})
        e = j.get("entities", {}).get(q, {})
        c = e.get("claims", {})
        def vals(p): return [(x["rank"], x["mainsnak"].get("datavalue", {}).get("value")) for x in c.get(p, [])]
        say(f"  {q} {e.get('labels', {}).get('en', {}).get('value')} | desc={e.get('descriptions', {}).get('en', {}).get('value')} | P3983={vals('P3983')} P17={[(r, v.get('id') if isinstance(v, dict) else v) for r, v in vals('P17')]} P31={[v.get('id') for r, v in vals('P31') if isinstance(v, dict)]} P576={vals('P576')}")
    say("== Q45 extreme points P1332-P1335")
    j = wd({"action": "wbgetentities", "ids": "Q45", "props": "claims"})
    c = j["entities"]["Q45"]["claims"]
    for p in ("P1332", "P1333", "P1334", "P1335"):
        for x in c.get(p, []):
            v = x["mainsnak"].get("datavalue", {}).get("value", {})
            quals = {k: [q.get("datavalue", {}).get("value") for q in vs] for k, vs in x.get("qualifiers", {}).items()}
            say(f"  {p} rank={x['rank']} lat={v.get('latitude')} lon={v.get('longitude')} quals={str(quals)[:150]}")
    return lq

def step_tagged(lq):
    leagues = " ".join(f"wd:{q}" for q in lq.values())
    say(f"== every item carrying either tag at any rank ({leagues})")
    q = """SELECT ?club ?clubLabel ?league ?rank ?start ?end ?type ?typeLabel ?country ?dis ?venue ?coord ?cls ?clsLabel WHERE {
 VALUES ?league { %s }
 ?club p:P118 ?st . ?st ps:P118 ?league . ?st wikibase:rank ?rank .
 OPTIONAL{?st pq:P580 ?start} OPTIONAL{?st pq:P582 ?end}
 OPTIONAL{?club wdt:P31 ?type} OPTIONAL{?club wdt:P17 ?country} OPTIONAL{?club wdt:P576 ?dis}
 OPTIONAL{?club wdt:P115 ?venue} OPTIONAL{?club wdt:P625 ?coord} OPTIONAL{?club wdt:P2094 ?cls}
 SERVICE wikibase:label { bd:serviceParam wikibase:language "en,pt". }
} ORDER BY ?clubLabel""" % leagues
    rows = sparql(q)
    if rows and "error" in rows[0]: say("  FAILED " + rows[0]["error"]["value"]); return
    byclub = {}
    for r in rows:
        k = r["club"]["value"].rsplit("/", 1)[1]
        d = byclub.setdefault(k, {"label": r.get("clubLabel", {}).get("value"), "tags": set(), "types": set(), "country": set(), "dis": set(), "venue": False, "coord": False, "cls": set()})
        d["tags"].add((r["league"]["value"].rsplit("/", 1)[1], r["rank"]["value"].rsplit("#", 1)[1], (r.get("start") or {}).get("value", "")[:4], (r.get("end") or {}).get("value", "")[:4]))
        if "typeLabel" in r: d["types"].add(r["typeLabel"]["value"])
        if "country" in r: d["country"].add(r["country"]["value"].rsplit("/", 1)[1])
        if "dis" in r: d["dis"].add(r["dis"]["value"][:4])
        d["venue"] |= "venue" in r; d["coord"] |= "coord" in r
        if "clsLabel" in r: d["cls"].add(r["clsLabel"]["value"])
    say(f"  {len(byclub)} items, {len(rows)} rows")
    for k, d in sorted(byclub.items(), key=lambda x: x[1]["label"] or ""):
        say(f"  {k} {d['label']} | tags={sorted(d['tags'])} | types={sorted(d['types'])} | P17={sorted(d['country'])} | P576={sorted(d['dis'])} | ground={d['venue']} coord={d['coord']} P2094={sorted(d['cls'])}")

def step_stadiumdb():
    say("== stadiumdb")
    s, b, _ = get("https://stadiumdb.com/robots.txt"); say(f"  robots {s} {b[:80]!r}")
    for slug in ["por", "prt", "portugal", "pt"]:
        s, b, _ = get(f"https://stadiumdb.com/stadiums/{slug}")
        t = b.decode("utf-8", "replace")
        m = re.search(r"<title>(.*?)</title>", t, re.S)
        say(f"  /stadiums/{slug}: HTTP {s} {len(b)} bytes title={m.group(1).strip()[:80] if m else None} rows={t.count('<tr')}")
        if s == 200 and len(b) > 20000:
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)
            for r in rows[:80]:
                cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
                say("     " + " | ".join(cells)[:140])
            break

if __name__ == "__main__":
    step = sys.argv[1]
    if step == "leagues":
        lq = step_leagues(); step_tagged(lq); step_stadiumdb()
    say("== DONE " + step)
