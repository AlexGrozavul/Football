#!/usr/bin/env python3
"""
TEMPORARY. Delete once the answer is written into CLAUDE.md.

Answers one question: why are roughly a third of the Regionalliga clubs
missing from data/clubs/DE.json? Writes nothing - it only prints.

It deliberately does NOT run the country-wide discovery query, which is
the one that keeps timing out. It works backwards from Wikidata's own
season items instead: each Regionalliga season item lists its
participating teams (P1923), so that list is what SHOULD be on the map.
Anything on it that is not in DE.json is then looked up one by one to
see which gate it fell through.
"""

import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
UA = ("football-fixture-planner/1.0 (personal project; "
      "https://github.com/AlexGrozavul/Football)")

# The five Regionalliga items already in data/league-tiers.csv.
RL = ["Q322128", "Q548937", "Q555836", "Q340179", "Q539678"]


def ask(query, timeout=90, tries=4):
    """Never raises. Returns (rows, error)."""
    for attempt in range(1, tries + 1):
        try:
            body = urllib.parse.urlencode({"query": query,
                                           "format": "json"}).encode()
            req = urllib.request.Request(ENDPOINT, data=body, headers={
                "User-Agent": UA,
                "Accept": "application/sparql-results+json",
                "Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
            return json.loads(raw)["results"]["bindings"], None
        except urllib.error.HTTPError as exc:
            print(f"      HTTP {exc.code}, attempt {attempt}/{tries}")
            if attempt == tries:
                return [], f"HTTP {exc.code}"
            time.sleep(20)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            print(f"      {type(exc).__name__}, attempt {attempt}/{tries}")
            if attempt == tries:
                return [], str(exc)
            time.sleep(20)
    return [], "exhausted retries"


def val(row, key):
    return row[key]["value"] if key in row else None


def qid(uri):
    return uri.rsplit("/", 1)[-1] if uri else None


def main():
    tiers, labels = {}, {}
    with open("data/league-tiers.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["leagueQid"]:
                tiers[row["leagueQid"]] = row["tier"]
                labels[row["leagueQid"]] = row["label"]

    print("=" * 72)
    print("A. What the club query actually returns for the five Regionalligen")
    print("=" * 72)
    rows, err = ask("""
    SELECT ?club ?clubLabel ?league ?venue ?venueLabel ?venueCoord ?clubCoord
    WHERE {
      VALUES ?league { %s }
      ?club wdt:P118 ?league .
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
      FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
      OPTIONAL { ?club wdt:P115 ?venue . OPTIONAL { ?venue wdt:P625 ?venueCoord } }
      OPTIONAL { ?club wdt:P625 ?clubCoord }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en" }
    }
    """ % " ".join("wd:" + l for l in RL))
    if err:
        print(f"  query failed: {err}")
        returned = {}
    else:
        returned = {}
        for row in rows:
            cid = qid(val(row, "club"))
            rec = returned.setdefault(cid, {"name": None, "venue": None,
                                            "coord": False, "leagues": set()})
            rec["name"] = rec["name"] or val(row, "clubLabel")
            rec["venue"] = rec["venue"] or val(row, "venueLabel")
            rec["leagues"].add(qid(val(row, "league")))
            if val(row, "venueCoord") or val(row, "clubCoord"):
                rec["coord"] = True
        no_coord = {k: v for k, v in returned.items() if not v["coord"]}
        print(f"  {len(returned)} clubs come back tagged with a Regionalliga")
        print(f"  {len(returned) - len(no_coord)} have coordinates, "
              f"{len(no_coord)} do not and are dropped")
        print("\n  Dropped for no coordinates:")
        for cid, rec in sorted(no_coord.items(), key=lambda x: x[1]["name"] or ""):
            print(f"    {cid:12s} {(rec['name'] or '?')[:40]:40s} "
                  f"ground: {rec['venue'] or '(none in Wikidata)'}")

    print()
    print("=" * 72)
    print("B. Who SHOULD be in each Regionalliga, per Wikidata's season items")
    print("=" * 72)
    want = {}
    for lid in RL:
        rows, err = ask("""
        SELECT ?season ?seasonLabel ?start ?team ?teamLabel WHERE {
          ?season wdt:P3450 wd:%s ; wdt:P580 ?start ; wdt:P1923 ?team .
          FILTER(YEAR(?start) >= 2024)
          SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en" }
        }
        """ % lid)
        if err:
            print(f"  {lid} {labels.get(lid, '?')}: query failed: {err}")
            continue
        seasons = {}
        for row in rows:
            sid = qid(val(row, "season"))
            seasons.setdefault(sid, {"label": val(row, "seasonLabel"),
                                     "start": val(row, "start"), "teams": {}})
            seasons[sid]["teams"][qid(val(row, "team"))] = val(row, "teamLabel")
        if not seasons:
            print(f"  {lid} {labels.get(lid, '?')}: no season item carries a "
                  f"participant list (P1923)")
            continue
        latest = max(seasons.values(), key=lambda s: s["start"])
        print(f"  {lid} {labels.get(lid, '?')}: latest season {latest['label']} "
              f"({latest['start'][:10]}) lists {len(latest['teams'])} teams")
        for tid, tlabel in latest["teams"].items():
            want[tid] = (tlabel, lid, latest["label"])
        time.sleep(3)

    if not want:
        print("\n  No season participant lists came back - B and C tell us nothing.")
        print("=" * 72)
        return

    print(f"\n  {len(want)} distinct clubs should be on the map at tier 4")
    have = {c["id"] for c in json.load(open("data/clubs/DE.json"))["clubs"]}
    missing = {k: v for k, v in want.items() if k not in have}
    print(f"  {len(want) - len(missing)} of them are in DE.json, "
          f"{len(missing)} are not")

    print()
    print("=" * 72)
    print("C. Why each missing club is missing")
    print("=" * 72)
    ids = list(missing)
    facts = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        rows, err = ask("""
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
        if err:
            print(f"  chunk {i // 50} failed: {err}")
            continue
        for row in rows:
            cid = qid(val(row, "club"))
            fact = facts.setdefault(cid, {"leagues": {}, "types": {},
                                          "venue": None, "coord": False,
                                          "dissolved": None})
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
        fact = facts.get(cid)
        if fact is None:
            reason = "not looked up (query failed)"
            lg, types = {}, {}
        else:
            lg, types = fact["leagues"], fact["types"]
            mapped = [l for l in lg if tiers.get(l, "") not in ("", "skip")]
            if fact["dissolved"]:
                reason = "P576 dissolved date is set"
            elif not lg:
                reason = "no P118 at all"
            elif not mapped:
                reason = "has P118, but not to a league in league-tiers.csv"
            elif not fact["coord"]:
                reason = "in a mapped league, but no coordinates anywhere"
            else:
                reason = "should have come through - look closer"
        tally[reason] = tally.get(reason, 0) + 1
        print(f"  {cid:12s} {(label or '?')[:38]:38s} {reason}")
        print("      P118 : " + (", ".join(f"{k} {v}" for k, v in lg.items())
                                 or "(none)"))
        print("      P31  : " + (", ".join(f"{k} {v}" for k, v in types.items())
                                 or "(none)"))
        if fact is not None:
            print(f"      ground: {fact['venue'] or '(none)'}   "
                  f"coords: {'yes' if fact['coord'] else 'NO'}   listed in: {season}")

    print("\n  Tally:")
    for reason, n in sorted(tally.items(), key=lambda x: -x[1]):
        print(f"    {n:4d}  {reason}")
    print("=" * 72)


if __name__ == "__main__":
    main()
