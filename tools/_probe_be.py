"""TEMPORARY probe #1 for the Belgium pass. Removed in the same branch."""
import csv, glob, json, os, re, sys, time, traceback, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc


def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

LANGS = "en|nl|fr|de"


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


def lab(ent, order=("en", "nl", "fr", "de")):
    for l in order:
        v = (ent.get("labels", {}).get(l) or {}).get("value")
        if v: return v
    return None


def labs(ent):
    return {l: v["value"] for l, v in ent.get("labels", {}).items()}


def vals(ent, prop):
    out = []
    for c in ent.get("claims", {}).get(prop, []):
        v = c["mainsnak"].get("datavalue", {}).get("value")
        if v is None: v = c["mainsnak"].get("snaktype")
        elif isinstance(v, dict) and "latitude" in v: v = (round(v["latitude"], 6), round(v["longitude"], 6))
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


def sparql(q, tag):
    res, err = fc.sparql_with_retry(q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p(tag, "err=", err, "rows=", len(rows))
    return rows


def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None


EN_LEAGUES = {}
EN_ROSTER = {}


def s0():
    E = ents(["Q31"])
    x = E.get("Q31", {})
    p("EXTREME Q31", lab(x), [(pr, vals(x, pr)) for pr in ("P1332", "P1333", "P1334", "P1335")])


def s1():
    for t, tier in [("Belgian Pro League", 1), ("Challenger Pro League", 2), ("Belgian First Division A", 1),
                    ("Belgian First Division B", 2)]:
        q = qid_for(t)
        p("ENWIKI", t, "->", q)
        if q and q not in EN_LEAGUES: EN_LEAGUES[q] = tier
    rows = sparql("""SELECT DISTINCT ?l ?lLabel WHERE {
      ?l wdt:P17 wd:Q31 ; wdt:P641 wd:Q2736 .
      ?l wdt:P31/wdt:P279* wd:Q15991303 .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,nl,fr" }
    }""", "BE-LEAGUES")
    for r in rows[:120]:
        p("  ", q_(fc.cell(r, "l")), "|", fc.cell(r, "lLabel"))
    e = ents(list(EN_LEAGUES))
    for q, x in e.items():
        p("LEAGUE", q, labs(x), "| P31", vals(x, "P31")[:4], "| P17", vals(x, "P17"), "| P3983", vals(x, "P3983"),
          "| P3450", vals(x, "P3450")[-3:], "| P1132", vals(x, "P1132"), "| sitelinks", sitelinks(x),
          "| P2094", vals(x, "P2094"))


def s2():
    tries = [(1, ["2026–27 Belgian Pro League", "2026–27 Belgian First Division A"]),
             (2, ["2026–27 Challenger Pro League", "2026–27 Belgian Challenger Pro League", "2026–27 Belgian First Division B"])]
    for tier, arts in tries:
        for art in arts:
            page, real, err = cr.fetch_article(art)
            if err:
                p("ARTICLE", art, "ERROR", err); time.sleep(1); continue
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
            for kw in ("relegat", "promot", "withdr", "expel", "dissol", "bankrupt", "licen", "U23", "Futures",
                       "reserve", "temporar", "merg", "renamed"):
                hits = [plain[max(0, m.start() - 160):m.start() + 160] for m in re.finditer(kw, plain, re.I)][:6]
                for h in hits: p("  CHANGE", tier, kw, "...", h)
            time.sleep(2)
            break


def s3():
    for slug in ["bel", "bgm", "blg", "be", "belgium"]:
        try:
            req = urllib.request.Request(f"https://stadiumdb.com/stadiums/{slug}", headers={"User-Agent": cr.USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode("utf-8", "replace"); st = r.status
        except urllib.error.HTTPError as ex:
            st, body = ex.code, ""
        except Exception as ex:
            st, body = str(ex), ""
        p("STADIUMDB", slug, st, len(body), body.count("<tr"), body.count("<table"))
        if st == 200 and body.count("<tr") > 3:
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S)
            for tr in rows[:400]:
                c = [cr.text_of(x) for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
                p("   SDB", " | ".join(c))
            break
        time.sleep(4)


TAGGED = {}


def s4():
    if not EN_LEAGUES:
        p("NO EN LEAGUES"); return
    rows = sparql("""SELECT ?club ?league ?rank WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
    }""" % " ".join("wd:" + l for l in EN_LEAGUES), "TAGGED")
    for r in rows:
        TAGGED.setdefault(q_(fc.cell(r, "club")), set()).add(
            (EN_LEAGUES.get(q_(fc.cell(r, "league"))), q_(fc.cell(r, "league")), q_(fc.cell(r, "rank")).split("#")[-1][:4]))
    allq = set(TAGGED) | set(EN_ROSTER)
    E = ents(sorted(allq))
    types = {}
    for q in sorted(allq, key=lambda q: lab(E.get(q, {})) or q):
        x = E.get(q, {})
        ty = [v[0] for v in vals(x, "P31")]
        if "Q5" in ty: continue
        for t in ty: types[t] = types.get(t, 0) + 1
        enl = [v for v in vals(x, "P118") if v[0] in EN_LEAGUES]
        p("ITEM", q, "|", labs(x), "| tags", sorted(TAGGED.get(q, []), key=str), "| roster", EN_ROSTER.get(q),
          "| EN-P118", enl, "| nP118", len(vals(x, "P118")), "| P118-all", [v[0] for v in vals(x, "P118")][:8],
          "| P576", vals(x, "P576") or "-",
          "| P17", [v[0] for v in vals(x, "P17")],
          "| P115", [(v[0], v[1]) + ((v[2],) if len(v) > 2 else ()) for v in vals(x, "P115")],
          "| P625", [v[0] for v in vals(x, "P625")], "| P31", ty[:5],
          "| P831", [v[0] for v in vals(x, "P831")], "| P361", [v[0] for v in vals(x, "P361")][:3],
          "| P2094", [v[0] for v in vals(x, "P2094")], "| sl", sitelinks(x))
        # not-a-club net, every label language the builder could see
        for lg, nm in labs(x).items():
            r = fc.not_a_club(nm, [])
            if r or re.search(r"seizoen|saison|season|histor|geschiedenis|wedstrijd|match|fictie|fictional|lijst|liste|list", nm, re.I):
                p("   NAMECHECK", q, lg, repr(nm), "-> CAUGHT" if r else "-> NOT CAUGHT")
    T = ents(list(types), props="labels")
    for t, n in sorted(types.items(), key=lambda kv: -kv[1]):
        tl = lab(T.get(t, {}))
        p("TYPE", t, tl, n, "| not_a_club:", bool(fc.not_a_club(None, [tl or ""])))


def s5():
    if not EN_LEAGUES: return
    L = " ".join("wd:" + l for l in EN_LEAGUES)
    rows = sparql("""SELECT DISTINCT ?club ?clubLabel ?league ?rank ?t ?tLabel WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
      ?club wdt:P31 ?t . ?t rdfs:label ?tl . FILTER(LANG(?tl) = "en")
      FILTER(CONTAINS(LCASE(?tl), "women") || CONTAINS(LCASE(?tl), "female") || CONTAINS(LCASE(?tl), "girls")
             || CONTAINS(LCASE(?tl), "ladies"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }""" % L, "WOMEN-TYPED")
    for r in rows:
        p("WOMEN-ITEM", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"), "| league", q_(fc.cell(r, "league")),
          q_(fc.cell(r, "rank")).split("#")[-1], "| type", fc.cell(r, "tLabel"))
    rows = sparql("""SELECT DISTINCT ?club ?clubLabel ?league ?rank ?l WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
      ?club rdfs:label|skos:altLabel|schema:description ?l .
      FILTER(LANG(?l) IN ("en", "nl", "fr", "de"))
      FILTER(CONTAINS(LCASE(?l), "women") || CONTAINS(LCASE(?l), "ladies") || CONTAINS(LCASE(?l), "vrouwen")
             || CONTAINS(LCASE(?l), "dames") || CONTAINS(LCASE(?l), "féminin") || CONTAINS(LCASE(?l), "feminin")
             || CONTAINS(LCASE(?l), "femmes") || CONTAINS(LCASE(?l), "frauen") || CONTAINS(LCASE(?l), "girls")
             || CONTAINS(LCASE(?l), " wfc") || CONTAINS(LCASE(?l), "w.f.c"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }""" % L, "WOMEN-NAMED-OR-DESCRIBED")
    for r in rows:
        p("WOMEN-NAMED-ITEM", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"), "| league", q_(fc.cell(r, "league")),
          q_(fc.cell(r, "rank")).split("#")[-1], "|", fc.cell(r, "l"))
    rows = sparql("""SELECT DISTINCT ?club ?clubLabel ?c ?cLabel WHERE {
      VALUES ?league { %s }
      ?club p:P118/ps:P118 ?league . ?club wdt:P2094 ?c .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" } }""" % L, "P2094-ON-TAGGED")
    for r in rows: p("  C", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"), fc.cell(r, "cLabel"))


def s5b():
    # fourth angle: women's items pointing at roster clubs by P831/P361
    if not EN_ROSTER: p("NO ROSTER"); return
    ids = " ".join("wd:" + q for q in EN_ROSTER)
    rows = sparql("""SELECT DISTINCT ?team ?teamLabel ?club ?clubLabel ?rel ?tLabel WHERE {
      VALUES ?club { %s }
      { ?team wdt:P831 ?club . BIND("P831" AS ?rel) } UNION { ?team wdt:P361 ?club . BIND("P361" AS ?rel) }
      OPTIONAL { ?team wdt:P31 ?t . }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,nl,fr" } }""" % ids, "ITEMS-POINTING-AT-ROSTER-CLUBS")
    for r in rows:
        p("  P", q_(fc.cell(r, "team")), fc.cell(r, "teamLabel"), "->", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"),
          fc.cell(r, "rel"), "| type", fc.cell(r, "tLabel"))
    teams = sorted({q_(fc.cell(r, "team")) for r in rows})
    E = ents(teams)
    for q in teams:
        x = E.get(q, {})
        p("  POINTER-P118", q, lab(x), vals(x, "P118"), "| P2094", vals(x, "P2094"), "| P625", vals(x, "P625"))


def s6():
    if not EN_LEAGUES: return
    rows = sparql("""SELECT ?club ?clubLabel ?league ?end ?endPrec ?start ?rank WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; a wikibase:BestRank ; wikibase:rank ?rank .
      OPTIONAL { ?st pqv:P582 ?ev . ?ev wikibase:timeValue ?end ; wikibase:timePrecision ?endPrec }
      OPTIONAL { ?st pq:P580 ?start }
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
      FILTER NOT EXISTS { ?club wdt:P576 ?d }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,nl,fr" }
    }""" % " ".join("wd:" + l for l in EN_LEAGUES), "P582-BE")
    n = 0
    for r in rows:
        n += 1
        p("P582-ROW", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"), EN_LEAGUES.get(q_(fc.cell(r, "league"))),
          (fc.cell(r, "start") or "")[:10], (fc.cell(r, "end") or "")[:10], fc.cell(r, "endPrec"),
          q_(fc.cell(r, "rank")).split("#")[-1])


for name, fn in [("0 extremes", s0), ("1 leagues", s1), ("2 articles", s2), ("4 items", s4),
                 ("5 women", s5), ("5b pointing", s5b), ("6 P582", s6), ("3 StadiumDB", s3)]:
    section(name, fn)
    time.sleep(2)
p("EN-TOP again", EN_LEAGUES)
p("=== END OF PROBE BE1 ===")
