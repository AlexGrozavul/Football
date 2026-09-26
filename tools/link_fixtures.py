#!/usr/bin/env python3
"""
link_fixtures.py -- which fetched fixtures belong to which club on the map.

The map's clubs are Wikidata items. The fixture files are not: they come
from football-data.org (data/fixtures/<CODE>.json) and from OpenLigaDB
(data/fixtures/openligadb-<shortcut>.json), and each source numbers its
teams its own way. Nothing joins the three. This tool builds that join
once, from the committed files, and writes it down:

    data/clubs/fixture-links.json        what the club sheet reads
    data/clubs/fixture-link-review.csv   everything it would not decide

It makes NO network request. It reads files already in the repository,
so it can run anywhere, and it never writes to a club file, a fixture
file or a hand-written file.

The page reads the mapping instead of matching names itself on every
load, so the matching happens in one place, is printed back in a run
summary, and can be corrected by hand.


HOW A TEAM IS MATCHED TO A CLUB
-------------------------------

By NAME, because neither fixture source publishes a Wikidata id, and
with the care the StadiumDB matcher and the roster check taught:

  1. EQUALITY, NOT CONTAINMENT. Both sides here are full club names, not
     StadiumDB's fragments, so after the legal-form words ("FC", "SV",
     "TSG" ...) and founding years are set aside, the words that are
     left must be the SAME words. Containment would put "1. FC Koeln"
     inside "Fortuna Koeln" - the one word "koeln" is all of the first.

  2. THE RESERVE MARKER MUST AGREE. "VfB Stuttgart II" never matches
     "VfB Stuttgart", in either direction. A first team's fixtures on a
     reserve side's sheet, or the other way round, is exactly the wrong
     answer that looks right.

  3. LEGAL FORMS AND YEARS MAY BE ABSENT, NOT DIFFERENT. "TSG Hoffenheim"
     matches "TSG 1899 Hoffenheim" because one side simply leaves the
     year out. But where both sides carry a legal form and they share
     none - "VfB Oldenburg" against a "VfL Oldenburg" - or both carry a
     year and they share none, it is a different club.

  4. A SHORT NAME NEEDS TWO WORDS. Each team has a long name and a short
     one. The short one is tried too - "SV Drochtersen/Assel" is how the
     map knows that club - but only when it still has at least two words
     after the legal forms are set aside. "Kiel", "Halle", "Eintracht"
     are fragments and match nothing on their own.

  5. COUNTRY. A team is only compared with clubs of its own country, and
     its country comes from the competition it plays in, never from its
     name: the Bundesliga and every OpenLigaDB competition this project
     fetches are German, the Premier League English, and so on. A team
     seen ONLY in the Champions League has no country from this data at
     all, so it is never linked - if its name would have matched a club,
     that is written to the review file for a person to judge, because a
     Dinamo is not a Dinamo just because the word agrees.

  6. WOMEN'S TEAMS ARE SKIPPED. Rule 6. None is in today's files; the
     guard is there so the first one does not land on a men's club.
     National-team competitions (EC, WC) are skipped for the same kind
     of reason: a country is not a club.

  7. AMBIGUITY IS REPORTED, NOT RESOLVED. A team whose name matches two
     clubs, or a club matched by two teams of one source, is linked to
     nothing, and both candidates go to the review file. The one
     exception is a VENUE: where OpenLigaDB records the ground of a
     team's home matches (today only the Regionalliga Nordost does), and
     exactly one candidate's ground agrees with it, that candidate is
     linked - and the link says it rests on name AND venue, and the run
     summary lists it. That is a second signal agreeing, not a pick.
     A venue that DISAGREES with a name match does not break the link:
     half the German ground names are a sponsor's name against the old
     one. It is reported.

A club with no confident link in either source shows fixtures as
unavailable on its sheet. That is the right answer for most of the map -
football-data.org's free tier has no Romanian competition and OpenLigaDB
carries two of the five Regionalliga divisions - and it is not a bug.


HAND CORRECTIONS
----------------

data/fixture-links-manual.csv is hand-written and wins over everything
this tool decides - rule 3. One row per decision:

    clubQid,source,teamId,action,note

source is `football-data` or `openligadb`. action is `link`, which
links that team to that club whatever the names say, or `reject`, which
removes a link this tool made. The `link` rows for one club and one
source replace whatever this tool found for that pair, and there may be
more than one: OpenLigaDB sometimes gives one club two ids, one per
competition, and two rows link both. Every row is printed back as understood,
and a row naming a club or team that does not exist is rejected with
its line number.


TICKETS
-------

The ticket files already carry a clubQid, so they need no name matching
at all: the club sheet joins them to the map by Q-id, which is exact.
What this tool adds is the READ-BACK of that join - which ticket clubs
are on the map, which are not, and whether the club name and country
written in club-tickets.csv agree with the map's. A disagreement is
reported, never corrected: the hand-written file wins.

Usage:  python3 tools/link_fixtures.py
"""

