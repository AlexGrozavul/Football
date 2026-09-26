"""TEMPORARY probe for the Switzerland tier 1/2 pass. Removed in the same branch."""
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

# 1. Swiss / Liechtenstein football leagues, with level and enwiki title
Q = """SELECT ?l ?lLabel ?level ?country ?type ?typeLabel ?en WHERE {
  VALUES ?country { wd:Q39 wd:Q347 }
  ?l wdt:P17 ?country ; wdt:P31 ?type .
  ?l wdt:P641 wd:Q2736 .
  OPTIONAL { ?l wdt:P3983 ?level }
  OPTIONAL { ?en schema:about ?l ; schema:isPartOf <https://en.wikipedia.org/> }
  ?l rdfs:label ?lab . FILTER(LANG(?lab) IN ("en","de","fr"))
  FILTER(CONTAINS(LCASE(?lab), "super league") || CONTAINS(LCASE(?lab), "challenge league")
         || CONTAINS(LCASE(?lab), "promotion league") || CONTAINS(LCASE(?lab), "nationalliga"))
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,de" }
}"""
res, err = fc.sparql_with_retry(Q)
rows = (res or {}).get("results", {}).get("bindings", [])
p("SWISS-LEAGUES", err, len(rows))
seen = set()
for r in rows:
    key = (fc.cell(r, "l"), fc.cell(r, "type"))
    if key in seen: continue
    seen.add(key)
    p("  ", fc.cell(r, "l"), "|", fc.cell(r, "lLabel"), "| level", fc.cell(r, "level"),
      "|", fc.cell(r, "country"), "|", fc.cell(r, "typeLabel"), "|", fc.cell(r, "en"))
time.sleep(3)

# 2. season articles
for art in ["2026–27 Swiss Super League", "2026–27 Swiss Challenge League"]:
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

# 3. StadiumDB slug
for slug in ["sui", "swi", "che", "switzerland", "ch"]:
    st, body = get(f"https://stadiumdb.com/stadiums/{slug}")
    p("STADIUMDB", slug, st, len(body), body.count("<tr"))
    time.sleep(5)
p("=== END OF PROBE ===")
