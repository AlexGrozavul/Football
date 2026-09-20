#!/usr/bin/env python3
"""TEMPORARY probe 2. Removed in the same branch once the answers are read."""
import json, urllib.parse, urllib.request

UA = ("football-fixture-planner/1.0 (personal project; "
      "https://github.com/AlexGrozavul/Football)")
API = "https://www.wikidata.org/w/api.php"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def entities(ids, props):
    q = urllib.parse.urlencode({"action":"wbgetentities","ids":"|".join(ids),
                                "props":props,"languages":"en|de|ro",
                                "format":"json","formatversion":"2"})
    return get(f"{API}?{q}").get("entities") or {}

def lab(e):
    L = (e or {}).get("labels") or {}
    for l in ("en","de","ro"):
        v = L.get(l)
        if isinstance(v,str): return v
        if isinstance(v,dict): return v.get("value")
    return ""

def desc(e):
    v = ((e or {}).get("descriptions") or {}).get("en")
    return v if isinstance(v,str) else (v or {}).get("value","")

# ---- 1. WHY ARE THESE ABSENT FROM THE CLUB LAYER?
#         The club query uses wdt:P118, which yields ONLY truthy statements:
#         the preferred-rank ones if any exist, otherwise the normal-rank
#         ones, and never a deprecated one. So a rank can hide a league.
print("### P118 STATEMENT RANKS (wdt: sees only truthy statements)")
ABSENT = ["Q15755", "Q368104", "Q141882", "Q571553", "Q97905916", "Q1386940"]
E = entities(ABSENT, "claims|labels")
for q in ABSENT:
    e = E.get(q) or {}
    c = e.get("claims") or {}
    print(f"  {q:11s} {lab(e)!r}")
    for s in c.get("P118") or []:
        ms = s.get("mainsnak") or {}
        v = (ms.get("datavalue") or {}).get("value") or {}
        val = v.get("id") if isinstance(v, dict) else f"<{ms.get('snaktype')}>"
        if ms.get("snaktype") != "value":
            val = f"<{ms.get('snaktype')}>"
        print(f"       P118 {str(val):12s} rank={s.get('rank')}")
    if not c.get("P118"):
        print("       P118 (none at all)")
    print(f"       P625 on club: {'yes' if c.get('P625') else 'no'}   "
          f"P115: {[((s.get('mainsnak') or {}).get('datavalue') or {}).get('value',{}).get('id') for s in (c.get('P115') or [])]}")
    print(f"       P576 dissolved: {'YES' if c.get('P576') else 'no'}")

# ---- 2. WHAT ARE THE UNMAPPED GERMAN LEAGUE Q-IDS?
#         30 Regionalliga clubs are invisible because their P118 names a
#         league that is not in league-tiers.csv. These are those leagues.
print()
print("### THE LEAGUE Q-IDS THAT KEEP 30 REGIONALLIGA CLUBS OFF THE MAP")
LEAGUES = ["Q878642","Q15735","Q316113","Q316686","Q317868","Q2188121",
           "Q1476473","Q821097","Q475887","Q317927","Q20028073","Q20025024",
           "Q1477024","Q283009","Q6954881","Q322128","Q548937","Q555836",
           "Q340179","Q539678","Q154069"]
L = entities(LEAGUES, "claims|labels|descriptions")
for q in LEAGUES:
    e = L.get(q) or {}
    c = e.get("claims") or {}
    lvl = [((s.get("mainsnak") or {}).get("datavalue") or {}).get("value")
           for s in (c.get("P3983") or [])]
    print(f"  {q:11s} {lab(e)[:44]:44s} P3983 level={lvl}")
    print(f"       {desc(e)[:96]!r}")

print()
print("### ANSWERS AGAIN (short)")
for q in ABSENT:
    e = E.get(q) or {}
    c = e.get("claims") or {}
    ranks = [(((s.get('mainsnak') or {}).get('datavalue') or {}).get('value',{}) or {}).get('id')
             or f"<{(s.get('mainsnak') or {}).get('snaktype')}>" for s in (c.get("P118") or [])]
    rk = [s.get("rank") for s in (c.get("P118") or [])]
    print(f"  {q:11s} {lab(e)[:26]:26s} P118={ranks} ranks={rk}")