import csv
import glob
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# The same folding, legal-form list, reserve markers and ground
# comparison the StadiumDB matcher uses, imported rather than copied:
# two copies of a name rule drift apart, and the drift is silent.
from crosscheck_stadiumdb import CLUB_FORMS, TEAM_MARKERS, ground_signal, words  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLUB_FILES = ["data/clubs/DE.json", "data/clubs/RO.json", "data/clubs/FR.json",
              "data/clubs/IT.json", "data/clubs/CH.json"]
FD_INDEX = "data/fixtures/index.json"
OLDB_INDEX = "data/fixtures/openligadb-index.json"
MANUAL_FILE = "data/fixture-links-manual.csv"
TICKETS_FILE = "data/club-tickets.csv"
OUT_FILE = "data/clubs/fixture-links.json"
REVIEW_FILE = "data/clubs/fixture-link-review.csv"

SOURCES = ("football-data", "openligadb")

# Which country a football-data.org competition's teams are in. A code
# that is not here is not assumed to be anybody's: its teams get no
# country, and a team with no country is never linked.
FD_COUNTRY = {
    "BL1": "DE",
    "PL": "GB", "ELC": "GB", "PD": "ES", "SA": "IT", "FL1": "FR",
    "DED": "NL", "PPL": "PT", "BSA": "BR",
}
# Competitions between national teams. A country is not a club.
FD_NATIONAL = {"EC", "WC"}

# Every OpenLigaDB competition fetch_openligadb.py names is German - the
# tool's own shortcut list is German leagues and the DFB-Pokal only.
OLDB_COUNTRY = "DE"

WOMEN_WORDS = {"frauen", "women", "womens", "feminin", "feminine", "damen", "ladies"}

REVIEW_COLUMNS = ["_verdict", "source", "teamId", "teamName", "teamCountry",
                  "competitions", "clubQid", "clubName", "candidates", "note"]


# ----------------------------------------------------------------- names

def name_parts(name):
    """(core words, legal forms, years, reserve markers) of a name."""
    ws = words(name)
    markers = frozenset(w for w in ws if w in TEAM_MARKERS)
    forms = frozenset(w for w in ws if w in CLUB_FORMS)
    # "1." in "1. FC Koeln" is part of the legal form, not a year.
    years = frozenset(w for w in ws if w.isdigit() and w not in TEAM_MARKERS and len(w) >= 2)
    core = frozenset(w for w in ws
                     if w not in TEAM_MARKERS and w not in CLUB_FORMS and not w.isdigit())
    return core, forms, years, markers


def names_match(ours, theirs, short=False):
    """Rules 1-4 of the docstring. True or False."""
    a_core, a_forms, a_years, a_mark = name_parts(ours)
    b_core, b_forms, b_years, b_mark = name_parts(theirs)
    if not a_core or not b_core:
        return False
    if short and len(b_core) < 2:
        return False
    if a_core != b_core:
        return False
    if a_mark != b_mark:
        return False
    if a_forms and b_forms and not (a_forms & b_forms):
        return False
    if a_years and b_years and not (a_years & b_years):
        return False
    return True


def is_women(name):
    return bool(set(words(name)) & WOMEN_WORDS)


