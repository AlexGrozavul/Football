"""TEMPORARY probe #4 for the Netherlands pass. Removed in the same branch."""
import json, re, sys, time, traceback, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr
import crosscheck_capacity as cc


def p(*a): print(" ".join(str(x) for x in a), flush=True)


def wikitext(title, lang="en"):
    args = {"action": "parse", "page": title, "prop": "wikitext", "format": "json",
            "formatversion": "2", "redirects": "1", "section": "0"}
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    return (d or {}).get("parse", {}).get("wikitext", "")


def infobox(title, keys=r"capacity|opened|name|tenants|surface|former|coordinates|location|owner"):
    wt = wikitext(title)
    keep = [re.sub(r"<ref.*?(</ref>|/>)", "", l.strip()) for l in wt.splitlines() if re.match(r"\s*\|\s*(%s)" % keys, l, re.I)]
    return " || ".join(keep)[:900] if keep else ("(no infobox lines)" if wt else "(no article)")


def intro(title, n=500):
    args = {"action": "query", "prop": "extracts", "exintro": "1", "explaintext": "1", "titles": title,
            "redirects": "1", "format": "json", "formatversion": "2"}
    d, e = cr.get_json_with_retry("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    pages = (d or {}).get("query", {}).get("pages", [])
    return re.sub(r"\s+", " ", (pages[0].get("extract") if pages else "") or "")[:n]


def osm():
    clubs = json.load(open("data/clubs/NL.json"))["clubs"]
    payload, err = cc.overpass_with_retry("NL")
    p("OVERPASS", err, len((payload or {}).get("elements", [])))
    st = cc.stadium_points(payload or {})
    for c in sorted(clubs, key=lambda c: c["name"]):
        best, bd = None, None
        for s in st:
            d = cc.metres(c["lat"], c["lon"], s["lat"], s["lon"])
            if bd is None or d < bd: best, bd = s, d
        p("OSM", c["name"], "| ours", c["capacity"], "| nearest", (best or {}).get("name"), "| osm cap", (best or {}).get("capacity"),
          (best or {}).get("tag"), "| metres", round(bd) if bd is not None else None)


def pages():
    for t in ["Cambuur Stadion", "De Adelaarshorst", "Stadion Woudestein", "AFAS Stadion", "Kras Stadion",
              "BUKO Stadion", "De Vijverberg", "Stadion de Goffert", "Sparta Stadion Het Kasteel", "MySteel Stadion"]:
        p("PAGE", t, "|", infobox(t))
        p("   INTRO", intro(t))
        time.sleep(1)


for n, f in [("osm", osm), ("pages", pages)]:
    p("##########", n)
    try: f()
    except Exception: p("FAILED", n, traceback.format_exc()[-600:])
p("=== END OF PROBE NL4 ===")
