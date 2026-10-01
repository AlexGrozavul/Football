"""TEMPORARY probe #3 for the England pass. Removed in the same branch."""
import re, sys, time, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr


def p(*a): print(" ".join(str(x) for x in a), flush=True)


def wikitext(title):
    args = {"action": "parse", "page": title, "prop": "wikitext", "redirects": "1", "format": "json", "formatversion": "2"}
    d, e = cr.get_json_with_retry("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    return ((d or {}).get("parse") or {}).get("wikitext") or ""


def infobox(title, keys):
    wt = wikitext(title)
    keep = [l.strip() for l in wt.splitlines() if re.match(r"\s*\|\s*(%s)" % keys, l, re.I)]
    return " || ".join(keep)[:900] if keep else ("(no infobox lines)" if wt else "(no article)")


def ent(ids):
    args = {"action": "wbgetentities", "props": "claims|labels|sitelinks", "languages": "en", "format": "json",
            "ids": "|".join(ids)}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), "ents")
    return (d or {}).get("entities", {})


def qid_for(title):
    args = {"action": "wbgetentities", "sites": "enwiki", "titles": title, "props": "info", "format": "json", "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    return next((k for k in ((d or {}).get("entities") or {}) if k.startswith("Q")), None)


def claims(x, prop):
    out = []
    for c in x.get("claims", {}).get(prop, []):
        v = c["mainsnak"].get("datavalue", {}).get("value")
        if isinstance(v, dict) and "latitude" in v: v = (v["latitude"], v["longitude"])
        elif isinstance(v, dict) and "amount" in v: v = v["amount"]
        elif isinstance(v, dict) and "id" in v: v = v["id"]
        elif isinstance(v, dict) and "time" in v: v = v["time"][:11]
        q = {k: [str(z.get("datavalue", {}).get("value", {}).get("time", ""))[:11] for z in zs]
             for k, zs in c.get("qualifiers", {}).items() if k in ("P580", "P582", "P585")}
        out.append((v, c["rank"][:4], q) if q else (v, c["rank"][:4]))
    return out


for t in ["Brentford F.C.", "Brentford Community Stadium", "Griffin Park"]:
    p("INFOBOX", t, "|", infobox(t, r"ground|stadium|capacity|coordinates|coord|tenants|opened|closed|demolish|name|fullname|location"))
    time.sleep(0.5)
qs = {t: qid_for(t) for t in ["Brentford Community Stadium", "Griffin Park"]}
p("QIDS", qs)
E = ent([q for q in qs.values() if q] + ["Q1546623", "Q19571"])
for q, x in E.items():
    p("ITEM", q, (x.get("labels", {}).get("en") or {}).get("value"), "| P625", claims(x, "P625"), "| P1083", claims(x, "P1083"),
      "| P576", claims(x, "P576"), "| P582", claims(x, "P582"), "| P115", claims(x, "P115"), "| P131", claims(x, "P131")[:2],
      "| enwiki", ((x.get("sitelinks") or {}).get("enwiki") or {}).get("title"))
p("=== END OF PROBE EN3 ===")