def shares_a_word(ours, theirs):
    """For the review file only: a club worth a look beside an unmatched
    team. A shared word of five letters or more, never a decision."""
    a = {w for w in name_parts(ours)[0] if len(w) >= 5}
    b = {w for w in name_parts(theirs)[0] if len(w) >= 5}
    return bool(a & b)


# --------------------------------------------------------------- reading

def read_json(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def load_clubs(problems):
    clubs = {}
    for rel in CLUB_FILES:
        try:
            data = read_json(rel)
        except (OSError, ValueError) as exc:
            problems.append(f"{rel}: could not be read ({exc})")
            continue
        for c in data.get("clubs", []):
            clubs[c["id"]] = {"id": c["id"], "name": c.get("name") or c["id"],
                              "country": data.get("country"),
                              "tier": c.get("tier"), "venue": c.get("venue")}
    return clubs


def load_teams(problems):
    """
    Every team in every fixture file, keyed by (source, teamId). A team
    id is the source's own and is stable across that source's
    competitions - football-data.org's 5 is Bayern in the Bundesliga and
    in the Champions League alike - so one team can carry several
    competitions.
    """
    teams = {}

    def team(source, tid, name, short):
        key = (source, str(tid))
        if key not in teams:
            teams[key] = {"source": source, "teamId": str(tid), "names": set(),
                          "short": set(), "competitions": [], "countries": set(),
                          "venues": Counter()}
        t = teams[key]
        if name:
            t["names"].add(name)
        if short:
            t["short"].add(short)
        return t

    try:
        fd_index = read_json(FD_INDEX)
    except (OSError, ValueError) as exc:
        problems.append(f"{FD_INDEX}: could not be read ({exc})")
        fd_index = {"competitions": {}}
    for code in sorted(fd_index.get("competitions", {})):
        if code in FD_NATIONAL:
            continue
        rel = f"data/fixtures/{code}.json"
        try:
            data = read_json(rel)
        except (OSError, ValueError) as exc:
            problems.append(f"{rel}: listed in {FD_INDEX} but could not be read ({exc})")
            continue
        comp = {"file": rel, "code": code, "label": data.get("name") or code}
        for tid, t in (data.get("teams") or {}).items():
            entry = team("football-data", tid, t.get("name"), t.get("shortName"))
            entry["competitions"].append(comp)
            if code in FD_COUNTRY:
                entry["countries"].add(FD_COUNTRY[code])

    try:
        oldb_index = read_json(OLDB_INDEX)
    except (OSError, ValueError) as exc:
        problems.append(f"{OLDB_INDEX}: could not be read ({exc})")
        oldb_index = {"competitions": {}}
    for shortcut in sorted(oldb_index.get("competitions", {})):
        meta = oldb_index["competitions"][shortcut]
        rel = f"data/fixtures/openligadb-{shortcut}.json"
        try:
            data = read_json(rel)
        except (OSError, ValueError) as exc:
            problems.append(f"{rel}: listed in {OLDB_INDEX} but could not be read ({exc})")
            continue
        comp = {"file": rel, "code": shortcut,
                "label": meta.get("label") or data.get("name") or shortcut}
        for tid, t in (data.get("teams") or {}).items():
            entry = team("openligadb", tid, t.get("name"), t.get("shortName"))
            entry["competitions"].append(comp)
            entry["countries"].add(OLDB_COUNTRY)
        # The venue signal: the ground OpenLigaDB records for a team's
        # HOME matches. Away matches say nothing about a team's ground.
        for m in data.get("matches") or []:
            home = (m.get("home") or {}).get("id")
            if home is not None and m.get("stadium"):
                teams[("openligadb", str(home))]["venues"][m["stadium"]] += 1
    return teams


def load_manual(clubs, teams, problems):
    """Read back data/fixture-links-manual.csv. Missing file = no rows."""
    rows = []
    path = os.path.join(ROOT, MANUAL_FILE)
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, restkey="__overflow__")
        for line, r in enumerate(reader, start=2):
            if r.get("__overflow__"):
                problems.append(f"{MANUAL_FILE} line {line}: more values than columns - "
                                f"a comma inside a cell needs the cell in double quotes")
                continue
            qid = (r.get("clubQid") or "").strip()
            source = (r.get("source") or "").strip()
            tid = (r.get("teamId") or "").strip()
            action = (r.get("action") or "").strip()
            if not qid and not source and not tid and not action:
                continue
            why = None
            if source not in SOURCES:
                why = f"source must be one of {', '.join(SOURCES)}"
            elif action not in ("link", "reject"):
                why = "action must be link or reject"
            elif qid not in clubs:
                why = f"{qid or '(blank)'} is not a club on the map"
            elif (source, tid) not in teams:
                why = f"{source} has no team {tid or '(blank)'} in the fixture files"
            if why:
                problems.append(f"{MANUAL_FILE} line {line}: rejected - {why}")
                continue
            rows.append({"line": line, "clubQid": qid, "source": source,
                         "teamId": tid, "action": action, "note": r.get("note") or ""})
    return rows


