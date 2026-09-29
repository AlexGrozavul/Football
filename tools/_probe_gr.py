"""TEMPORARY probe #1 for the Greece pass and the league-tag end-date (P582)
measurement. Removed in the same branch."""
import csv, glob, json, os, re, sys, time, traceback, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc

TODAY = "2026-09-27"


def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

LANGS = "en|el|de"


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


def lab(ent, order=("en", "el", "de")):
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


# ======================================================================

def wikitext(title, lang="en", section="0"):
    args = {"action": "parse", "page": title, "prop": "wikitext", "format": "json",
            "formatversion": "2", "redirects": "1"}
    if section is not None: args["section"] = section
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    return (d or {}).get("parse", {}).get("wikitext", "")


def infobox(title, lang="en", keys=r"dissolved|league|season|position|ground|capacity|coordinates|coord|current|fullname|founded|stadium|name|opened|location|home|tenants|γήπεδο|έδρα|χωρητικότητα|πρωτάθλημα|ίδρυση|διάλυση|coordinates|seating|record"):
    wt = wikitext(title, lang)
    keep = [l.strip() for l in wt.splitlines() if re.match(r"\s*\|\s*(%s)" % keys, l, re.I)]
    return " || ".join(keep)[:1000] if keep else ("(no infobox lines)" if wt else "(no article)")


def intro(title, lang="en", n=700):
    args = {"action": "query", "prop": "extracts", "exintro": "1", "explaintext": "1", "titles": title,
            "redirects": "1", "format": "json", "formatversion": "2"}
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    pages = (d or {}).get("query", {}).get("pages", [])
    return re.sub(r"\s+", " ", (pages[0].get("extract") if pages else "") or "")[:n]


def t1():
    E = ents(["Q63980269", "Q235114", "Q1436035", "Q1421208", "Q41", "Q30646111"])
    for q, x in E.items():
        p("ENT", q, labs(x), "| P31", [v[0] for v in vals(x, "P31")][:5], "| P17", [v[0] for v in vals(x, "P17")],
          "| P3983", vals(x, "P3983"), "| P1332-5", [vals(x, k) for k in ("P1332", "P1333", "P1334", "P1335")],
          "| sl", sitelinks(x))


def t2():
    for term in ["Asteras Tripolis B", "Αστέρας Τρίπολης Β", "Asteras Tripoli B"]:
        for lang in ("en", "el"):
            args = {"action": "wbsearchentities", "search": term, "language": lang, "limit": "10", "format": "json"}
            d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), term)
            for r in (d or {}).get("search", []):
                p("SEARCH", term, lang, r.get("id"), r.get("label"), "|", r.get("description"))
            time.sleep(1)
    Q = """SELECT ?t ?tLabel WHERE { { ?t wdt:P831 wd:Q757320 } UNION { ?t wdt:P361 wd:Q757320 } UNION { wd:Q757320 wdt:P527 ?t }
           SERVICE wikibase:label { bd:serviceParam wikibase:language "en,el" } }"""
    res, err = fc.sparql_with_retry(Q)
    for r in (res or {}).get("results", {}).get("bindings", []):
        p("ASTERAS-REL", q_(fc.cell(r, "t")), fc.cell(r, "tLabel"))
    E = ents(["Q757320"])
    x = E.get("Q757320", {})
    p("ASTERAS", {k: vals(x, k) for k in ("P31", "P527", "P355", "P831", "P361", "P115", "P118")})


def t3():
    for t in ["Niki Volos F.C.", "Panathinaikos F.C.", "AEK Athens F.C.", "Agia Sophia Stadium", "Anagennisi Karditsa F.C.",
              "Municipal Stadium of Karditsa", "Athens Kallithea F.C.", "Grigoris Lamprakis Stadium", "A.P.S. Zakynthos",
              "Hellas Syros F.C.", "Nestos Chrysoupoli F.C.", "Marko 1927 F.C.", "Asteras Tripolis F.C.",
              "Theodoros Kolokotronis Stadium", "AEL FC Arena", "Atromitos F.C.", "Peristeri Stadium",
              "Olympiacos F.C. B", "PAOK B", "Panionios F.C.", "Nea Smyrni Stadium", "Panthrakikos F.C.", "Komotini Municipal Stadium",
              "Kalamata F.C.", "Olympic Stadium (Athens)", "Apostolos Nikolaidis Stadium", "Panetolikos F.C."]:
        p("INFOBOX", t, "|", infobox(t))
        time.sleep(0.4)
    for t in ["Sporting Club fivois", "Équipe fédérale Reims-Champagne", "Società Ginnastica di Torino"]:
        for lang in ("en", "fr", "it"):
            ib = infobox(t, lang)
            if ib != "(no article)":
                p("INFOBOX-P582", lang, t, "|", ib)
                p("INTRO-P582", lang, t, "|", intro(t, lang, 500))
    E = ents(["Q1514915", "Q3590859", "Q116949682", "Q113573418", "Q141319965", "Q5014471"])
    for q, x in E.items():
        n, en, _el = sitelinks(x)
        s = x.get("sitelinks") or {}
        p("P582ITEM", q, lab(x), "| P31", [v[0] for v in vals(x, "P31")], "| P576", vals(x, "P576"), "| P571", vals(x, "P571"),
          "| P118", vals(x, "P118"), "| sl", sorted(s)[:8])
        for site in ("enwiki", "frwiki", "itwiki", "rowiki"):
            t = (s.get(site) or {}).get("title")
            if t:
                lang = site[:2]
                p("   ", site, t, "| INFOBOX", infobox(t, lang, keys=r"dissolved|desfiin|scioglimento|dissolution|disparition|league|liga|campionato|championnat|season|sezon|stagione|position|founded|fondat|fondazione|fondation|nume|name|nom"))
                p("   ", site, t, "| INTRO", intro(t, lang, 500))


def overpass(q):
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=data, headers={"User-Agent": cr.USER_AGENT})
    with urllib.request.urlopen(req, timeout=200) as r:
        return json.loads(r.read().decode())


def t4():
    for town, lat, lon in [("Chrysoupoli", 40.983, 24.700), ("Ermoupoli", 37.444, 24.940), ("Zakynthos", 37.782, 20.897),
                           ("Markopoulo", 37.884, 23.930), ("Karditsa", 39.365, 21.921), ("Kallithea", 37.955, 23.702)]:
        q = f"""[out:json][timeout:120];(nwr[leisure=stadium](around:4000,{lat},{lon});nwr[leisure=pitch][sport=soccer](around:4000,{lat},{lon}););out center tags;"""
        try:
            d = overpass(q)
        except Exception as ex:
            p("OSM", town, "ERROR", ex); time.sleep(10); continue
        for el in d.get("elements", []):
            c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
            t = el.get("tags", {})
            if t.get("leisure") == "pitch" and not t.get("name"): continue
            p("OSM", town, f"{el['type']}/{el['id']}", t.get("leisure"), "|", t.get("name"), "|", t.get("name:en"), "|",
              t.get("capacity"), "|", t.get("wikidata"), "|", t.get("operator"), "|", round(c["lat"], 6), round(c["lon"], 6))
        unnamed = sum(1 for el in d.get("elements", []) if el.get("tags", {}).get("leisure") == "pitch" and not el.get("tags", {}).get("name"))
        p("OSM", town, "unnamed soccer pitches:", unnamed)
        time.sleep(8)


for name, fn in [("t1 leagues/box", t1), ("t2 Asteras B", t2), ("t3 infoboxes", t3), ("t4 OSM", t4)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE GR2 ===")
