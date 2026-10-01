"""TEMPORARY probe #5 for the Belgium pass. Removed in the same branch."""
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


def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None



def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None


def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None




def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None


def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None



def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None


def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None






ROSTER = """Q187528 Q732002 Q509170 Q364698 Q19585 Q190916 Q216032 Q18232 Q618620 Q536651 Q1668203 Q113000 Q916199 Q138248 Q190561 Q196160 Q849544 Q376635
Q2268833 Q1065328 Q1423718 Q18001655 Q650917 Q95183770 Q2456491 Q1347229 Q2313985 Q2308515 Q925973 Q101625593 Q113884742 Q117384089 Q114056326""".split()


def a_same_label():
    E = ents(ROSTER, props="labels")
    labels = set()
    for q in ROSTER:
        for l, v in E.get(q, {}).get("labels", {}).items():
            labels.add((v["value"].replace('"', ''), l))
    vals_ = " ".join('"%s"@%s' % lv for lv in sorted(labels))
    rows = sparql("""SELECT DISTINCT ?x ?xLabel ?t ?tLabel WHERE {
      VALUES ?lab { %s } ?x rdfs:label ?lab . ?x wdt:P31 ?t .
      VALUES ?t { wd:Q476028 wd:Q103229495 wd:Q14752149 wd:Q2412834 wd:Q847017 wd:Q15944511 wd:Q4438121 wd:Q31855 wd:Q783794 wd:Q891723 wd:Q20639856 }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,nl,fr" } }""" % vals_, "SAME-LABEL-ITEMS")
    seen = {}
    for r in rows: seen.setdefault((q_(fc.cell(r, "x")), fc.cell(r, "xLabel")), []).append(fc.cell(r, "tLabel"))
    for (q, l), ts in sorted(seen.items(), key=lambda kv: kv[0][1] or ""):
        p("  SL", q, l, ts, "ON-ROSTER" if q in ROSTER else "NOT-ON-ROSTER")


def b_women_pointing():
    ids = " ".join("wd:" + q for q in ROSTER)
    rows = sparql("""SELECT DISTINCT ?team ?teamLabel ?club ?rel ?tLabel WHERE {
      VALUES ?club { %s }
      { ?team wdt:P831 ?club . BIND("P831" AS ?rel) } UNION { ?team wdt:P361 ?club . BIND("P361" AS ?rel) }
      UNION { ?team wdt:P749 ?club . BIND("P749" AS ?rel) } UNION { ?team wdt:P127 ?club . BIND("P127" AS ?rel) }
      ?team wdt:P31 ?t . ?t rdfs:label ?tl . FILTER(LANG(?tl) = "en")
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,nl,fr" } }""" % ids, "ALL-POINTING-AT-ROSTER")
    for r in rows:
        p("  P", q_(fc.cell(r, "team")), fc.cell(r, "teamLabel"), "->", q_(fc.cell(r, "club")), fc.cell(r, "rel"),
          "| type", fc.cell(r, "tLabel"))


for name, fn in [("a same label", a_same_label), ("b pointing", b_women_pointing)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE BE5 ===")