# -------------------------------------------------------------- matching

def team_label(t):
    return sorted(t["names"])[0] if t["names"] else t["teamId"]


def team_country(t):
    """One country, or None when the data gives none or gives two."""
    return next(iter(t["countries"])) if len(t["countries"]) == 1 else None


def candidates_for(t, clubs, country=None):
    """Clubs whose name matches any of the team's names, optionally only
    in one country. Returns {qid: 'name' | 'short-name'}."""
    found = {}
    for qid, c in clubs.items():
        if country and c["country"] != country:
            continue
        if any(names_match(c["name"], n) for n in t["names"]):
            found[qid] = "name"
        elif any(names_match(c["name"], n, short=True) for n in t["short"]):
            found.setdefault(qid, "short-name")
    return found


def venue_of(t):
    return t["venues"].most_common(1)[0][0] if t["venues"] else None


def link_record(t, basis, club):
    venue = venue_of(t)
    agrees = ground_signal(club["venue"], venue) if venue else None
    return {
        "source": t["source"],
        "teamId": t["teamId"],
        "teamName": team_label(t),
        "basis": basis,
        "venue": ({"theirs": venue, "agrees": agrees} if venue else None),
        "competitions": [{"code": c["code"], "file": c["file"], "label": c["label"]}
                         for c in t["competitions"]],
    }


def review(verdict, t=None, club=None, candidates=(), note=""):
    return {
        "_verdict": verdict,
        "source": t["source"] if t else "",
        "teamId": t["teamId"] if t else "",
        "teamName": team_label(t) if t else "",
        "teamCountry": (team_country(t) or "") if t else "",
        "competitions": ";".join(c["code"] for c in t["competitions"]) if t else "",
        "clubQid": club["id"] if club else "",
        "clubName": club["name"] if club else "",
        "candidates": "; ".join(candidates),
        "note": note,
    }


