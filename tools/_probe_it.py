"""TEMPORARY probe 2 for the Italy tier 1/2 pass. Removed in the same branch."""
import json, re, sys, time, urllib.request, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr

def p(*a): print(" ".join(str(x) for x in a), flush=True)

ids = ["Q8428", "Q56542463", "Q650365", "Q534448", "Q2037", "Q3626037"]
q = urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(ids),
    "props": "claims|labels|sitelinks", "languages": "en|it", "format": "json"})
data, err = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + q, "entities")
p("ENTITIES", err)
titles = {}
for qid in ids:
    ent = (data or {}).get("entities", {}).get(qid, {})
    t = cr.enwiki_title(ent); titles[qid] = t
    p("ENTITY", qid, (ent.get("labels", {}).get("it") or {}).get("value"),
      "| sitelinks", len(ent.get("sitelinks", {})), "| enwiki", t)
    cl = ent.get("claims", {})
    for prop in ("P31", "P17", "P118", "P571", "P576", "P115", "P625", "P1366", "P156"):
        for c in cl.get(prop, []):
            ms = c["mainsnak"]; v = ms.get("datavalue", {}).get("value")
            if isinstance(v, dict):
                v = v.get("id") or v.get("time") or (v.get("latitude"), v.get("longitude"))
            v = v or ms.get("snaktype")
            quals = {k: [ (qq.get("datavalue", {}).get("value") or {}).get("time") or (qq.get("datavalue", {}).get("value") or {}).get("id") for qq in vs] for k, vs in (c.get("qualifiers") or {}).items() if k in ("P580", "P582")}
            p("   ", prop, v, c.get("rank"), quals or "")
time.sleep(2)

# infobox lines that state the club's current state
for qid, t in titles.items():
    if not t:
        p("INFOBOX", qid, "no enwiki article"); continue
    page, real, err = cr.fetch_article(t)
    if err:
        p("INFOBOX", qid, t, "ERROR", err); continue
    m = re.search(r'<table class="infobox.*?</table>', page, re.S)
    box = cr.text_of(m.group(0)) if m else ""
    keep = []
    for key in ("Dissolved", "Founded", "Ground", "League", "Capacity", "2025–26", "2024–25", "Serie"):
        for mm in re.finditer(re.escape(key) + r".{0,120}", box):
            keep.append(mm.group(0)[:140])
    p("INFOBOX", qid, real, "|", " || ".join(dict.fromkeys(keep))[:900])
    time.sleep(2)
p("=== END OF PROBE 2 ===")
