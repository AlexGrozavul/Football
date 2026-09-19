#!/usr/bin/env python3
"""
check_tickets.py -- read-back and validation for the three ticket files.

    data/club-tickets.csv         who may buy and how the club allocates
    data/club-ticket-windows.csv  when a recurring window tends to open
    data/club-ticket-prices.csv   face values and observed resale prices

These three files were written by hand and, until this tool existed,
nothing read them at all. So a typo in a vocabulary column - "inferrred"
for "inferred", "face_value" for "face-value" - sat in the file looking
exactly like a checked fact, and the read-back convention this project
relies on was not honoured for them.

This tool never writes to any of the three files. It reads them, prints
back what it understood, and complains. Nothing here corrects anything:
a rejected row is named with its line number and left alone, because the
fix belongs in the file, not in the code.

It exits 1 when there is a problem, so a workflow step shows red instead
of a green tick over a broken file.

Usage:  python3 tools/check_tickets.py [--full]

        --full prints every note in its entirety. Without it a note is
        shown as its first and last 60 characters plus a length, which
        is enough to see that a note is the one you wrote - the comma
        bug that truncates one is caught by the overflow check below
        rather than by reading the text.


TWO KINDS OF VOCABULARY, AND THE DIFFERENCE MATTERS
---------------------------------------------------

CLOSED vocabularies are the ones CLAUDE.md actually lists. A value that
is not on the list is a typo or a misunderstanding, so the row is
REJECTED and the allowed values are printed. These are dateSource,
basis, cutoff, kind and priceBasis.

OPEN vocabularies are the columns where nobody has written down what the
allowed values are, because so far there is one club in the file and
whatever it needed is all that exists. Inventing a closed list for them
would mean rejecting the first legitimate value a second club needs. So
the tool holds the values currently in use, REPORTS anything new, and
keeps the row. A typo is by definition a new value, so it still gets
caught; a real new value gets caught too, and the remedy is to add it to
the list in this file, which is a deliberate act rather than a silent
one.

The open lists live in KNOWN below. They are seeded from the FC Bayern
rows and from nothing else, and that is the honest state of them.
"""

import csv
import datetime
import os
import re
import sys

# ---------------------------------------------------------------- config

TICKETS_FILE = "data/club-tickets.csv"
WINDOWS_FILE = "data/club-ticket-windows.csv"
PRICES_FILE = "data/club-ticket-prices.csv"

# ------------------------------------------------------------- csv safety

# The same guard as fetch_clubs.py, for the same reason. csv.DictReader
# hands back any value past the last column under a single "rest" key,
# and left at its default that key is None - so a dictionary built from
# the row throws the overflow away without a word. That is what cut two
# notes in half before anyone noticed. An object() is used rather than a
# string so no column name, present or future, can collide with it.
OVERFLOW = object()


def _s(v):
    return (v or "").strip()


