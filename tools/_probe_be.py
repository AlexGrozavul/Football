"""TEMPORARY probe #4 for the Belgium pass. Removed in the same branch."""
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





def a_items():
    ids = ["Q16062685", "Q20751559", "Q1874231", "Q97686604", "Q3250417", "Q109045011", "Q2308515", "Q265477",
           "Q15694367", "Q677582", "Q135110334", "Q3153676", "Q1708705", "Q285074", "Q3496100"]
    E = ents(ids, props="claims|labels|descriptions|sitelinks")
    for q in ids:
        x = E.get(q, {})
        p("ITEM", q, labs(x), "| desc", {k: v["value"] for k, v in x.get("descriptions", {}).items() if k in ("en", "nl", "fr")},
          "| P31", [v[0] for v in vals(x, "P31")][:3], "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083"),
          "| P466", [v[0] for v in vals(x, "P466")][:6], "| P131", [v[0] for v in vals(x, "P131")][:2], "| P576", vals(x, "P576"),
          "| P6375", vals(x, "P6375")[:1], "| sl", sitelinks(x))


def b_osm():
    q = """[out:json][timeout:120];
area["ISO3166-1"="BE"][admin_level=2]->.a;
nwr["name"~"Urbain|Leunen|Pairay|Schiervelde|Patro|Sportpark|Daknam|Rocourt|Vedette|Boverie|Freethiel|Kuipje|Stayen|Breydel|Dufrasne|Kehrweg",i](area.a);
out tags center;"""
    body = urllib.parse.urlencode({"data": q}).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=body,
                                         headers={"User-Agent": cr.USER_AGENT})
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read().decode())
            break
        except Exception as ex:
            p("OVERPASS-ERR", ex); time.sleep(45); d = None
    for el in (d or {}).get("elements", []):
        t = el.get("tags", {})
        c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        if not any(k in t for k in ("leisure", "building", "sport", "landuse")): continue
        p("OSM", el["type"] + "/" + str(el["id"]), t.get("name"), "|", c.get("lat"), c.get("lon"), "| leisure", t.get("leisure"),
          "| building", t.get("building"), "| sport", t.get("sport"), "| cap", t.get("capacity"), "| addr", t.get("addr:city"),
          t.get("addr:street"))


for name, fn in [("a items", a_items), ("b osm", b_osm)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE BE4 ===")
