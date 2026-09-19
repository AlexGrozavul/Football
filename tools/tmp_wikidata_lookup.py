#!/usr/bin/env python3
"""
tmp_wikidata_lookup.py -- THROWAWAY. Delete once the answers are in
CLAUDE.md and data/clubs-manual.csv.

The sandbox this was written in cannot reach wikidata.org at all (the
egress proxy answers 403 to CONNECT). GitHub's runners can, so this
runs there and prints. It writes no data file and nothing reads its
output but a human.

Four questions, all of them already written down in CLAUDE.md as
blocked on network access:

  1. Where is Q7596368 (Stadionul Buftea / CNF Buftea)? CS Dinamo
     Bucuresti (Q113577526) needs its coordinates, and until it has
     them it sits on top of the senior club at Stadionul Dinamo.
  2. Which of Q14551982 and Q701290 is the real SSV Ulm 1846? The test
     is the one already used for Lok Leipzig: more Wikipedia sitelinks
     wins. Both branches are prepared in CLAUDE.md.
  3. Does Q1387764 (FC Triesenberg) really carry the German 3. Liga
     tag, and is its country Liechtenstein? Recorded as inference.
  4. What does Wikidata actually claim for Q7671747 (TSV 1860 Muenchen
     II)? Informational: the ground is believed copied from the senior
     club and is NOT being trusted either way.
"""

import json
import sys
import urllib.parse
import urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
ENTITY = "https://www.wikidata.org/wiki/Special:EntityData/%s.json"
UA = ("football-fixture-planner/1.0 (personal project; "
      "https://github.com/AlexGrozavul/Football)")

# A sitelink key ending in "wiki" is a Wikipedia EXCEPT for these, which
# are other Wikimedia projects. wikibase:sitelinks counts every project,
# so it is the wrong number for a "which item do the Wikipedias use"
# test - that is the test CLAUDE.md records for Lok Leipzig (39 v 2).
NOT_WIKIPEDIA = {
    "commonswiki", "specieswiki", "metawiki", "wikidatawiki",
    "sourceswiki", "mediawikiwiki", "incubatorwiki", "outreachwiki",
    "wikimaniawiki", "foundationwiki",
}


