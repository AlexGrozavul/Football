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

# Discovery: which leagues does Wikidata place in this country, and how
# many clubs does each of them have.
#
# This is the question turned round. Asking it the old way - every club
# in the country, collect the leagues they carry - died at the query
# service's 60-second ceiling for Germany every single time, so Germany
# never reached the seed list at all. Measured on 2026-09-16, this shape
# answers in 6.9 seconds with 118 German leagues, labels included, and
# returns the same 56 Romanian leagues the old one did.
#
# THE TRADE-OFF, which the run summary also prints: this finds leagues
# LOCATED IN the country, not leagues this country's clubs PLAY IN. A
# German club playing in a league Wikidata places abroad no longer puts
# that league into Germany's seed list. Nothing has been seen to fall
# through that gap, but nothing rules it out either - and a seed list
# that arrives beats one that times out.
#
# The counting happens in the subquery and the labels are added outside
# it. The label service cannot run inside an aggregate, and it was the
# label service, not the join, that made the old query too slow.
#
# Still no "is a football club" filter, so nothing is missed - the cost
# is that other sports show up in the seed list, which you mark "skip".
# People are excluded: Wikidata puts P118 on managers and players as
# well as clubs.
DISCOVERY_QUERY = """
SELECT ?league ?leagueLabel ?clubs WHERE {
  {
    SELECT ?league (COUNT(DISTINCT ?club) AS ?clubs) WHERE {
      ?league wdt:P17 wd:%(country)s .
      ?club wdt:P118 ?league .
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
      FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
    }
    GROUP BY ?league
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "%(lang)s,en" }
}
"""

# Printed in the run summary next to the seed list, because the seed
# list is what the trade-off changes and a comment in the code is no use
# to anyone reading the summary.
DISCOVERY_TRADE_OFF = (
    "Leagues are found by asking which leagues Wikidata places IN the "
    "country and counting the clubs in each. That is not the same "
    "question as which leagues this country's clubs PLAY IN: a German "
    "club playing in a league Wikidata places abroad will not put that "
    "league in this list. The old question timed out for Germany every "
    "time and produced no German leagues at all, so this is the trade "
    "being made. clubsSeen therefore counts every club carrying that "
    "league tag, not only the clubs of this country.")

