"""TEMPORARY probe #1 for the England pass. Removed in the same branch."""
import csv, glob, json, os, re, sys, time, traceback, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc


def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

LANGS = "en"


def ents(ids, props="claims|labels|sitelinks"):
    out = {}
    ids = list(dict.fromkeys(i for i in ids if i))
    for i in range(0, len(ids), 45):
        args = {"action": "wbgetentities", "props": props, "languages": LANGS,
                "format": "json", "ids": "|".join(ids[i:i + 45])}
        d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), "ents")
        if e: p("ENTS-ERROR", e)
        out.update((d or {}).get("entities", {}))
        time.sleep(1)
    return out


def lab(ent):
    return (ent.get("labels", {}).get("en") or {}).get("value")


def vals(ent, prop):
    out = []
    for c in ent.get("claims", {}).get(prop, []):
        v = c["mainsnak"].get("datavalue", {}).get("value")
        if v is None: v = c["mainsnak"].get("snaktype")
        elif isinstance(v, dict) and "latitude" in v: v = (round(v["latitude"], 5), round(v["longitude"], 5))
        elif isinstance(v, dict) and "amount" in v: v = v["amount"]
        elif isinstance(v, dict) and "id" in v: v = v["id"]
        elif isinstance(v, dict) and "time" in v: v = v["time"][:11]
        qual = {k: [str(x.get("datavalue", {}).get("value", {}).get("time", x.get("datavalue", {}).get("value", "")))[:11]
                    for x in xs]
                for k, xs in c.get("qualifiers", {}).items() if k in ("P580", "P582", "P585")}
        r = c.get("rank")[:4]
        out.append((v, r, qual) if qual else (v, r))
    return out


def sitelinks(ent):
    s = ent.get("sitelinks") or {}
    return len(s), (s.get("enwiki") or {}).get("title")


def section(name, fn):
    p(f"########## {name}")
    try:
        fn()
    except Exception:
        p("SECTION-FAILED", name, traceback.format_exc()[-800:])


def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None


EN_LEAGUES = {}


def s0():
    E = ents(["Q21", "Q145", "Q25"])
    for q in ("Q21", "Q145", "Q25"):
        x = E.get(q, {})
        p("EXTREME", q, lab(x), [(pr, vals(x, pr)) for pr in ("P1332", "P1333", "P1334", "P1335")])


def s1():
    for t, tier in [("Premier League", 1), ("EFL Championship", 2)]:
        q = qid_for(t)
        p("ENWIKI", t, "->", q)
        if q: EN_LEAGUES[q] = tier
    Q = """SELECT DISTINCT ?l ?lLabel ?c WHERE {
      VALUES ?c { wd:Q21 wd:Q145 }
      ?l wdt:P17 ?c ; wdt:P641 wd:Q2736 ; rdfs:label ?lab .
      FILTER(LANG(?lab) = "en")
      FILTER(CONTAINS(LCASE(?lab), "premier league") || CONTAINS(LCASE(?lab), "championship"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }"""
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("EN-LEAGUE-SEARCH", err, len(rows))
    for r in rows[:60]:
        p("  ", q_(fc.cell(r, "l")), "|", fc.cell(r, "lLabel"), "| P17", q_(fc.cell(r, "c")))
    e = ents(list(EN_LEAGUES))
    for q, x in e.items():
        p("LEAGUE", q, lab(x), "| P31", vals(x, "P31")[:4], "| P17", vals(x, "P17"), "| P3983", vals(x, "P3983"),
          "| P3450", vals(x, "P3450")[-3:], "| P1132", vals(x, "P1132"), "| sitelinks", sitelinks(x))


EN_ROSTER = {}


def s2():
    for art, tier in [("2026–27 Premier League", 1), ("2026–27 EFL Championship", 2)]:
        page, real, err = cr.fetch_article(art)
        if err:
            p("ARTICLE", art, "ERROR", err); continue
        tables, shape = cr.roster_tables(page)
        p("ARTICLE", art, "->", real, "|", shape, "| tables", len(tables))
        names, caps = [], {}
        for t, h in tables:
            p("  HEAD", h[:8])
            left = []
            for title, cap in cr.rows_of(t, h, left):
                if title not in names: names.append(title); caps[title] = cap
            for x in left: p("  LEFT-OUT", x)
        got, fails = cr.qids_for_titles(names)
        p("RESOLVED", art, len(got), "of", len(names), "| failures", fails)
        for n in names:
            p("   ", got.get(n, "-"), "|", n, "|", caps.get(n))
            if got.get(n): EN_ROSTER.setdefault(got[n], []).append((tier, n, caps.get(n)))
        plain = cr.text_of(page)
        for kw in ("relegat", "promot", "withdr", "expel", "dissol", "administration", "deduct", "Welsh", "Wales", "groundshar", "temporar"):
            hits = [plain[max(0, m.start() - 150):m.start() + 150] for m in re.finditer(kw, plain, re.I)][:5]
            for h in hits: p("  CHANGE", tier, kw, "...", h)
        time.sleep(2)


