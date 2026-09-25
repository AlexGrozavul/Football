"""TEMPORARY probe 2 for the France tier 1/2 pass. Removed in the same branch."""
import json, sys, time, urllib.request, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc

def p(*a): print(" ".join(str(x) for x in a), flush=True)

# 1. clubs tagged Ligue 1/2 that the club query drops for no position
Q = """SELECT ?club ?clubLabel ?league WHERE {
  VALUES ?league { wd:Q13394 wd:Q217374 }
  ?club wdt:P118 ?league .
  FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
  FILTER NOT EXISTS { ?club wdt:P576 ?d }
  FILTER NOT EXISTS { ?club wdt:P625 ?c }
  FILTER NOT EXISTS { ?club wdt:P115/wdt:P625 ?vc }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" }
}"""
rows, err = fc.sparql_with_retry(Q)
p("DROPPED-NO-COORD", err)
for r in rows or []:
    p("  ", fc.cell(r, "club"), fc.cell(r, "clubLabel"), fc.cell(r, "league"))

# 2. the three tier-2 extras: every P118 with rank and qualifiers, P576, P31
ids = ["Q2619514", "Q1132418", "Q369349", "Q24937450", "Q180305"]
q = urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(ids),
    "props": "claims|labels|sitelinks", "languages": "en|fr", "format": "json"})
data, err = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + q, "entities")
for qid, ent in (data or {}).get("entities", {}).items():
    cl = ent.get("claims", {})
    p("ENTITY", qid, (ent.get("labels", {}).get("fr") or {}).get("value"),
      "sitelinks", len(ent.get("sitelinks", {})), "enwiki", cr.enwiki_title(ent))
    for prop in ("P31", "P17", "P118", "P576", "P115"):
        for c in cl.get(prop, []):
            ms = c["mainsnak"]; v = ms.get("datavalue", {}).get("value")
            v = v.get("id") if isinstance(v, dict) and "id" in v else (v.get("time") if isinstance(v, dict) else v or ms.get("snaktype"))
            quals = {k: [ (qq.get("datavalue", {}).get("value") or {}).get("time") or (qq.get("datavalue", {}).get("value") or {}).get("id") for qq in vs] for k, vs in (c.get("qualifiers") or {}).items() if k in ("P580", "P582", "P3831")}
            p("   ", prop, v, c.get("rank"), quals)

# 3. are the extras in the 2026-27 Championnat National? (evidence only - tier 3 is NOT mapped)
for art in ["2026–27 Championnat National"]:
    page, real, err = cr.fetch_article(art)
    if err:
        p("ARTICLE", art, "ERROR", err); continue
    tables, shape = cr.roster_tables(page)
    names = []
    for t, h in tables:
        for title, cap in cr.rows_of(t, h):
            if title not in names: names.append(title)
    got, fails = cr.qids_for_titles(names)
    p("ARTICLE", real, len(tables), shape, "clubs", len(names), "resolved", len(got), fails)
    for n in names: p("   ", got.get(n, "-"), n)
p("=== END OF PROBE 2 ===")
