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

    files = sorted(f for f in os.listdir(CLUB_DIR)
                   if f.endswith(".json") and f != "index.json")
    if not files:
        sys.exit(f"no country files in {CLUB_DIR}")

    rows, summary, failures = [], [], []

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
            failures.append(f"{code}: {error} - no cross-check done for this country")
            continue

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

        summary.append(
            f"{code}  {len(clubs)} clubs  |  {agree} agree  |  {differ} differ  |  "
            f"{only_osm} OSM only  |  {only_wd} Wikidata only  |  "
            f"{neither} neither  |  {unmatched} no OSM ground nearby")

    header = ["clubQid", "name", "country", "tier", "venue", "capacity",
              "lat", "lon", "ticketUrl", "source", "note",
              "_wikidata", "_osm", "_osmName", "_osmTag", "_metres", "_verdict"]

    rows.sort(key=lambda r: (r["country"], r["_verdict"], r["name"]))
    with open(REVIEW_FILE, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print()
    print("=" * 74)
    print("CAPACITY CROSS-CHECK")
    print("=" * 74)
    for line in summary:
        print("  " + line)
    print()
    print(f"  {len(rows)} club(s) need your eye - written to {REVIEW_FILE}")
    print("  Columns starting with _ are evidence and are ignored by the")
    print("  club builder. Put the figure you trust in the capacity column,")
    print("  then paste the row into data/clubs-manual.csv.")
    if rows:
        print()
        print("  Biggest disagreements:")
        ranked = [r for r in rows if r["_wikidata"] and r["_osm"]]
        ranked.sort(key=lambda r: -abs(int(r["_wikidata"]) - int(r["_osm"])))
        for row in ranked[:12]:
            print(f"    {row['name'][:34]:34s} wikidata {row['_wikidata']:>7} "
                  f"vs osm {row['_osm']:>7}  ({row['_osmName'] or 'unnamed'})")
    if failures:
        print()
        for f in failures:
            print("  ! " + f)
    print("=" * 74)


if __name__ == "__main__":
    main()
