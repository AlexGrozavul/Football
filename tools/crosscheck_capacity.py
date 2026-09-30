#!/usr/bin/env python3
"""
crosscheck_capacity.py -- accuracy pass for the club layer.

Reads data/clubs/*.json and asks OpenStreetMap for every stadium in the
same country. Matches a club to a stadium by position, not by name, and
compares the two capacity figures.

It NEVER changes a club file. It writes data/clubs/capacity-review.csv,
a list of disagreements for you to judge. Where two independent sources
agree, the number is almost certainly right and the row is left out.
Where they disagree, or only one has a figure, you decide - and the row
is written in the column order of data/clubs-manual.csv so the ones you
accept can be pasted straight across.

Free, no key. Overpass is a shared volunteer service, so this asks for
one country at a time and waits between requests.

The review file is decided COUNTRY BY COUNTRY, since 2026-09-30, the way
propose_coordinates.py has decided coordinate-review.csv since
2026-09-26: a country whose answer came back replaces its own rows, a
country Overpass did not answer for keeps its rows exactly as its last
good run left them, and the summary says WRITTEN or UNCHANGED against
every country. Until then one country's timeout threw away every other
country's answer - six runs in a row on 2026-09-29 and 2026-09-30, each
losing a different country.

Usage:  python3 tools/crosscheck_capacity.py
"""

import csv
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------- config

CLUB_DIR = "data/clubs"
REVIEW_FILE = os.path.join(CLUB_DIR, "capacity-review.csv")

OVERPASS = "https://overpass-api.de/api/interpreter"
USER_AGENT = ("football-fixture-planner/1.0 (personal project; "
              "https://github.com/AlexGrozavul/Football)")

# How close a stadium has to be to count as the club's ground.
MATCH_RADIUS_M = 500

# Below this the two sources are treated as agreeing. Capacities shift by
# a few seats constantly; only real disagreements are worth your time.
AGREE_WITHIN = 0.05

REQUEST_GAP_SECONDS = 20
TIMEOUT_SECONDS = 240
MAX_RETRIES = 3

OVERPASS_QUERY = """
[out:json][timeout:180];
area["ISO3166-1"="%(iso)s"][admin_level=2]->.a;
(
  nwr["leisure"="stadium"](area.a);
  nwr["building"="stadium"](area.a);
);
out tags center;
"""

CAPACITY_TAGS = ("capacity", "seats", "capacity:persons", "capacity:seats")

HEADER = ["clubQid", "name", "country", "tier", "venue", "capacity",
          "lat", "lon", "ticketUrl", "source", "note",
          "_wikidata", "_osm", "_osmName", "_osmTag", "_metres", "_verdict"]


# ------------------------------------------------------------------ http