def main():
    problems = []
    clubs = load_clubs(problems)
    teams = load_teams(problems)
    # A file that did not read is a failed run, not a smaller answer:
    # writing the mapping without it would drop every link through that
    # file with a green tick. The last good mapping is kept instead.
    if problems or not clubs or not teams:
        if not clubs or not teams:
            problems.append("no clubs or no fixture teams were read - nothing to link")
        report_failure(problems)
        sys.exit(1)
    manual = load_manual(clubs, teams, problems)

    reviews = []
    links = defaultdict(list)          # qid -> [link records]
    by_venue = []                      # links a venue settled, for the summary

    # First pass: each team, in its own country, against every club.
    proposed = defaultdict(list)       # (source, qid) -> [(team, basis)]
    for key in sorted(teams, key=lambda k: (k[0], int(k[1]) if k[1].isdigit() else 0)):
        t = teams[key]
        if any(is_women(n) for n in t["names"]):
            reviews.append(review("skipped-women", t, note="rule 6: men's football only"))
            continue
        country = team_country(t)
        if country is None:
            # No country from the data. Never linked; a match it WOULD
            # have made is for a person to judge.
            would = candidates_for(t, clubs)
            if would:
                reviews.append(review(
                    "country-unknown", t,
                    candidates=[f"{q} {clubs[q]['name']} ({clubs[q]['country']})" for q in would],
                    note="the team plays only in competitions that give it no country "
                         "(or in two countries' leagues), so a name match is not trusted"))
            continue
        if country not in {c["country"] for c in clubs.values()}:
            # A foreign league. Checked anyway, so a cross-country name
            # clash is SEEN rather than silently impossible.
            would = candidates_for(t, clubs)
            if would:
                reviews.append(review(
                    "cross-country-blocked", t,
                    candidates=[f"{q} {clubs[q]['name']} ({clubs[q]['country']})" for q in would],
                    note=f"the team's league is in {country}; names agree, countries do not"))
            continue

        found = candidates_for(t, clubs, country)
        if len(found) == 1:
            qid, basis = next(iter(found.items()))
            proposed[(t["source"], qid)].append((t, basis))
        elif len(found) > 1:
            venue = venue_of(t)
            agreeing = [q for q in found if venue and ground_signal(clubs[q]["venue"], venue)]
            if len(agreeing) == 1:
                qid = agreeing[0]
                proposed[(t["source"], qid)].append((t, found[qid] + "+venue"))
                by_venue.append((t, clubs[qid], sorted(found)))
            else:
                reviews.append(review(
                    "ambiguous-team", t,
                    candidates=[f"{q} {clubs[q]['name']}" for q in sorted(found)],
                    note="the team's name matches more than one club on the map; none linked"))
        else:
            near = [f"{q} {c['name']}" for q, c in sorted(clubs.items())
                    if c["country"] == country
                    and any(shares_a_word(c["name"], n) for n in t["names"] | t["short"])]
            reviews.append(review(
                "unmatched-team", t, candidates=near,
                note=("no club on the map has this name; candidates share a word and are "
                      "listed for a look, not proposed" if near else
                      "no club on the map has this name")))

    # Second pass: a club matched by two teams of ONE source is ambiguous.
    for (source, qid), found in sorted(proposed.items()):
        club = clubs[qid]
        if len(found) > 1:
            reviews.append(review(
                "ambiguous-club", None, club,
                candidates=[f"{source} {t['teamId']} {team_label(t)}" for t, _ in found],
                note=f"more than one {source} team matches this club; none linked"))
            continue
        t, basis = found[0]
        rec = link_record(t, basis, club)
        links[qid].append(rec)
        if rec["venue"] and rec["venue"]["agrees"] is False:
            reviews.append(review(
                "venue-disagrees", t, club,
                candidates=[f"ours: {club['venue'] or '-'}", f"theirs: {rec['venue']['theirs']}"],
                note="linked on the name; the ground names differ, which is often a "
                     "sponsor's name against the old one - worth one look"))

    # Hand corrections win. The `link` rows for one club and one source
    # are, together, that club's whole answer for that source - so two
    # rows can link both of OpenLigaDB's ids for one club, which is the
    # shape the Saarbruecken and Wuerzburg duplicates have.
    applied = []
    hand_links = defaultdict(list)
    for row in manual:
        if row["action"] == "link":
            hand_links[(row["clubQid"], row["source"])].append(row)
    for (qid, source), rows in hand_links.items():
        before = [r["teamId"] for r in links[qid] if r["source"] == source]
        links[qid] = [r for r in links[qid] if r["source"] != source]
        for row in rows:
            t = teams[(source, row["teamId"])]
            links[qid].append(link_record(t, "manual", clubs[qid]))
            applied.append((row, "linked" + (f" (automatic was {', '.join(before)})"
                                             if before else "")))
            # A team linked by hand to one club must not stay linked to another.
            for other in list(links):
                if other != qid:
                    links[other] = [r for r in links[other]
                                    if not (r["source"] == source
                                            and r["teamId"] == row["teamId"])]
    for row in manual:
        if row["action"] == "reject":
            qid = row["clubQid"]
            before = len(links[qid])
            links[qid] = [r for r in links[qid]
                          if not (r["source"] == row["source"] and r["teamId"] == row["teamId"])]
            applied.append((row, "removed" if len(links[qid]) < before else "nothing to remove"))
    links = {q: sorted(r, key=lambda x: (x["source"], x["teamId"]))
             for q, r in links.items() if r}

    tickets = ticket_readback(clubs, problems)

    write_outputs(clubs, links, reviews)
    summary(clubs, teams, links, reviews, by_venue, manual, applied, tickets, problems)
    sys.exit(1 if problems else 0)


