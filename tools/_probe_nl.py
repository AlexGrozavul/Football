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
    for t, lang in [("VV DOS", "nl"), ("VV DOS", "de"), ("VCV Zeeland", "nl"), ("DOS Utrecht", "fr")]:
        p("PAGE", lang, t, "| INFOBOX", infobox(t, lang))
        p("   INTRO", intro(t, lang, 900))
        time.sleep(1)


def c_pointing():
    # per club, small queries: every item pointing at a roster club by P831 or P361, with its types
    E = ents(ROSTER, props="labels")
    for q in ROSTER:
        for prop in ("P831", "P361"):
            Q = """SELECT DISTINCT ?team ?teamLabel ?t ?tLabel WHERE {
              ?team wdt:%s wd:%s . OPTIONAL { ?team wdt:P31 ?t }
              SERVICE wikibase:label { bd:serviceParam wikibase:language "en,nl" } }""" % (prop, q)
            res, err = fc.sparql_with_retry(Q)
            rows = (res or {}).get("results", {}).get("bindings", [])
            if err: p("POINT-ERR", q, prop, err)
            seen = {}
            for r in rows:
                seen.setdefault((q_(fc.cell(r, "team")), fc.cell(r, "teamLabel")), []).append(fc.cell(r, "tLabel"))
            for (t, l), ts in seen.items():
                p("POINT", q, lab(E.get(q, {})), prop, "<-", t, l, ts)
            time.sleep(1)


for name, fn in [("a pages", a_pages), ("c pointing", c_pointing)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE NL3 ===")
