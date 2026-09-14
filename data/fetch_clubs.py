#!/usr/bin/env python3
"""
fetch_clubs.py -- step 4, Wikidata half.

Fetches football clubs for the configured countries and writes one file
per country to data/clubs/.

League names in Wikidata are fragmented: Romania's top flight appears as
both "Liga 1" and "Superliga" under different items, and Germany carries
several defunct Regionalliga items alongside the current five. So this
script never interprets a league NAME. It records the league's Q-id and
looks the tier up in data/league-tiers.csv, which you control.

A league that is not in that file is not guessed at. Its clubs get no
tier, and the league is written to data/clubs/unmapped-leagues.csv ready
for you to paste into league-tiers.csv once you have decided.

Because only leagues you have mapped count, defunct league tags are
ignored automatically - you simply never map them.

Stdlib only. No API key. Wikidata asks for a descriptive User-Agent.

Usage:  python3 tools/fetch_clubs.py
"""

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------- config

OUT_DIR = "data/clubs"
TIER_FILE = "data/league-tiers.csv"
SEED_FILE = os.path.join(OUT_DIR, "unmapped-leagues.csv")

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = ("football-fixture-planner/1.0 (personal project; "
              "https://github.com/AlexGrozavul/Football)")

COUNTRIES = [
    ("DE", "Q183", "Germany"),
    ("RO", "Q218", "Romania"),
]

REQUEST_GAP_SECONDS = 5
TIMEOUT_SECONDS = 90
MAX_RETRIES = 3

QUERY = """
SELECT ?club ?clubLabel ?league ?leagueLabel
       ?venue ?venueLabel ?capacity ?coord ?cityLabel
WHERE {
  ?club wdt:P31/wdt:P279* wd:Q476028 ;
        wdt:P17 wd:%(country)s .
  FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
  OPTIONAL { ?club wdt:P118 ?league }
  OPTIONAL {
    ?club wdt:P115 ?venue .
    OPTIONAL { ?venue wdt:P625 ?venueCoord }
    OPTIONAL { ?venue wdt:P1083 ?capacity }
  }
  OPTIONAL { ?club wdt:P625 ?clubCoord }
  OPTIONAL { ?club wdt:P159 ?city }
  BIND(COALESCE(?venueCoord, ?clubCoord) AS ?coord)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "%(lang)s,en" }
}
"""

POINT_RE = re.compile(r"Point\(\s*(-?[\d.]+)\s+(-?[\d.]+)\s*\)")


# ------------------------------------------------------------------ http

