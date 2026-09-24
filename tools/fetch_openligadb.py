#!/usr/bin/env python3
"""
fetch_openligadb.py -- step 3, OpenLigaDB half.

Fetches the current season's matches for the German competitions that
football-data.org's free tier does not cover, and writes one file per
competition to data/fixtures/, plus data/fixtures/openligadb-index.json.

    2. Bundesliga, 3. Liga, DFB-Pokal, and whichever Regionalliga
    divisions OpenLigaDB actually carries.

The Bundesliga is deliberately NOT fetched here. football-data.org
already covers it (data/fixtures/BL1.json), and a second copy would mean
reconciling two sets of match and team ids for no benefit.

This file feeds the map and the app. It NEVER becomes calendar events:
the .ics feeds stay hand-curated through data/fixtures-manual.csv, and
build_calendars.py does not read data/fixtures/ at all.

Nothing here is invented. Every value written comes from the API
response. A value the API does not give stays blank and is counted in
the summary - OpenLigaDB writes a missing kickoff as 1970-01-01, and
that is read as "no date", never as a date.

A source that returns nothing is a failed fetch, not an empty league.
OpenLigaDB answers HTTP 200 with [] for a league shortcut it has never
heard of, so an empty list is treated as a failure and the last good
file is kept, exactly as fetch_fixtures.py keeps its own.

OpenLigaDB is free and keyless. No token, no secret.

Stdlib only.

Usage:  python3 tools/fetch_openligadb.py
Exits 1 if any competition that should have come back did not, so the
workflow step shows red instead of a green tick. Files that did come
back are still written.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------- config

OUT_DIR = "data/fixtures"
FILE_PREFIX = "openligadb-"
INDEX_FILE = "openligadb-index.json"
API_BASE = "https://api.openligadb.de"

# Shortcuts are OpenLigaDB's own and were read off its league list on
# 2026-09-24, not guessed. Several are user-created on that site, and
# the list also carries copies (e.g. "bl2h", a second 2. Bundesliga with
# no results in it) - so the shortcut is chosen by hand, here, and the
# tool never picks one by matching a league name.
#
# shortcut None means: this division exists, OpenLigaDB does not carry
# it this season. It is reported on every run, not silently absent.
#
# watch=True is for a shortcut that is listed but has never held a
# match. "regio-bayern" on 2026-09-24 was a stub: four teams, no
# fixtures. Until it has produced a file, an empty answer from it is
# reported as "not carried yet" rather than as a failure - otherwise the
# run would be red every day for a thing nobody can fix. Once a file
# exists it is protected like every other one: an empty answer is then a
# failed fetch and the file is kept.
COMPETITIONS = [
    # (shortcut,       label,                   tier, watch)
    ("bl2",           "2. Bundesliga",          2,    False),
    ("bl3",           "3. Liga",                3,    False),
    ("dfb",           "DFB-Pokal",              None, False),
    ("rln",           "Regionalliga Nord",      4,    False),
    ("rlno",          "Regionalliga Nordost",   4,    False),
    ("regio-bayern",  "Regionalliga Bayern",    4,    True),
    (None,            "Regionalliga West",      4,    False),
    (None,            "Regionalliga Südwest",   4,    False),
]

# Never fetched, and printed as such, so nobody adds it back by accident.
EXCLUDED = [("bl1", "Bundesliga", "football-data.org already covers it as BL1")]

# Rule 6: men's football only. A league whose own name says women's is
# refused even if a shortcut above ever comes to point at one.
WOMENS_MARKERS = ("frauen", "women", "damen", "juniorinnen")

# OpenLigaDB writes a missing kickoff as this. It is not a date.
NO_DATE_SENTINEL = "1970-01-01"

REQUEST_GAP_SECONDS = 1
TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
USER_AGENT = "football-fixture-planner (personal, non-commercial)"


# ------------------------------------------------------------------ http

def api_get(path):
    req = urllib.request.Request(
        API_BASE + path,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_get_with_retry(path):
    """Returns (data, None) or (None, reason)."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return api_get(path), None
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None, "404 - OpenLigaDB does not know this league/season"
            if exc.code == 429 and attempt < MAX_RETRIES:
                wait = int(exc.headers.get("Retry-After") or 30)
                print(f"    rate limited, waiting {wait}s")
                time.sleep(wait)
                continue
            if 500 <= exc.code < 600 and attempt < MAX_RETRIES:
                print(f"    server error {exc.code}, retrying")
                time.sleep(10)
                continue
            return None, f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < MAX_RETRIES:
                print(f"    network error, retrying: {getattr(exc, 'reason', exc)}")
                time.sleep(10)
                continue
            return None, f"network error: {getattr(exc, 'reason', exc)}"
        except json.JSONDecodeError as exc:
            return None, f"answer was not JSON: {exc.msg}"
    return None, "exhausted retries"