def _wrap(text, width=66, indent=""):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(indent + line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(indent + line)
    return lines


# --------------------------------------------------------- the schemas

# required: the row is rejected without it.
# optional: allowed, checked if present.
SCHEMA = {
    TICKETS_FILE: {
        "required": ["clubQid", "club", "team"],
        "optional": ["ticketUrl", "access", "salesModel", "requestTypes",
                     "cutoff", "closesEarly", "demand", "resale", "checked",
                     "source", "note"],
        # One row per club per team.
        "key": ["clubQid", "team"],
    },
    WINDOWS_FILE: {
        # dateSource and basis are required because CLAUDE.md says every
        # window row carries both: one says how much to trust the date,
        # the other says where the pattern came from, and collapsing them
        # loses exactly the distinction that matters.
        "required": ["clubQid", "club", "team", "window", "opensEstimate",
                     "estimateFor", "dateSource", "basis"],
        "optional": ["label", "pastCycle", "checked", "source", "note"],
        # One row per club per team per window.
        "key": ["clubQid", "team", "window"],
    },
    PRICES_FILE: {
        "required": ["clubQid", "club", "team", "season", "competition",
                     "stage", "kind", "category", "price", "currency"],
        "optional": ["opponentTier", "placeType", "priceBasis", "checked",
                     "source", "note"],
        # The key has been one column short TWICE, and both times the
        # file already held the proof before anyone noticed.
        #
        # kind was the first. CLAUDE.md described this file as one row
        # per club per team per season per competition per stage per
        # category, and the FC Bayern rows carried a face value AND an
        # observed resale price for the same Bundesliga category 1 seat.
        # Those are two different facts about one seat and both belong
        # in the file, so kind is part of what identifies a row.
        #
        # opponentTier was the second, and it was found the same way.
        # The club's own price page carries TWO Champions League
        # league-phase tables side by side - one for the strongest
        # visitor, one for the rest - same competition, same stage, same
        # categories, different prices. Without this column the second
        # table is not a second fact, it is a duplicate key, and the
        # checker would have thrown away whichever one was written
        # second. A blank cell means the club publishes one price for
        # that row's stage, which is the ordinary case.
        #
        # Two observations of the same category are also a real thing -
        # a price somebody saw twice, at two prices - so a duplicate
        # among resale-observed rows is reported rather than rejected.
        # Two face values for one category is a plain mistake and is
        # rejected: a category has one published price.
        "key": ["clubQid", "team", "season", "competition", "stage",
                "category", "kind", "opponentTier"],
    },
}

# ---- closed vocabularies: from CLAUDE.md, a row with anything else is
#      rejected.
CLOSED = {
    (WINDOWS_FILE, "dateSource"): ["confirmed", "inferred", "disputed"],
    (WINDOWS_FILE, "basis"): ["published", "observed-past-cycle",
                              "user-supplied", "unknown"],
    (TICKETS_FILE, "cutoff"): ["stated", "none", "unknown"],
    (PRICES_FILE, "kind"): ["face-value", "resale-observed"],
    # incl-vat-excl-fees is the one German consumer price pages actually
    # quote: the price includes VAT, because the Preisangabenverordnung
    # requires a consumer price to, and the booking and system fees are
    # added on top at checkout. Neither of the two values this list
    # started with can say that, and both of them say something false
    # about the FC Bayern rows - see CLAUDE.md.
    (PRICES_FILE, "priceBasis"): ["excl-vat-fees", "incl-vat-fees",
                                  "incl-vat-excl-fees", "unknown"],
}

# ---- open vocabularies: values currently in use. Anything else is
#      reported and the row is kept. Add a value here when a real one
#      turns up; do not add one to silence a typo.
KNOWN = {
    (TICKETS_FILE, "team"): ["men"],
    (WINDOWS_FILE, "team"): ["men"],
    (PRICES_FILE, "team"): ["men"],
    (TICKETS_FILE, "access"): ["members-only"],
    (TICKETS_FILE, "salesModel"): ["request-then-lottery"],
    (TICKETS_FILE, "closesEarly"): ["yes", "no", "unknown",
                                    "yes-when-overbooked"],
    (TICKETS_FILE, "demand"): ["overbooked-usually"],
    (TICKETS_FILE, "resale"): ["official-members-only"],
    (WINDOWS_FILE, "window"): ["season-ticket-renewal",
                               "bundesliga-single-match",
                               "bundesliga-away-block",
                               "away-season-ticket",
                               "ucl-league-phase"],
    (PRICES_FILE, "competition"): ["bundesliga", "dfb-pokal", "ucl"],
    (PRICES_FILE, "stage"): ["regular", "early-rounds", "league-phase"],
    (PRICES_FILE, "category"): ["1", "2", "3", "4", "5"],
    (PRICES_FILE, "opponentTier"): ["top-opponent", "standard-opponent"],
    (PRICES_FILE, "placeType"): ["standing", "seat"],
}

# requestTypes is a semicolon-separated list, so its tokens are checked
# one at a time rather than the whole cell.
KNOWN_REQUEST_TYPES = ["home", "away", "ucl", "pokal"]

# ---- the columns that must never hold a date.
#
# CLAUDE.md: "No cell in this file ever holds a date." That is about the
# rule-bearing cells, not about checked (which is a date by design), not
# about source (a URL may carry a year), and not about note (prose that
# legitimately discusses past dates). So the check is aimed at the cells
# that state a rule.
NO_DATE_COLUMNS = {
    TICKETS_FILE: ["access", "salesModel", "requestTypes", "cutoff",
                   "closesEarly", "demand", "resale"],
    # opensEstimate is the important one. It is deliberately loose text -
    # "late June", "after the UCL draw" - because there is no format that
    # turns "late June" into a day, and rounding it to one is the exact
    # failure rule 1 exists to prevent.
    WINDOWS_FILE: ["opensEstimate", "label"],
    PRICES_FILE: ["competition", "stage", "kind", "opponentTier",
                  "category", "placeType", "priceBasis"],
}

MONTHS = ("januar|february|februar|january|märz|maerz|march|april|mai|may|"
          "juni|june|juli|july|august|september|oktober|october|november|"
          "dezember|december|jan|feb|mär|mar|apr|jun|jul|aug|sep|okt|oct|"
          "nov|dez|dec")

# A DAY is a deadline. A month is a pattern. Only day-level precision is
# refused, which is why "late June" passes and "30 June" does not.
DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),                     # 2026-06-30
    re.compile(r"\b\d{1,2}\.\s?\d{1,2}\.\s?\d{2,4}\b"),       # 30.06.2026
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),               # 30/06/2026
    re.compile(r"\b\d{1,2}\.?\s+(" + MONTHS + r")\b", re.I),  # 30 June
    re.compile(r"\b(" + MONTHS + r")\s+\d{1,2}\b", re.I),     # June 30
]

