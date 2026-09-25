"""TEMPORARY probe for the Italy tier 1/2 pass. Removed in the same branch."""
import json, sys, time, urllib.request, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc

def p(*a): print(" ".join(str(x) for x in a), flush=True)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": cr.USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return str(e), ""

def show(ent, qid):
    cl = ent.get("claims", {})
    p("ENTITY", qid, (ent.get("labels", {}).get("en") or {}).get("value"),
      "| it:", (ent.get("labels", {}).get("it") or {}).get("value"),
      "| sitelinks", len(ent.get("sitelinks", {})), "| enwiki", cr.enwiki_title(ent))
    for prop in ("P31", "P17", "P118", "P576", "P115", "P3983"):
        for c in cl.get(prop, []):
            ms = c["mainsnak"]; v = ms.get("datavalue", {}).get("value")
            v = v.get("id") if isinstance(v, dict) and "id" in v else (v.get("time") if isinstance(v, dict) else v or ms.get("snaktype"))
            p("   ", prop, v, c.get("rank"))

# 1. league items and the two Milan clubs, by enwiki title
q = urllib.parse.urlencode({"action": "wbgetentities", "sites": "enwiki",
    "titles": "Inter Milan|AC Milan", "props": "claims|labels|sitelinks",
    "languages": "en|it", "format": "json"})
data, err = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + q, "entities")
p("TITLES", err)
for qid, ent in (data or {}).get("entities", {}).items():
    show(ent, qid)
time.sleep(3)

# 2. every item on a Serie A or Serie B tag (any rank) whose label names Inter or Milan
Q = """SELECT DISTINCT ?club ?clubLabel ?rank ?league WHERE {
  VALUES ?league { wd:Q15804 wd:Q194052 }
  ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
  ?club rdfs:label ?l . FILTER(LANG(?l) IN ("en","it"))
  FILTER(CONTAINS(LCASE(?l), "inter") || CONTAINS(LCASE(?l), "milan"))
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en" }
}"""
res, err = fc.sparql_with_retry(Q)
rows = (res or {}).get("results", {}).get("bindings", [])
p("MILAN-CANDIDATES", err, len(rows))
for r in rows:
    p("  ", fc.cell(r, "club"), fc.cell(r, "clubLabel"), fc.cell(r, "league"), fc.cell(r, "rank"))
time.sleep(3)

# 3. season articles
for art in ["2026–27 Serie A", "2026–27 Serie B"]:
    page, real, err = cr.fetch_article(art)
    if err:
        p("ARTICLE", art, "ERROR", err); continue
    tables, shape = cr.roster_tables(page)
    names = []
    for t, h in tables:
        for title, cap in cr.rows_of(t, h):
            if title not in names: names.append(title)
    p("ARTICLE", art, "->", real, "tables", len(tables), shape, "clubs", len(names))
    got, fails = cr.qids_for_titles(names)
    p("  resolved", len(got), "of", len(names), "failures", fails)
    for n in names:
        p("   ", got.get(n, "-"), n)
    time.sleep(2)

# 4. StadiumDB slug
for slug in ["ita", "italy", "it"]:
    st, body = get(f"https://stadiumdb.com/stadiums/{slug}")
    p("STADIUMDB", slug, st, len(body), body.count("<tr"))
    time.sleep(5)
p("=== END OF PROBE ===")