def s3():
    for slug in ["eng", "gbr", "england", "uk"]:
        try:
            req = urllib.request.Request(f"https://stadiumdb.com/stadiums/{slug}", headers={"User-Agent": cr.USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode("utf-8", "replace"); st = r.status
        except urllib.error.HTTPError as ex:
            st, body = ex.code, ""
        except Exception as ex:
            st, body = str(ex), ""
        p("STADIUMDB", slug, st, len(body), body.count("<tr"))
        if st == 200 and body.count("<tr") > 3:
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S)
            for tr in rows[:400]:
                c = [cr.text_of(x) for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
                p("   SDB", " | ".join(c))
            break
        time.sleep(4)


def s4():
    if not EN_LEAGUES:
        p("NO EN LEAGUES"); return
    Q = """SELECT ?club ?league ?rank WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
    }""" % " ".join("wd:" + l for l in EN_LEAGUES)
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("TAGGED", err, len(rows))
    tags = {}
    for r in rows:
        tags.setdefault(q_(fc.cell(r, "club")), set()).add(
            (EN_LEAGUES.get(q_(fc.cell(r, "league"))), q_(fc.cell(r, "rank")).split("#")[-1][:4]))
    allq = set(tags) | set(EN_ROSTER)
    E = ents(sorted(allq))
    types = {}
    for q in sorted(allq, key=lambda q: lab(E.get(q, {})) or q):
        x = E.get(q, {})
        ty = [v[0] for v in vals(x, "P31")]
        if "Q5" in ty: continue
        for t in ty: types[t] = types.get(t, 0) + 1
        enl = [v for v in vals(x, "P118") if v[0] in EN_LEAGUES]
        p("ITEM", q, "|", lab(x), "| tags", sorted(tags.get(q, []), key=str), "| roster", EN_ROSTER.get(q),
          "| EN-P118", enl, "| nP118", len(vals(x, "P118")), "| P576", vals(x, "P576") or "-",
          "| P17", [v[0] for v in vals(x, "P17")],
          "| P115", [(v[0], v[1]) + ((v[2],) if len(v) > 2 else ()) for v in vals(x, "P115")],
          "| P625", [v[0] for v in vals(x, "P625")], "| P31", ty[:4],
          "| P831", [v[0] for v in vals(x, "P831")], "| P361", [v[0] for v in vals(x, "P361")][:3], "| sl", sitelinks(x))
    T = ents(list(types), props="labels")
    for t, n in sorted(types.items(), key=lambda kv: -kv[1]):
        p("TYPE", t, lab(T.get(t, {})), n)


def s5():
    # rule 6, deliberately: every item typed as a women's team or club carrying EITHER league at ANY rank,
    # and any roster item typed that way
    if not EN_LEAGUES: return
    Q = """SELECT DISTINCT ?club ?clubLabel ?league ?rank ?t ?tLabel WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
      ?club wdt:P31 ?t . ?t rdfs:label ?tl . FILTER(LANG(?tl) = "en")
      FILTER(CONTAINS(LCASE(?tl), "women") || CONTAINS(LCASE(?tl), "female") || CONTAINS(LCASE(?tl), "girls")
             || CONTAINS(LCASE(?tl), "ladies"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }""" % " ".join("wd:" + l for l in EN_LEAGUES)
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("WOMEN-TYPED", err, len(rows))
    for r in rows:
        p("WOMEN-ITEM", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"), "| league", q_(fc.cell(r, "league")),
          q_(fc.cell(r, "rank")).split("#")[-1], "| type", q_(fc.cell(r, "t")), fc.cell(r, "tLabel"))
    # and by NAME: an item whose label says women / ladies / WFC, whatever its type
    Q2 = """SELECT DISTINCT ?club ?clubLabel ?league ?rank WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank ; rdfs:label ?l .
      FILTER(LANG(?l) = "en")
      FILTER(CONTAINS(LCASE(?l), "women") || CONTAINS(LCASE(?l), "ladies") || CONTAINS(LCASE(?l), "w.f.c")
             || CONTAINS(LCASE(?l), " wfc") || CONTAINS(LCASE(?l), "girls"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }""" % " ".join("wd:" + l for l in EN_LEAGUES)
    res, err = fc.sparql_with_retry(Q2)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("WOMEN-NAMED", err, len(rows))
    for r in rows:
        p("WOMEN-NAMED-ITEM", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"), "| league", q_(fc.cell(r, "league")),
          q_(fc.cell(r, "rank")).split("#")[-1])


def s6():
    # the P582 measurement: truthy tags with end dates
    if not EN_LEAGUES: return
    Q = """SELECT ?club ?clubLabel ?league ?end ?endPrec ?start ?rank WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; a wikibase:BestRank ; wikibase:rank ?rank .
      OPTIONAL { ?st pqv:P582 ?ev . ?ev wikibase:timeValue ?end ; wikibase:timePrecision ?endPrec }
      OPTIONAL { ?st pq:P580 ?start }
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
      FILTER NOT EXISTS { ?club wdt:P576 ?d }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }""" % " ".join("wd:" + l for l in EN_LEAGUES)
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("P582-EN", err, len(rows))
    for r in rows:
        if fc.cell(r, "end") or fc.cell(r, "start"):
            p("P582-ROW", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"), EN_LEAGUES.get(q_(fc.cell(r, "league"))),
              (fc.cell(r, "start") or "")[:10], (fc.cell(r, "end") or "")[:10], fc.cell(r, "endPrec"),
              q_(fc.cell(r, "rank")).split("#")[-1])


for name, fn in [("0 extremes", s0), ("1 leagues", s1), ("2 articles", s2), ("4 items", s4),
                 ("5 women", s5), ("6 P582", s6), ("3 StadiumDB", s3)]:
    section(name, fn)
    time.sleep(2)
p("EN-TOP again", EN_LEAGUES)
p("=== END OF PROBE EN1 ===")