SEASON_RE = re.compile(r"^\d{4}-\d{2}$")       # 2026-27
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
QID_RE = re.compile(r"^Q\d+$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


def looks_like_a_date(value):
    for pattern in DATE_PATTERNS:
        found = pattern.search(value)
        if found:
            return found.group(0)
    return None


def overflow_problem(path, line, columns, extra):
    """
    The complaint for a row carrying more values than the header has
    columns. Word for word the same shape as fetch_clubs.py's, because
    it is the same mistake and the same remedy.
    """
    lost = ", ".join(repr(_s(v)) for v in extra)
    return (f"{path} line {line}: this row has {columns + len(extra)} values but "
            f"the header has {columns} columns, so {lost} would be thrown away. "
            f"A comma inside a cell splits that cell in two - put double quotes "
            f'round the whole cell ("like, this") to keep the comma. Row ignored.')


# ------------------------------------------------------------- the reader

def read_file(path, today):
    """
    Returns (rows, problems, notices).

    rows     accepted rows, each with its line number under "_line"
    problems things that rejected a row, or that stop the file being read
    notices  things reported without rejecting anything
    """
    rows, problems, notices = [], [], []
    schema = SCHEMA[path]
    required, optional = schema["required"], schema["optional"]

    if not os.path.exists(path):
        problems.append(f"{path}: file not found")
        return rows, problems, notices

    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, restkey=OVERFLOW)
        if not reader.fieldnames:
            problems.append(f"{path} is empty - it needs a header row")
            return rows, problems, notices

        headers = [_s(h) for h in reader.fieldnames]
        missing = [h for h in required if h not in headers]
        if missing:
            problems.append(f"{path} line 1: missing required column(s) "
                            f"{', '.join(repr(m) for m in missing)}. "
                            f"Nothing in this file was read.")
            return rows, problems, notices
        for h in headers:
            if h and h not in required + optional:
                notices.append(f"{path} line 1: column {h!r} is not one this "
                               f"tool knows about. It is read back below but "
                               f"nothing checks it.")

        seen_keys = {}
        for raw in reader:
            line = reader.line_num
            extra = raw.pop(OVERFLOW, None)
            if extra:
                problems.append(overflow_problem(
                    path, line, len(reader.fieldnames), extra))
                continue
            row = {_s(k): _s(v) for k, v in raw.items() if k is not None}
            if not any(row.values()):
                continue

            rejected = False

            # ---- required cells
            for field in required:
                if not row.get(field):
                    problems.append(f"{path} line {line}: {field} is required "
                                    f"and is empty. Row ignored.")
                    rejected = True
            if rejected:
                continue

            # ---- club Q-id
            if not QID_RE.match(row["clubQid"]):
                problems.append(f"{path} line {line}: clubQid "
                                f"{row['clubQid']!r} is not a Q-id. Row ignored.")
                continue

            # ---- closed vocabularies
            for field in headers:
                allowed = CLOSED.get((path, field))
                if not allowed:
                    continue
                value = row.get(field, "")
                if not value:
                    continue
                if value not in allowed:
                    problems.append(
                        f"{path} line {line}: {field} is {value!r}, which is "
                        f"not one of {', '.join(allowed)}. Row ignored.")
                    rejected = True
            if rejected:
                continue

            # ---- no dates in the rule-bearing cells
            for field in NO_DATE_COLUMNS.get(path, []):
                value = row.get(field, "")
                if not value:
                    continue
                hit = looks_like_a_date(value)
                if hit:
                    problems.append(
                        f"{path} line {line}: {field} is {value!r}, which "
                        f"contains a date ({hit!r}). These files hold rules "
                        f"and patterns, never a deadline - a day-level date "
                        f"belongs in football-rules.json or "
                        f"fixtures-manual.csv, hand-written. A month on its "
                        f"own (\"late June\") is fine. Row ignored.")
                    rejected = True
            if rejected:
                continue

            # ---- per-file checks
            problem, notice = check_row(path, line, row, today)
            problems.extend(problem)
            # A rejected row's softer remarks are not worth printing -
            # they are about a row nobody is keeping, and they bury the
            # complaint that actually rejected it.
            if problem:
                continue
            notices.extend(notice)

            # ---- duplicate key
            key = tuple(row.get(k, "") for k in schema["key"])
            if key in seen_keys:
                repeatable = (path == PRICES_FILE
                              and row.get("kind") == "resale-observed")
                if repeatable:
                    notices.append(
                        f"{path} line {line}: a second resale-observed row for "
                        f"{' / '.join(key)}, the first on line {seen_keys[key]}. "
                        f"Two observations of one category are a real thing, so "
                        f"both are kept - but if this is the same sighting "
                        f"entered twice, one of them is a duplicate.")
                else:
                    problems.append(
                        f"{path} line {line}: this is a second row for "
                        f"{' / '.join(key)}, already given on line "
                        f"{seen_keys[key]}. This file holds one row per "
                        f"{' per '.join(schema['key'])}. Row ignored.")
                    continue
            else:
                seen_keys[key] = line

            # ---- open vocabularies: reported, never rejected
            for field in headers:
                known = KNOWN.get((path, field))
                if not known:
                    continue
                value = row.get(field, "")
                if value and value not in known:
                    extra_note = ""
                    if field == "team" and value.lower() != "men":
                        extra_note = (" CLAUDE.md rule 6 says men's football "
                                      "only, for now, so this row may not "
                                      "belong here at all.")
                    notices.append(
                        f"{path} line {line}: {field} is {value!r}, which this "
                        f"tool has not seen in this file before. Nothing is "
                        f"rejected - if it is a typo, fix the file; if it is "
                        f"real, add it to KNOWN in tools/check_tickets.py."
                        + extra_note)
            if path == TICKETS_FILE and row.get("requestTypes"):
                for token in row["requestTypes"].split(";"):
                    token = token.strip()
                    if token and token not in KNOWN_REQUEST_TYPES:
                        notices.append(
                            f"{path} line {line}: requestTypes contains "
                            f"{token!r}, which this tool has not seen before. "
                            f"Reported, not rejected.")

            row["_line"] = line
            rows.append(row)

    return rows, problems, notices


