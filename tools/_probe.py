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
    for attempt in range(4):
        s, b, h = get(f"https://{host}/w/api.php?" + urllib.parse.urlencode(p))
        try: j = json.loads(b)
        except Exception: return {"error": f"HTTP {s} {b[:200]!r}"}
        if isinstance(j.get("error"), dict) and j["error"].get("code") == "maxlag" and attempt < 3:
            time.sleep(int(h.get("Retry-After", "6") or 6)); continue
        if "error" in j: say(f"  (api error {host}: {str(j['error'])[:160]})")
        return j
    return j

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
    c = j.get("entities", {}).get("Q45", {}).get("claims", {})
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


def qid(r, k): return r[k]["value"].rsplit("/", 1)[1] if k in r else None
def val(r, k): return r[k]["value"] if k in r else None

def step_pt2():
    # roster titles -> Q-ids
    titles = []
    for t in ["2026–27 Primeira Liga", "2026–27 Liga Portugal 2"]:
        title, tabs = article(t)
        for tb in tabs:
            hdr = [c[1] for c in tb[0] if c[0] == "T"][:5] if tb else []
            if hdr[:3] == ["Team", "Location", "Stadium"]:
                for row in tb[1:]:
                    links = [c[1] for c in row if c[0] == "L"]
                    if links: titles.append(links[0])
    say(f"== roster titles {len(titles)}")
    qs = {}
    for i in range(0, len(titles), 40):
        r, red = pageprops(titles[i:i + 40])
        redmap = {x["from"]: x["to"] for x in red}
        for t in titles[i:i + 40]:
            qs[t] = r.get(redmap.get(t, t))
    say("  " + "; ".join(f"{t}={q}" for t, q in qs.items()))
    roster = [q for q in qs.values() if q and q != "MISSING"]
    values = " ".join(f"wd:{q}" for q in roster)
    say("== box points of Q45")
    rows = sparql("""SELECT ?p ?rank ?c WHERE { VALUES ?p { p:P1332 p:P1333 p:P1334 p:P1335 }
      wd:Q45 ?p ?s . ?s ?ps ?c . FILTER(STRSTARTS(STR(?ps), "http://www.wikidata.org/prop/statement/P133") && STRENDS(STR(?ps), STRAFTER(STR(?p), "prop/")) ) ?s wikibase:rank ?rank }""")
    if rows and "error" in rows[0]: say("  FAILED " + rows[0]["error"]["value"])
    else:
        for r in rows: say(f"  {val(r,'p').rsplit('/',1)[1]} {val(r,'rank').rsplit('#',1)[1]} {val(r,'c')}")
    say("== leagues P3983/P17")
    rows = sparql("""SELECT ?l ?lLabel ?lvl ?c ?cLabel WHERE { VALUES ?l { wd:Q182994 wd:Q754488 } OPTIONAL{?l wdt:P3983 ?lvl} OPTIONAL{?l wdt:P17 ?c}
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }""")
    for r in rows: say("  " + str({k: v["value"].rsplit("/", 1)[-1] for k, v in r.items()}))
    say("== roster clubs: truthy labels, types, grounds (every P115 statement with rank/dates), ground coord and capacity")
    rows = sparql("""SELECT ?c ?cLabel ?type ?typeLabel ?g ?gLabel ?gr ?gs ?ge ?gc ?gcap WHERE { VALUES ?c { %s }
      OPTIONAL{?c wdt:P31 ?type}
      OPTIONAL{?c p:P115 ?st . ?st ps:P115 ?g . ?st wikibase:rank ?gr . OPTIONAL{?st pq:P580 ?gs} OPTIONAL{?st pq:P582 ?ge}
               OPTIONAL{?g wdt:P625 ?gc} OPTIONAL{?g wdt:P1083 ?gcap}}
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,pt". } }""" % values)
    if rows and "error" in rows[0]: say("  FAILED " + rows[0]["error"]["value"])
    else:
        by = {}
        for r in rows:
            d = by.setdefault(qid(r, "c"), {"l": val(r, "cLabel"), "t": set(), "g": set()})
            if "typeLabel" in r: d["t"].add(val(r, "typeLabel"))
            if "g" in r: d["g"].add((qid(r, "g"), val(r, "gLabel"), qid(r, "gr") if False else val(r, "gr").rsplit("#", 1)[1], (val(r, "gs") or "")[:4], (val(r, "ge") or "")[:4], (val(r, "gc") or "")[:40], val(r, "gcap")))
        for k, d in by.items():
            say(f"  {k} {d['l']} | {sorted(d['t'])}")
            for g in sorted(d["g"], key=lambda x: str(x)): say(f"      ground {g}")
        say(f"  roster clubs seen {len(by)} of {len(roster)}; missing: {[q for q in roster if q not in by]}")
    say("== related items (P749/P361/P831/P127/P1830 either way) and same-label items of other Q-ids in PT")
    rows = sparql("""SELECT ?c ?x ?xLabel ?xDesc ?typeLabel ?prop WHERE { VALUES ?c { %s }
      { ?x ?pp ?c . VALUES ?pp { wdt:P749 wdt:P361 wdt:P831 wdt:P127 wdt:P1830 } BIND("x->c" AS ?prop) } UNION
      { ?c ?pp ?x . VALUES ?pp { wdt:P749 wdt:P361 wdt:P831 } BIND("c->x" AS ?prop) }
      FILTER(?x != ?c) OPTIONAL{?x wdt:P31 ?type} OPTIONAL{?x schema:description ?xDesc FILTER(LANG(?xDesc)="en")}
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,pt". } }""" % values)
    if rows and "error" in rows[0]: say("  FAILED " + rows[0]["error"]["value"])
    else:
        by = {}
        for r in rows:
            by.setdefault((qid(r, "c"), qid(r, "x"), val(r, "xLabel"), val(r, "xDesc"), val(r, "prop")), set()).add(val(r, "typeLabel"))
        for k, t in sorted(by.items(), key=lambda x: str(x)): say(f"  {k} types={sorted(x for x in t if x)}")
        say(f"  {len(by)} related rows")
    rows = sparql("""SELECT ?c ?cl ?o ?oLabel ?typeLabel WHERE { VALUES ?c { %s } ?c rdfs:label ?cl FILTER(LANG(?cl) IN ("en","pt"))
      ?o rdfs:label ?cl . ?o wdt:P17 wd:Q45 . FILTER(?o != ?c) OPTIONAL{?o wdt:P31 ?type}
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,pt". } }""" % values)
    if rows and "error" in rows[0]: say("  FAILED same-label " + rows[0]["error"]["value"])
    else:
        say(f"  same-label other items in Portugal: {len(rows)}")
        for r in rows: say(f"    {qid(r,'c')} '{val(r,'cl')}' = {qid(r,'o')} {val(r,'oLabel')} {val(r,'typeLabel')}")
    say("== women's angles: items carrying either tag whose label/description/class says women's")
    rows = sparql("""SELECT DISTINCT ?x ?xLabel ?xDesc WHERE { VALUES ?l { wd:Q182994 wd:Q754488 } ?x wdt:P118|wdt:P2094 ?l .
      OPTIONAL{?x schema:description ?xDesc FILTER(LANG(?xDesc)="en")} ?x rdfs:label ?lab FILTER(LANG(?lab) IN ("en","pt"))
      FILTER(REGEX(?lab, "fem|women|mulher|ladies|dames", "i") || REGEX(COALESCE(?xDesc,""), "women|female", "i"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }""")
    say("  " + (str(rows[0]) if rows and "error" in rows[0] else f"{len(rows)} items: " + str([(qid(r,'x'), val(r,'xLabel')) for r in rows])))
    say("  women's team items typed women's pointing at any roster club were listed above under related items (look for 'women' in the description)")


