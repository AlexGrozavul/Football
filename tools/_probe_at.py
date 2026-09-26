"""TEMPORARY probe #1 for the Austria pass, the multi-ground check and the two
Swiss Challenge League clubs. Removed in the same branch."""
import csv, re, sys, time, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc

def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

# ---- 1. Austrian leagues
Q = """SELECT ?l ?lLabel ?level ?en ?typeLabel WHERE {
  ?l wdt:P17 wd:Q40 ; wdt:P641 wd:Q2736 .
  OPTIONAL { ?l wdt:P3983 ?level }
  OPTIONAL { ?l wdt:P31 ?type }
  OPTIONAL { ?en schema:about ?l ; schema:isPartOf <https://en.wikipedia.org/> }
  ?l rdfs:label ?lab . FILTER(LANG(?lab) IN ("en","de"))
  FILTER(CONTAINS(LCASE(?lab), "bundesliga") || CONTAINS(LCASE(?lab), "2. liga")
         || CONTAINS(LCASE(?lab), "erste liga") || CONTAINS(LCASE(?lab), "second league")
         || CONTAINS(LCASE(?lab), "regionalliga"))
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,de" }
}"""
res, err = fc.sparql_with_retry(Q)
rows = (res or {}).get("results", {}).get("bindings", [])
p("AT-LEAGUES", err, len(rows))
seen = {}
for r in rows:
    k = q_(fc.cell(r, "l"))
    s = seen.setdefault(k, [fc.cell(r, "lLabel"), fc.cell(r, "level"), fc.cell(r, "en"), set()])
    if fc.cell(r, "typeLabel"): s[3].add(fc.cell(r, "typeLabel"))
for k, (lab, lev, en, ty) in sorted(seen.items(), key=lambda kv: str(kv[1][1])):
    p("  ", k, "|", lab, "| level", lev, "|", en, "|", sorted(ty))
time.sleep(3)
at_top = [k for k, v in seen.items() if v[1] in ("1", "2")]
p("AT-TOP", at_top)

# ---- 2. season articles
for art in ["2026–27 Austrian Football Bundesliga", "2026–27 Austrian Football Second League"]:
    page, real, e = cr.fetch_article(art)
    if e:
        p("ARTICLE", art, "ERROR", e); continue
    tables, shape = cr.roster_tables(page)
    names, caps = [], {}
    for t, h in tables:
        p("  HEAD", h[:8])
        for title, cap in cr.rows_of(t, h):
            if title not in names: names.append(title); caps[title] = cap
    got, fails = cr.qids_for_titles(names)
    p("ARTICLE", art, "->", real, "|", shape, "| tables", len(tables), "| clubs", len(names),
      "| resolved", len(got), "| failures", fails)
    for n in names:
        p("   ", got.get(n, "-"), "|", n, "|", caps.get(n))
    time.sleep(2)

