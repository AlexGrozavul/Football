"""TEMPORARY probe #1 for the Spain pass. Removed in the same branch."""
import csv, glob, json, os, re, sys, time, traceback, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc

TODAY = "2026-09-30"


def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

LANGS = "en|es|ca"


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


def lab(ent, order=("en", "es", "ca")):
    for l in order:
        v = (ent.get("labels", {}).get(l) or {}).get("value")
        if v: return v
    return None


def labs(ent):
    return {l: (ent.get("labels", {}).get(l) or {}).get("value") for l in ("en", "es")
            if (ent.get("labels", {}).get(l) or {}).get("value")}


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
    return len(s), (s.get("enwiki") or {}).get("title"), (s.get("eswiki") or {}).get("title")


def section(name, fn):
    p(f"########## {name}")
    try:
        fn()
    except Exception:
        p("SECTION-FAILED", name, traceback.format_exc()[-800:])



ES_LEAGUES = {}


def s0():
    E = ents(["Q29"])
    x = E.get("Q29", {})
    for pr in ("P1332", "P1333", "P1334", "P1335"):
        p("EXTREME", pr, vals(x, pr))


def s1():
    Q = """SELECT ?l ?lLabel ?level ?en ?type WHERE {
      ?l wdt:P17 wd:Q29 ; wdt:P641 wd:Q2736 .
      OPTIONAL { ?l wdt:P3983 ?level }
      OPTIONAL { ?l wdt:P31 ?type }
      OPTIONAL { ?en schema:about ?l ; schema:isPartOf <https://en.wikipedia.org/> }
      ?l rdfs:label ?lab .
      FILTER(LANG(?lab) IN ("en", "es"))
      FILTER(CONTAINS(LCASE(?lab), "la liga") || CONTAINS(LCASE(?lab), "laliga")
             || CONTAINS(LCASE(?lab), "segunda") || CONTAINS(LCASE(?lab), "primera"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,es" }
    }"""
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("ES-LEAGUES", err, len(rows))
    seen = {}
    for r in rows:
        k = q_(fc.cell(r, "l"))
        s = seen.setdefault(k, [fc.cell(r, "lLabel"), set(), fc.cell(r, "en"), set()])
        if fc.cell(r, "level"): s[1].add(fc.cell(r, "level"))
        if fc.cell(r, "type"): s[3].add(q_(fc.cell(r, "type")))
    for k, (lb, lev, en, ty) in sorted(seen.items(), key=lambda kv: str(sorted(kv[1][1]))):
        p("  ", k, "|", lb, "| level", sorted(lev), "|", en, "|", sorted(ty))
    for k, v in seen.items():
        en = urllib.parse.unquote(v[2] or "")
        if en.endswith("/La_Liga"): ES_LEAGUES[k] = 1
        if en.endswith("/Segunda_División"): ES_LEAGUES[k] = 2
    p("ES-TOP", ES_LEAGUES)
    e = ents(list(ES_LEAGUES))
    for q, x in e.items():
        p("LEAGUE", q, labs(x), "| P31", vals(x, "P31"), "| P17", vals(x, "P17"), "| P3983", vals(x, "P3983"),
          "| P3450", vals(x, "P3450")[-3:], "| P1132", vals(x, "P1132"), "| sitelinks", sitelinks(x))


ES_ROSTER = {}


def s2():
    for art, tier in [("2026–27 La Liga", 1), ("2026–27 Segunda División", 2)]:
        page, real, err = cr.fetch_article(art)
        if err:
            p("ARTICLE", art, "ERROR", err); continue
        tables, shape = cr.roster_tables(page)
        p("ARTICLE", art, "->", real, "|", shape, "| tables", len(tables))
        names, caps = [], {}
        for t, h in tables:
            p("  HEAD", h[:8])
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)[1:]:
                cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)
                links = re.findall(r'<a[^>]+href="/wiki/([^"#:]+)"', tr)
                p("  ROW", tier, [cr.text_of(c)[:40] for c in cells][:6], "| links",
                  [urllib.parse.unquote(l) for l in links][:3])
            left = []
            for title, cap in cr.rows_of(t, h, left):
                if title not in names: names.append(title); caps[title] = cap
            for x in left: p("  LEFT-OUT", x)
        got, fails = cr.qids_for_titles(names)
        p("RESOLVED", art, len(got), "of", len(names), "| failures", fails)
        for n in names:
            p("   ", got.get(n, "-"), "|", n, "|", caps.get(n))
            if got.get(n): ES_ROSTER.setdefault(got[n], []).append((tier, n, caps.get(n)))
        plain = cr.text_of(page)
        for kw in ("relegat", "promot", "withdr", "exclu", "dissol", "licen", "merg", "renam", "deduct", "reserve"):
            hits = [plain[max(0, m.start() - 160):m.start() + 160] for m in re.finditer(kw, plain, re.I)][:6]
            for h in hits: p("  CHANGE", tier, kw, "...", h)
        time.sleep(2)


def s3():
    for slug in ["esp", "spa", "spain", "es"]:
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
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S)[:250]:
                p("   SDB", [cr.text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)])
            break
        time.sleep(4)


def s4():
    if not ES_LEAGUES:
        p("NO ES LEAGUES"); return
    Q = """SELECT ?club ?league ?rank WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
    }""" % " ".join("wd:" + l for l in ES_LEAGUES)
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("TAGGED", err, len(rows))
    tags = {}
    for r in rows:
        tags.setdefault(q_(fc.cell(r, "club")), set()).add(
            (ES_LEAGUES.get(q_(fc.cell(r, "league"))), q_(fc.cell(r, "rank")).split("#")[-1][:4]))
    allq = set(tags) | set(ES_ROSTER)
    E = ents(sorted(allq))
    venues = []
    for q in sorted(allq, key=lambda q: lab(E.get(q, {})) or q):
        x = E.get(q, {})
        types = [v[0] for v in vals(x, "P31")]
        if "Q5" in types: continue
        esl = [v for v in vals(x, "P118") if v[0] in ES_LEAGUES]
        venues += [v[0] for v in vals(x, "P115") if isinstance(v[0], str) and v[0].startswith("Q")]
        p("ITEM", q, "|", labs(x), "| tags", sorted(tags.get(q, []), key=str), "| roster", ES_ROSTER.get(q),
          "| ES-P118", esl, "| nP118", len(vals(x, "P118")), "| P576", vals(x, "P576") or "-",
          "| P17", [v[0] for v in vals(x, "P17")],
          "| P115", vals(x, "P115"), "| P625", vals(x, "P625"), "| P31", types[:4],
          "| P831", vals(x, "P831"), "| P361", vals(x, "P361")[:3], "| sl", sitelinks(x))
    G = ents(venues)
    for q, x in G.items():
        p("GROUND", q, "|", labs(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083")[:4],
          "| P131", [v[0] for v in vals(x, "P131")][:2], "| sl", sitelinks(x)[:2])


for name, fn in [("0 ES extremes", s0), ("1 ES leagues", s1), ("2 ES articles", s2), ("3 ES StadiumDB", s3),
                 ("4 ES items", s4)]:
    section(name, fn)
    time.sleep(2)
p("ES-TOP again", ES_LEAGUES)
p("=== END OF PROBE ES1 ===")