def sparql(query):
    body = urllib.parse.urlencode({"query": query, "format": "json"}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sparql_with_retry(query):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return sparql(query), None
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                wait = int(exc.headers.get("Retry-After") or 60)
                print(f"    rate limited, waiting {wait}s")
                time.sleep(wait)
                continue
            if exc.code in (500, 502, 503, 504) and attempt < MAX_RETRIES:
                print(f"    server error {exc.code}, retrying")
                time.sleep(15)
                continue
            return None, f"HTTP {exc.code}"
        except urllib.error.URLError as exc:
            if attempt < MAX_RETRIES:
                print(f"    network error, retrying: {exc.reason}")
                time.sleep(15)
                continue
            return None, f"network error: {exc.reason}"
        except TimeoutError:
            if attempt < MAX_RETRIES:
                print("    timed out, retrying")
                continue
            return None, "query timed out"
    return None, "exhausted retries"


# ------------------------------------------------------------ tier table

def qid(uri):
    return uri.rsplit("/", 1)[-1] if uri else None


def load_tiers():
    """
    data/league-tiers.csv -- header: leagueQid,tier,label,country

    tier is a whole number (1 = top flight) or the word "skip" to exclude
    a league entirely, which is how you drop women's or reserve leagues
    if you do not want them on the map.
    """
    tiers, problems = {}, []
    if not os.path.exists(TIER_FILE):
        problems.append(f"{TIER_FILE} does not exist yet - no club will get a tier")
        return tiers, problems

    with open(TIER_FILE, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or "leagueQid" not in reader.fieldnames:
            problems.append(f"{TIER_FILE} line 1: header must contain leagueQid and tier")
            return tiers, problems
        for row in reader:
            line = reader.line_num
            key = (row.get("leagueQid") or "").strip()
            raw = (row.get("tier") or "").strip().lower()
            if not key:
                continue
            if not re.match(r"^Q\d+$", key):
                problems.append(f"{TIER_FILE} line {line}: {key!r} is not a Q-id")
                continue
            if raw == "skip":
                tiers[key] = "skip"
            elif raw.isdigit():
                tiers[key] = int(raw)
            else:
                problems.append(
                    f"{TIER_FILE} line {line}: tier {raw!r} must be a whole number or 'skip'")
    return tiers, problems


# --------------------------------------------------------------- shaping

def cell(row, name):
    item = row.get(name)
    return item.get("value") if item else None


def build_clubs(rows, tiers):
    """Fold the flat SPARQL rows into one record per club."""
    clubs = {}
    leagues = {}

    for row in rows:
        cid = qid(cell(row, "club"))
        if not cid:
            continue

        club = clubs.setdefault(cid, {
            "id": cid, "name": None, "leagues": [], "tier": None,
            "venue": None, "capacity": None, "lat": None, "lon": None,
            "city": None,
        })

        label = cell(row, "clubLabel")
        if label and not label.startswith("Q"):
            club["name"] = label

        lid = qid(cell(row, "league"))
        if lid:
            if lid not in club["leagues"]:
                club["leagues"].append(lid)
            entry = leagues.setdefault(lid, {"id": lid, "label": None, "clubs": set()})
            entry["clubs"].add(cid)
            llabel = cell(row, "leagueLabel")
            if llabel and not llabel.startswith("Q"):
                entry["label"] = llabel

        venue = cell(row, "venueLabel")
        if venue and not venue.startswith("Q") and not club["venue"]:
            club["venue"] = venue

        cap = cell(row, "capacity")
        if cap and club["capacity"] is None:
            try:
                club["capacity"] = int(float(cap))
            except ValueError:
                pass

        coord = cell(row, "coord")
        if coord and club["lat"] is None:
            match = POINT_RE.match(coord)
            if match:
                club["lon"] = round(float(match.group(1)), 6)
                club["lat"] = round(float(match.group(2)), 6)

        city = cell(row, "cityLabel")
        if city and not city.startswith("Q") and not club["city"]:
            club["city"] = city

    # Tier comes only from leagues you have mapped. Unmapped and skipped
    # leagues are ignored, which is what keeps defunct tags out.
    ambiguous = []
    for club in clubs.values():
        mapped = [tiers[l] for l in club["leagues"]
                  if l in tiers and tiers[l] != "skip"]
        if mapped:
            club["tier"] = min(mapped)
            if len(set(mapped)) > 1:
                ambiguous.append(club["name"] or club["id"])

    return clubs, leagues, ambiguous


# ------------------------------------------------------------------ main

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tiers, tier_problems = load_tiers()

    all_leagues = {}
    index, failures, report = {}, [], []

    for position, (code, country_qid, name) in enumerate(COUNTRIES):
        if position:
            time.sleep(REQUEST_GAP_SECONDS)

        print(f"  {code}  {name}")
        lang = {"DE": "de", "RO": "ro"}.get(code, "en")
        query = QUERY % {"country": country_qid, "lang": lang}
        data, error = sparql_with_retry(query)

        if error:
            failures.append(f"{code} ({name}): {error} - existing file left untouched")
            continue

        rows = data.get("results", {}).get("bindings", [])
        clubs, leagues, ambiguous = build_clubs(rows, tiers)

        for lid, entry in leagues.items():
            existing = all_leagues.setdefault(
                lid, {"id": lid, "label": entry["label"], "clubs": 0, "country": code})
            existing["clubs"] += len(entry["clubs"])
            if not existing["label"]:
                existing["label"] = entry["label"]

        keep = {cid: c for cid, c in clubs.items()
                if c["tier"] is not None and c["lat"] is not None}
        no_tier = sum(1 for c in clubs.values() if c["tier"] is None)
        no_coord = sum(1 for c in clubs.values()
                       if c["tier"] is not None and c["lat"] is None)
        with_cap = sum(1 for c in keep.values() if c["capacity"])
        with_venue = sum(1 for c in keep.values() if c["venue"])

        payload = {
            "source": "Wikidata",
            "note": "Tier comes from data/league-tiers.csv, never from a league name.",
            "country": code,
            "countryName": name,
            "clubs": [keep[k] for k in sorted(keep)],
        }
        with open(os.path.join(OUT_DIR, f"{code}.json"), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1, ensure_ascii=False)
            fh.write("\n")

        by_tier = {}
        for club in keep.values():
            by_tier[club["tier"]] = by_tier.get(club["tier"], 0) + 1

        index[code] = {
            "name": name,
            "onMap": len(keep),
            "byTier": dict(sorted(by_tier.items())),
            "withVenueName": with_venue,
            "withCapacity": with_cap,
        }
        report.append(
            f"{code}  {len(keep):4d} on the map  |  {with_venue} named grounds, "
            f"{with_cap} with capacity  |  dropped: {no_tier} no mapped league, "
            f"{no_coord} no coordinates")
        if ambiguous:
            report.append(f"    {len(ambiguous)} club(s) map to more than one tier; "
                          f"took the highest division. First: {ambiguous[0]}")

    with open(os.path.join(OUT_DIR, "index.json"), "w", encoding="utf-8") as fh:
        json.dump({"source": "Wikidata", "countries": index}, fh,
                  indent=1, ensure_ascii=False)
        fh.write("\n")

    # Seed file: every league seen, with the tier column blank where you
    # have not decided. Paste the lines you want into league-tiers.csv.
    unmapped = sorted((l for l in all_leagues.values() if l["id"] not in tiers),
                      key=lambda l: (-l["clubs"], l["id"]))
    with open(SEED_FILE, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["leagueQid", "tier", "label", "country", "clubsSeen"])
        for league in unmapped:
            writer.writerow([league["id"], "", league["label"] or "",
                             league["country"], league["clubs"]])

    print()
    print("=" * 70)
    print("CLUB LAYER")
    print("=" * 70)
    for line in report:
        print("  " + line)
    if tier_problems:
        print()
        for p in tier_problems:
            print("  ! " + p)
    print()
    print(f"  {len(all_leagues)} leagues seen, {len(all_leagues) - len(unmapped)} mapped.")
    if unmapped:
        print(f"  {len(unmapped)} unmapped - written to {SEED_FILE}. Biggest:")
        for league in unmapped[:12]:
            print(f"    {league['id']:10s} {league['clubs']:4d} clubs  "
                  f"{league['country']}  {league['label'] or '(no label)'}")
    if failures:
        print()
        print("  NOT FETCHED THIS RUN:")
        for f in failures:
            print("  ! " + f)
    print("=" * 70)


if __name__ == "__main__":
    main()