# ---- 3. StadiumDB slug
for slug in ["aut", "austria", "at", "ost"]:
    try:
        req = urllib.request.Request(f"https://stadiumdb.com/stadiums/{slug}",
                                     headers={"User-Agent": cr.USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode("utf-8", "replace"); st = r.status
    except urllib.error.HTTPError as ex:
        st, body = ex.code, ""
    except Exception as ex:
        st, body = str(ex), ""
    p("STADIUMDB", slug, st, len(body), body.count("<tr"))
    time.sleep(5)

# ---- 4. clubs with more than one truthy P115, every mapped league + Austria's top two
leagues = []
with open("data/league-tiers.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["tier"] != "skip": leagues.append(row["leagueQid"])
leagues += at_top
Q4 = """SELECT ?club ?clubLabel ?venue ?venueLabel ?rank ?start ?end ?cap ?coord WHERE {
  VALUES ?league { %s }
  ?club wdt:P118 ?league .
  FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
  FILTER NOT EXISTS { ?club wdt:P576 ?d }
  ?club p:P115 ?st . ?st ps:P115 ?venue ; wikibase:rank ?rank .
  FILTER(?rank != wikibase:DeprecatedRank)
  OPTIONAL { ?st pq:P580 ?start } OPTIONAL { ?st pq:P582 ?end }
  OPTIONAL { ?venue wdt:P1083 ?cap } OPTIONAL { ?venue wdt:P625 ?coord }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,de,fr,it,ro" }
}""" % " ".join("wd:" + l for l in leagues)
res, err = fc.sparql_with_retry(Q4)
rows = (res or {}).get("results", {}).get("bindings", [])
p("MULTI-P115 query", err, len(rows), "rows over", len(leagues), "leagues")
clubs = {}
for r in rows:
    c = q_(fc.cell(r, "club"))
    ent = clubs.setdefault(c, {"label": fc.cell(r, "clubLabel"), "v": {}})
    v = q_(fc.cell(r, "venue"))
    d = ent["v"].setdefault(v, {"label": fc.cell(r, "venueLabel"), "rank": q_(fc.cell(r, "rank")).split("#")[-1],
                                "start": set(), "end": set(), "cap": set(), "coord": set()})
    for k in ("start", "end", "cap", "coord"):
        if fc.cell(r, k): d[k].add(fc.cell(r, k)[:40])
n = 0
for c, ent in sorted(clubs.items(), key=lambda kv: kv[1]["label"] or ""):
    ranks = [d["rank"] for d in ent["v"].values()]
    best = "PreferredRank" if "PreferredRank" in ranks else "NormalRank"
    truthy = {v: d for v, d in ent["v"].items() if d["rank"] == best}
    if len(truthy) < 2:
        continue
    n += 1
    p("MULTI", c, "|", ent["label"])
    for v, d in truthy.items():
        p("     ", v, "|", d["label"], "|", d["rank"], "| start", sorted(d["start"]), "| end", sorted(d["end"]),
          "| cap", sorted(d["cap"]), "| coord", sorted(d["coord"]))
p("MULTI-COUNT", n)
time.sleep(3)

# ---- 5. Rapperswil-Jona and Stade Nyonnais
def ents(ids=None, titles=None):
    args = {"action": "wbgetentities", "props": "claims|labels|sitelinks", "languages": "en|de|fr",
            "format": "json"}
    if ids: args["ids"] = "|".join(ids)
    else: args.update(sites="enwiki", titles="|".join(titles))
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), "ents")
    return (d or {}).get("entities", {}), e

def vals(ent, prop):
    out = []
    for c in ent.get("claims", {}).get(prop, []):
        v = c["mainsnak"].get("datavalue", {}).get("value")
        if isinstance(v, dict) and "latitude" in v: v = (round(v["latitude"], 6), round(v["longitude"], 6))
        elif isinstance(v, dict) and "amount" in v: v = v["amount"]
        elif isinstance(v, dict) and "id" in v: v = v["id"]
        elif isinstance(v, dict) and "time" in v: v = v["time"][:11]
        qual = {k: [x.get("datavalue", {}).get("value", {}).get("time", "")[:11] for x in xs]
                for k, xs in c.get("qualifiers", {}).items() if k in ("P580", "P582")}
        out.append((v, c.get("rank"), qual) if qual else (v, c.get("rank")))
    return out

e5, err = ents(ids=["Q681483", "Q673268"])
p("SWISS2", err)
venues = []
for qid, ent in e5.items():
    p("CLUB", qid, (ent.get("labels", {}).get("en") or {}).get("value"), "| enwiki", cr.enwiki_title(ent),
      "| P118", vals(ent, "P118"), "| P115", vals(ent, "P115"), "| P625", vals(ent, "P625"),
      "| P576", vals(ent, "P576"), "| P17", vals(ent, "P17"), "| P159", vals(ent, "P159"))
    venues += [v[0] for v in vals(ent, "P115") if isinstance(v[0], str)]
if venues:
    ev, err = ents(ids=venues)
    for qid, ent in ev.items():
        p("GROUND", qid, (ent.get("labels", {}).get("en") or {}).get("value"), "| enwiki", cr.enwiki_title(ent),
          "| P625", vals(ent, "P625"), "| P1083", vals(ent, "P1083"), "| P466", vals(ent, "P466"))

def infobox(title):
    qs = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "wikitext",
                                 "format": "json", "formatversion": "2", "redirects": "1", "section": "0"})
    d, e = cr.get_json_with_retry(f"{cr.WIKIPEDIA_API}?{qs}", title)
    return (d or {}).get("parse", {}).get("wikitext", "")

for title in ["FC Rapperswil-Jona", "FC Stade Nyonnais", "Stadion Grünfeld", "Stade de Colovray"]:
    wt = infobox(title)
    keep = [l.strip() for l in wt.splitlines()
            if re.match(r"\s*\|\s*(ground|capacity|coordinates|coord|league|season|position|dissolved|tenants|location|opened)\b", l, re.I)]
    p("INFOBOX", title, "|", " || ".join(keep)[:700] if keep else ("(no infobox lines)" if wt else "(no article)"))
    time.sleep(1)

for art in ["2026–27 Swiss Challenge League", "2026–27 Swiss Super League"]:
    page, real, e = cr.fetch_article(art)
    plain = cr.text_of(page or "")
    for kw in ("Rapperswil", "Nyon"):
        hits = [plain[max(0, m.start()-150):m.start()+200] for m in re.finditer(kw, plain)][:4]
        p("MENTION", art, kw, len(hits))
        for h in hits: p("    ...", h)
    time.sleep(2)
p("=== END OF PROBE AT1 ===")