def step_grounds():
    say("== overpass robots")
    s_, b, _ = get("https://overpass-api.de/robots.txt"); say(f"  robots {s_} {b[:120]!r}")
    q = ('[out:json][timeout:150];area["ISO3166-1"="PT"][admin_level=2]->.a;('
         'nwr(area.a)["name"~"Alverca|Lusit.nia|Aur.lio Pereira|Aves|Lu.s Filipe Menezes|Jorge Sampaio|Rio Maior|Benfica Campus|Futebol Campus|CTFD|PortoGaia|S.o Lu.s|Casa Pia|Pina Manique",i]["leisure"~"stadium|pitch|sports_centre|training_ground"];'
         'nwr(area.a)["name"~"Alverca|Lusit.nia|Aur.lio Pereira|Aves|Lu.s Filipe Menezes|Jorge Sampaio|Rio Maior|Benfica Campus|Futebol Campus|CTFD|PortoGaia|S.o Lu.s",i]["building"="stadium"];'
         ');out center tags;')
    for attempt in range(3):
        s_, b, _ = get("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": q}).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"}, tries=2)
        if s_ == 200: break
        say(f"  overpass HTTP {s_} {b[:100]!r}"); time.sleep(30)
    if s_ == 200:
        els = json.loads(b)["elements"]; say(f"  {len(els)} elements")
        for e in els:
            t = e.get("tags", {}); c = e.get("center") or {"lat": e.get("lat"), "lon": e.get("lon")}
            say(f"  {e['type']}/{e['id']} name={t.get('name')!r} leisure={t.get('leisure')} sport={t.get('sport')} cap={t.get('capacity')} operator={t.get('operator')} at {c.get('lat')},{c.get('lon')}")
    say("== wikidata ground items (labels, aliases, coords, capacity)")
    ids = "wd:Q2586520 wd:Q15110461 wd:Q5510501 wd:Q2945331 wd:Q1370765"
    rows = sparql("""SELECT ?i ?l ?alias ?c ?cap ?typeLabel WHERE { VALUES ?i { %s }
      OPTIONAL{?i rdfs:label ?l FILTER(LANG(?l) IN ("en","pt"))} OPTIONAL{?i skos:altLabel ?alias FILTER(LANG(?alias) IN ("en","pt"))}
      OPTIONAL{?i wdt:P625 ?c} OPTIONAL{?i wdt:P1083 ?cap} OPTIONAL{?i wdt:P31 ?type}
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }""" % ids)
    by = {}
    for r in rows:
        if "error" in r: say("  FAILED " + r["error"]["value"]); break
        d = by.setdefault(qid(r, "i"), {"l": set(), "a": set(), "c": set(), "cap": set(), "t": set()})
        for k, f in (("l", "l"), ("a", "alias"), ("c", "c"), ("cap", "cap"), ("t", "typeLabel")):
            if f in r: d[k].add(val(r, f)[:60])
    for k, d in by.items(): say(f"  {k} labels={sorted(d['l'])} aliases={sorted(d['a'])} P625={sorted(d['c'])} P1083={sorted(d['cap'])} types={sorted(d['t'])}")
    say("== grounds of Aves club item Q1023163 and its P115 item")
    rows = sparql("""SELECT ?g ?gLabel ?c ?cap ?gr WHERE { wd:Q1023163 p:P115 ?st . ?st ps:P115 ?g . ?st wikibase:rank ?gr . OPTIONAL{?g wdt:P625 ?c} OPTIONAL{?g wdt:P1083 ?cap}
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,pt". } }""")
    for r in rows: say("  " + str({k: v["value"][-60:] for k, v in r.items()}))
    say("== PT sports venues by label")
    rows = sparql("""SELECT DISTINCT ?s ?sLabel ?c ?cap WHERE { ?s wdt:P17 wd:Q45 ; wdt:P625 ?c ; wdt:P31/wdt:P279* wd:Q1076486 ; rdfs:label ?l .
      FILTER(LANG(?l) IN ("en","pt") && REGEX(?l, "Alverca|Lusit.nia de Lourosa|Aur.lio Pereira|Aves|Lu.s Filipe Menezes|Rio Maior|CTFD|Casa Pia|Pina Manique", "i")) OPTIONAL{?s wdt:P1083 ?cap}
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,pt". } }""")
    for r in rows: say("  " + str({k: v["value"][-70:] for k, v in r.items()}))


