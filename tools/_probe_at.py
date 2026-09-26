"""TEMPORARY probe #4: ground coordinates for the hand rows. Removed in the same branch."""
import sys, time, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr

def p(*a): print(" ".join(str(x) for x in a), flush=True)

def show(ents):
    for q, x in ents.items():
        cl = x.get("claims", {})
        def v(prop):
            out = []
            for c in cl.get(prop, []):
                d = c["mainsnak"].get("datavalue", {}).get("value")
                if isinstance(d, dict) and "latitude" in d: d = (round(d["latitude"], 6), round(d["longitude"], 6))
                elif isinstance(d, dict) and "amount" in d: d = d["amount"]
                elif isinstance(d, dict) and "id" in d: d = d["id"]
                out.append((d, c.get("rank")[:4]))
            return out
        p("ENT", q, (x.get("labels", {}).get("en") or x.get("labels", {}).get("de") or {}).get("value"),
          "| P625", v("P625"), "| P1083", v("P1083"), "| P466", v("P466")[:5], "| P131", v("P131")[:2],
          "| enwiki", cr.enwiki_title(x))

def by_ids(ids):
    u = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbgetentities", "ids": "|".join(ids), "props": "claims|labels|sitelinks",
        "languages": "en|de", "format": "json"})
    d, e = cr.get_json_with_retry(u, "ids")
    show((d or {}).get("entities", {}))

def by_titles(site, titles):
    u = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbgetentities", "sites": site, "titles": "|".join(titles), "props": "claims|labels|sitelinks",
        "languages": "en|de", "format": "json"})
    d, e = cr.get_json_with_retry(u, "titles")
    show({k: v for k, v in (d or {}).get("entities", {}).items() if not k.startswith("-")})

by_ids(["Q26868807", "Q42296825", "Q20180568", "Q97889239", "Q2498860", "Q551837", "Q628059"])
time.sleep(1)
by_titles("enwiki", ["Raiffeisen Arena (Linz)", "WIRmachenDRUCK Arena", "Mechatronik Arena"])
time.sleep(1)
by_titles("dewiki", ["WIRmachenDRUCK Arena", "Raiffeisen Arena (Linz)", "Stadion Grünfeld"])
args = {"action": "wbsearchentities", "search": "WIRmachenDRUCK Arena", "language": "de", "format": "json"}
d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), "s")
p("SEARCH", [(h.get("id"), h.get("label"), h.get("description")) for h in (d or {}).get("search", [])])
p("=== END OF PROBE AT4 ===")