def get(url, data=None):
    req = urllib.request.Request(
        url, data=data,
        headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sparql(query):
    body = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    return get(ENDPOINT, body)


def entity(qid):
    return get(ENTITY % qid)["entities"][qid]


def claims(ent, prop):
    out = []
    for st in ent.get("claims", {}).get(prop, []):
        main = st.get("mainsnak", {})
        if main.get("snaktype") != "value":
            out.append("(no value)")
            continue
        val = main["datavalue"]["value"]
        if isinstance(val, dict) and "id" in val:
            out.append(val["id"])
        elif isinstance(val, dict) and "latitude" in val:
            out.append((round(val["latitude"], 6), round(val["longitude"], 6)))
        elif isinstance(val, dict) and "amount" in val:
            out.append(val["amount"].lstrip("+"))
        else:
            out.append(val)
    return out


def label(ent, langs=("en", "de", "ro")):
    for lang in langs:
        if lang in ent.get("labels", {}):
            return ent["labels"][lang]["value"]
    return "(no label)"


def wikipedias(ent):
    keys = [k for k in ent.get("sitelinks", {})
            if k.endswith("wiki") and k not in NOT_WIKIPEDIA]
    return sorted(keys)


def rule(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def safe(fn, *args):
    try:
        return fn(*args), None
    except Exception as exc:                      # noqa: BLE001 - one-off
        return None, f"{type(exc).__name__}: {exc}"


# ------------------------------------------------------------------ 1

rule("1. Q7596368 - the ground CS Dinamo Bucuresti needs coordinates from")

for qid in ("Q7596368", "Q113577526", "Q204237"):
    ent, err = safe(entity, qid)
    if err:
        print(f"  {qid}  COULD NOT BE READ: {err}")
        continue
    print(f"  {qid}  {label(ent)}")
    print(f"      P625 coordinates : {claims(ent, 'P625') or '(none on the item)'}")
    print(f"      P1083 capacity   : {claims(ent, 'P1083') or '(none)'}")
    print(f"      P115 home venue  : {claims(ent, 'P115') or '(none)'}")
    print(f"      P17 country      : {claims(ent, 'P17') or '(none)'}")
    print(f"      P131 located in  : {claims(ent, 'P131') or '(none)'}")
    print(f"      P118 league      : {claims(ent, 'P118') or '(none)'}")

# ------------------------------------------------------------------ 2

rule("2. SSV Ulm 1846 - which item do the Wikipedias use?")

counts = {}
for qid in ("Q14551982", "Q701290"):
    ent, err = safe(entity, qid)
    if err:
        print(f"  {qid}  COULD NOT BE READ: {err}")
        continue
    wikis = wikipedias(ent)
    counts[qid] = len(wikis)
    print(f"  {qid}  {label(ent)}")
    print(f"      Wikipedia sitelinks : {len(wikis)}  {wikis if len(wikis) <= 12 else wikis[:12] + ['...']}")
    print(f"      all sitelinks       : {len(ent.get('sitelinks', {}))}")
    print(f"      P118 league         : {claims(ent, 'P118') or '(none)'}")
    print(f"      P115 home venue     : {claims(ent, 'P115') or '(none)'}")
    print(f"      P625 coordinates    : {claims(ent, 'P625') or '(none)'}")
    print(f"      P31 instance of     : {claims(ent, 'P31') or '(none)'}")
    print(f"      P576 dissolved      : {claims(ent, 'P576') or '(none)'}")

if len(counts) == 2:
    a, b = "Q14551982", "Q701290"
    if counts[a] == counts[b]:
        print(f"\n  TIE at {counts[a]} each - the sitelink test does NOT decide this.")
    else:
        win = a if counts[a] > counts[b] else b
        lose = b if win == a else a
        print(f"\n  WINNER: {win} ({counts[win]} Wikipedias) over {lose} ({counts[lose]}).")
        if win == "Q701290":
            print("  -> CLAUDE.md branch one: Q14551982 becomes a skip row and its")
            print("     hand-written tier 4 correction is deleted with it.")
        else:
            print("  -> CLAUDE.md branch two: keep the Q14551982 tier 4 correction,")
            print("     and Q701290 gets the skip row instead.")

# ------------------------------------------------------------------ 3

rule("3. Q1387764 FC Triesenberg - is the 3. Liga tag really there?")

ent, err = safe(entity, "Q1387764")
if err:
    print(f"  COULD NOT BE READ: {err}")
else:
    print(f"  {label(ent)}")
    print(f"      P17 country     : {claims(ent, 'P17') or '(none)'}   (Q347 = Liechtenstein)")
    print(f"      P118 league     : {claims(ent, 'P118') or '(none)'}   (Q154069 = German 3. Liga)")
    print(f"      P115 home venue : {claims(ent, 'P115') or '(none)'}")
    print(f"      P625 coordinates: {claims(ent, 'P625') or '(none)'}")
    print(f"      P131 located in : {claims(ent, 'P131') or '(none)'}")

# ------------------------------------------------------------------ 4

rule("4. Q7671747 TSV 1860 Muenchen II - what does Wikidata claim?")
print("  Informational only. The ground is NOT being taken from here:")
print("  it is believed copied from the senior club and stays unconfirmed.")

ent, err = safe(entity, "Q7671747")
if err:
    print(f"  COULD NOT BE READ: {err}")
else:
    print(f"  {label(ent)}")
    print(f"      P118 league     : {claims(ent, 'P118') or '(none)'}")
    print(f"      P115 home venue : {claims(ent, 'P115') or '(none)'}")
    print(f"      P625 coordinates: {claims(ent, 'P625') or '(none)'}")
    print(f"      P1083 capacity  : {claims(ent, 'P1083') or '(none)'}")

# --------------------------------------------------- label the Q-ids seen

rule("Labels for every Q-id printed above, so none of it has to be guessed")

ids = set()
for line_qid in ("Q7596368", "Q113577526", "Q204237", "Q14551982",
                 "Q701290", "Q1387764", "Q7671747"):
    ent, err = safe(entity, line_qid)
    if err:
        continue
    for prop in ("P115", "P17", "P118", "P131", "P31"):
        for val in claims(ent, prop):
            if isinstance(val, str) and val.startswith("Q"):
                ids.add(val)

if ids:
    values = " ".join("wd:" + i for i in sorted(ids))
    res, err = safe(sparql, """
    SELECT ?item ?itemLabel ?coord WHERE {
      VALUES ?item { %s }
      OPTIONAL { ?item wdt:P625 ?coord }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,de,ro" }
    }
    """ % values)
    if err:
        print(f"  SPARQL could not be reached: {err}")
    else:
        for row in res["results"]["bindings"]:
            qid = row["item"]["value"].rsplit("/", 1)[-1]
            lbl = row.get("itemLabel", {}).get("value", "")
            crd = row.get("coord", {}).get("value", "")
            print(f"  {qid:12s} {lbl}   {crd}")

print()
print("=" * 70)
print("END OF THROWAWAY LOOKUP")
print("=" * 70)