def step_verify():
    say("== preferred-rank novalue/somevalue P118 on items in Portugal (or carrying P17 Q45) - query A/B shape")
    rows = sparql("""SELECT ?x ?xLabel ?dis WHERE { ?x p:P118 ?st . ?st wikibase:rank wikibase:PreferredRank . ?st a wdno:P118 .
       ?x wdt:P17 wd:Q45 . OPTIONAL{?x wdt:P576 ?dis} SERVICE wikibase:label { bd:serviceParam wikibase:language "en,pt". } }""")
    say("  " + (str(rows[0]) if rows and "error" in rows[0] else f"{len(rows)} items: " + str([(qid(r,'x'), val(r,'xLabel'), (val(r,'dis') or '')[:4]) for r in rows])))
    rows = sparql("""SELECT ?x ?xLabel ?dis WHERE { ?x p:P118 ?st . ?st wikibase:rank wikibase:PreferredRank . ?st ps:P118 ?v . FILTER(?v = wikibase:Somevalue || isBLANK(?v))
       ?x wdt:P17 wd:Q45 . OPTIONAL{?x wdt:P576 ?dis} SERVICE wikibase:label { bd:serviceParam wikibase:language "en,pt". } }""")
    say("  somevalue: " + (str(rows[0]) if rows and "error" in rows[0] else f"{len(rows)} items: " + str([(qid(r,'x'), val(r,'xLabel')) for r in rows])))
    rows = sparql("""SELECT ?x ?xLabel WHERE { VALUES ?l { wd:Q182994 wd:Q754488 } ?x p:P118 ?st . ?st ps:P118 ?l . ?st wikibase:rank wikibase:DeprecatedRank .
       SERVICE wikibase:label { bd:serviceParam wikibase:language "en,pt". } }""")
    say("  deprecated-rank tags on either league: " + (str(rows[0]) if rows and "error" in rows[0] else f"{len(rows)}: " + str([(qid(r,'x'), val(r,'xLabel')) for r in rows])))
    say("== overpass retry (small queries, 4 tries each, 40 s apart)")
    qs = {
      "aurelio": '[out:json][timeout:60];nwr["name"~"Aur.lio Pereira",i](38.6,-9.1,38.9,-8.6);out center tags;',
      "lusitania": '[out:json][timeout:60];nwr["name"~"Lusit.nia|Lourosa",i]["leisure"~"stadium|pitch|sports_centre"](40.8,-8.6,41.0,-8.4);out center tags;',
      "alverca": '[out:json][timeout:60];nwr["name"~"Alverca",i]["leisure"~"stadium|pitch|sports_centre"](38.85,-9.1,38.95,-8.95);out center tags;',
      "portogaia": '[out:json][timeout:60];nwr["name"~"Menezes|CTFD|PortoGaia",i](41.0,-8.6,41.12,-8.45);out center tags;',
    }
    for k, q in qs.items():
        for attempt in range(4):
            s_, b, _ = get("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": q}).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"}, tries=1)
            if s_ == 200: break
            time.sleep(40)
        if s_ != 200: say(f"  {k}: HTTP {s_} {b[:60]!r}"); continue
        els = json.loads(b)["elements"]; say(f"  {k}: {len(els)} elements")
        for e in els:
            t = e.get("tags", {}); c = e.get("center") or {"lat": e.get("lat"), "lon": e.get("lon")}
            say(f"    {e['type']}/{e['id']} name={t.get('name')!r} leisure={t.get('leisure')} sport={t.get('sport')} cap={t.get('capacity')} at {c.get('lat')},{c.get('lon')}")

if __name__ == "__main__":
    step = sys.argv[1]
    if step == "leagues":
        lq = step_leagues()
        for f in (lambda: step_tagged(lq), step_stadiumdb):
            try: f()
            except Exception as e: say(f"  STEP FAILED {e!r}")
    if step == "pt2":
        try: step_pt2()
        except Exception as e: say(f"  STEP FAILED {e!r}")
    if step == "grounds":
        try: step_grounds()
        except Exception as e: say(f"  STEP FAILED {e!r}")
    if step == "verify":
        try: step_verify()
        except Exception as e: say(f"  STEP FAILED {e!r}")
    say("== DONE " + step)
