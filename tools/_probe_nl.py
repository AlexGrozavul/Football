"""TEMPORARY probe #2 for the Netherlands pass. Removed in the same branch."""
import csv, glob, json, os, re, sys, time, traceback, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc


def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

LANGS = "en|nl"
ROSTER = """Q24904 Q81888 Q191264 Q875120 Q370712 Q134241 Q854167 Q749589 Q24711 Q200321 Q318348 Q269151 Q11938 Q209895 Q1071713 Q19603 Q24680 Q332664
Q653119 Q221927 Q875169 Q1045811 Q876699 Q1061627 Q636315 Q11961 Q1770361 Q50573061 Q13534332 Q24068131 Q876568 Q332642 Q24699 Q24719 Q1149034 Q219233 Q738060 Q24689""".split()
LEAGUES = ["Q167541", "Q610823"]
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


def lab(ent, order=("en", "nl")):
    for l in order:
        v = (ent.get("labels", {}).get(l) or {}).get("value")
        if v: return v
    return None


def labs(ent):
    return {l: (ent.get("labels", {}).get(l) or {}).get("value") for l in ("en", "el")
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
    return len(s), (s.get("enwiki") or {}).get("title"), (s.get("elwiki") or {}).get("title")




def section(name, fn):
    p(f"########## {name}")
    try:
        fn()
    except Exception:
        p("SECTION-FAILED", name, traceback.format_exc()[-800:])


def wikitext(title, lang="en", section="0"):
    args = {"action": "parse", "page": title, "prop": "wikitext", "format": "json",
            "formatversion": "2", "redirects": "1"}
    if section is not None: args["section"] = section
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    return (d or {}).get("parse", {}).get("wikitext", "")


def infobox(title, lang="en", keys=r"dissolved|league|season|position|ground|capacity|coordinates|current|fullname|founded|stadium|name|opened|location|home|tenants|ligue|competitie|opgeheven|stadion|opgericht|fusie|merger|defunct|ceased|defunct|last"):
    wt = wikitext(title, lang)
    keep = [l.strip() for l in wt.splitlines() if re.match(r"\s*\|\s*(%s)" % keys, l, re.I)]
    return " || ".join(keep)[:1100] if keep else ("(no infobox lines)" if wt else "(no article)")


def intro(title, lang="en", n=800):
    args = {"action": "query", "prop": "extracts", "exintro": "1", "explaintext": "1", "titles": title,
            "redirects": "1", "format": "json", "formatversion": "2"}
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    pages = (d or {}).get("query", {}).get("pages", [])
    return re.sub(r"\s+", " ", (pages[0].get("extract") if pages else "") or "")[:n]


def sparql(q, tag):
    res, err = fc.sparql_with_retry(q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p(tag, "err=", err, "rows=", len(rows))
    return rows


def a_pages():
    for t, lang in [("Achilles '29", "en"), ("Achilles '29", "nl"), ("VV DOS", "en"), ("Jong FC Twente", "en"),
                    ("FC Volendam", "en"), ("Jong Ajax", "en"), ("Jong AZ", "en"), ("Jong PSV", "en"),
                    ("Jong FC Utrecht", "en"), ("Jong FC Twente", "nl")]:
        p("PAGE", lang, t, "| INFOBOX", infobox(t, lang))
        p("   INTRO", intro(t, lang))
        time.sleep(1)


def b_unknown():
    E = ents(["Q134609074", "Q14229572", "Q2426022", "Q784572"], props="claims|labels|descriptions|aliases|sitelinks")
    for q, x in E.items():
        p("ITEM", q, "labels", {k: v["value"] for k, v in x.get("labels", {}).items()},
          "| desc", {k: v["value"] for k, v in x.get("descriptions", {}).items()},
          "| aliases", {k: [a["value"] for a in v] for k, v in x.get("aliases", {}).items()},
          "| sitelinks", {k: v["title"] for k, v in (x.get("sitelinks") or {}).items()},
          "| props", sorted(x.get("claims", {}).keys()))
        for pr in ("P31", "P17", "P118", "P571", "P576", "P159", "P115", "P625", "P1366", "P1365", "P138", "P1448", "P1559"):
            if pr in x.get("claims", {}): p("    ", q, pr, vals(x, pr))


def c_women():
    ids = " ".join("wd:" + q for q in ROSTER)
    rows = sparql("""SELECT DISTINCT ?team ?teamLabel ?club ?clubLabel ?t ?tLabel ?rel WHERE {
      VALUES ?club { %s }
      { ?team wdt:P831 ?club . BIND("P831" AS ?rel) } UNION { ?team wdt:P361 ?club . BIND("P361" AS ?rel) }
      ?team wdt:P31 ?t . ?t rdfs:label ?tl . FILTER(LANG(?tl) = "en")
      FILTER(CONTAINS(LCASE(?tl), "women") || CONTAINS(LCASE(?tl), "female"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }""" % ids, "WOMEN-POINTING-AT-ROSTER-CLUBS")
    for r in rows:
        p("  W", q_(fc.cell(r, "team")), fc.cell(r, "teamLabel"), "->", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"),
          fc.cell(r, "rel"), "| type", fc.cell(r, "tLabel"))
    wq = sorted({q_(fc.cell(r, "team")) for r in rows})
    E = ents(wq)
    for q in wq:
        x = E.get(q, {})
        p("  W-P118", q, lab(x), [v for v in vals(x, "P118")], "| P2094", vals(x, "P2094"))
    # P2094 on every tagged item: competition class
    rows = sparql("""SELECT DISTINCT ?club ?clubLabel ?c ?cLabel WHERE {
      VALUES ?league { wd:Q167541 wd:Q610823 }
      ?club wdt:P118|p:P118/ps:P118 ?league . ?club wdt:P2094 ?c .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" } }""", "P2094-ON-TAGGED")
    for r in rows: p("  C", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"), fc.cell(r, "cLabel"))
    # any women's-typed item at all that carries either league at any rank, by P118 statement
    rows = sparql("""SELECT DISTINCT ?club ?clubLabel ?t ?tLabel WHERE {
      VALUES ?league { wd:Q167541 wd:Q610823 }
      ?club p:P118/ps:P118 ?league ; wdt:P31 ?t .
      ?t rdfs:label ?tl . FILTER(LANG(?tl) = "en" && (CONTAINS(LCASE(?tl), "wom") || CONTAINS(LCASE(?tl), "fem")))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" } }""", "WOMEN-TYPED-AGAIN")
    for r in rows: p("  X", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"), fc.cell(r, "tLabel"))


def d_shapes():
    ids = " ".join("wd:" + q for q in ROSTER)
    # shape 5: men's team items pointing at roster clubs
    rows = sparql("""SELECT DISTINCT ?team ?teamLabel ?club ?clubLabel ?rel ?tLabel WHERE {
      VALUES ?club { %s }
      { ?team wdt:P831 ?club . BIND("P831" AS ?rel) } UNION { ?team wdt:P361 ?club . BIND("P361" AS ?rel) }
      ?team wdt:P31 ?t .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" } }""" % ids, "ITEMS-POINTING-AT-ROSTER-CLUBS")
    for r in rows:
        p("  P", q_(fc.cell(r, "team")), fc.cell(r, "teamLabel"), "->", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"),
          fc.cell(r, "rel"), "| type", fc.cell(r, "tLabel"))
    # shapes 1/2/3: other items with the SAME English label as a roster club
    E = ents(ROSTER, props="labels")
    labs_ = sorted({lab(E[q]) for q in ROSTER if q in E and lab(E[q])})
    vals_ = " ".join('"%s"@en' % l.replace('"', '') for l in labs_)
    rows = sparql("""SELECT DISTINCT ?x ?xLabel ?t ?tLabel WHERE {
      VALUES ?lab { %s } ?x rdfs:label ?lab . ?x wdt:P31 ?t .
      VALUES ?t { wd:Q476028 wd:Q103229495 wd:Q14752149 wd:Q2412834 wd:Q847017 wd:Q15944511 wd:Q4438121 wd:Q31855 wd:Q783794 wd:Q891723 }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" } }""" % vals_, "SAME-LABEL-ITEMS")
    seen = {}
    for r in rows: seen.setdefault((q_(fc.cell(r, "x")), fc.cell(r, "xLabel")), []).append(fc.cell(r, "tLabel"))
    for (q, l), ts in sorted(seen.items(), key=lambda kv: kv[0][1]):
        p("  SL", q, l, ts, "ON-ROSTER" if q in ROSTER else "NOT-ON-ROSTER")


def e_grounds():
    ids = ["Q2200744", "Q108060876", "Q1958120", "Q3264211", "Q1067235", "Q14852091", "Q132997935", "Q1140346"]
    E = ents(ids)
    for q in ids:
        x = E.get(q, {})
        p("GROUND", q, lab(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083"), "| P131", vals(x, "P131")[:2],
          "| P31", [v[0] for v in vals(x, "P31")][:3], "| P576", vals(x, "P576"))


for name, fn in [("a pages", a_pages), ("b unknown items", b_unknown), ("c women", c_women), ("d shapes", d_shapes),
                 ("e grounds", e_grounds)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE NL2 ===")
