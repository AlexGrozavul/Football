"""TEMPORARY probe for the France tier 1/2 pass. Removed in the same branch."""
import json, sys, time, urllib.request, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr

UA = cr.USER_AGENT
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return str(e), ""

out = []
def p(*a):
    s = " ".join(str(x) for x in a); out.append(s); print(s, flush=True)

# 1. league items by enwiki title
q = urllib.parse.urlencode({"action": "wbgetentities", "sites": "enwiki",
    "titles": "Ligue 1|Ligue 2|Championnat National", "props": "claims|labels|sitelinks",
    "languages": "en|fr", "format": "json"})
st, body = get("https://www.wikidata.org/w/api.php?" + q)
data = json.loads(body) if body else {}
for qid, ent in (data.get("entities") or {}).items():
    cl = ent.get("claims", {})
    def vals(prop):
        r = []
        for c in cl.get(prop, []):
            dv = c["mainsnak"].get("datavalue", {}).get("value")
            r.append((dv.get("id") if isinstance(dv, dict) and "id" in dv else dv, c.get("rank")))
        return r
    p("LEAGUE", qid, (ent.get("labels", {}).get("en") or {}).get("value"),
      "P17", vals("P17"), "P31", vals("P31"), "P3983", vals("P3983"))

# 2. season articles and their rosters
for art in ["2026–27 Ligue 1", "2026–27 Ligue 2"]:
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
for slug in ["fra", "france", "fr", "fre"]:
    st, body = get(f"https://stadiumdb.com/stadiums/{slug}")
    p("STADIUMDB", slug, st, len(body), body.count("<tr"))
    time.sleep(5)
p("=== END OF PROBE ===")
