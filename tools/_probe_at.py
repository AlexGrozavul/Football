"""TEMPORARY probe #2 for the Austria pass: every item carrying an Austrian
tier 1/2 tag at any rank, both rosters' raw rows, the multi-P115 clubs in
every mapped country (split, no label service), and Stadion Gruenfeld.
Removed in the same branch."""
import csv, json, re, sys, time, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc

def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

def ents(ids, props="claims|labels|sitelinks"):
    out = {}
    ids = list(dict.fromkeys(ids))
    for i in range(0, len(ids), 45):
        args = {"action": "wbgetentities", "props": props, "languages": "en|de|fr|it|ro",
                "format": "json", "ids": "|".join(ids[i:i+45])}
        d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), "ents")
        if e: p("ENTS-ERROR", e)
        out.update((d or {}).get("entities", {}))
        time.sleep(1)
    return out

def lab(ent):
    for l in ("en", "de", "fr", "it", "ro"):
        v = (ent.get("labels", {}).get(l) or {}).get("value")
        if v: return v
    return None

def vals(ent, prop):
    out = []
    for c in ent.get("claims", {}).get(prop, []):
        v = c["mainsnak"].get("datavalue", {}).get("value")
        if v is None: v = c["mainsnak"].get("snaktype")
        elif isinstance(v, dict) and "latitude" in v: v = (round(v["latitude"], 6), round(v["longitude"], 6))
        elif isinstance(v, dict) and "amount" in v: v = v["amount"]
        elif isinstance(v, dict) and "id" in v: v = v["id"]
        elif isinstance(v, dict) and "time" in v: v = v["time"][:11]
        qual = {k: [str(x.get("datavalue", {}).get("value", {}).get("time", ""))[:11] for x in xs]
                for k, xs in c.get("qualifiers", {}).items() if k in ("P580", "P582")}
        r = c.get("rank")[:4]
        out.append((v, r, qual) if qual else (v, r))
    return out

def wikitext(title):
    qs = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "wikitext",
                                 "format": "json", "formatversion": "2", "redirects": "1", "section": "0"})
    d, e = cr.get_json_with_retry(f"{cr.WIKIPEDIA_API}?{qs}", title)
    return (d or {}).get("parse", {}).get("wikitext", "")

def infobox(title, keys="dissolved|league|season|position|ground|capacity|coordinates|coord|current|fullname|founded|tenants"):
    wt = wikitext(title)
    keep = [l.strip() for l in wt.splitlines() if re.match(r"\s*\|\s*(%s)\b" % keys, l, re.I)]
    return " || ".join(keep)[:700] if keep else ("(no infobox lines)" if wt else "(no article)")

# ---- 1. the 2. Liga item and its current season
e = ents(["Q650236", "Q219592", "Q135643013"])
for q in ("Q650236", "Q219592", "Q135643013"):
    x = e.get(q, {})
    p("LEAGUE", q, lab(x), "| P31", vals(x, "P31"), "| P17", vals(x, "P17"), "| P3983", vals(x, "P3983"),
      "| P3450", vals(x, "P3450"), "| P2094", vals(x, "P2094"), "| P155", vals(x, "P155"))

# ---- 2. raw rows of both Austrian season articles
roster = {}
texts = {}
for art, tier in [("2026–27 Austrian Football Bundesliga", 1), ("2026–27 Austrian Football Second League", 2)]:
    page, real, err = cr.fetch_article(art)
    if err: p("ARTICLE", art, "ERROR", err); continue
    texts[art] = page
    tables, shape = cr.roster_tables(page)
    names = []
    for t, h in tables:
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)[1:]:
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)
            links = re.findall(r'<a[^>]+href="/wiki/([^"#:]+)"', tr)
            p("  ROW", tier, [cr.text_of(c) for c in cells], "| links", [urllib.parse.unquote(l) for l in links][:4])
        for title, cap in cr.rows_of(t, h):
            if title not in names: names.append(title)
    got, fails = cr.qids_for_titles(names)
    for n, q in got.items():
        roster.setdefault(q, []).append((tier, n))
    time.sleep(2)

# ---- 3. every item carrying an Austrian tier 1/2 tag at any rank
Q = """SELECT ?club ?league ?rank WHERE {
  VALUES ?league { wd:Q219592 wd:Q650236 }
  ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
  FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
}"""
res, err = fc.sparql_with_retry(Q)
rows = (res or {}).get("results", {}).get("bindings", [])
p("TAGGED", err, len(rows))
tags = {}
for r in rows:
    tags.setdefault(q_(fc.cell(r, "club")), set()).add(
        ({"Q219592": "BL", "Q650236": "2L"}[q_(fc.cell(r, "league"))], q_(fc.cell(r, "rank")).split("#")[-1][:4]))
allq = set(tags) | set(roster)
E = ents(sorted(allq), props="claims|labels|sitelinks|info")
for q in sorted(allq, key=lambda q: lab(E.get(q, {})) or q):
    x = E.get(q, {})
    types = [v[0] for v in vals(x, "P31")]
    if "Q5" in types: continue
    p("ITEM", q, "|", lab(x), "| tags", sorted(tags.get(q, [])), "| P118 all", vals(x, "P118")[:8],
      "| P576", vals(x, "P576") or "-", "| P17", [v[0] for v in vals(x, "P17")],
      "| P115", vals(x, "P115"), "| P625", vals(x, "P625"), "| P31", types[:4],
      "| links", len(x.get("sitelinks", {})), "| enwiki", cr.enwiki_title(x),
      "| roster", roster.get(q, "NOT IN EITHER"))