def check_row(path, line, row, today):
    """Checks that belong to one file only. Returns (problems, notices)."""
    problems, notices = [], []

    # ---- checked: an ISO date, and not in the future
    checked = row.get("checked", "")
    if checked:
        if not ISO_DATE_RE.match(checked):
            problems.append(f"{path} line {line}: checked is {checked!r}, "
                            f"which is not a YYYY-MM-DD date. Row ignored.")
        else:
            try:
                when = datetime.date.fromisoformat(checked)
                if when > today:
                    notices.append(f"{path} line {line}: checked is {checked}, "
                                   f"which is in the future. Reported, not "
                                   f"rejected.")
            except ValueError:
                problems.append(f"{path} line {line}: checked is {checked!r}, "
                                f"which is not a real date. Row ignored.")
    else:
        notices.append(f"{path} line {line}: checked is empty, so there is no "
                       f"record of when anyone last looked at this row.")

    # ---- urls
    for field in ("ticketUrl", "source"):
        value = row.get(field, "")
        if not value:
            continue
        for url in value.split(";"):
            url = url.strip()
            if url and not url.startswith(("http://", "https://")):
                notices.append(f"{path} line {line}: {field} contains "
                               f"{url!r}, which is not a URL. Reported, not "
                               f"rejected.")

    if path == WINDOWS_FILE:
        cycle = row.get("estimateFor", "")
        if not SEASON_RE.match(cycle):
            problems.append(
                f"{path} line {line}: estimateFor is {cycle!r}, which is not a "
                f"cycle like 2027-28. \"late June\" means nothing without the "
                f"cycle it is about. Row ignored.")

        # An estimate whose basis is a past cycle somebody read, with no
        # past cycle written down, is the one combination that cannot be
        # true. A blank pastCycle beside basis user-supplied is fine and
        # deliberate - that is the file admitting the pattern rests on
        # nothing written down.
        if row.get("basis") == "observed-past-cycle" and not row.get("pastCycle"):
            notices.append(
                f"{path} line {line}: basis is observed-past-cycle but "
                f"pastCycle is empty. An estimate reasoned from a past window "
                f"somebody read should say which window that was. Reported, "
                f"not rejected.")
        if row.get("dateSource") == "confirmed" and row.get("basis") not in ("published", ""):
            notices.append(
                f"{path} line {line}: dateSource is confirmed but basis is "
                f"{row.get('basis')!r}. Confirmed means a published source "
                f"said so. Reported, not rejected.")

    if path == PRICES_FILE:
        season = row.get("season", "")
        if not SEASON_RE.match(season):
            problems.append(
                f"{path} line {line}: season is {season!r}, which is not a "
                f"season like 2026-27. A face value without a season is a "
                f"wrong number waiting to happen. Row ignored.")

        price = row.get("price", "")
        try:
            value = float(price.replace(",", "."))
            if value <= 0:
                problems.append(f"{path} line {line}: price is {price!r}. "
                                f"Row ignored.")
        except ValueError:
            problems.append(f"{path} line {line}: price is {price!r}, which is "
                            f"not a number. Row ignored.")

        currency = row.get("currency", "")
        if not CURRENCY_RE.match(currency):
            problems.append(f"{path} line {line}: currency is {currency!r}, "
                            f"which is not a three-letter code like EUR. "
                            f"Row ignored.")

        # An observation is never written as though the club had stated
        # it, so a resale-observed row with priceBasis excl-vat-fees is
        # claiming to know something an observation cannot.
        if row.get("kind") == "resale-observed" and row.get("priceBasis") not in ("unknown", ""):
            notices.append(
                f"{path} line {line}: kind is resale-observed but priceBasis "
                f"is {row.get('priceBasis')!r}. A price somebody saw once "
                f"rarely says whether it was before or after VAT and fees. "
                f"Reported, not rejected.")

    return problems, notices


