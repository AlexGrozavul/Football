"""TEMPORARY probe #4 for the Switzerland pass. Removed in the same branch."""
import json, re, sys, time, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr

def p(*a): print(" ".join(str(x) for x in a), flush=True)

def wikitext(title):
    qs = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "wikitext",
                                 "format": "json", "formatversion": "2", "redirects": "1", "section": "0"})
    d, e = cr.get_json_with_retry(f"{cr.WIKIPEDIA_API}?{qs}", title)
    return (d or {}).get("parse", {}).get("wikitext", "")

for title in ["FC Lugano", "AIL Arena", "Stadio di Cornaredo"]:
    wt = wikitext(title)
    keep = [l.strip() for l in wt.splitlines()
            if re.match(r"\s*\|\s*(ground|capacity|coordinates|opened|tenants|former_names|location|season|league)\b", l, re.I)]
    p("INFOBOX", title, "|", " || ".join(keep)[:600] if keep else ("(no infobox lines)" if wt else "(no article)"))
    time.sleep(1)

q = urllib.parse.urlencode({"action": "wbgetentities", "sites": "enwiki",
    "titles": "Stade de la Tuilière|AIL Arena|Stadio di Cornaredo|Stade Olympique de la Pontaise",
    "props": "claims|labels|sitelinks", "languages": "en|fr|it", "format": "json"})
data, err = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + q, "entities")
p("ENTITIES", err)
for qid, ent in (data or {}).get("entities", {}).items():
    cl = ent.get("claims", {})
    def vals(prop):
        out = []
        for c in cl.get(prop, []):
            v = c["mainsnak"].get("datavalue", {}).get("value")
            if isinstance(v, dict) and "latitude" in v: v = (v["latitude"], v["longitude"])
            elif isinstance(v, dict) and "amount" in v: v = v["amount"]
            elif isinstance(v, dict) and "id" in v: v = v["id"]
            elif isinstance(v, dict) and "time" in v: v = v["time"]
            out.append((v, c.get("rank")))
        return out
    p("ENTITY", qid, (ent.get("labels", {}).get("en") or {}).get("value"), "| enwiki", cr.enwiki_title(ent),
      "| P625", vals("P625"), "| P1083", vals("P1083"), "| P466 tenant", vals("P466"), "| P1619 opened", vals("P1619"))

# the Challenge League stadium rows, whole
page, real, e = cr.fetch_article("2026–27 Swiss Challenge League")
tables, shape = cr.roster_tables(page)
for t, h in tables:
    p("CL HEAD", h)
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)[1:]:
        p("   CL ROW", [cr.text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)])
p("=== END OF PROBE 4 ===")