# ---------------------------------------------------------------- tickets

def ticket_readback(clubs, problems):
    """The Q-id join between club-tickets.csv and the map, read back."""
    out = []
    path = os.path.join(ROOT, TICKETS_FILE)
    try:
        fh = open(path, encoding="utf-8", newline="")
    except OSError as exc:
        problems.append(f"{TICKETS_FILE}: could not be read ({exc})")
        return out
    with fh:
        for line, r in enumerate(csv.DictReader(fh), start=2):
            qid = (r.get("clubQid") or "").strip()
            club = clubs.get(qid)
            row = {"line": line, "qid": qid, "club": r.get("club") or "",
                   "team": r.get("team") or "", "country": r.get("country") or "",
                   "onMap": bool(club), "notes": []}
            if club:
                if not names_match(club["name"], row["club"]) and \
                        not names_match(row["club"], club["name"]):
                    row["notes"].append(f"name differs: map says '{club['name']}'")
                if row["country"] and row["country"] != club["country"]:
                    row["notes"].append(f"country differs: map file is {club['country']}")
                if not row["country"]:
                    row["notes"].append("country blank in club-tickets.csv")
            if row["team"] != "men":
                row["notes"].append("team is not 'men' - the sheet shows men's rows only")
            out.append(row)
    return out


# ---------------------------------------------------------------- output