def overpass(iso):
    body = urllib.parse.urlencode({"data": OVERPASS_QUERY % {"iso": iso}}).encode("utf-8")
    req = urllib.request.Request(
        OVERPASS, data=body,
        headers={"User-Agent": USER_AGENT,
                 "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def overpass_with_retry(iso):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return overpass(iso), None
        except urllib.error.HTTPError as exc:
            # 429 and 504 are Overpass saying it is busy, not that the
            # query is wrong. Waiting is the documented remedy.
            if exc.code in (429, 502, 503, 504) and attempt < MAX_RETRIES:
                print(f"    Overpass busy ({exc.code}), waiting 60s")
                time.sleep(60)
                continue
            return None, f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < MAX_RETRIES:
                print(f"    network problem, retrying: {exc}")
                time.sleep(30)
                continue
            return None, f"network error: {exc}"
    return None, "exhausted retries"


# --------------------------------------------------------------- helpers

def metres(lat1, lon1, lat2, lon2):
    R = 6371000.0
    r = math.pi / 180
    dLat = (lat2 - lat1) * r
    dLon = (lon2 - lon1) * r
    a = (math.sin(dLat / 2) ** 2 +
         math.cos(lat1 * r) * math.cos(lat2 * r) * math.sin(dLon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def parse_capacity(tags):
    """
    OSM capacity tags are free text. '25,667' and '25667' are the same
    number; 'unknown' and '~30000' are not usable figures.
    """
    for key in CAPACITY_TAGS:
        raw = tags.get(key)
        if not raw:
            continue
        cleaned = raw.replace(",", "").replace(".", "").strip()
        if re.fullmatch(r"\d+", cleaned):
            value = int(cleaned)
            if 100 <= value <= 200000:
                return value, key
    return None, None


def stadium_points(payload):
    """Flatten the Overpass answer into (lat, lon, name, capacity, tag)."""
    out = []
    for el in payload.get("elements", []):
        tags = el.get("tags") or {}
        lat = el.get("lat") if el.get("lat") is not None else (el.get("center") or {}).get("lat")
        lon = el.get("lon") if el.get("lon") is not None else (el.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        cap, key = parse_capacity(tags)
        out.append({
            "lat": lat, "lon": lon,
            "name": tags.get("name") or tags.get("official_name"),
            "capacity": cap, "tag": key,
        })
    return out


def nearest(club, stadiums):
    best, best_d = None, None
    for s in stadiums:
        d = metres(club["lat"], club["lon"], s["lat"], s["lon"])
        if best_d is None or d < best_d:
            best, best_d = s, d
    if best is not None and best_d <= MATCH_RADIUS_M:
        return best, round(best_d)
    return None, (round(best_d) if best_d is not None else None)


# ------------------------------------------------------------------ main

def main():
    if not os.path.isdir(CLUB_DIR):
        sys.exit(f"{CLUB_DIR} does not exist - run the club layer first")

    # A country file is named by its two-letter code. fixture-links.json
    # lives in the same folder and is not one - reading it as a country
    # file crashed this tool on 2026-09-25.
    files = sorted(f for f in os.listdir(CLUB_DIR)
                   if re.match(r"^[A-Z]{2}\.json$", f))
    if not files:
        sys.exit(f"no country files in {CLUB_DIR}")

    # One entry per country this run looked at: its rows and whatever did
    # not come back. A country with anything in "incomplete" may not
    # replace its own rows in the review file; see write_review.
    results, summary = {}, []

    for position, filename in enumerate(files):
        code = filename[:-5]
        with open(os.path.join(CLUB_DIR, filename), encoding="utf-8") as fh:
            data = json.load(fh)
        clubs = [c for c in data.get("clubs", []) if c.get("lat") is not None]
        if not clubs:
            continue

        if position:
            time.sleep(REQUEST_GAP_SECONDS)
        print(f"  {code}  asking OpenStreetMap for stadiums")
        payload, error = overpass_with_retry(code)
        if error:
            results[code] = {"rows": [], "incomplete": [f"Overpass: {error}"]}
            summary.append(f"{code}  {len(clubs)} clubs  |  not checked - Overpass: {error}")
            continue

        rows = []
        stadiums = stadium_points(payload)
        with_cap = sum(1 for s in stadiums if s["capacity"])
        print(f"      {len(stadiums)} stadiums, {with_cap} with a usable capacity")

        agree = differ = only_wd = only_osm = neither = unmatched = 0

        for club in clubs:
            match, distance = nearest(club, stadiums)
            wd = club.get("capacity")
            osm = match["capacity"] if match else None

            if match is None:
                unmatched += 1
                verdict = "no stadium in OSM within %dm" % MATCH_RADIUS_M
                if wd is None:
                    neither += 1
                else:
                    continue   # Wikidata has a figure, OSM has no ground: nothing to compare
            elif wd is not None and osm is not None:
                spread = abs(wd - osm) / max(wd, osm)
                if spread <= AGREE_WITHIN:
                    agree += 1
                    continue
                differ += 1
                verdict = f"sources differ by {round(spread * 100)}%"
            elif wd is None and osm is not None:
                only_osm += 1
                verdict = "only OpenStreetMap has a figure"
            elif wd is not None and osm is None:
                only_wd += 1
                continue       # one source, nothing to check it against
            else:
                neither += 1
                verdict = "neither source has a capacity"

            rows.append({
                "clubQid": club.get("id", ""),
                "name": club.get("name", ""),
                "country": code,
                "tier": "",
                "venue": "",
                "capacity": "",
                "lat": "", "lon": "",
                "ticketUrl": "", "source": "",
                "note": "",
                "_wikidata": wd if wd is not None else "",
                "_osm": osm if osm is not None else "",
                "_osmName": (match or {}).get("name") or "",
                "_osmTag": (match or {}).get("tag") or "",
                "_metres": distance if distance is not None else "",
                "_verdict": verdict,
            })

        results[code] = {"rows": rows, "incomplete": []}
        summary.append(
            f"{code}  {len(clubs)} clubs  |  {agree} agree  |  {differ} differ  |  "
            f"{only_osm} OSM only  |  {only_wd} Wikidata only  |  "
            f"{neither} neither  |  {unmatched} no OSM ground nearby")

    written, kept, partial, others = write_review(results)
    fresh = [row for code in written + partial for row in results[code]["rows"]]

    print()
    print("=" * 74)
    print("CAPACITY CROSS-CHECK")
    print("=" * 74)
    for line in summary:
        print("  " + line)
    print()
    # Country by country, because that is how the file is decided. A green
    # tick on this workflow says only that the tool ran; these lines say
    # which countries in the file are this run's and which are not.
    for code in results:
        count = len(results[code]["rows"])
        if code in written:
            print(f"  {code}  WRITTEN - complete answer, {count} row(s) replace "
                  f"this country's rows")
        elif code in partial:
            print(f"  {code}  WRITTEN AS PARTIAL - {REVIEW_FILE} did not exist, so "
                  f"there was nothing to protect; this country was NOT checked")
        else:
            print(f"  {code}  UNCHANGED - Overpass did not answer for this country, "
                  f"so its rows are exactly as the last successful run for {code} "
                  f"left them ({kept[code]} row(s))")
        for reason in results[code]["incomplete"]:
            print(f"        did not come back: {reason}")
    if others:
        print(f"  Rows for countries this run did not check were kept as they "
              f"were: {', '.join(others)}")
    print()
    if written or partial:
        print(f"  {len(fresh)} row(s) from this run need your eye - written to "
              f"{REVIEW_FILE}")
        print("  Columns starting with _ are evidence and are ignored by the")
        print("  club builder. Put the figure you trust in the capacity column,")
        print("  then paste the row into data/clubs-manual.csv.")
    else:
        print(f"  Overpass answered for no country. {REVIEW_FILE} was NOT")
        print("  rewritten; it is exactly as the last successful runs left it.")
    if fresh:
        ranked = [r for r in fresh if r["_wikidata"] != "" and r["_osm"] != ""]
        ranked.sort(key=lambda r: -abs(int(r["_wikidata"]) - int(r["_osm"])))
        if ranked:
            print()
            print("  Biggest disagreements:")
        for row in ranked[:12]:
            print(f"    {row['name'][:34]:34s} wikidata {row['_wikidata']:>7} "
                  f"vs osm {row['_osm']:>7}  ({row['_osmName'] or 'unnamed'})")
    print("=" * 74)


def write_review(results):
    """
    Decide, COUNTRY BY COUNTRY, whose rows this run may replace, and write
    the file. Returns (written, kept, partial, others).

    The rule is the one this file always had, applied to one country at a
    time instead of to the whole run: a country Overpass could not answer
    for contributes no rows, and writing that over its rows would delete
    evidence nobody has worked through yet - with a green tick. So a
    country whose answer did not come back keeps exactly the rows the
    last good run for it left, byte for byte, and a country whose answer
    came back replaces its own rows and nobody else's. Until 2026-09-30
    one country's timeout threw away every country's answer.

    The first run is still the one exception, and still for the whole
    file: with no file there is nothing to protect, so a partial list is
    written and the summary says so. It is NOT extended to "a country
    with no rows yet": a country that did not come back is never written
    into an existing file, even where that file has nothing for it.
    """
    existing = os.path.exists(REVIEW_FILE)
    old = {}
    if existing:
        with open(REVIEW_FILE, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                old.setdefault(row.get("country", ""), []).append(row)

    written, partial, kept = [], [], {}
    out = {}
    for code, result in results.items():
        if not result["incomplete"]:
            written.append(code)
            out[code] = sorted(result["rows"], key=lambda r: (r["_verdict"], r["name"]))
        elif not existing:
            partial.append(code)
            out[code] = result["rows"]
        else:
            kept[code] = len(old.get(code, []))
            out[code] = old.get(code, [])
    # A country in the file that this run did not look at at all - one
    # whose club file is gone or has no placed club - is not this run's
    # to delete either.
    others = sorted(c for c in old if c not in results)
    for code in others:
        out[code] = old[code]

    if not written and not partial:
        return written, kept, partial, others

    with open(REVIEW_FILE, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADER)
        writer.writeheader()
        for code in sorted(out):
            for row in out[code]:
                writer.writerow({k: row.get(k, "") for k in HEADER})
    return written, kept, partial, others


if __name__ == "__main__":
    main()