# --------------------------------------------------------------- shaping

def clean(value):
    """Strip OpenLigaDB's trailing spaces ('Steigerwaldstadion '); '' -> None."""
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def team_fields(raw):
    if not isinstance(raw, dict) or raw.get("teamId") is None:
        return None
    return {
        "id": raw.get("teamId"),
        "name": clean(raw.get("teamName")),
        "shortName": clean(raw.get("shortName")),
        "crest": clean(raw.get("teamIconUrl")),
    }


def kickoff_utc(raw):
    """The UTC kickoff, or None when the source has none (the 1970 sentinel)."""
    value = clean(raw.get("matchDateTimeUTC"))
    if not value or value.startswith(NO_DATE_SENTINEL):
        return None
    return value


def final_score(raw):
    """
    The result OpenLigaDB labels 'Endergebnis', and nothing else.

    A cup tie can carry extra results (after extra time, on penalties).
    None of them is promoted to the final score by guessing from their
    order; if there is no 'Endergebnis' the goals stay blank.
    """
    for r in raw.get("matchResults") or []:
        if clean(r.get("resultName")) == "Endergebnis":
            return r.get("pointsTeam1"), r.get("pointsTeam2")
    return None, None


def match_fields(raw):
    group = raw.get("group") or {}
    loc = raw.get("location") or {}
    home_goals, away_goals = final_score(raw)
    return {
        "id": raw.get("matchID"),
        "utcDate": kickoff_utc(raw),
        "finished": bool(raw.get("matchIsFinished")),
        "round": clean(group.get("groupName")),
        "roundOrder": group.get("groupOrderID"),
        "home": team_fields(raw.get("team1")),
        "away": team_fields(raw.get("team2")),
        "homeGoals": home_goals,
        "awayGoals": away_goals,
        "results": [
            {
                "name": clean(r.get("resultName")),
                "home": r.get("pointsTeam1"),
                "away": r.get("pointsTeam2"),
            }
            for r in sorted(raw.get("matchResults") or [],
                            key=lambda r: (r.get("resultOrderID") or 0,
                                           r.get("resultID") or 0))
        ],
        "stadium": clean(loc.get("locationStadium")),
        "city": clean(loc.get("locationCity")),
        "viewers": raw.get("numberOfViewers"),
    }


def collect_teams(matches):
    teams = {}
    for m in matches:
        for side in ("home", "away"):
            t = m.get(side)
            if t and t.get("id") is not None:
                teams[str(t["id"])] = t
    return dict(sorted(teams.items(), key=lambda kv: int(kv[0])))


def crest_host(url):
    try:
        return urllib.parse.urlsplit(url).hostname or "?"
    except ValueError:
        return "?"


# ------------------------------------------------------------------ main

def out_path(shortcut):
    return os.path.join(OUT_DIR, f"{FILE_PREFIX}{shortcut}.json")


