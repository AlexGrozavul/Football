"""TEMPORARY probe #3 for the Spain pass. Removed in the same branch."""
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





def wikitext(title, lang="en"):
    args = {"action": "parse", "page": title, "prop": "wikitext", "redirects": "1", "format": "json", "formatversion": "2"}
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    return ((d or {}).get("parse") or {}).get("wikitext") or ""


def infobox(title, lang="en", keys=r"ground|stadium|capacity|coordinates|coord|tenants|opened|closed|demolish|name|fullname|estadio|capacidad"):
    wt = wikitext(title, lang)
    keep = [l.strip() for l in wt.splitlines() if re.match(r"\s*\|\s*(%s)" % keys, l, re.I)]
    return " || ".join(keep)[:1200] if keep else ("(no infobox lines)" if wt else "(no article)")


def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None


def t1():
    for t in ["Real Betis", "FC Andorra", "RCD Espanyol", "UD Almería", "RC Celta Fortuna", "CE Sabadell FC"]:
        p("CLUB-INFOBOX", t, "|", infobox(t))
        time.sleep(0.4)
    for t in ["Real Betis Balompié", "Futbol Club Andorra", "Real Club Deportivo Espanyol de Barcelona", "Unión Deportiva Almería"]:
        p("CLUB-INFOBOX-ES", t, "|", infobox(t, "es"))
        time.sleep(0.4)
    titles = ["Estadio de La Cartuja", "Estadio Benito Villamarín", "Estadi de la FAF", "Estadi Nacional (Andorra)",
              "RCDE Stadium", "Estadi de Sarrià", "UD Almería Stadium", "Balaídos Stadium", "Estadi de la Nova Creu Alta"]
    qs = {}
    for t in titles:
        qs[t] = qid_for(t); time.sleep(0.3)
    E = ents([q for q in qs.values() if q] + ["Q18125598", "Q473223", "Q1325234", "Q126844", "Q1130617", "Q1326578",
                                               "Q3393440", "Q1313926"])
    for q, x in E.items():
        p("GROUND", q, labs(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083")[:5], "| P131",
          [v[0] for v in vals(x, "P131")][:2], "| P576", vals(x, "P576"), "| P5817", vals(x, "P5817"),
          "| sl", sitelinks(x))
    p("GROUND-TITLES", qs)
    for t in ["Estadio de La Cartuja", "Estadi de la FAF", "RCDE Stadium"]:
        p("GROUND-INFOBOX", t, "|", infobox(t))


def t2():
    # rule 6: items carrying ANY mapped league whose type is a women's team or club, in every country
    tiers = {}
    with open("data/league-tiers.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["tier"].strip().isdigit():
                tiers[r["leagueQid"].strip()] = (r["tier"].strip(), r["country"].strip())
    Q = """SELECT DISTINCT ?club ?clubLabel ?league ?t ?tLabel WHERE {
      VALUES ?league { %s }
      ?club wdt:P118 ?league ; wdt:P31 ?t .
      ?t rdfs:label ?tl . FILTER(LANG(?tl) = "en")
      FILTER(CONTAINS(LCASE(?tl), "women") || CONTAINS(LCASE(?tl), "female") || CONTAINS(LCASE(?tl), "girls"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,es,de,fr,it,ro" }
    }""" % " ".join("wd:" + l for l in tiers)
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("WOMEN", err, len(rows))
    onmap = {}
    for f in glob.glob("data/clubs/[A-Z][A-Z].json"):
        for c in json.load(open(f, encoding="utf-8")).get("clubs", []):
            onmap[c["id"]] = os.path.basename(f)[:2]
    for r in rows:
        c = q_(fc.cell(r, "club")); lg = q_(fc.cell(r, "league"))
        p("WOMEN-ITEM", c, fc.cell(r, "clubLabel"), "| league", lg, tiers.get(lg), "| type", q_(fc.cell(r, "t")),
          fc.cell(r, "tLabel"), "| on map:", onmap.get(c, "no"))
    # and the match-item type, to see if it is on any map
    Q2 = """SELECT DISTINCT ?club ?clubLabel ?t ?tLabel WHERE {
      VALUES ?league { %s }
      ?club wdt:P118 ?league ; wdt:P31 ?t .
      ?t rdfs:label ?tl . FILTER(LANG(?tl) = "en")
      FILTER(CONTAINS(LCASE(?tl), "match") || CONTAINS(LCASE(?tl), "game") || CONTAINS(LCASE(?tl), "final"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }""" % " ".join("wd:" + l for l in tiers)
    res, err = fc.sparql_with_retry(Q2)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("MATCHTYPE", err, len(rows))
    for r in rows:
        c = q_(fc.cell(r, "club"))
        p("MATCH-ITEM", c, fc.cell(r, "clubLabel"), "| type", q_(fc.cell(r, "t")), fc.cell(r, "tLabel"),
          "| on map:", onmap.get(c, "no"))


for name, fn in [("t1 grounds", t1), ("t2 women and matches", t2)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE ES3 ===")
