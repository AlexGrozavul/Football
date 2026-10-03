#!/usr/bin/env python3
"""
check_derbies.py -- read-back and checks for data/derbies.csv.

data/derbies.csv is hand-written: one row per derby, two clubs by their
Wikidata Q-ids, what kind of derby it is, and a source that NAMES the
rivalry. The map tab's Derbies panel reads it. Nothing writes to it.

This tool never writes to it either. It reads it, prints back every row
exactly as understood, and complains. A rejected row is named with its
line number and left alone, because the fix belongs in the file. It
exits 1 when a row was rejected, so a workflow step shows red rather
than a green tick over a broken file.

Usage:  python3 tools/check_derbies.py [--full]

        --full prints every note in full. Without it a long note is shown
        as its start and end plus a length.


WHAT REJECTS A ROW
------------------
- a required cell left empty: name, clubA, clubB, kind, source
- a source that is not a URL. Rule 2 of this file: no derby goes in
  without a published source that names it. A row with no source is
  exactly the plausible guess CLAUDE.md forbids.
- a club cell that is not a Q-id, or the same Q-id on both sides
- a Q-id that is in no data/clubs/*.json, UNLESS the row's offMap cell
  names that side. A Q-id nobody can find on the map is most likely a
  typo, and a typo that quietly reads as "not on the map yet" would hide
  forever. Keeping a row whose club is genuinely off the map - relegated
  below the tiers this project tracks, or dropped by a gate - is
  allowed, but it has to be said out loud: offMap reads "B: League One;
  GB tracks tiers 1-2" (A, B, or A+B, a colon, the reason). Decided by
  Alexandru, 2026-10-03.
- an offMap cell that does not start with A:, B: or A+B:
- a second row for the same pair of clubs, either way round
- a row with more values than the header has columns (an unquoted comma)
- a rulesId that is not an id in football-rules.json's bucketList

WHAT IS REPORTED AND KEPT
-------------------------
- a kind other than city, regional or historic. Those three are the
  kinds this file was designed with; a new one is reported so it is a
  deliberate addition, never a silent one.
- an offMap marker on a side whose club IS on the map now - the club has
  arrived, and the marker should go
- a clubAName / clubBName that differs from the map's name for that Q-id
  (the map's name is shown in the panel; the hand-written one is what
  you meant)
- a derby in which neither club is at tier 1 or 2 (out of the scope the
  file was built for)
- a derby whose two clubs are in DIFFERENT divisions this season: they
  can only meet in a cup, so it is probably not played this season. The
  panel says so too.
- a club with no fixture source, from data/clubs/fixture-links.json
- every derby-shaped entry in football-rules.json's bucketList that no
  row here points at with rulesId, and every rulesId pair whose titles
  should be compared by eye. football-rules.json is never written.
"""

import csv
import glob
import json
import os
import re
import sys

DERBIES_FILE = "data/derbies.csv"
CLUBS_GLOB = "data/clubs/??.json"
LINKS_FILE = "data/clubs/fixture-links.json"
TIERS_FILE = "data/league-tiers.csv"
RULES_FILE = "data/football-rules.json"

REQUIRED = ["name", "clubA", "clubB", "kind", "source"]
OPTIONAL = ["clubAName", "clubBName", "offMap", "rulesId", "note"]
KINDS = ["city", "regional", "historic"]

QID_RE = re.compile(r"^Q[1-9][0-9]*$")
URL_RE = re.compile(r"^https?://\S+$")
OFFMAP_RE = re.compile(r"^(A\+B|A|B)\s*:\s*(\S.*)$")

# Same guard as every other reader in tools/: a value past the last
# column is a comma that was meant to be inside a cell.
OVERFLOW = object()


def _s(v):
    return (v or "").strip()


def _wrap(text, width=66):
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


def load_clubs():
    clubs = {}
    for path in sorted(glob.glob(CLUBS_GLOB)):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        country = data.get("country") or os.path.basename(path)[:2]
        for c in data.get("clubs", []):
            clubs[c["id"]] = {"name": c.get("name"), "tier": c.get("tier"),
                              "country": c.get("country") or country,
                              "leagues": c.get("leagues") or [],
                              "lat": c.get("lat"), "lon": c.get("lon")}
    return clubs


def load_links():
    if not os.path.exists(LINKS_FILE):
        return None
    with open(LINKS_FILE, encoding="utf-8") as fh:
        return json.load(fh).get("clubs", {})