def load_previous(shortcut):
    path = out_path(shortcut)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        print(f"    note: existing {path} unreadable, ignoring it")
        return None


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def latest_listing(leagues, shortcut):
    """
    OpenLigaDB's own entry for this shortcut in its newest listed season.
    The season is read off the source's league list, not derived from
    today's date.
    """
    rows = [l for l in leagues if l.get("leagueShortcut") == shortcut]
    if not rows:
        return None
    return max(rows, key=lambda l: int(str(l.get("leagueSeason") or 0)))


def fetch_one(shortcut, label, listing):
    """Returns (payload, stats, None) or (None, None, reason)."""
    season = str(listing.get("leagueSeason"))
    league_name = clean(listing.get("leagueName")) or label

    if any(w in league_name.lower() for w in WOMENS_MARKERS):
        return None, None, (f"OpenLigaDB names this league {league_name!r}, "
                            f"which is a women's competition - refused (rule 6)")

    data, error = api_get_with_retry(
        f"/getmatchdata/{urllib.parse.quote(shortcut)}/{season}")
    if error:
        return None, None, f"season {season}: {error}"
    if not isinstance(data, list):
        return None, None, f"season {season}: answer was not a list of matches"
    if not data:
        return None, None, (f"season {season}: OpenLigaDB returned no matches. "
                            f"It answers an unknown league the same way, so this "
                            f"is a failed fetch, not an empty league")

    # Every match must say it belongs to what was asked for. A mismatch
    # means the answer is about something else and none of it is kept.
    wrong = [m.get("matchID") for m in data
             if str(m.get("leagueShortcut") or "").lower() != shortcut.lower()
             or str(m.get("leagueSeason")) != season]
    if wrong:
        return None, None, (f"season {season}: {len(wrong)} of {len(data)} matches "
                            f"carry another league or season, e.g. match {wrong[0]}")

    matches = [match_fields(m) for m in data]
    matches.sort(key=lambda m: (m.get("utcDate") or "9999", m.get("id") or 0))
    teams = collect_teams(matches)

    payload = {
        "source": "OpenLigaDB (api.openligadb.de)",
        "note": "Fetched data. Feeds the map and the app only - never the calendars.",
        "shortcut": shortcut,
        "leagueId": listing.get("leagueId"),
        "name": league_name,
        "season": season,
        "matches": matches,
        "teams": teams,
    }

    crests = [t["crest"] for t in teams.values() if t.get("crest")]
    hosts = {}
    for url in crests:
        h = crest_host(url)
        hosts[h] = hosts.get(h, 0) + 1
    stats = {
        "matches": len(matches),
        "finished": sum(1 for m in matches if m["finished"]),
        "teams": len(teams),
        "crests": len(crests),
        "crestHosts": dict(sorted(hosts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "noDate": sum(1 for m in matches if not m["utcDate"]),
        "finishedNoScore": sum(1 for m in matches
                               if m["finished"] and m["homeGoals"] is None),
        "noTeam": sum(1 for m in matches if not m["home"] or not m["away"]),
        "withStadium": sum(1 for m in matches if m["stadium"]),
    }
    return payload, stats, None


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    report, failures, absent, index = [], [], [], {}
    not_carried = []
    all_hosts = {}

    print("  league list")
    leagues, error = api_get_with_retry("/getavailableleagues")
    if not error and (not isinstance(leagues, list) or not leagues):
        error = "league list came back empty - a failed fetch, not an empty site"
    if error:
        leagues = None
        print(f"  ! {error}")

    for position, (shortcut, label, tier, watch) in enumerate(COMPETITIONS):
        if shortcut is None:
            not_carried.append(label)
            absent.append(f"{label}: not carried by OpenLigaDB this season - "
                          f"no file, nothing to fall back on")
            continue

        if position:
            time.sleep(REQUEST_GAP_SECONDS)
        print(f"  {shortcut:13s} {label}")

        if leagues is None:
            payload, stats, reason = None, None, f"league list unavailable ({error})"
        else:
            listing = latest_listing(leagues, shortcut)
            if listing is None:
                payload, stats, reason = None, None, "shortcut not in OpenLigaDB's league list"
            else:
                payload, stats, reason = fetch_one(shortcut, label, listing)

        if reason:
            kept = load_previous(shortcut)
            if watch and not kept:
                not_carried.append(label)
                absent.append(f"{label}: OpenLigaDB lists '{shortcut}' but it gave "
                              f"no usable matches ({reason.split(':')[0]}). Watched: "
                              f"not a failure until it has produced a file once")
                continue
            if kept:
                index[shortcut] = {
                    "label": label,
                    "tier": tier,
                    "name": kept.get("name"),
                    "season": kept.get("season"),
                    "matches": len(kept.get("matches", [])),
                    "teams": len(kept.get("teams", {})),
                    "lastFetchFailed": True,
                }
                failures.append(
                    f"{shortcut} ({label}): {reason} - file left untouched, still "
                    f"holds {len(kept.get('matches', []))} matches for season "
                    f"{kept.get('season')}")
            else:
                failures.append(f"{shortcut} ({label}): {reason} - no file to fall back on")
            continue

        write_json(out_path(shortcut), payload)
        index[shortcut] = {
            "label": label,
            "tier": tier,
            "name": payload["name"],
            "season": payload["season"],
            "matches": stats["matches"],
            "teams": stats["teams"],
        }
        for h, n in stats["crestHosts"].items():
            all_hosts[h] = all_hosts.get(h, 0) + n

        line = (f"{shortcut:13s} {payload['season']}  {stats['matches']:4d} matches, "
                f"{stats['finished']:4d} played, {stats['teams']:3d} teams, "
                f"{stats['crests']:3d} with a crest")
        report.append(line)
        gaps = []
        if stats["noDate"]:
            gaps.append(f"{stats['noDate']} with no kickoff time (left blank)")
        if stats["finishedNoScore"]:
            gaps.append(f"{stats['finishedNoScore']} finished with no 'Endergebnis' (goals left blank)")
        if stats["noTeam"]:
            gaps.append(f"{stats['noTeam']} missing a team")
        if stats["teams"] - stats["crests"]:
            gaps.append(f"{stats['teams'] - stats['crests']} teams with no crest")
        for g in gaps:
            report.append(f"{'':13s}   - {g}")

    write_json(os.path.join(OUT_DIR, INDEX_FILE), {
        "source": "OpenLigaDB (api.openligadb.de)",
        "note": ("One file per competition in this folder, named openligadb-<shortcut>.json. "
                 "Map and app only. The Bundesliga is not here: see index.json (football-data.org)."),
        "competitions": dict(sorted(index.items())),
        "notCarried": sorted(not_carried),
    })

    print()
    print("=" * 66)
    print("OPENLIGADB FIXTURES FETCHED")
    print("=" * 66)
    for line in report:
        print("  " + line)
    total = sum(v["matches"] for v in index.values())
    teams_total = sum(v["teams"] for v in index.values())
    print(f"  {'':13s}       {total:4d} matches across {len(index)} competitions, "
          f"{teams_total} team entries")
    if all_hosts:
        print()
        print("  CREST URLS - where they point. These are hotlinks to whatever")
        print("  site each was taken from, not images OpenLigaDB licenses. Check")
        print("  each image's own licence before using it on a public page.")
        for h, n in sorted(all_hosts.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"    {n:4d}  {h}")
    print()
    print("  NOT FETCHED, ON PURPOSE:")
    for code, label, why in EXCLUDED:
        print(f"  - {code} ({label}): {why}")
    if absent:
        print()
        print("  NOT ON OPENLIGADB:")
        for a in absent:
            print("  - " + a)
    if failures:
        print()
        print("  NOT FETCHED THIS RUN:")
        for f in failures:
            print("  ! " + f)
    print("=" * 66)

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
