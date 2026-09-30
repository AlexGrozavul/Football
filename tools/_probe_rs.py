"""TEMPORARY probe, removed in the same branch. Reads Wikidata and
Wikipedia for: CS Lotru Brezoi Q141319965, Victoria Ineu Q5014471 (their
own pages, current revision), the Romanian 2026-27 season articles, and
the Super League Greece 2 row for Asteras Tripolis B."""
import json, re, sys, urllib.parse, urllib.request
sys.path.insert(0, "tools")
UA = {"User-Agent": "football-fixture-planner/1.0 (personal project; https://github.com/AlexGrozavul/Football)"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def wd(qid):
    q = urllib.parse.urlencode({"action": "wbgetentities", "ids": qid, "format": "json",
                                "props": "labels|sitelinks|claims|descriptions", "languages": "en|ro"})
    return get("https://www.wikidata.org/w/api.php?" + q)["entities"][qid]

def wikitext(site, title):
    q = urllib.parse.urlencode({"action": "query", "prop": "revisions", "titles": title,
                                "rvprop": "content|timestamp", "rvslots": "main",
                                "format": "json", "formatversion": "2", "redirects": "1"})
    page = get(f"https://{site}.wikipedia.org/w/api.php?" + q)["query"]["pages"][0]
    rev = page["revisions"][0]
    return page["title"], rev["timestamp"], rev["slots"]["main"]["content"]

print("=" * 70)
for qid in ("Q141319965", "Q5014471"):
    e = wd(qid)
    print(f"### {qid}  labels={ {k: v['value'] for k, v in e.get('labels', {}).items()} }")
    print(f"    descriptions={ {k: v['value'] for k, v in e.get('descriptions', {}).items()} }")
    print(f"    P576={[c['mainsnak'].get('datavalue', {}).get('value') for c in e['claims'].get('P576', [])]}")
    for c in e["claims"].get("P118", []):
        v = c["mainsnak"].get("datavalue", {}).get("value", {}).get("id")
        quals = {p: [x.get("datavalue", {}).get("value", {}).get("time") for x in xs]
                 for p, xs in c.get("qualifiers", {}).items() if p in ("P580", "P582")}
        print(f"    P118 {v} rank={c['rank']} {quals}")
    links = {k: v["title"] for k, v in e.get("sitelinks", {}).items()}
    print(f"    sitelinks={links}")
    for site in ("enwiki", "rowiki"):
        if site not in links:
            print(f"    {site}: NO ARTICLE")
            continue
        title, ts, text = wikitext(site[:2], links[site])
        print(f"    --- {site} '{title}', current revision {ts}")
        m = re.search(r"\{\{\s*Infobox.*?\n\}\}", text, re.S | re.I)
        box = m.group(0) if m else ""
        for line in box.splitlines():
            if re.search(r"league|liga|season|sezon|position|pozi|dissolved|desfiin|ground|stadion|founded|fondat|campionat", line, re.I):
                print("      | " + line.strip()[:220])
        for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\{\{[^{}]*\}\}|<ref[^>]*/>|<ref.*?</ref>", "", text, flags=re.S)):
            if re.search(r"Liga (IV|V|VI|a IV|a V|a VI|III|a III)|relegat|retrogr|withdr|retras|dissolv|desfiin", s, re.I):
                print("      > " + re.sub(r"\s+", " ", s).strip()[:300])
print("=" * 70)
for art in ("2026–27 Liga I", "2026–27 Liga II", "2026–27 Liga III"):
    try:
        title, ts, text = wikitext("en", art)
    except Exception as exc:
        print(f"{art}: FAILED {exc}"); continue
    hits = [l.strip()[:200] for l in text.splitlines() if re.search(r"Lotru|Brezoi|Ineu", l)]
    print(f"{art} (rev {ts}, {len(text)} chars): {len(hits)} line(s) naming Lotru/Brezoi/Ineu")
    for h in hits[:10]:
        print("    " + h)
print("=" * 70)
import check_rosters as cr
html_text, title, err = cr.fetch_article("2026–27 Super League Greece 2")
print("SL2", title, err)
for table, headers in cr.roster_tables(html_text):
    for row in cr.table_rows(table, headers):
        if "asteras" in cr.fold(row.get("team") or row.get("shown") or ""):
            print("    ROW", {k: row.get(k) for k in ("team", "title", "why", "shown")})
            print("    folded clean team:", repr(cr.fold(cr.clean_team(row["team"]))))
print("=" * 70)
