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
for site, art in (("ro", "Liga a III-a 2026-2027"), ("ro", "Liga a IV-a Vâlcea")):
    try:
        title, ts, text = wikitext(site, art)
    except Exception as exc:
        print(f"{art}: FAILED {exc}"); continue
    hits = [l.strip()[:200] for l in text.splitlines() if re.search(r"Lotru|Brezoi|Ineu", l)]
    print(f"{art} (rev {ts}, {len(text)} chars): {len(hits)} line(s) naming Lotru/Brezoi/Ineu")
    for m in re.finditer(r"Lotru|Brezoi|Ineu", text):
        print("    ..." + text[max(0, m.start()-400):m.end()+300].replace("\n", " / ") + "...")
print("=" * 70)
