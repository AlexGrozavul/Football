"""TEMPORARY probe #2 for the Switzerland pass: every item carrying a Swiss
tier 1/2 tag at any rank, checked against both 2026-27 rosters, and - for the
stale-active-club pattern (shape 6) - P576, the enwiki infobox and each
article's team-changes text. Removed in the same branch."""
import json, re, sys, time, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc

def p(*a): print(" ".join(str(x) for x in a), flush=True)

LEAGUES = {"Q202699": "Super League", "Q669073": "Challenge League"}
Q = """SELECT ?club ?clubLabel ?league ?rank ?dis ?country ?coord ?venue ?links ?typeLabel WHERE {
  VALUES ?league { wd:Q202699 wd:Q669073 }
  ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
  OPTIONAL { ?club wdt:P576 ?dis }
  OPTIONAL { ?club wdt:P17 ?country }
  OPTIONAL { ?club wdt:P625 ?coord }
  OPTIONAL { ?club wdt:P115 ?venue }
  OPTIONAL { ?club wikibase:sitelinks ?links }
  OPTIONAL { ?club wdt:P31 ?type }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "de,fr,it,en" }
}"""
res, err = fc.sparql_with_retry(Q)
rows = (res or {}).get("results", {}).get("bindings", [])
p("TAGGED", err, len(rows))
items = {}
for r in rows:
    q = fc.cell(r, "club").rsplit("/", 1)[-1]
    it = items.setdefault(q, {"label": fc.cell(r, "clubLabel"), "tags": set(), "dis": set(),
                              "country": set(), "coord": False, "venue": False,
                              "links": fc.cell(r, "links"), "types": set()})
    it["tags"].add((LEAGUES[fc.cell(r, "league").rsplit("/", 1)[-1]], fc.cell(r, "rank").rsplit("#", 1)[-1]))
    if fc.cell(r, "dis"): it["dis"].add(fc.cell(r, "dis")[:10])
    if fc.cell(r, "country"): it["country"].add(fc.cell(r, "country").rsplit("/", 1)[-1])
    it["coord"] |= bool(fc.cell(r, "coord")); it["venue"] |= bool(fc.cell(r, "venue"))
    if fc.cell(r, "typeLabel"): it["types"].add(fc.cell(r, "typeLabel"))
time.sleep(3)

# rosters
roster = {}
texts = {}
for art, tier in [("2026–27 Swiss Super League", 1), ("2026–27 Swiss Challenge League", 2)]:
    page, real, e = cr.fetch_article(art)
    if e:
        p("ARTICLE", art, "ERROR", e); continue
    texts[art] = page
    tables, shape = cr.roster_tables(page)
    names = []
    for t, h in tables:
        for title, cap in cr.rows_of(t, h):
            if title not in names: names.append(title)
    got, fails = cr.qids_for_titles(names)
    for n, q in got.items():
        roster[q] = (tier, n)
    time.sleep(2)
p("ROSTER", len(roster))

for q, it in sorted(items.items(), key=lambda kv: kv[1]["label"] or ""):
    p("ITEM", q, "|", it["label"], "| tags", sorted(it["tags"]), "| P576", sorted(it["dis"]) or "-",
      "| P17", sorted(it["country"]) or "-", "| coord", it["coord"], "| venue", it["venue"],
      "| sitelinks", it["links"], "| types", sorted(it["types"]), "| roster", roster.get(q, "NOT IN EITHER"))

# the roster clubs no tagged item covers
for q, (tier, n) in roster.items():
    if q not in items:
        p("ROSTER-ONLY", q, tier, n)

# team-changes text in each article
for art, page in texts.items():
    plain = cr.text_of(page)
    for kw in ("Team changes", "relegat", "promot", "withdr", "exclu", "licen", "dissol", "bankrupt"):
        for m in re.finditer(kw, plain, re.I):
            p("CHANGES", art, "|", kw, "|", plain[max(0, m.start()-200):m.start()+300])
            break

# infobox of every tagged item that the club query would keep but no roster names
def infobox(title):
    qs = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "wikitext",
                                 "format": "json", "formatversion": "2", "redirects": "1", "section": "0"})
    d, e = cr.get_json_with_retry(f"{cr.WIKIPEDIA_API}?{qs}", title)
    if e or "error" in (d or {}):
        return None
    return d["parse"]["wikitext"]

qs = [q for q, it in items.items() if q not in roster]
ents = {}
for i in range(0, len(qs), 40):
    u = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbgetentities", "ids": "|".join(qs[i:i+40]), "props": "sitelinks", "format": "json"})
    d, e = cr.get_json_with_retry(u, "entities")
    ents.update((d or {}).get("entities", {}))
    time.sleep(1)
for q in qs:
    title = cr.enwiki_title(ents.get(q, {}))
    if not title:
        p("INFOBOX", q, items[q]["label"], "| no enwiki article"); continue
    wt = infobox(title) or ""
    keep = [l.strip() for l in wt.splitlines()
            if re.match(r"\s*\|\s*(dissolved|league|season|position|ground|current|fullname|founded)\b", l, re.I)]
    p("INFOBOX", q, title, "|", " || ".join(keep)[:700])
    time.sleep(1)
p("=== END OF PROBE 2 ===")
