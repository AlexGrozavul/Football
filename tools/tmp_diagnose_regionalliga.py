#!/usr/bin/env python3
"""
TEMPORARY. Delete once the answer is written into CLAUDE.md.

Answers one question: why are roughly a third of the Regionalliga clubs
missing from data/clubs/DE.json? Writes nothing - it only prints.

It works backwards from Wikidata's own season items: each Regionalliga
season item lists its participating teams (P1923), so that list is what
SHOULD be on the map. Anything on it that is not in DE.json is then
looked up one by one to see which gate it fell through.
"""

import csv
import json
import time
import urllib.parse
import urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
UA = ("football-fixture-planner/1.0 (personal project; "
      "https://github.com/AlexGrozavul/Football)")

# The five Regionalliga items already in data/league-tiers.csv.
RL = ["Q322128", "Q548937", "Q555836", "Q340179", "Q539678"]


def ask(query, timeout=90):
    body = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={
        "User-Agent": UA,
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded"})
    start = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
    return json.loads(raw)["results"]["bindings"], time.time() - start


def val(row, key):
    return row[key]["value"] if key in row else None


def qid(uri):
    return uri.rsplit("/", 1)[-1] if uri else None


def main():
    tiers = {}
    with open("data/league-tiers.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["leagueQid"]:
                tiers[row["leagueQid"]] = (row["tier"], row["label"])

    print("=" * 72)
    print("A. Discovery query for Germany, with the human exclusion in place")
    print("=" * 72)
    rows, took = ask("""
    SELECT ?club ?league ?leagueLabel WHERE {
      ?club wdt:P17 wd:Q183 ; wdt:P118 ?league .
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
      FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en" }
    }
    """)
    print(f"  {len(rows)} rows in {took:.1f}s")
    leagues = {}
    for row in rows:
        lid = qid(val(row, "league"))
        entry = leagues.setdefault(lid, {"n": 0, "label": None})
        entry["n"] += 1
        label = val(row, "leagueLabel")
        if label and not label.startswith("Q"):
            entry["label"] = label
    print(f"  {len(leagues)} distinct leagues, "
          f"{sum(1 for l in leagues if l in tiers)} of them mapped")

    print("\n  Every league whose label mentions Regionalliga:")
    for lid, entry in sorted(leagues.items(), key=lambda x: -x[1]["n"]):
        if "egionalliga" in (entry["label"] or ""):
            mark = "MAPPED  " if lid in tiers else "unmapped"
            print(f"    {mark} {lid:12s} {entry['n']:4d} clubs  {entry['label']}")

    print("\n  The 25 biggest unmapped German leagues:")
    shown = 0
    for lid, entry in sorted(leagues.items(), key=lambda x: -x[1]["n"]):
        if lid in tiers or shown >= 25:
            continue
        print(f"    {lid:12s} {entry['n']:4d} clubs  {entry['label'] or '(no label)'}")
        shown += 1

    print()
    print("=" * 72)
    print("B. Who SHOULD be in each Regionalliga, per Wikidata's season items")
    print("=" * 72)
    want = {}
    for lid in RL:
        rows, _ = ask("""
        SELECT ?season ?seasonLabel ?start ?team ?teamLabel WHERE {
          ?season wdt:P3450 wd:%s ; wdt:P580 ?start ; wdt:P1923 ?team .
          FILTER(YEAR(?start) >= 2024)
          SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en" }
        }
        """ % lid)
        seasons = {}
        for row in rows:
            sid = qid(val(row, "season"))
            seasons.setdefault(sid, {"label": val(row, "seasonLabel"),
                                     "start": val(row, "start"), "teams": {}})
            seasons[sid]["teams"][qid(val(row, "team"))] = val(row, "teamLabel")
        name = tiers.get(lid, ("", "?"))[1]
        if not seasons:
            print(f"  {lid} {name}: no season item with a participant list")
            continue
        latest = max(seasons.values(), key=lambda s: s["start"])
        print(f"  {lid} {name}: latest season {latest['label']} "
              f"({latest['start'][:10]}) lists {len(latest['teams'])} teams")
        for tid, tlabel in latest["teams"].items():
            want[tid] = (tlabel, lid, latest["label"])
        time.sleep(3)

    print(f"\n  {len(want)} distinct clubs should be on the map at tier 4")
    have = {c["id"] for c in json.load(open("data/clubs/DE.json"))["clubs"]}
    missing = {k: v for k, v in want.items() if k not in have}
    print(f"  {len(want) - len(missing)} of them are in DE.json, {len(missing)} are not")

    print()
    print("=" * 72)
    print("C. Why each missing club is missing")
    print("=" * 72)
    ids = list(missing)
    facts = {}
    for i in range(0, len(ids), 60):
        chunk = ids[i:i + 60]
        rows, _ = ask("""
        SELECT ?club ?clubLabel ?league ?leagueLabel ?type ?typeLabel
               ?venue ?venueLabel ?venueCoord ?clubCoord ?dissolved WHERE {
          VALUES ?club { %s }
          OPTIONAL { ?club wdt:P118 ?league }
          OPTIONAL { ?club wdt:P31 ?type }
          OPTIONAL { ?club wdt:P115 ?venue . OPTIONAL { ?venue wdt:P625 ?venueCoord } }
          OPTIONAL { ?club wdt:P625 ?clubCoord }
          OPTIONAL { ?club wdt:P576 ?dissolved }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en" }
        }
        """ % " ".join("wd:" + c for c in chunk))
        for row in rows:
            cid = qid(val(row, "club"))
            fact = facts.setdefault(cid, {"name": None, "leagues": {}, "types": {},
                                          "venue": None, "coord": False,
                                          "dissolved": None})
            fact["name"] = fact["name"] or val(row, "clubLabel")
            lid = qid(val(row, "league"))
            if lid:
                fact["leagues"][lid] = val(row, "leagueLabel")
            tid = qid(val(row, "type"))
            if tid:
                fact["types"][tid] = val(row, "typeLabel")
            fact["venue"] = fact["venue"] or val(row, "venueLabel")
            if val(row, "venueCoord") or val(row, "clubCoord"):
                fact["coord"] = True
            fact["dissolved"] = fact["dissolved"] or val(row, "dissolved")
        time.sleep(3)

    tally = {}
    for cid, (label, _lid, season) in sorted(missing.items(),
                                             key=lambda x: x[1][0] or ""):
        fact = facts.get(cid, {})
        lg = fact.get("leagues", {})
        mapped = [l for l in lg if l in tiers and tiers[l][0] not in ("", "skip")]
        if fact.get("dissolved"):
            reason = "P576 dissolved date set"
        elif not lg:
            reason = "no P118 at all"
        elif not mapped:
            reason = "P118 present, but pointing at no mapped league"
        elif not fact.get("coord"):
            reason = "mapped league, but no coordinates"
        else:
            reason = "should have come through - look closer"
        tally[reason] = tally.get(reason, 0) + 1
        print(f"  {cid:12s} {(label or '?')[:38]:38s} {reason}")
        print("      P118 : " + (", ".join(f"{k} {v}" for k, v in lg.items()) or "(none)"))
        print("      P31  : " + (", ".join(f"{k} {v}" for k, v in
                                           fact.get("types", {}).items()) or "(none)"))
        print(f"      venue: {fact.get('venue') or '(none)'}   "
              f"coords: {'yes' if fact.get('coord') else 'NO'}   in: {season}")

    print("\n  Tally:")
    for reason, n in sorted(tally.items(), key=lambda x: -x[1]):
        print(f"    {n:4d}  {reason}")
    print("=" * 72)


if __name__ == "__main__":
    main()