def write_outputs(clubs, links, reviews):
    doc = {
        "source": "tools/link_fixtures.py, from data/fixtures/ and data/clubs/",
        "note": ("Which fixture-source team each map club is. Generated - do not edit; "
                 "hand corrections go in data/fixture-links-manual.csv. A club that is "
                 "not listed has no confident link, and its sheet says fixtures are "
                 "unavailable."),
        "clubs": {q: {"name": clubs[q]["name"], "links": links[q]}
                  for q in sorted(links, key=lambda q: (clubs[q]["country"], clubs[q]["name"]))},
        # Why a club that a name DID match is still unlinked, so its sheet
        # can say "ambiguous" rather than the generic "not carried".
        "notLinked": {r["clubQid"]: (f"More than one fixture team matches this club's name "
                                     f"({r['candidates']}), so none was linked. "
                                     f"See {REVIEW_FILE}; a row in {MANUAL_FILE} settles it.")
                      for r in sorted(reviews, key=lambda r: r["clubQid"])
                      if r["_verdict"] == "ambiguous-club" and r["clubQid"] not in links},
    }
    # No timestamp in the file: a run that changes nothing must write
    # the same bytes, or the workflow commits a diff every day.
    with open(os.path.join(ROOT, OUT_FILE), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    order = ["ambiguous-team", "ambiguous-club", "country-unknown", "cross-country-blocked",
             "venue-disagrees", "unmatched-team", "skipped-women"]
    reviews.sort(key=lambda r: (order.index(r["_verdict"]), r["source"], r["teamName"],
                                r["clubName"]))
    with open(os.path.join(ROOT, REVIEW_FILE), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=REVIEW_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(reviews)


def report_failure(problems):
    print("=" * 74)
    print("FIXTURE LINKS - NOT WRITTEN")
    for p in problems:
        print("  ! " + p)
    print(f"  {OUT_FILE} and {REVIEW_FILE} are left as the last good run left them.")
    print("=" * 74)


def summary(clubs, teams, links, reviews, by_venue, manual, applied, tickets, problems):
    p = print
    p("=" * 74)
    p("FIXTURE LINKS")
    p("=" * 74)
    per_source = Counter(t["source"] for t in teams.values())
    p(f"  clubs on the map: {len(clubs)}    fixture teams read: "
      + ", ".join(f"{s} {n}" for s, n in sorted(per_source.items())))
    p()
    linked = {q: r for q, r in links.items()}
    p(f"LINKED - {len(linked)} of {len(clubs)} map clubs have fixtures from at least one source")
    for q in sorted(linked, key=lambda q: (clubs[q]["country"], clubs[q]["tier"] or 99,
                                           clubs[q]["name"])):
        c = clubs[q]
        bits = []
        for r in linked[q]:
            comps = "+".join(x["code"] for x in r["competitions"])
            extra = "" if r["basis"] == "name" else f" [{r['basis']}]"
            if r["venue"] and r["venue"]["agrees"] is False:
                extra += " [venue differs]"
            bits.append(f"{r['source']} {r['teamId']} ({comps}){extra}")
        p(f"  {c['country']} t{c['tier']}  {c['name']:<34} {q:<11} " + "; ".join(bits))
    p()
    unlinked = [c for q, c in clubs.items() if q not in linked]
    p(f"NOT LINKED - {len(unlinked)} clubs, whose sheets say fixtures are unavailable")
    by = Counter((c["country"], c["tier"]) for c in unlinked)
    for (country, tier), n in sorted(by.items(), key=lambda x: (x[0][0], x[0][1] or 99)):
        p(f"  {country} tier {tier}: {n}")
    p("  (The Romanian ones are expected: football-data.org's free tier carries no")
    p("   Romanian competition. Most German tier-4 ones are too: OpenLigaDB has the")
    p("   Regionalliga Nord and Nordost only. Tier 1-3 German clubs listed here are")
    p("   the ones worth a look, and are named below.)")
    for c in sorted(unlinked, key=lambda c: (c["country"], c["tier"] or 99, c["name"])):
        if c["country"] == "DE" and (c["tier"] or 99) <= 3:
            p(f"    ! DE t{c['tier']} {c['name']} {c['id']}")
    p()
    if by_venue:
        p(f"SETTLED BY VENUE - {len(by_venue)} (the name matched several clubs, one ground agreed)")
        for t, c, cands in by_venue:
            p(f"  {t['source']} {t['teamId']} {team_label(t)} -> {c['name']} {c['id']} "
              f"(candidates {', '.join(cands)})")
        p()
    counts = Counter(r["_verdict"] for r in reviews)
    p(f"FOR A PERSON TO JUDGE - {REVIEW_FILE}, {len(reviews)} rows")
    for v, n in sorted(counts.items()):
        p(f"  {v}: {n}")
    for r in reviews:
        if r["_verdict"] in ("ambiguous-team", "ambiguous-club", "country-unknown",
                             "cross-country-blocked", "venue-disagrees"):
            who = r["teamName"] or r["clubName"]
            p(f"  [{r['_verdict']}] {r['source']} {r['teamId']} {who} -> {r['candidates']}")
    p("  unmatched-team rows are German fixture teams with no club on the map. Most")
    p("  are lower-league DFB-Pokal sides the map does not carry; where a candidate")
    p("  sharing a word is listed, it is a pointer and not a proposal.")
    for r in reviews:
        if r["_verdict"] == "unmatched-team" and r["candidates"]:
            p(f"    {r['source']} {r['teamId']} {r['teamName']}  ?  {r['candidates']}")
    p()
    p(f"HAND CORRECTIONS - {MANUAL_FILE}: {len(manual)} row(s) accepted")
    for row, outcome in applied:
        p(f"  line {row['line']}: {row['action']} {row['source']} {row['teamId']} -> "
          f"{row['clubQid']} {clubs[row['clubQid']]['name']}: {outcome}")
    p()
    p(f"TICKETS - {TICKETS_FILE}, joined to the map by clubQid (exact, no name matching)")
    for t in tickets:
        state = "on the map" if t["onMap"] else "NOT on the map - the sheet cannot show it"
        p(f"  line {t['line']}: {t['qid']} {t['club']} ({t['team']}, {t['country'] or '-'}): {state}")
        for n in t["notes"]:
            p(f"      ! {n}")
    if problems:
        p()
        for x in problems:
            p("  ! " + x)
    p("=" * 74)


if __name__ == "__main__":
    main()