# ------------------------------------------------------------- read-back

def show_note(value, full):
    if not value:
        return ["(empty)"]
    if full or len(value) <= 130:
        return _wrap(value, width=64)
    head, tail = value[:60], value[-60:]
    return _wrap(f"{head} ... [{len(value)} characters] ... {tail}", width=64)


def read_back(path, rows, full):
    print()
    print(f"  {path}")
    if not rows:
        print("    no rows accepted")
        return
    for row in rows:
        print(f"    line {row['_line']}:")
        for field, value in row.items():
            if field == "_line":
                continue
            if field == "note":
                lines = show_note(value, full)
                print(f"      {field:14s} {lines[0]}")
                for line in lines[1:]:
                    print(f"      {'':14s} {line}")
            else:
                print(f"      {field:14s} {value if value else '(empty)'}")
        print()


# ------------------------------------------------------------------ main

def main():
    full = "--full" in sys.argv
    today = datetime.date.today()

    print("=" * 70)
    print("  Ticket files: read-back and checks")
    print("=" * 70)

    all_problems, all_notices, by_file = [], [], {}
    for path in (TICKETS_FILE, WINDOWS_FILE, PRICES_FILE):
        rows, problems, notices = read_file(path, today)
        by_file[path] = rows
        all_problems.extend(problems)
        all_notices.extend(notices)

    # ---- cross-file: a window or a price for a club with no ticket row
    known_clubs = {(r["clubQid"], r.get("team", "")) for r in by_file[TICKETS_FILE]}
    for path in (WINDOWS_FILE, PRICES_FILE):
        for row in by_file[path]:
            pair = (row["clubQid"], row.get("team", ""))
            if pair not in known_clubs:
                all_notices.append(
                    f"{path} line {row['_line']}: {row.get('club')} "
                    f"({pair[0]}, {pair[1]}) has no row in {TICKETS_FILE}, so "
                    f"nothing says who may buy or how the club allocates. "
                    f"Reported, not rejected.")

    # ---- the read-back
    print()
    print("READ-BACK - every accepted row, exactly as this tool understood it.")
    if not full:
        print("Notes are shortened; run with --full to print them whole.")
    for path in (TICKETS_FILE, WINDOWS_FILE, PRICES_FILE):
        read_back(path, by_file[path], full)

    # ---- the counts
    print("=" * 70)
    for path in (TICKETS_FILE, WINDOWS_FILE, PRICES_FILE):
        rejected = len([p for p in all_problems if p.startswith(path)])
        print(f"  {path}: {len(by_file[path])} row(s) accepted, "
              f"{rejected} problem(s)")

    # ---- what was reported but changed nothing
    if all_notices:
        print()
        print(f"REPORTED, NOTHING REJECTED ({len(all_notices)})")
        for notice in all_notices:
            for i, line in enumerate(_wrap(notice, width=66)):
                print(("  - " if i == 0 else "    ") + line)

    # ---- what was rejected
    if all_problems:
        print()
        print(f"PROBLEMS ({len(all_problems)}) - each row named here was "
              f"IGNORED, not corrected.")
        for problem in all_problems:
            for i, line in enumerate(_wrap(problem, width=66)):
                print(("  ! " if i == 0 else "    ") + line)
        print()
        for line in _wrap(
                "Nothing in this tool writes to any of the three files. Fix "
                "the file and run it again."):
            print("  " + line)
        print("=" * 70)
        return 1

    print()
    print("  No problems. Every row was read.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
