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
MANUAL_FILE = "data/clubs-manual.csv"

# Columns of data/clubs-manual.csv. Header-driven, so order does not
# matter and unused columns may be left out.
MANUAL_REQUIRED = ("name",)
MANUAL_OPTIONAL = ("clubQid", "country", "tier", "venue", "capacity",
                   "lat", "lon", "ticketUrl", "source", "note")

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

# Discovery: every club in the country that carries any league tag. No
# type filter, so nothing is missed - the cost is that other sports show
# up in the seed list, which you mark "skip".
DISCOVERY_QUERY = """
SELECT ?club ?league ?leagueLabel WHERE {
  ?club wdt:P17 wd:%(country)s ; wdt:P118 ?league .
  FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "%(lang)s,en" }
}
"""

# Clubs: restricted to the leagues you mapped, so no type filter is
# needed and reserve teams are no longer excluded by accident.
CLUB_QUERY = """
SELECT ?club ?clubLabel ?league ?venue ?venueLabel ?capacity ?coord ?cityLabel
WHERE {
  VALUES ?league { %(leagues)s }
  ?club wdt:P118 ?league .
  FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
  OPTIONAL {
    ?club wdt:P115 ?venue .
    OPTIONAL { ?venue wdt:P625 ?venueCoord }
    OPTIONAL { ?venue wdt:P1083 ?capacity }
  }
  OPTIONAL { ?club wdt:P625 ?clubCoord }
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
    tiers, labels, problems = {}, {}, []
    if not os.path.exists(TIER_FILE):
        problems.append(f"{TIER_FILE} does not exist yet - no club will get a tier")
        return tiers, labels, problems

    with open(TIER_FILE, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or "leagueQid" not in reader.fieldnames:
            problems.append(f"{TIER_FILE} line 1: header must contain leagueQid and tier")
            return tiers, labels, problems
        for row in reader:
            line = reader.line_num
            key = (row.get("leagueQid") or "").strip()
            raw = (row.get("tier") or "").strip().lower()
            if not key:
                continue
            if not re.match(r"^Q\d+$", key):
                problems.append(f"{TIER_FILE} line {line}: {key!r} is not a Q-id")
                continue
            labels[key] = {"label": (row.get("label") or "").strip(),
                           "country": (row.get("country") or "").strip()}
            if raw == "skip":
                tiers[key] = "skip"
            elif raw.isdigit():
                tiers[key] = int(raw)
            else:
                problems.append(
                    f"{TIER_FILE} line {line}: tier {raw!r} must be a whole number or 'skip'")
    return tiers, labels, problems


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



# ------------------------------------------------------ manual overrides

def _s(v):
    return (v or "").strip()


def load_manual():
    """
    data/clubs-manual.csv -- hand-written corrections and additions.

    A row with a clubQid overrides that club: only the cells you fill in
    are changed, blanks leave the fetched value alone. A row without one
    adds a club Wikidata does not have, or has wrong beyond repair.

    The word "skip" in the tier column removes that club from the output
    entirely, which is how a duplicate Wikidata item is dropped. It needs
    a clubQid, because there has to be something there to remove, and it
    ignores every other cell on the row.

    Hand-written data always wins. That is the point of the file.
    """
    rows, problems = [], []
    if not os.path.exists(MANUAL_FILE):
        return rows, problems

    with open(MANUAL_FILE, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            problems.append(f"{MANUAL_FILE} is empty - it needs a header row")
            return rows, problems
        headers = [_s(h) for h in reader.fieldnames]
        for need in MANUAL_REQUIRED:
            if need not in headers:
                problems.append(f"{MANUAL_FILE} line 1: missing required column {need!r}")
                return rows, problems
        for h in headers:
            if h and h not in MANUAL_REQUIRED + MANUAL_OPTIONAL:
                problems.append(f"{MANUAL_FILE} line 1: column {h!r} not recognised, ignored")

        for raw in reader:
            line = reader.line_num
            row = {_s(k): _s(v) for k, v in raw.items() if k is not None}
            if not any(row.values()):
                continue
            if not row.get("name"):
                problems.append(f"{MANUAL_FILE} line {line}: name is required")
                continue

            qid_val = row.get("clubQid", "")
            if qid_val and not re.match(r"^Q\d+$", qid_val):
                problems.append(f"{MANUAL_FILE} line {line}: clubQid {qid_val!r} is not a Q-id")
                continue

            tier_raw = row.get("tier", "")
            if tier_raw.lower() == "skip":
                if not qid_val:
                    problems.append(
                        f"{MANUAL_FILE} line {line}: tier 'skip' removes a club that is "
                        f"already there, so it needs a clubQid - row ignored")
                    continue
                ignored = [f for f in ("venue", "capacity", "lat", "lon", "ticketUrl")
                           if row.get(f)]
                if ignored:
                    problems.append(
                        f"{MANUAL_FILE} line {line}: tier is 'skip', so "
                        + ", ".join(ignored) + " on this row are ignored")
                row["tier"] = "skip"
            elif tier_raw and not tier_raw.isdigit():
                problems.append(
                    f"{MANUAL_FILE} line {line}: tier {tier_raw!r} must be a whole number "
                    f"or 'skip'")
                row["tier"] = ""

            if row.get("capacity") and not row["capacity"].isdigit():
                problems.append(
                    f"{MANUAL_FILE} line {line}: capacity {row['capacity']!r} is not a whole number")
                row["capacity"] = ""
            for coord in ("lat", "lon"):
                if row.get(coord):
                    try:
                        float(row[coord])
                    except ValueError:
                        problems.append(
                            f"{MANUAL_FILE} line {line}: {coord} {row[coord]!r} is not a number")
                        row[coord] = ""

            row["_line"] = line
            rows.append(row)
    return rows, problems


def apply_manual(clubs, manual_rows, country_code):
    """Returns (applied_notes, problems). Mutates clubs in place."""
    notes, problems = [], []
    by_name = {}
    for club in clubs.values():
        if club.get("name"):
            by_name.setdefault(club["name"].lower(), []).append(club)

    for row in manual_rows:
        if row.get("country") and row["country"] != country_code:
            continue

        target = None
        if row.get("clubQid"):
            target = clubs.get(row["clubQid"])
            if target is None:
                problems.append(
                    f"{MANUAL_FILE} line {row['_line']}: {row['clubQid']} is not in this "
                    f"country's fetched clubs - check the Q-id, or leave it blank to add "
                    f"the club instead")
                continue

        # "skip" in the tier column drops the club altogether. Everything
        # else on the row is ignored, so this is handled before any of the
        # cell-by-cell overriding below.
        if row.get("tier") == "skip":
            gone = clubs.pop(row["clubQid"])
            label = gone.get("name") or gone["id"]
            for same in by_name.get((gone.get("name") or "").lower(), []):
                if same is gone:
                    by_name[gone["name"].lower()].remove(same)
                    break
            notes.append(f"removed {label} ({gone['id']}) - tier says skip")
            continue

        if target is None:
            # New club. Needs enough to put a pin on a map.
            missing = [f for f in ("tier", "lat", "lon") if not row.get(f)]
            if missing:
                problems.append(
                    f"{MANUAL_FILE} line {row['_line']}: adding {row['name']!r} needs "
                    + ", ".join(missing))
                continue
            clash = by_name.get(row["name"].lower())
            if clash:
                problems.append(
                    f"{MANUAL_FILE} line {row['_line']}: {row['name']!r} already exists as "
                    f"{clash[0]['id']} - put that Q-id in clubQid to correct it instead of "
                    f"adding a second copy")
                continue
            new_id = "MANUAL-" + re.sub(r"[^a-z0-9]+", "-", row["name"].lower()).strip("-")
            target = {"id": new_id, "name": row["name"], "leagues": [], "tier": None,
                      "venue": None, "capacity": None, "lat": None, "lon": None,
                      "city": None}
            clubs[new_id] = target
            notes.append(f"added {row['name']}")
        else:
            changed = [f for f in ("name", "tier", "venue", "capacity", "lat", "lon")
                       if row.get(f)]
            notes.append(f"corrected {target.get('name') or target['id']}"
                         + (f" ({', '.join(changed)})" if changed else " (no change)"))

        if row.get("name"):     target["name"] = row["name"]
        if row.get("tier"):     target["tier"] = int(row["tier"])
        if row.get("venue"):    target["venue"] = row["venue"]
        if row.get("capacity"): target["capacity"] = int(row["capacity"])
        if row.get("lat"):      target["lat"] = round(float(row["lat"]), 6)
        if row.get("lon"):      target["lon"] = round(float(row["lon"]), 6)
        if row.get("ticketUrl"): target["ticketUrl"] = row["ticketUrl"]
        if row.get("source"):   target["source"] = row["source"]
        if row.get("note"):     target["note"] = row["note"]
        target["manual"] = True

    return notes, problems


# ------------------------------------------------------------------ main

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tiers, labels, tier_problems = load_tiers()
    manual_rows, manual_problems = load_manual()

    all_leagues, index, failures, report = {}, {}, [], []

    for position, (code, country_qid, name) in enumerate(COUNTRIES):
        if position:
            time.sleep(REQUEST_GAP_SECONDS)
        lang = {"DE": "de", "RO": "ro"}.get(code, "en")
        print(f"  {code}  {name}")

        # 1. discovery - which leagues exist, for the seed file
        disc, error = sparql_with_retry(DISCOVERY_QUERY % {"country": country_qid, "lang": lang})
        if error:
            failures.append(f"{code} ({name}) league discovery: {error}")
        else:
            for row in disc.get("results", {}).get("bindings", []):
                lid = qid(cell(row, "league"))
                if not lid:
                    continue
                entry = all_leagues.setdefault(
                    lid, {"id": lid, "label": None, "clubs": 0, "country": code})
                entry["clubs"] += 1
                llabel = cell(row, "leagueLabel")
                if llabel and not llabel.startswith("Q"):
                    entry["label"] = llabel

        # 2. clubs - only the leagues mapped for this country
        wanted = [lid for lid, t in tiers.items()
                  if t != "skip" and labels.get(lid, {}).get("country", code) == code]
        clubs = {}
        if wanted:
            time.sleep(REQUEST_GAP_SECONDS)
            values = " ".join("wd:" + lid for lid in wanted)
            data, error = sparql_with_retry(
                CLUB_QUERY % {"leagues": values, "lang": lang})
            if error:
                failures.append(f"{code} ({name}) clubs: {error} - file left untouched")
                continue
            clubs, _leagues, ambiguous = build_clubs(
                data.get("results", {}).get("bindings", []), tiers)
        else:
            ambiguous = []
            failures.append(f"{code} ({name}): no leagues mapped for this country yet")

        applied, applied_problems = apply_manual(clubs, manual_rows, code)
        manual_problems.extend(applied_problems)

        keep = {cid: c for cid, c in clubs.items()
                if c["tier"] is not None and c["lat"] is not None}
        for club in keep.values():
            lid = next((l for l in club["leagues"] if tiers.get(l) == club["tier"]), None)
            meta = labels.get(lid or "", {})
            label = meta.get("label")
            if not label:
                # Hand-added or hand-retiered clubs carry no league tag,
                # so fall back to the league mapped at that tier here.
                for other, t in tiers.items():
                    info = labels.get(other, {})
                    if t == club["tier"] and info.get("country") == code:
                        label = info.get("label")
                        break
            club["competition"] = label or None
        no_coord = sum(1 for c in clubs.values()
                       if c["tier"] is not None and c["lat"] is None)
        with_cap = sum(1 for c in keep.values() if c["capacity"])
        with_venue = sum(1 for c in keep.values() if c["venue"])
        manual_count = sum(1 for c in keep.values() if c.get("manual"))

        with open(os.path.join(OUT_DIR, f"{code}.json"), "w", encoding="utf-8") as fh:
            json.dump({
                "source": "Wikidata, corrected by data/clubs-manual.csv",
                "note": "Tier comes from data/league-tiers.csv, never from a league name.",
                "country": code, "countryName": name,
                "clubs": [keep[k] for k in sorted(keep)],
            }, fh, indent=1, ensure_ascii=False)
            fh.write("\n")

        by_tier = {}
        for club in keep.values():
            by_tier[club["tier"]] = by_tier.get(club["tier"], 0) + 1
        index[code] = {"name": name, "onMap": len(keep),
                       "byTier": dict(sorted(by_tier.items())),
                       "withVenueName": with_venue, "withCapacity": with_cap,
                       "handCorrected": manual_count}

        report.append(f"{code}  {len(keep):4d} on the map  |  {with_venue} grounds, "
                      f"{with_cap} capacities, {manual_count} hand-corrected  |  "
                      f"{no_coord} dropped for no coordinates")
        for note in applied:
            report.append(f"    {note}")
        if ambiguous:
            report.append(f"    {len(ambiguous)} club(s) in more than one mapped tier; "
                          f"took the highest. First: {ambiguous[0]}")

    with open(os.path.join(OUT_DIR, "index.json"), "w", encoding="utf-8") as fh:
        json.dump({"source": "Wikidata", "countries": index}, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

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
    for problem in tier_problems + manual_problems:
        print("  ! " + problem)
    print()
    print(f"  {len(all_leagues)} leagues seen, {len(all_leagues) - len(unmapped)} mapped, "
          f"{len(unmapped)} unmapped (see {SEED_FILE})")
    for league in unmapped[:10]:
        print(f"    {league['id']:11s} {league['clubs']:4d} clubs  {league['country']}  "
              f"{league['label'] or '(no label)'}")
    if failures:
        print()
        for f in failures:
            print("  ! " + f)
    print("=" * 70)


if __name__ == "__main__":
    main()