def load_tiers():
    with open(TIERS_FILE, encoding="utf-8-sig", newline="") as fh:
        return [{k: _s(v) for k, v in r.items()} for r in csv.DictReader(fh)]


def load_rules():
    if not os.path.exists(RULES_FILE):
        return None
    with open(RULES_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def division(club, tiers):
    """(country, tier, league label or None). The league is named only
    where the country maps exactly one league at that tier, or the club's
    own tags name exactly one - the same rule the club sheet uses."""
    at = [t for t in tiers if t["country"] == club["country"]
          and t["tier"] == str(club["tier"])]
    own = [t for t in at if t["leagueQid"] in club["leagues"]]
    if len(own) == 1:
        return own[0]["label"]
    if len(at) == 1:
        return at[0]["label"]
    return None


def same_division(a, b, tiers):
    """'same', 'different' or 'unknown', with a reason."""
    if a["country"] != b["country"]:
        return "different", f"{a['country']} and {b['country']} pyramids"
    if a["tier"] != b["tier"]:
        return "different", f"tier {a['tier']} and tier {b['tier']}"
    la, lb = division(a, tiers), division(b, tiers)
    if la and lb:
        if la == lb:
            return "same", la
        return "different", f"{la} and {lb}"
    # Romania's Liga III is one Wikidata item for several series, and
    # Germany's tier 4 tags are often stale: the file cannot say.
    return "unknown", (f"both tier {a['tier']} in {a['country']}, but nothing "
                       f"here says whether they are in the same division")


def main():
    full = "--full" in sys.argv[1:]
    clubs = load_clubs()
    links = load_links()
    tiers = load_tiers()
    rules = load_rules()
    bucket = {b.get("id"): b for b in (rules or {}).get("bucketList", [])}

    problems, notices, rows = [], [], []

    print("=" * 70)
    print(f"{DERBIES_FILE} - read back exactly as understood")
    print(f"{len(clubs)} clubs on the map in {CLUBS_GLOB}; "
          f"{'no ' + LINKS_FILE if links is None else str(len(links)) + ' with a fixture link'}")
    print("=" * 70)

    if not os.path.exists(DERBIES_FILE):
        print(f"  ! {DERBIES_FILE}: file not found")
        return 1

    with open(DERBIES_FILE, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, restkey=OVERFLOW)
        headers = [_s(h) for h in (reader.fieldnames or [])]
        missing = [h for h in REQUIRED if h not in headers]
        if missing:
            print(f"  ! {DERBIES_FILE} line 1: missing required column(s) "
                  f"{', '.join(missing)}. Nothing in this file was read.")
            return 1
        for h in headers:
            if h and h not in REQUIRED + OPTIONAL:
                notices.append(f"line 1: column {h!r} is not one this tool "
                               f"knows. It is ignored.")

        seen_pairs = {}
        for raw in reader:
            line = reader.line_num
            extra = raw.pop(OVERFLOW, None)
            if extra:
                problems.append(
                    f"line {line}: {len(extra)} more value(s) than the header "
                    f"has columns, starting {extra[0]!r}. A comma inside a "
                    f'cell splits it in two - quote the whole cell ("a, b"). '
                    f"Row ignored.")
                continue
            row = {_s(k): _s(v) for k, v in raw.items() if k is not None}
            if not any(row.values()):
                continue
            label = row.get("name") or "(no name)"

            empty = [f for f in REQUIRED if not row.get(f)]
            if empty:
                why = (" A derby without a source naming it is a guess, and "
                       "this file holds none." if "source" in empty else "")
                problems.append(f"line {line} ({label}): {', '.join(empty)} "
                                f"empty.{why} Row ignored.")
                continue

            urls = [u.strip() for u in row["source"].split(";") if u.strip()]
            bad = [u for u in urls if not URL_RE.match(u)]
            if not urls or bad:
                problems.append(f"line {line} ({label}): source {bad[0] if bad else row['source']!r} "
                                f"is not a URL. The source has to be a page "
                                f"that names the rivalry. Row ignored.")
                continue

            a, b = row["clubA"], row["clubB"]
            notq = [q for q in (a, b) if not QID_RE.match(q)]
            if notq:
                problems.append(f"line {line} ({label}): {notq[0]!r} is not a "
                                f"Q-id. Row ignored.")
                continue
            if a == b:
                problems.append(f"line {line} ({label}): clubA and clubB are "
                                f"both {a}. Row ignored.")
                continue

            off_sides, off_reason = set(), ""
            if row.get("offMap"):
                m = OFFMAP_RE.match(row["offMap"])
                if not m:
                    problems.append(
                        f"line {line} ({label}): offMap is {row['offMap']!r}. "
                        f"It must start A:, B: or A+B: and then say why the "
                        f"club is not on the map. Row ignored.")
                    continue
                off_sides = {"A", "B"} if m.group(1) == "A+B" else {m.group(1)}
                off_reason = m.group(2)

            reject = False
            for side, q in (("A", a), ("B", b)):
                if q not in clubs and side not in off_sides:
                    problems.append(
                        f"line {line} ({label}): club{side} {q} is in no "
                        f"{CLUBS_GLOB} file. If that is a typo, fix it. If the "
                        f"club really is off the map, say so in offMap "
                        f"(\"{side}: why\"). Row ignored.")
                    reject = True
                if q in clubs and side in off_sides:
                    notices.append(
                        f"line {line} ({label}): offMap names side {side}, but "
                        f"{q} {clubs[q]['name']} is on the map now. The marker "
                        f"can go.")
            if reject:
                continue

            if row.get("rulesId") and rules is not None and row["rulesId"] not in bucket:
                problems.append(f"line {line} ({label}): rulesId "
                                f"{row['rulesId']!r} is not an id in "
                                f"{RULES_FILE}'s bucketList. Row ignored.")
                continue

            pair = frozenset((a, b))
            if pair in seen_pairs:
                problems.append(f"line {line} ({label}): a second row for "
                                f"{a} and {b}, already on line "
                                f"{seen_pairs[pair]}. Row ignored.")
                continue
            seen_pairs[pair] = line

            if row["kind"] not in KINDS:
                notices.append(f"line {line} ({label}): kind is "
                               f"{row['kind']!r}, not one of "
                               f"{', '.join(KINDS)}. Kept. If it is real, add "
                               f"it to KINDS in tools/check_derbies.py and to "
                               f"the panel.")

            for side, q in (("A", a), ("B", b)):
                given = row.get(f"club{side}Name")
                if given and q in clubs and clubs[q]["name"] != given:
                    notices.append(f"line {line} ({label}): club{side}Name is "
                                   f"{given!r}; the map calls {q} "
                                   f"{clubs[q]['name']!r}. Kept - the panel "
                                   f"shows the map's name.")
                if not given and q not in clubs:
                    notices.append(f"line {line} ({label}): club{side} {q} is "
                                   f"off the map and has no club{side}Name, so "
                                   f"nothing names it in the read-back.")

            row["_line"] = line
            row["_off"] = off_sides
            row["_offReason"] = off_reason
            rows.append(row)

    # ---------------------------------------------------- the read-back
    def side(q, nm):
        c = clubs.get(q)
        if c:
            return f"{q} {c['name']} [{c['country']} tier {c['tier']}]"
        return f"{q} {nm or '(no name given)'} [NOT ON THE MAP]"

    def note_text(v):
        if full or len(v) <= 160:
            return v
        return f"{v[:70]} ... {v[-60:]} ({len(v)} chars)"

    def fixture_side(q):
        if q not in clubs:
            return "off the map"
        if links is None:
            return "fixture links file missing"
        e = links.get(q)
        if not e:
            return "no fixture source"
        return "; ".join(
            f"{l['source']} {l['teamId']} ({', '.join(c['code'] for c in l['competitions'])})"
            for l in e["links"])

    by_country = {}
    on_map_both, src_both, out_of_scope, cross_div = [], [], [], []
    no_source = []
    for r in rows:
        a, b = r["clubA"], r["clubB"]
        ca, cb = clubs.get(a), clubs.get(b)
        countries = sorted({c["country"] for c in (ca, cb) if c}) or ["(off map)"]
        country = "/".join(countries)
        by_country.setdefault(country, []).append(r)

        print()
        print(f"line {r['_line']}: {r['name']}  [{r['kind']}]")
        print(f"  A  {side(a, r.get('clubAName'))}")
        print(f"     fixtures: {fixture_side(a)}")
        print(f"  B  {side(b, r.get('clubBName'))}")
        print(f"     fixtures: {fixture_side(b)}")
        for u in r["source"].split(";"):
            print(f"  source  {u.strip()}")
        if r["_off"]:
            print(f"  offMap  {'+'.join(sorted(r['_off']))}: {r['_offReason']}")
        if r.get("rulesId"):
            print(f"  rulesId {r['rulesId']} -> football-rules.json: "
                  f"{bucket.get(r['rulesId'], {}).get('title')!r}")
        if r.get("note"):
            for i, t in enumerate(_wrap(note_text(r["note"]), 62)):
                print(("  note    " if i == 0 else "          ") + t)

        if ca and cb:
            on_map_both.append(r)
            verdict, why = same_division(ca, cb, tiers)
            if verdict == "same":
                print(f"  league  same division ({why}): a league meeting is due "
                      f"this season")
            elif verdict == "different":
                print(f"  league  DIFFERENT divisions ({why}): they can only "
                      f"meet in a cup, so probably not played this season")
                cross_div.append(r)
            else:
                print(f"  league  not known: {why}")
            if links is not None and links.get(a) and links.get(b):
                src_both.append(r)
            else:
                no_source.append(r)
        if not any(c and c["tier"] in (1, 2) for c in (ca, cb)):
            out_of_scope.append(r)
            notices.append(f"line {r['_line']} ({r['name']}): neither club "
                           f"on the map is at tier 1 or 2. This file was "
                           f"built for tier 1-2 derbies; kept.")

    # -------------------------------------------- football-rules.json
    print()
    print("=" * 70)
    print(f"CROSS-CHECK with {RULES_FILE} (read only, never written)")
    if rules is None:
        print("  the file was not found")
    else:
        pointed = {r["rulesId"]: r for r in rows if r.get("rulesId")}
        derbyish = [b for b in rules.get("bucketList", [])
                    if b.get("trueDerby") is not None
                    or "derby" in (b.get("title") or "").lower()]
        for b in derbyish:
            r = pointed.get(b.get("id"))
            if r:
                print(f"  = {b['id']}: {b.get('title')!r}")
                print(f"      line {r['_line']}: {r['name']!r}, "
                      f"{side(r['clubA'], r.get('clubAName'))} v "
                      f"{side(r['clubB'], r.get('clubBName'))}")
            else:
                print(f"  - {b['id']}: {b.get('title')!r} - no row here "
                      f"points at it")

    # ----------------------------------------------------- the counts
    print()
    print("=" * 70)
    print("PER COUNTRY")
    for country in sorted(by_country):
        rs = by_country[country]
        both = [r for r in rs if r in on_map_both]
        src = [r for r in rs if r in src_both]
        print(f"  {country:10} {len(rs):3} derbies, {len(both):3} with both "
              f"clubs on the map, {len(src):3} with a fixture source on both "
              f"sides")
    print(f"  {'total':10} {len(rows):3} derbies, {len(on_map_both):3} with both "
          f"clubs on the map, {len(src_both):3} with a fixture source on both sides")
    if cross_div:
        print()
        print(f"DIFFERENT DIVISIONS THIS SEASON ({len(cross_div)}) - cup meetings only:")
        for r in cross_div:
            print(f"  line {r['_line']}: {r['name']}")
    off = [r for r in rows if r["_off"]]
    if off:
        print()
        print(f"NOT ON THE MAP YET ({len(off)}) - kept, left out of the panel "
              f"until both clubs are on it:")
        for r in off:
            print(f"  line {r['_line']}: {r['name']} - "
                  f"{'+'.join(sorted(r['_off']))}: {r['_offReason']}")
    if no_source:
        print()
        print(f"BOTH ON THE MAP, NO FIXTURE SOURCE ON ONE OR BOTH SIDES "
              f"({len(no_source)}):")
        for r in no_source:
            missing = [clubs[q]["name"] for q in (r["clubA"], r["clubB"])
                       if not (links or {}).get(q)]
            print(f"  line {r['_line']}: {r['name']} - none for "
                  f"{' and '.join(missing)}")

    if notices:
        print()
        print(f"REPORTED, NOTHING REJECTED ({len(notices)})")
        for n in notices:
            for i, t in enumerate(_wrap(n)):
                print(("  - " if i == 0 else "    ") + t)

    if problems:
        print()
        print(f"PROBLEMS ({len(problems)}) - each row named here was IGNORED, "
              f"not corrected.")
        for p in problems:
            for i, t in enumerate(_wrap(f"{DERBIES_FILE} {p}")):
                print(("  ! " if i == 0 else "    ") + t)
        print("=" * 70)
        return 1

    print()
    print(f"  No problems. {len(rows)} row(s) read.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
