"""TEMPORARY probe #5 for the Netherlands pass (Cambuur's ground). Removed in the same branch."""
import json, re, sys, time, traceback, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr
import crosscheck_capacity as cc


def p(*a): print(" ".join(str(x) for x in a), flush=True)


def get(url, tag):
    d, e = cr.get_json_with_retry(url, tag)
    if e: p("ERR", tag, e)
    return d or {}


def wikitext(title, lang="en"):
    d = get(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "page": title, "prop": "wikitext", "format": "json", "formatversion": "2",
         "redirects": "1", "section": "0"}), title)
    return d.get("parse", {}).get("wikitext", "")


def infobox(title, lang="en"):
    wt = wikitext(title, lang)
    keep = [re.sub(r"<ref.*?(</ref>|/>)", "", l.strip()) for l in wt.splitlines()
            if re.match(r"\s*\|\s*(capacity|opened|name|tenants|coordinates|location|capaciteit|geopend|bouwjaar|coörd|plaats|naam|club)", l, re.I)]
    return " || ".join(keep)[:900] if keep else ("(no infobox lines)" if wt else "(no article)")


def intro(title, lang="en", n=600):
    d = get(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "prop": "extracts", "exintro": "1", "explaintext": "1", "titles": title,
         "redirects": "1", "format": "json", "formatversion": "2"}), title)
    pages = d.get("query", {}).get("pages", [])
    return re.sub(r"\s+", " ", (pages[0].get("extract") if pages else "") or "")[:n]


def claims(q):
    d = get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbgetentities", "ids": q, "props": "claims|labels|sitelinks|descriptions", "languages": "en|nl",
         "format": "json"}), q)
    return (d.get("entities") or {}).get(q, {})


def val(c, prop):
    out = []
    for s in c.get("claims", {}).get(prop, []):
        v = s["mainsnak"].get("datavalue", {}).get("value")
        if isinstance(v, dict) and "latitude" in v: v = (v["latitude"], v["longitude"])
        elif isinstance(v, dict) and "amount" in v: v = v["amount"]
        elif isinstance(v, dict) and "id" in v: v = v["id"]
        elif isinstance(v, dict) and "time" in v: v = v["time"]
        q = {k: [x.get("datavalue", {}).get("value", {}).get("time", "")[:11] for x in xs]
             for k, xs in s.get("qualifiers", {}).items() if k in ("P580", "P582")}
        out.append((v, s["rank"][:4], q) if q else (v, s["rank"][:4]))
    return out


def main():
    for t, lang in [("Kooi Stadion", "en"), ("Kooi Stadion", "nl"), ("SC Cambuur", "en")]:
        p("PAGE", lang, t, "|", infobox(t, lang)); p("   INTRO", intro(t, lang, 800)); time.sleep(1)
    # the stadium's Wikidata item, via the enwiki / nlwiki title
    for site, title in [("enwiki", "Kooi Stadion"), ("nlwiki", "Kooi Stadion")]:
        d = get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "wbgetentities", "sites": site, "titles": title, "props": "info", "format": "json"}), title)
        for k in d.get("entities", {}):
            p("QID", site, title, k)
            if k.startswith("Q"):
                c = claims(k)
                p("  ITEM", k, {l: v["value"] for l, v in c.get("labels", {}).items()},
                  "| desc", {l: v["value"] for l, v in c.get("descriptions", {}).items()})
                for pr in ("P31", "P17", "P131", "P625", "P1083", "P571", "P580", "P576", "P466", "P1001", "P137"):
                    if pr in c.get("claims", {}): p("    ", pr, val(c, pr))
    # Cambuur's own item: ground statements and their labels
    c = claims("Q875120")
    p("CAMBUUR P115", val(c, "P115"), "| P625", val(c, "P625"))
    for q in [v[0] for v in val(c, "P115")]:
        g = claims(q)
        p("  OLD-GROUND", q, {l: v["value"] for l, v in g.get("labels", {}).items()}, "| P625", val(g, "P625"),
          "| P1083", val(g, "P1083"), "| P576", val(g, "P576"), "| P582", val(g, "P582"))
    # OSM: every stadium within 6 km of the old pin, with coordinates
    payload, err = cc.overpass_with_retry("NL")
    p("OVERPASS", err)
    for s in cc.stadium_points(payload or {}):
        d = cc.metres(53.205278, 5.814722, s["lat"], s["lon"])
        if d < 6000: p("OSM-NEAR", s["name"], s["lat"], s["lon"], s["capacity"], s["tag"], round(d))


try: main()
except Exception: p("FAILED", traceback.format_exc()[-800:])
p("=== END OF PROBE NL5 ===")