# Clubs: restricted to the leagues you mapped, so no "is a football
# club" filter is needed and reserve teams are no longer excluded by
# accident. People are excluded here too - a manager carries the league
# he manages in, so without this line he arrives as a club with no
# ground and no coordinates.
#
# P31 is asked for as well, not to filter by type - that decision stands
# - but so that the handful of items which are plainly not clubs at all
# can be named and left out. This query is bounded by the leagues you
# mapped, a few hundred items, so it is nothing like the country-wide
# discovery query and one more optional property costs nothing
# measurable.
#
# P17 is asked for on the same terms and for the same reason: to REPORT,
# never to filter. See the country sanity check below. Filtering on P17
# was considered and rejected because the clubs that are missing are
# exactly the ones whose fields are not filled in; reporting on it
# cannot drop anybody.
CLUB_QUERY = """
SELECT ?club ?clubLabel ?league ?venue ?venueLabel ?capacity ?coord ?cityLabel ?typeLabel ?country
WHERE {
  VALUES ?league { %(leagues)s }
  ?club wdt:P118 ?league .
  FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
  FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
  OPTIONAL { ?club wdt:P31 ?type }
  OPTIONAL { ?club wdt:P17 ?country }
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

# Printed in the run summary every time the country check runs, because
# what this check CANNOT see matters as much as what it flags.
COUNTRY_CHECK_NOTE = (
    "The country check reports and never removes. It uses two signals: a "
    "rectangle round the country, and Wikidata's own P17 on the club. "
    "Neither is enough alone. The rectangle cannot tell a German club "
    "from a Swiss or Austrian one near the border, because a rectangle "
    "big enough for Germany also covers northern Switzerland, western "
    "Austria and all of Liechtenstein - it caught FC Triesenberg only "
    "because Liechtenstein is south of Germany's southernmost point. P17 "
    "covers that gap but is blank on many clubs, and a club with no P17 "
    "inside the rectangle is never mentioned. So nothing flagged here "
    "does not mean nothing is wrong.")




# ------------------------------------------------------------- csv safety

# csv.DictReader hands back any value past the last column under a single
# "rest" key. Left at its default that key is None, and a dictionary
# comprehension that skips None throws the values away without a word -
# which is what quietly cut two notes in half the first time a comma was
# typed inside one. An object() is used rather than a string so that no
# column name, present or future, can collide with it.
OVERFLOW = object()


def _s(v):
    return (v or "").strip()


def _wrap(text, width=66):
    """Line-wrapping for the summary, so a long explanation stays readable."""
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return lines


def overflow_problem(path, line, columns, extra):
    """
    The complaint for a row carrying more values than the header has
    columns. Says what would have been lost and how to keep it, because
    the fix is in the file, not in the code.
    """
    lost = ", ".join(repr(_s(v)) for v in extra)
    return (f"{path} line {line}: this row has {columns + len(extra)} values but "
            f"the header has {columns} columns, so {lost} would be thrown away. "
            f"A comma inside a cell splits that cell in two - put double quotes "
            f'round the whole cell ("like, this") to keep the comma. Row ignored.')


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
        except ValueError:
            # The query service answers 200 with a half-written body when
            # a query runs past its own 60-second limit, so a broken JSON
            # answer means "too slow", not "wrong query". Without this the
            # whole script dies on one slow query and no country is
            # written at all.
            if attempt < MAX_RETRIES:
                print("    answer was cut off mid-JSON, retrying")
                time.sleep(15)
                continue
            return None, ("answer cut off mid-JSON - the query service gave up "
                          "on this query (its limit is 60s)")
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
        reader = csv.DictReader(fh, restkey=OVERFLOW)
        if not reader.fieldnames or "leagueQid" not in reader.fieldnames:
            problems.append(f"{TIER_FILE} line 1: header must contain leagueQid and tier")
            return tiers, labels, problems
        for row in reader:
            line = reader.line_num
            extra = row.pop(OVERFLOW, None)
            if extra:
                problems.append(overflow_problem(
                    TIER_FILE, line, len(reader.fieldnames), extra))
                continue
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


# --------------------------------------------------------- not a club

# Some Wikidata items carry a league tag exactly as a club does and are
# not clubs. Five German ones are squad lists - "Kader der 2.
# Fussball-Bundesliga 2019/20", "Mannschaftskader der deutschen
# Fussball-Bundesliga 2013/14" and so on. They are not people, so the
# wd:Q5 filter never touched them, and they stayed off the map only
# because they happen to have no coordinates. That is luck, not a rule:
# one of them gaining a P625 would put a squad list on the map as a pin.
#
# Two nets, and the run summary says which one caught what, by name:
#
#   1. What Wikidata says the item IS. The club query now asks for P31,
#      which costs nothing there because that query is bounded by the
#      leagues you mapped. This is the net that should do the work.
#   2. The item's NAME, for anything whose type is missing or says
#      nothing useful. A backstop only - a name is weaker evidence than
#      a type, so it is anchored at the start of the name and kept to
#      the shapes a list article has and a club never does.
#
# This is not the "is a football club" filter that was deliberately not
# added. That one would have said which items to KEEP, by type, and
# dropped 44 leagues' worth of clubs whose type is simply not filled in.
# This one says which items to THROW OUT, and an item with no type at
# all passes it untouched.
NOT_A_CLUB_TYPES = ("kader", "list of ", "liste", "listă", "lista ")

NOT_A_CLUB_NAME = re.compile(
    r"^\s*(mannschaftskader|kader|liste\b|listă|lista|list of)\b", re.IGNORECASE)


def not_a_club(name, kinds):
    """
    Returns the reason this item is not a club, or None if it is one.
    The reason is written for the run summary, so it says what was seen.
    """
    for kind in kinds:
        low = kind.lower()
        for word in NOT_A_CLUB_TYPES:
            if word in low:
                return f"Wikidata says it is a {kind!r}, which is a list, not a club"
    if name and NOT_A_CLUB_NAME.match(name):
        return ("its name is the title of a squad list, not the name of a club "
                "(Wikidata gives it no type that says so)")
    return None


# --------------------------------------------------------------- shaping

def cell(row, name):
    item = row.get(name)
    return item.get("value") if item else None


def build_clubs(rows, tiers):
    """
    Fold the flat SPARQL rows into one record per club.

    Returns (clubs, leagues, ambiguous, dropped, countries). "dropped" is
    the items that carried a league tag but are not clubs - see
    not_a_club above; they are named in the run summary rather than
    removed quietly. "countries" is Wikidata's own P17 per club, as
    Q-ids, and is used only by the country sanity check.
    """
    clubs = {}
    leagues = {}
    kinds = {}
    # Wikidata's own P17 per club, kept BESIDE the club and not on it:
    # the club dictionary is written to the country file as it stands,
    # and this is evidence for a report, not data for the map.
    countries = {}

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

        kind = cell(row, "typeLabel")
        if kind and not kind.startswith("Q"):
            seen = kinds.setdefault(cid, [])
            if kind not in seen:
                seen.append(kind)

        home = qid(cell(row, "country"))
        if home:
            seen = countries.setdefault(cid, [])
            if home not in seen:
                seen.append(home)

    # The items that are not clubs at all, thrown out before anything
    # else looks at them.
    dropped = []
    for cid in sorted(clubs):
        reason = not_a_club(clubs[cid].get("name"), kinds.get(cid, []))
        if not reason:
            continue
        gone = clubs.pop(cid)
        for entry in leagues.values():
            entry["clubs"].discard(cid)
        dropped.append(f"{gone.get('name') or cid} ({cid}) - {reason}")

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

    return clubs, leagues, ambiguous, dropped, countries


# ------------------------------------------------- country sanity check

# A rectangle round each country, with a small margin on every side.
# Hand-written from the country's own extreme points, and deliberately
# no tighter than that: this is a net for a club that is plainly
# somewhere else, not a border survey.
#
#   DE  south 47.2701 (Haldenwanger Eck), north 55.0583 (Ellenbogen,
#       Sylt), west 5.8663 (Selfkant), east 15.0419 (Neissaue)
#   RO  south 43.6187 (Zimnicea), north 48.2673 (Horodistea),
#       west 20.2619 (Beba Veche), east 29.6912 (Sulina)
COUNTRY_BOX = {
    "DE": {"lat": (47.15, 55.15), "lon": (5.75, 15.15)},
    "RO": {"lat": (43.50, 48.35), "lon": (20.15, 29.80)},
}

COUNTRY_REVIEW = os.path.join(OUT_DIR, "country-review.csv")

# So a Q-id in the report is readable without looking it up. A country
# that is not in here is printed as its Q-id and nothing is invented.
COUNTRY_NAMES = {
    "Q183": "Germany", "Q218": "Romania", "Q39": "Switzerland",
    "Q347": "Liechtenstein", "Q40": "Austria", "Q142": "France",
    "Q31": "Belgium", "Q55": "Netherlands", "Q36": "Poland",
    "Q213": "Czechia", "Q28": "Hungary", "Q403": "Serbia",
    "Q219": "Bulgaria", "Q212": "Ukraine", "Q217": "Moldova",
    "Q38": "Italy", "Q29": "Spain", "Q145": "United Kingdom",
    "Q41": "Greece", "Q43": "Turkey", "Q184": "Belarus",
    "Q32": "Luxembourg", "Q33": "Finland", "Q34": "Sweden",
    "Q20": "Norway", "Q35": "Denmark",
}


def country_review(keep, club_countries, code, country_qid):
    """
    Which clubs in this country's file do not look like they belong in it.

    REPORTS, never drops - the same shape as capacity-review.csv. The
    club query is bounded by LEAGUE and never by country, so any foreign
    club whose Wikidata item carries a mapped league's Q-id arrives as a
    club of that country. It has happened twice: SC Veltheim, which is
    Swiss, and FC Triesenberg, which is in Liechtenstein, both carrying
    Q154069, the German 3. Liga. Both were found by eye, months apart.

    Adding a country FILTER to the query was considered and rejected in
    CLAUDE.md for a good reason: P17 is exactly the field the missing
    clubs already lack, so a filter on it would quietly drop real ones.
    Reporting on it drops nobody. A club with no P17 whose coordinates
    are inside the box is never mentioned at all.

    Two independent signals, because ONE OF THEM IS NOT ENOUGH:

      1. The box. Catches a club that is plainly somewhere else.
      2. Wikidata's own P17. Catches a club sitting inside the box but
         belonging to another country.

    CLAUDE.md used to say a bounding box alone would have caught both
    Veltheim and Triesenberg. It would not have. Veltheim is in
    Winterthur, near 47.51N 8.72E, and any rectangle wide enough to hold
    Germany also holds northern Switzerland, western Austria and the
    whole of Liechtenstein; tightening it enough to exclude Winterthur
    would cut off real German clubs in the far south. Signal 1 catches
    Triesenberg, at 47.11N, which is south of Germany's southernmost
    point. Signal 2 is the one that would have caught Veltheim.

    A hand-corrected club is checked like any other and the row says so.
    Hand-written data wins on the map, as it always does - but a report
    is not an override, and a mistyped coordinate in clubs-manual.csv is
    exactly the kind of thing worth seeing.
    """
    box = COUNTRY_BOX.get(code)
    rows = []
    for cid in sorted(keep):
        club = keep[cid]
        lat, lon = club.get("lat"), club.get("lon")
        if lat is None or lon is None:
            continue                      # never reaches the map anyway

        signals, details = [], []

        if box and not (box["lat"][0] <= lat <= box["lat"][1]
                        and box["lon"][0] <= lon <= box["lon"][1]):
            signals.append("outside the box")
            details.append(
                f"{lat}/{lon} is outside the {code} box "
                f"(lat {box['lat'][0]}..{box['lat'][1]}, "
                f"lon {box['lon'][0]}..{box['lon'][1]})")

        tagged = club_countries.get(cid, [])
        if tagged and country_qid not in tagged:
            named = ", ".join(f"{COUNTRY_NAMES.get(q, 'country ' + q)} ({q})"
                              for q in tagged)
            signals.append("Wikidata says another country")
            details.append(
                f"P17 on the item says {named}, not "
                f"{COUNTRY_NAMES.get(country_qid, country_qid)}")

        if not signals:
            continue

        rows.append({
            "clubQid": cid,
            "name": club.get("name") or cid,
            "inFile": code,
            "tier": club.get("tier"),
            "venue": club.get("venue") or "",
            "lat": lat,
            "lon": lon,
            "handCorrected": "yes" if club.get("manual") else "no",
            "signal": " + ".join(signals),
            "detail": "; ".join(details),
        })
    return rows


# ------------------------------------------------------ manual overrides

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
        reader = csv.DictReader(fh, restkey=OVERFLOW)
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
            extra = raw.pop(OVERFLOW, None)
            if extra:
                problems.append(overflow_problem(
                    MANUAL_FILE, line, len(reader.fieldnames), extra))
                continue
            row = {_s(k): _s(v) for k, v in raw.items()}
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

    # Which countries' league discovery came back. A country that did not
    # answer means the seed list is only part of the picture, and a part
    # of the picture must not overwrite a whole one.
    discovery_missing = []

    # Same rule again for the country sanity check. Its review file lists
    # every country at once, so a run that lost one country knows only
    # part of the answer - writing that part would delete the rest with a
    # green tick, which is the exact failure the review files already
    # guard against.
    clubs_missing = []
    country_rows = []

    for position, (code, country_qid, name) in enumerate(COUNTRIES):
        if position:
            time.sleep(REQUEST_GAP_SECONDS)
        lang = {"DE": "de", "RO": "ro"}.get(code, "en")
        print(f"  {code}  {name}")

        # 1. discovery - which leagues Wikidata places in this country,
        #    and how many clubs each has, for the seed file
        started = time.monotonic()
        disc, error = sparql_with_retry(DISCOVERY_QUERY % {"country": country_qid, "lang": lang})
        took = time.monotonic() - started
        # How long the discovery query took, every run. The whole reason
        # this query was rewritten is that the old one was too slow to
        # answer at all, so how close the new one runs to the query
        # service's 60-second ceiling is worth knowing before it starts
        # failing rather than after.
        if error:
            failures.append(f"{code} ({name}) league discovery: {error} "
                            f"(gave up after {took:.1f}s including retries)")
            discovery_missing.append(f"{code} ({name}): {error}")
        else:
            seen_here = 0
            for row in disc.get("results", {}).get("bindings", []):
                lid = qid(cell(row, "league"))
                if not lid:
                    continue
                seen_here += 1
                try:
                    count = int(cell(row, "clubs") or 0)
                except ValueError:
                    count = 0
                entry = all_leagues.setdefault(
                    lid, {"id": lid, "label": None, "clubs": 0, "country": code})
                # A league placed in two countries is possible and would
                # otherwise silently look like one country's.
                if code not in entry["country"].split(";"):
                    entry["country"] = ";".join(sorted(
                        set(entry["country"].split(";")) | {code}))
                entry["clubs"] += count
                llabel = cell(row, "leagueLabel")
                if llabel and not llabel.startswith("Q"):
                    entry["label"] = llabel
            report.append(f"{code}  {seen_here} leagues placed in this country by Wikidata, "
                          f"answered in {took:.1f}s")

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
                clubs_missing.append(f"{code} ({name}): {error}")
                continue
            clubs, _leagues, ambiguous, dropped, club_countries = build_clubs(
                data.get("results", {}).get("bindings", []), tiers)
        else:
            ambiguous, dropped, club_countries = [], [], {}
            failures.append(f"{code} ({name}): no leagues mapped for this country yet")
            clubs_missing.append(f"{code} ({name}): no leagues mapped yet")

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

        flagged = country_review(keep, club_countries, code, country_qid)
        country_rows.extend(flagged)

        report.append(f"{code}  {len(keep):4d} on the map  |  {with_venue} grounds, "
                      f"{with_cap} capacities, {manual_count} hand-corrected  |  "
                      f"{no_coord} dropped for no coordinates")
        if flagged:
            report.append(f"    {len(flagged)} club(s) do not look like they belong in "
                          f"this country's file - NOT removed, see {COUNTRY_REVIEW}:")
            for row in flagged:
                report.append(f"      {row['name']} ({row['clubQid']}) - {row['detail']}")
        else:
            report.append("    country check: every club on this map is where "
                          "this file says it should be")
        for note in dropped:
            report.append(f"    left out, not a club: {note}")
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

    # The seed list is a file you read and paste from, so it is treated
    # like the review files: a run that lost a country knows only part
    # of the answer, and writing that part would delete the rest with a
    # green tick. The first run is the exception - there is nothing
    # there to protect, so a partial list is written and said to be one.
    seed_note = ""
    if discovery_missing and os.path.exists(SEED_FILE):
        seed_note = ("league discovery failed for " +
                     ", ".join(discovery_missing) +
                     f" - {SEED_FILE} left exactly as the last good run left it")
    else:
        with open(SEED_FILE, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["leagueQid", "tier", "label", "country", "clubsSeen"])
            for league in unmapped:
                writer.writerow([league["id"], "", league["label"] or "",
                                 league["country"], league["clubs"]])
        if discovery_missing:
            seed_note = (f"{SEED_FILE} did not exist, so it was written from a "
                         "run that is missing " + ", ".join(discovery_missing) +
                         " - it is a partial list")

    # The country review file, under the same rule as the seed list and
    # the two other review files: a run that lost a country holds only
    # part of the answer, and writing that part would delete the rest.
    # The first run is the exception - with no file there is nothing to
    # protect, so a partial list is written and labelled as partial.
    country_note = ""
    if clubs_missing and os.path.exists(COUNTRY_REVIEW):
        country_note = ("clubs could not be fetched for " +
                        ", ".join(clubs_missing) +
                        f" - {COUNTRY_REVIEW} left exactly as the last good "
                        f"run left it")
    else:
        with open(COUNTRY_REVIEW, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["clubQid", "name", "inFile", "tier", "venue",
                             "lat", "lon", "handCorrected", "signal", "detail"])
            for row in country_rows:
                writer.writerow([row["clubQid"], row["name"], row["inFile"],
                                 row["tier"], row["venue"], row["lat"],
                                 row["lon"], row["handCorrected"],
                                 row["signal"], row["detail"]])
        if clubs_missing:
            country_note = (f"{COUNTRY_REVIEW} did not exist, so it was written "
                            "from a run that is missing " +
                            ", ".join(clubs_missing) + " - it is a partial list")

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
    by_country = {}
    for league in unmapped:
        by_country[league["country"]] = by_country.get(league["country"], 0) + 1
    for country in sorted(by_country):
        print(f"    {country}: {by_country[country]} unmapped")
    for league in unmapped[:10]:
        print(f"    {league['id']:11s} {league['clubs']:4d} clubs  {league['country']}  "
              f"{league['label'] or '(no label)'}")
    if seed_note:
        print("  ! " + seed_note)
    print()
    if country_rows:
        print(f"  {len(country_rows)} club(s) flagged by the country check - "
              f"listed, NOT removed (see {COUNTRY_REVIEW})")
    else:
        print("  country check: nothing flagged in any country")
    for line in _wrap(COUNTRY_CHECK_NOTE):
        print("  " + line)
    if country_note:
        print("  ! " + country_note)
    print()
    for line in _wrap(DISCOVERY_TRADE_OFF):
        print("  " + line)
    if failures:
        print()
        for f in failures:
            print("  ! " + f)
    print("=" * 70)


if __name__ == "__main__":
    main()
