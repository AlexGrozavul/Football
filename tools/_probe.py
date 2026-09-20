#!/usr/bin/env python3
"""TEMPORARY probe. Removed in the same branch once the answers are read."""
import json, urllib.parse, urllib.request

UA = ("football-fixture-planner/1.0 (personal project; "
      "https://github.com/AlexGrozavul/Football)")
API = "https://www.wikidata.org/w/api.php"

PAIRS = [
    ("FC Augsburg",        "Q15755",      "Q97905916"),
    ("FC Erzgebirge Aue",  "Q141882",     "Q97927365"),
    ("SV Babelsberg 03",   "Q571553",     "Q97927380"),
    ("Bihor Oradea",       "Q113541238",  "Q1386940"),
]
SOLO = ["Q368104", "Q24884611", "Q2188121", "Q819400", "Q537301", "Q2188121"]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def entities(ids, props="claims|labels|sitelinks|descriptions"):
    q = urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(ids),
                                "props": props, "languages": "en|de|ro",
                                "format": "json", "formatversion": "2"})
    return get(f"{API}?{q}").get("entities") or {}

def qids(claims, p):
    out = []
    for s in claims.get(p) or []:
        v = ((s.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {}
        if isinstance(v, dict) and v.get("id"):
            out.append(v["id"])
        else:
            out.append(f"<{(s.get('mainsnak') or {}).get('snaktype')}>")
    return out

def lab(e, langs=("en","de","ro")):
    L = e.get("labels") or {}
    for l in langs:
        v = L.get(l)
        if isinstance(v, str): return v
        if isinstance(v, dict): return v.get("value")
    return ""

def desc(e):
    D = e.get("descriptions") or {}
    v = D.get("en")
    return v if isinstance(v, str) else (v or {}).get("value", "")

def show(qid, e):
    if not e or e.get("missing"):
        print(f"    {qid}: MISSING"); return
    c = e.get("claims") or {}
    sl = e.get("sitelinks")
    n = len(sl) if isinstance(sl, (list, dict)) else 0
    enw = None
    if isinstance(sl, list):
        enw = next((x.get("title") for x in sl if x.get("site")=="enwiki"), None)
    elif isinstance(sl, dict):
        enw = (sl.get("enwiki") or {}).get("title")
    print(f"    {qid}  {lab(e)!r}")
    print(f"       desc      : {desc(e)!r}")
    print(f"       sitelinks : {n}   enwiki={enw!r}")
    print(f"       P31 type  : {qids(c,'P31')}")
    print(f"       P118 league: {qids(c,'P118')}")
    print(f"       P115 venue : {qids(c,'P115')}   P625 on club: {'yes' if c.get('P625') else 'no'}")
    print(f"       P576 dissolved: {'YES ' + str(qids(c,'P576')) if c.get('P576') else 'no'}")
    print(f"       P17 country: {qids(c,'P17')}   P1448/P1449: {'-'}")

print("### DUPLICATE PAIRS")
ids = [q for _, a, b in PAIRS for q in (a, b)] + SOLO
E = entities(sorted(set(ids)))
for name, a, b in PAIRS:
    print(f"  {name}")
    show(a, E.get(a)); show(b, E.get(b))
print()
print("### SOLO ITEMS")
for q in dict.fromkeys(SOLO):
    show(q, E.get(q))
print()
print("### WHAT THE TYPE Q-IDS ARE")
types = set()
for e in E.values():
    if e and not e.get("missing"):
        types.update(t for t in qids((e.get("claims") or {}), "P31") if t.startswith("Q"))
T = entities(sorted(types), props="labels|descriptions")
for t in sorted(types):
    print(f"    {t}: {lab(T.get(t) or {})!r} - {desc(T.get(t) or {})!r}")
print()
print("### ANSWERS AGAIN (short)")
for name, a, b in PAIRS:
    for q in (a, b):
        e = E.get(q) or {}
        c = e.get("claims") or {}
        sl = e.get("sitelinks")
        n = len(sl) if isinstance(sl,(list,dict)) else 0
        print(f"  {name:20s} {q:11s} sitelinks={n:3d} P31={qids(c,'P31')} P118={qids(c,'P118')}")