# infoboxes for items not in either roster that the club query would keep
for q in sorted(allq):
    x = E.get(q, {})
    if q in roster or vals(x, "P576") or "Q5" in [v[0] for v in vals(x, "P31")]:
        continue
    t = cr.enwiki_title(x)
    p("INFOBOX", q, lab(x), "|", t, "|", infobox(t) if t else "no enwiki")
    time.sleep(1)

# team changes text
for art, page in texts.items():
    plain = cr.text_of(page)
    for kw in ("Team changes", "relegat", "promot", "withdr", "exclu", "licen", "dissol", "bankrupt", "insolv"):
        for m in list(re.finditer(kw, plain, re.I))[:2]:
            p("CHANGES", art, "|", kw, "|", plain[max(0, m.start()-200):m.start()+300])

# ---- 4. multi-P115, per country, no label service
tiers = {}
with open("data/league-tiers.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["tier"] != "skip": tiers.setdefault(row["country"], []).append(row["leagueQid"])
Q4 = """SELECT ?club ?venue ?rank ?start ?end WHERE {
  VALUES ?league { %s }
  ?club wdt:P118 ?league .
  FILTER NOT EXISTS { ?club wdt:P576 ?d }
  ?club p:P115 ?st . ?st ps:P115 ?venue ; wikibase:rank ?rank .
  FILTER(?rank != wikibase:DeprecatedRank)
  OPTIONAL { ?st pq:P580 ?start } OPTIONAL { ?st pq:P582 ?end }
}"""
multi = {}
for country, leagues in tiers.items():
    time.sleep(3)
    res, err = fc.sparql_with_retry(Q4 % " ".join("wd:" + l for l in leagues))
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("MULTI-QUERY", country, err, len(rows))
    clubs = {}
    for r in rows:
        c = q_(fc.cell(r, "club"))
        v = q_(fc.cell(r, "venue"))
        d = clubs.setdefault(c, {}).setdefault(v, {"rank": q_(fc.cell(r, "rank")).split("#")[-1][:4],
                                                  "start": set(), "end": set()})
        if fc.cell(r, "start"): d["start"].add(fc.cell(r, "start")[:10])
        if fc.cell(r, "end"): d["end"].add(fc.cell(r, "end")[:10])
    for c, vs in clubs.items():
        best = "Pref" if any(d["rank"] == "Pref" for d in vs.values()) else "Norm"
        truthy = {v: d for v, d in vs.items() if d["rank"] == best}
        if len(truthy) > 1:
            multi[c] = (country, truthy)
p("MULTI-COUNT", len(multi))
M = ents(list(multi) + [v for _, t in multi.values() for v in t], props="claims|labels|sitelinks")
for c, (country, truthy) in sorted(multi.items(), key=lambda kv: kv[1][0]):
    x = M.get(c, {})
    p("MULTI", country, c, "|", lab(x), "| P625 on club", vals(x, "P625"), "| enwiki", cr.enwiki_title(x))
    for v, d in truthy.items():
        g = M.get(v, {})
        p("      ", v, "|", lab(g), "|", d["rank"], "| start", sorted(d["start"]), "| end", sorted(d["end"]),
          "| P1083", vals(g, "P1083"), "| P625", vals(g, "P625"), "| P576/P3999", vals(g, "P576") + vals(g, "P3999"))
    t = cr.enwiki_title(x)
    if t:
        p("       INFOBOX", infobox(t, "ground|capacity"))
        time.sleep(1)

# ---- 5. Stadion Gruenfeld
for s in ["Stadion Grünfeld", "Grünfeld Rapperswil"]:
    args = {"action": "wbsearchentities", "search": s, "language": "de", "format": "json", "limit": 8}
    d, e2 = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), "search")
    for hit in (d or {}).get("search", []):
        p("SEARCH", s, "|", hit.get("id"), "|", hit.get("label"), "|", hit.get("description"))
    time.sleep(1)
for t in ["Stadion Grünfeld", "FC Rapperswil-Jona"]:
    qs = urllib.parse.urlencode({"action": "parse", "page": t, "prop": "wikitext", "format": "json",
                                 "formatversion": "2", "redirects": "1", "section": "0"})
    d, e2 = cr.get_json_with_retry("https://de.wikipedia.org/w/api.php?" + qs, t)
    wt = (d or {}).get("parse", {}).get("wikitext", "")
    keep = [l.strip() for l in wt.splitlines()
            if re.match(r"\s*\|\s*(Stadion|Kapazität|Plätze|Koordinaten|Breitengrad|Längengrad|lat|long|NS|EW|Liga|Spielstätte|Zuschauer)", l, re.I)]
    coords = re.findall(r"\{\{Coordinate[^}]*\}\}", wt)
    p("DEWIKI", t, "|", " || ".join(keep)[:600] if keep else ("(no lines)" if wt else "(no article)"), "|", coords[:2])
    time.sleep(1)
req = urllib.request.Request("https://stadiumdb.com/stadiums/sui", headers={"User-Agent": cr.USER_AGENT})
with urllib.request.urlopen(req, timeout=60) as r:
    body = r.read().decode("utf-8", "replace")
for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S):
    txt = cr.text_of(tr)
    if re.search(r"Rapperswil|Nyon|Grünfeld|Colovray", txt): p("SDB-SUI", txt)
p("=== END OF PROBE AT2 ===")
