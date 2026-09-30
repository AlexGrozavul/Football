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
for site, t in (("ro", "Tricotaje Ineu"), ("en", "Tricotaje Ineu"), ("ro", "CS Victoria Ineu"), ("ro", "CS Lotru Brezoi (fotbal)")):
    q = urllib.parse.urlencode({"action": "query", "titles": t, "redirects": "1", "prop": "pageprops|info",
                                "ppprop": "wikibase_item", "format": "json", "formatversion": "2"})
    d = get(f"https://{site}.wikipedia.org/w/api.php?" + q)["query"]
    print(site, repr(t), "redirects:", d.get("redirects"), "pages:", [(p.get("title"), p.get("missing"), (p.get("pageprops") or {}).get("wikibase_item")) for p in d["pages"]])
for site, art in (("ro", "Liga a III-a 2026-2027"), ("en", "2026–27 Liga III")):
    title, ts, text = wikitext(site, art)
    print(f"--- {site} {art} rev {ts}")
    for m in re.finditer(r"Ineu|Tricotaje|Lotru|Brezoi", text):
        print("    ..." + text[max(0, m.start()-1500):m.end()+200].replace("\n", " / ") + "...")
        print()
# what the rowiki page for Victoria Ineu says about 2025-26 / 2026-27
title, ts, text = wikitext("ro", "CS Victoria Ineu")
for m in re.finditer(r"2025|2026|Tricotaje", text):
    print("    VI..." + text[max(0, m.start()-200):m.end()+200].replace("\n", " / ") + "...")
print("=" * 70)
