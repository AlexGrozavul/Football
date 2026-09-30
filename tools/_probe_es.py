"""TEMPORARY probe #2 for the Spain pass. Removed in the same branch."""
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


def infobox(title, lang="en", keys=r"dissolved|league|season|position|ground|capacity|current|fullname|founded|stadium|name|opened|home|tenants|liga|temporada|posici|estadio|capacidad|desaparici|fundaci|categor|seating|record"):
    wt = wikitext(title, lang)
    keep = [l.strip() for l in wt.splitlines() if re.match(r"\s*\|\s*(%s)" % keys, l, re.I)]
    return " || ".join(keep)[:1100] if keep else ("(no infobox lines)" if wt else "(no article)")


def intro(title, lang="en", n=600):
    args = {"action": "query", "prop": "extracts", "exintro": "1", "explaintext": "1", "titles": title,
            "redirects": "1", "format": "json", "formatversion": "2"}
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    pages = (d or {}).get("query", {}).get("pages", [])
    return re.sub(r"\s+", " ", (pages[0].get("extract") if pages else "") or "")[:n]


SUSPECTS = ["Q582342", "Q11997", "Q11971", "Q10308", "Q10383", "Q108708", "Q11984", "Q12158", "Q11963", "Q847030",
            "Q12308", "Q843396", "Q12168", "Q1067737", "Q611653", "Q10467", "Q15966154", "Q515516",
            "Q2311865", "Q12260", "Q1386854", "Q1067750", "Q10300", "Q123750485"]


def t1():
    E = ents(SUSPECTS, props="claims|labels|sitelinks|descriptions")
    for q in SUSPECTS:
        x = E.get(q, {})
        s = x.get("sitelinks") or {}
        allp118 = vals(x, "P118")
        lg = ents([v[0] for v in allp118 if isinstance(v[0], str) and v[0].startswith("Q")], props="labels")
        p("SUSPECT", q, labs(x), "| desc", ((x.get("descriptions") or {}).get("en") or {}).get("value"),
          "| P31", [v[0] for v in vals(x, "P31")], "| P576", vals(x, "P576"),
          "| ALL-P118", [(v[0], lab(lg.get(v[0], {})), v[1:]) for v in allp118],
          "| P115", vals(x, "P115"), "| P831", vals(x, "P831"))
        for site in ("enwiki", "eswiki"):
            t = (s.get(site) or {}).get("title")
            if t:
                lang = site[:2]
                p("   ", site, t, "| INFOBOX", infobox(t, lang))
                p("   ", site, t, "| INTRO", intro(t, lang, 500))
        time.sleep(0.5)


def t2():
    # every item carrying either league, best rank, with end dates - the P582 measurement for Spain
    lg = {"Q324867": 1, "Q35615": 2}
    Q = """SELECT ?club ?league ?end ?endPrec ?start ?rank WHERE {
      VALUES ?league { wd:Q324867 wd:Q35615 }
      ?club p:P118 ?st . ?st ps:P118 ?league ; a wikibase:BestRank ; wikibase:rank ?rank .
      OPTIONAL { ?st pqv:P582 ?ev . ?ev wikibase:timeValue ?end ; wikibase:timePrecision ?endPrec }
      OPTIONAL { ?st pq:P580 ?start }
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
      FILTER NOT EXISTS { ?club wdt:P576 ?d }
    }"""
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("P582-ES", err, len(rows))
    for r in rows:
        p("P582-ROW", q_(fc.cell(r, "club")), lg.get(q_(fc.cell(r, "league"))), (fc.cell(r, "start") or "")[:10],
          (fc.cell(r, "end") or "")[:10], fc.cell(r, "endPrec"), q_(fc.cell(r, "rank")).split("#")[-1])


def t3():
    # the grounds named for clubs in both 2026-27 tables, for positions and capacities
    for t in ["Estadio de Vallecas", "Butarque Stadium", "Estadio de La Cartuja", "Estadio Benito Villamarín",
              "Zubieta Facilities", "Estadi de la FAF", "Nou Estadi Encamp", "Balaídos Stadium", "Estadio Abanca-Balaídos",
              "Estadi de la Nova Creu Alta", "Estadio Alfonso Murube", "Nuevo Pepico Amat", "Bernabéu (stadium)",
              "Camp Nou", "Estadi Olímpic Lluís Companys", "Anoeta Stadium", "Metropolitano Stadium"]:
        p("INFOBOX-GROUND", t, "|", infobox(t, keys=r"capacity|coordinates|coord|tenants|opened|renovated|name|fullname|seating|record"))
        time.sleep(0.4)


for name, fn in [("t1 suspects", t1), ("t2 P582", t2), ("t3 grounds", t3)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE ES2 ===")
