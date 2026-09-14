#!/usr/bin/env python3
"""
fetch_fixtures.py -- step 3, football-data.org half.

Fetches the current season's matches for each competition the free tier
covers and writes one file per competition to data/fixtures/, plus a
small index.json. One file each keeps the daily commit down to the
leagues that actually played.

This file feeds the map and the app. It NEVER becomes calendar events:
the .ics feeds stay hand-curated through data/fixtures-manual.csv.

Nothing here is invented. Every value written comes from the API
response. If a competition cannot be fetched, whatever was fetched last
time is kept rather than replaced with a gap.

Stdlib only. Needs FOOTBALL_DATA_TOKEN in the environment.

Usage:  FOOTBALL_DATA_TOKEN=... python3 tools/fetch_fixtures.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------- config

OUT_DIR = "data/fixtures"
API_BASE = "https://api.football-data.org/v4"

# The twelve competitions on the free tier.
COMPETITIONS = [
    ("WC",  "FIFA World Cup"),
    ("CL",  "UEFA Champions League"),
    ("BL1", "Bundesliga"),
    ("DED", "Eredivisie"),
    ("BSA", "Campeonato Brasileiro Serie A"),
    ("PD",  "Primera Division"),
    ("FL1", "Ligue 1"),
    ("ELC", "Championship"),
    ("PPL", "Primeira Liga"),
    ("EC",  "European Championship"),
    ("SA",  "Serie A"),
    ("PL",  "Premier League"),
]

# Free tier allows 10 requests per minute. 7s between calls keeps us
# under it with room to spare; twelve competitions take about 80s.
REQUEST_GAP_SECONDS = 7
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3


# ------------------------------------------------------------------ http

def api_get(path, token):
    """One GET against the API. Returns parsed JSON or raises."""
    req = urllib.request.Request(
        API_BASE + path,
        headers={
            "X-Auth-Token": token,
            "User-Agent": "football-fixture-planner (personal, non-commercial)",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_get_with_retry(path, token):
    """
    Retry on rate limiting and transient server errors.

    A 403 is not retried: it means the token does not cover this
    competition, which no amount of waiting will fix.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return api_get(path, token), None
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                return None, "403 - this token does not have access to this competition"
            if exc.code == 404:
                return None, "404 - no such competition"
            if exc.code == 429:
                wait = int(exc.headers.get("Retry-After") or 60)
                if attempt == MAX_RETRIES:
                    return None, f"429 rate limited, gave up after {MAX_RETRIES} tries"
                print(f"    rate limited, waiting {wait}s")
                time.sleep(wait)
                continue
            if 500 <= exc.code < 600 and attempt < MAX_RETRIES:
                print(f"    server error {exc.code}, retrying")
                time.sleep(10)
                continue
            return None, f"HTTP {exc.code}"
        except urllib.error.URLError as exc:
            if attempt < MAX_RETRIES:
                print(f"    network error, retrying: {exc.reason}")
                time.sleep(10)
                continue
            return None, f"network error: {exc.reason}"
    return None, "exhausted retries"


# --------------------------------------------------------------- shaping

def team_fields(raw):
    """Keep only what the map and the app need."""
    if not isinstance(raw, dict):
        return None
    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "shortName": raw.get("shortName"),
        "tla": raw.get("tla"),
        "crest": raw.get("crest"),
    }


def match_fields(raw):
    score = raw.get("score") or {}
    full = score.get("fullTime") or {}
    return {
        "id": raw.get("id"),
        "utcDate": raw.get("utcDate"),
        "status": raw.get("status"),
        "matchday": raw.get("matchday"),
        "stage": raw.get("stage"),
        "group": raw.get("group"),
        "home": team_fields(raw.get("homeTeam")),
        "away": team_fields(raw.get("awayTeam")),
        "homeGoals": full.get("home"),
        "awayGoals": full.get("away"),
        "winner": score.get("winner"),
    }


def collect_teams(matches):
    """Build a team index out of the match data - costs no extra requests."""
    teams = {}
    for m in matches:
        for side in ("home", "away"):
            t = m.get(side)
            if t and t.get("id") is not None:
                teams[str(t["id"])] = t
    return dict(sorted(teams.items(), key=lambda kv: int(kv[0])))


# ------------------------------------------------------------------ main

def load_previous(code):
    path = os.path.join(OUT_DIR, f"{code}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        print(f"    note: existing {path} unreadable, ignoring it")
        return None


def write_competition(code, payload):
    path = os.path.join(OUT_DIR, f"{code}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return path


def main():
    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not token:
        sys.exit(
            "FOOTBALL_DATA_TOKEN is not set.\n"
            "In GitHub: Settings > Secrets and variables > Actions, and the "
            "secret must be named exactly FOOTBALL_DATA_TOKEN."
        )

    os.makedirs(OUT_DIR, exist_ok=True)

    report, failures, index = [], [], {}

    for position, (code, label) in enumerate(COMPETITIONS):
        if position:
            time.sleep(REQUEST_GAP_SECONDS)

        print(f"  {code:4s} {label}")
        data, error = api_get_with_retry(f"/competitions/{code}/matches", token)

        if error:
            kept = load_previous(code)
            if kept:
                index[code] = {
                    "name": kept.get("name", label),
                    "matches": len(kept.get("matches", [])),
                    "teams": len(kept.get("teams", {})),
                    "seasonStart": kept.get("seasonStart"),
                    "seasonEnd": kept.get("seasonEnd"),
                    "lastFetchFailed": True,
                }
                failures.append(
                    f"{code} ({label}): {error} - file left untouched, "
                    f"still holds {len(kept.get('matches', []))} matches")
            else:
                failures.append(f"{code} ({label}): {error} - no file to fall back on")
            continue

        matches = [match_fields(m) for m in data.get("matches", [])]
        matches.sort(key=lambda m: (m.get("utcDate") or "", m.get("id") or 0))
        teams = collect_teams(matches)

        season = (data.get("competition") or {}).get("currentSeason") or {}
        payload = {
            "source": "football-data.org v4",
            "note": "Fetched data. Feeds the map and the app only - never the calendars.",
            "code": code,
            "name": (data.get("competition") or {}).get("name") or label,
            "seasonStart": season.get("startDate"),
            "seasonEnd": season.get("endDate"),
            "matches": matches,
            "teams": teams,
        }
        write_competition(code, payload)

        index[code] = {
            "name": payload["name"],
            "matches": len(matches),
            "teams": len(teams),
            "seasonStart": payload["seasonStart"],
            "seasonEnd": payload["seasonEnd"],
        }

        played = sum(1 for m in matches if m.get("status") == "FINISHED")
        crests = sum(1 for t in teams.values() if t.get("crest"))
        report.append(f"{code:4s} {len(matches):4d} matches, {played:4d} played, "
                      f"{len(teams):3d} teams, {crests:3d} with a crest")

    with open(os.path.join(OUT_DIR, "index.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "source": "football-data.org v4",
            "note": "One file per competition in this folder. Map and app only.",
            "competitions": dict(sorted(index.items())),
        }, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    print()
    print("=" * 66)
    print("FIXTURES FETCHED")
    print("=" * 66)
    for line in report:
        print("  " + line)
    total = sum(v["matches"] for v in index.values())
    teams_total = sum(v["teams"] for v in index.values())
    print(f"  {'':4s} {total:4d} matches across {len(index)} competitions, "
          f"{teams_total} team entries")
    if failures:
        print()
        print("  NOT FETCHED THIS RUN:")
        for f in failures:
            print("  ! " + f)
    print("=" * 66)


if __name__ == "__main__":
    main()
