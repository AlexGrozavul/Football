#!/usr/bin/env python3
"""
check_tickets.py -- read-back and validation for the ticket files.

    data/club-tickets.csv         who may buy and how the club allocates
    data/club-ticket-windows.csv  when a recurring window tends to open
    data/club-ticket-prices.csv   face values and observed resale prices
    data/club-ticket-phases.csv   the phases of a window, in order
    data/club-ticket-rules.csv    one sourced fact per row, general or
                                  a derby override
    data/club-ticket-demand.csv   sell-out track record, one row a season
    data/ticket-sources.csv       every citation, one row each

The first three were written by hand and, until this tool existed,
nothing read them at all. So a typo in a vocabulary column - "inferrred"
for "inferred", "face_value" for "face-value" - sat in the file looking
exactly like a checked fact, and the read-back convention this project
relies on was not honoured for them. The other four were added on
2026-09-23 for the derby PDF, whose structure the first three could not
hold without losing something - see CLAUDE.md.

This tool never writes to any of these files. It reads them, prints
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
basis, cutoff, kind, priceBasis, and since 2026-09-23 confidence, scope
and urlComplete.

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
rows and, since 2026-09-23, the 1. FC Nürnberg and Inter rows from the
derby PDF - three clubs, and nothing else. That is the honest state of
them.
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
# Added 2026-09-23 for the derby PDF, whose structure the first three
# could not hold without losing something. See CLAUDE.md.
PHASES_FILE = "data/club-ticket-phases.csv"
RULES_FILE = "data/club-ticket-rules.csv"
DEMAND_FILE = "data/club-ticket-demand.csv"
SOURCES_FILE = "data/ticket-sources.csv"

# Sources first, because every other file's sourceRefs are resolved
# against it; windows before phases, because a phase must name a window
# that exists.
FILES = [SOURCES_FILE, TICKETS_FILE, WINDOWS_FILE, PHASES_FILE,
         PRICES_FILE, RULES_FILE, DEMAND_FILE]

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
                     "cutoff", "closesEarly", "demand", "resale",
                     # updateTracking: how the club tells people a sale is
                     # coming. minorEligibility: whether an under-18 can
                     # buy. Both are standing facts about the club, which
                     # is why they are columns here and not rules rows.
                     "updateTracking", "minorEligibility",
                     "checked", "source", "note", "ref", "sourceRefs"],
        # One row per club per team. A derby is not a second row here: a
        # derby override is a scope in club-ticket-rules.csv.
        "key": ["clubQid", "team"],
    },
    WINDOWS_FILE: {
        # dateSource and basis are required because CLAUDE.md says every
        # window row carries both: one says how much to trust the date,
        # the other says where the pattern came from, and collapsing them
        # loses exactly the distinction that matters.
        "required": ["clubQid", "club", "team", "window", "opensEstimate",
                     "estimateFor", "dateSource", "basis"],
        "optional": ["label", "pastCycle", "checked", "source", "note",
                     "scope", "opponentQid", "ref", "sourceRefs"],
        # One row per club per team per window per opponent. opponentQid
        # is in the key so a club with two derbies can have a
        # derby-home window for each.
        "key": ["clubQid", "team", "window", "opponentQid"],
    },
    PHASES_FILE: {
        # One row per phase of a window, in order. Phase 1 opens first.
        # The one day-level date a phase may carry is in pastCycle, and
        # it is a PAST window with a source - exactly what pastCycle
        # already means in the windows file. A future phase date is
        # never written here; rule 1 puts that in football-rules.json.
        "required": ["clubQid", "club", "team", "window", "phase", "buyers",
                     "confidence", "basis"],
        "optional": ["eligibility", "opensRelative", "pastCycle",
                     "pastCycleFor", "maxTickets", "relevance", "ref",
                     "sourceRefs", "source", "checked", "note"],
        "key": ["clubQid", "team", "window", "phase"],
    },
    RULES_FILE: {
        # One fact per row, each with its own confidence and its own
        # sources. scope says whether the fact is the club's general
        # rule or an override for one fixture; see LAYERING in main().
        "required": ["clubQid", "club", "team", "topic", "rule",
                     "confidence", "basis"],
        "optional": ["scope", "opponentQid", "season", "ref", "sourceRefs",
                     "source", "checked", "note"],
        # ref is in the key because one PDF item can be split into two
        # topics, and two items can share a topic.
        "key": ["clubQid", "team", "scope", "opponentQid", "topic", "ref",
                "season"],
    },
    DEMAND_FILE: {
        # A sell-out track record: one row per club per fixture per
        # season, rather than one estimate standing in for all of them.
        "required": ["clubQid", "club", "team", "season", "outcome",
                     "confidence", "basis"],
        "optional": ["scope", "opponentQid", "timing", "attendance", "ref",
                     "sourceRefs", "source", "checked", "note"],
        "key": ["clubQid", "team", "scope", "opponentQid", "season"],
    },
    SOURCES_FILE: {
        # Every citation as its own row. Other files point at a row here
        # by sourceId in their sourceRefs cell. The ids are the source
        # document's own codes (N9, I2) so they can be looked up in it;
        # a later document with its own codes must prefix them, and a
        # repeated id is rejected rather than silently shadowed.
        "required": ["sourceId", "publisher", "publisherKind", "url"],
        "optional": ["club", "title", "published", "urlComplete",
                     "document", "note"],
        "key": ["sourceId"],
    },
    PRICES_FILE: {
        "required": ["clubQid", "club", "team", "season", "competition",
                     "stage", "kind", "category", "price", "currency"],
        "optional": ["opponentTier", "placeType", "priceBasis", "checked",
                     "source", "note", "priceClass", "priceMax", "scope",
                     "opponentQid", "confidence", "ref", "sourceRefs"],
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
        #
        # priceClass was the THIRD, 2026-09-23, and again the file held
        # the proof: 1. FC Nürnberg publishes a normal price and a member
        # price for the same seat in the same category table. Without
        # the column the checker rejected nine member rows as duplicates
        # of the normal ones. A blank priceClass means the row does not
        # distinguish - the FC Bayern rows predate the column.
        #
        # scope and opponentQid ride along for the same reason
        # opponentTier did: a derby's price and the general price for the
        # same seat are two facts.
        "key": ["clubQid", "team", "season", "competition", "stage",
                "category", "kind", "opponentTier", "priceClass", "scope",
                "opponentQid"],
    },
}

# Files with a clubQid, which is every file except the sources list.
CLUB_FILES = [TICKETS_FILE, WINDOWS_FILE, PHASES_FILE, PRICES_FILE,
              RULES_FILE, DEMAND_FILE]

# confidence carries the source document's own tag on a FACT, and it is
# deliberately a different column from dateSource. dateSource decides
# what a calendar does with a date, and adding a value to it would change
# calendar behaviour; confidence decides nothing, it only says how sure
# anybody is. The mapping from the derby PDF, applied exactly:
#   [VERIFIED]    -> confirmed,  basis published
#   [INFERENCE]   -> inferred,   basis observed-past-cycle
#   [UNVERIFIED]  -> unverified, basis unknown
# unverified is not disputed. disputed means possibly the wrong year or
# the wrong event; unverified means somebody looked and could not confirm
# it, and the row says so rather than being dropped.
CONFIDENCE = ["confirmed", "inferred", "unverified"]
BASIS = ["published", "observed-past-cycle", "user-supplied", "unknown"]
SCOPE = ["general", "derby-home", "derby-away"]

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
    (PRICES_FILE, "confidence"): CONFIDENCE,
    (PHASES_FILE, "confidence"): CONFIDENCE,
    (RULES_FILE, "confidence"): CONFIDENCE,
    (DEMAND_FILE, "confidence"): CONFIDENCE,
    (PHASES_FILE, "basis"): BASIS,
    (RULES_FILE, "basis"): BASIS,
    (DEMAND_FILE, "basis"): BASIS,
    (WINDOWS_FILE, "scope"): SCOPE,
    (PRICES_FILE, "scope"): SCOPE,
    (RULES_FILE, "scope"): SCOPE,
    (DEMAND_FILE, "scope"): SCOPE,
    # How much of a citation's URL is actually there. A source document
    # can print a URL it has itself cut short; that is recorded, never
    # repaired by guessing the missing part.
    (SOURCES_FILE, "urlComplete"): ["yes", "truncated-in-pdf",
                                    "domain-only", "suspect"],
}

# ---- open vocabularies: values currently in use. Anything else is
#      reported and the row is kept. Add a value here when a real one
#      turns up; do not add one to silence a typo.
#
#      The Nürnberg and Inter values were added 2026-09-23, from the
#      derby PDF and nothing else - two more clubs, not a survey.
KNOWN = {
    (TICKETS_FILE, "team"): ["men"],
    (WINDOWS_FILE, "team"): ["men"],
    (PRICES_FILE, "team"): ["men"],
    (PHASES_FILE, "team"): ["men"],
    (RULES_FILE, "team"): ["men"],
    (DEMAND_FILE, "team"): ["men"],
    (TICKETS_FILE, "access"): ["members-only", "open-with-member-presale",
                               "open-with-account"],
    (TICKETS_FILE, "salesModel"): ["request-then-lottery", "phased-sale",
                                   "open-sale"],
    (TICKETS_FILE, "closesEarly"): ["yes", "no", "unknown",
                                    "yes-when-overbooked"],
    (TICKETS_FILE, "demand"): ["overbooked-usually"],
    (TICKETS_FILE, "resale"): ["official-members-only",
                               "official-face-value-only",
                               "official-season-ticket-resale"],
    (TICKETS_FILE, "minorEligibility"): ["unknown", "via-guardian-account"],
    (WINDOWS_FILE, "window"): ["season-ticket-renewal",
                               "bundesliga-single-match",
                               "bundesliga-away-block",
                               "away-season-ticket",
                               "ucl-league-phase",
                               "home-single-match", "derby-home",
                               "rueckrunde-half-season-ticket",
                               "season-ticket-resale"],
    (PHASES_FILE, "eligibility"): [
        "members", "season-ticket-and-fan-clubs", "free-sale",
        "second-tier-blue-season-ticket", "full-season-ticket",
        "plus-season-ticket-and-inter-club-plus",
        "base-season-ticket-and-inter-club-base", "siamo-noi-card",
        "interista-registered", "bper-mastercard", "open-sale"],
    (PRICES_FILE, "competition"): ["bundesliga", "dfb-pokal", "ucl",
                                   "2-bundesliga", "serie-a"],
    (PRICES_FILE, "stage"): ["regular", "early-rounds", "league-phase"],
    (PRICES_FILE, "category"): [
        "1", "2", "3", "4", "5",
        "haupttribuene-kat-1", "haupttribuene-kat-2", "haupttribuene-kat-3",
        "gegengerade-kat-1", "gegengerade-kat-2", "gegengerade-kat-3",
        "kurve-sitz-kat-1", "kurve-sitz-kat-2", "nordkurve-stehplatz",
        "terzo-rosso", "terzo-rosso-centrale", "secondo-rosso",
        "secondo-rosso-centrale", "primo-rosso-laterale", "primo-arancio",
        "secondo-arancio", "secondo-arancio-centrale", "poltroncina-rossa",
        "secondo-verde"],
    # category-a / category-b are the CLUB'S OWN labels (Nürnberg's
    # Preiskategorie A and B), unlike top-opponent / standard-opponent,
    # which are this project's description of two Bayern tables.
    (PRICES_FILE, "opponentTier"): ["top-opponent", "standard-opponent",
                                    "category-a", "category-b"],
    (PRICES_FILE, "placeType"): ["standing", "seat"],
    (PRICES_FILE, "priceClass"): ["normal", "member"],
    (RULES_FILE, "topic"): [
        "sales-channel", "membership", "presale-rights", "fees",
        "update-tracking", "queue", "sector-separation", "personalisation",
        "ticket-format", "away-end", "capacity", "box-office",
        "price-category", "free-sale-reached", "sales-mechanism",
        "resale-platform", "resale-price-cap", "resale-prices", "access",
        "ticket-types", "transfer", "fidelity-card", "presale-eligibility",
        "legal-framework", "residency-limits", "fidelity-card-foreign",
        "card-cutoff", "purchase-limit", "second-ticket-card", "minors",
        "sector-rules", "away-allocation", "price-list",
        "unofficial-resale", "entrances", "source-caveat"],
    (DEMAND_FILE, "outcome"): ["sold-out", "nearly-sold-out", "seats-left",
                               "sold-out-before-open-sale"],
    (SOURCES_FILE, "publisherKind"): ["club", "league", "press", "fan-site",
                                      "government", "other-club"],
}

# Semicolon-separated lists, so their tokens are checked one at a time
# rather than the whole cell.
KNOWN_TOKENS = {
    (TICKETS_FILE, "requestTypes"): ["home", "away", "ucl", "pokal"],
    (TICKETS_FILE, "updateTracking"): ["newsletter", "per-match-article",
                                       "notify-button", "news-section"],
}

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
                  "category", "placeType", "priceBasis", "priceClass"],
    # A phase's opening is stated relative to something - "34 days
    # before kickoff", "the day the DFL schedules the match". Its past
    # date, if a source gave one, belongs in pastCycle, which is exempt
    # exactly as it is in the windows file.
    PHASES_FILE: ["buyers", "eligibility", "opensRelative"],
    DEMAND_FILE: ["outcome", "timing"],
    # rules.rule is NOT here, on purpose: it is a sourced statement of
    # fact and often has to name a past date to say what happened ("the
    # DFL scheduled the Dec 2025 derby on 5 Nov 2025"). That is note-like
    # prose, not a deadline.
    RULES_FILE: ["topic"],
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


def split_urls(value):
    """
    A source cell is a semicolon-separated list of URLs, and a URL can
    itself contain a semicolon - the SSC Napoli one in ticket-sources.csv
    does, exactly as the derby PDF prints it. So the list is split only
    at a semicolon that is followed by the next http(s) URL.
    """
    return [u.strip() for u in re.split(r";(?=\s*https?://)", value or "")
            if u.strip()]


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

def read_file(path, today, sources=None):
    """
    Returns (rows, problems, notices).

    sources  the accepted rows of ticket-sources.csv, keyed by sourceId,
             so a sourceRefs cell can be resolved. None while that file
             itself is being read.

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
            if path in CLUB_FILES and not QID_RE.match(row["clubQid"]):
                problems.append(f"{path} line {line}: clubQid "
                                f"{row['clubQid']!r} is not a Q-id. Row ignored.")
                continue

            # ---- scope and opponent. A derby row has to say which derby,
            #      and a general row must not name an opponent, or the
            #      layering in main() would apply it to the wrong fixture.
            scope = row.get("scope", "")
            opponent = row.get("opponentQid", "")
            if scope.startswith("derby-") and not QID_RE.match(opponent):
                problems.append(f"{path} line {line}: scope is {scope!r} but "
                                f"opponentQid is {opponent!r}. A derby row "
                                f"must name the opponent's Q-id. Row ignored.")
                continue
            if opponent and not scope.startswith("derby-"):
                problems.append(f"{path} line {line}: opponentQid is "
                                f"{opponent!r} but scope is "
                                f"{scope or '(empty)'!r}. Only a derby row "
                                f"names an opponent. Row ignored.")
                continue

            # ---- citations. A sourceRefs id that does not exist is a
            #      citation pointing at nothing, which is worse than no
            #      citation because it looks checked.
            if sources is not None and row.get("sourceRefs"):
                dangling = [s.strip() for s in row["sourceRefs"].split(";")
                            if s.strip() and s.strip() not in sources]
                if dangling:
                    problems.append(
                        f"{path} line {line}: sourceRefs names "
                        f"{', '.join(dangling)}, which is not in "
                        f"{SOURCES_FILE}. Row ignored.")
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
            problem, notice = check_row(path, line, row, today, sources)
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
            for (tpath, field), known in KNOWN_TOKENS.items():
                if tpath != path or not row.get(field):
                    continue
                for token in row[field].split(";"):
                    token = token.strip()
                    if token and token not in known:
                        notices.append(
                            f"{path} line {line}: {field} contains "
                            f"{token!r}, which this tool has not seen before. "
                            f"Reported, not rejected.")

            # ---- the two standing fields. Blank is allowed - nobody may
            #      know yet - but a blank is reported, never left silent.
            if path == TICKETS_FILE:
                for field in ("updateTracking", "minorEligibility"):
                    if field in headers and not row.get(field):
                        notices.append(
                            f"{path} line {line}: {field} is empty for "
                            f"{row.get('club')}, so nothing records "
                            f"{'how this club announces a sale' if field == 'updateTracking' else 'whether an under-18 can buy'}.")

            row["_line"] = line
            rows.append(row)

    return rows, problems, notices


def check_row(path, line, row, today, sources=None):
    """Checks that belong to one file only. Returns (problems, notices)."""
    problems, notices = [], []
    has_checked = "checked" in SCHEMA[path]["optional"] + SCHEMA[path]["required"]

    # ---- checked: an ISO date, and not in the future
    checked = row.get("checked", "")
    if not has_checked:
        pass
    elif checked:
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

    # ---- confidence against basis. The mapping is fixed (see CONFIDENCE
    #      above), so a pairing outside it is almost certainly a slip.
    conf, basis = row.get("confidence", ""), row.get("basis", "")
    expected = {"confirmed": "published", "inferred": "observed-past-cycle",
                "unverified": "unknown"}
    if conf and basis and path in (PHASES_FILE, RULES_FILE, DEMAND_FILE):
        if basis != expected[conf] and basis != "user-supplied":
            notices.append(
                f"{path} line {line}: confidence is {conf!r} but basis is "
                f"{basis!r}; the mapping says {expected[conf]!r}. Reported, "
                f"not rejected.")

    # ---- a source row's URL that the source document cut short
    if path == SOURCES_FILE:
        if row.get("urlComplete", "") not in ("", "yes"):
            notices.append(
                f"{path} line {line}: {row['sourceId']}'s URL is marked "
                f"{row['urlComplete']!r} - it may not open as written. "
                f"Reported, not rejected.")

    # ---- a row's source URLs against the citations it names. Every URL
    #      in source should belong to one of the sources in sourceRefs,
    #      and every cited source should have its URL in source; either
    #      mismatch means the two cells have drifted apart.
    if sources and row.get("sourceRefs") and path != SOURCES_FILE:
        cited = set()
        for ref in row["sourceRefs"].split(";"):
            if ref.strip() in sources:
                cited.update(split_urls(sources[ref.strip()]["url"]))
        listed = set(split_urls(row.get("source", "")))
        stray = listed - cited
        absent = cited - listed
        if stray:
            notices.append(f"{path} line {line}: source lists "
                           f"{', '.join(sorted(stray))}, which belongs to "
                           f"none of the sources in sourceRefs. Reported, "
                           f"not rejected.")
        if absent and listed:
            notices.append(f"{path} line {line}: sourceRefs cites "
                           f"{', '.join(sorted(absent))} but source does not "
                           f"list it. Reported, not rejected.")

    if path == PHASES_FILE:
        if not re.match(r"^[1-9]\d*$", row.get("phase", "")):
            problems.append(f"{path} line {line}: phase is "
                            f"{row.get('phase')!r}, which is not 1, 2, 3... "
                            f"Row ignored.")
        if row.get("maxTickets") and not row["maxTickets"].isdigit():
            problems.append(f"{path} line {line}: maxTickets is "
                            f"{row['maxTickets']!r}, not a whole number. "
                            f"Row ignored.")
        if row.get("pastCycle") and not SEASON_RE.match(row.get("pastCycleFor", "")):
            notices.append(f"{path} line {line}: pastCycle is filled but "
                           f"pastCycleFor is {row.get('pastCycleFor')!r}, not a "
                           f"cycle like 2025-26. A past date needs its "
                           f"season. Reported, not rejected.")

    if path in (RULES_FILE, DEMAND_FILE):
        season = row.get("season", "")
        if season and not SEASON_RE.match(season):
            problems.append(f"{path} line {line}: season is {season!r}, "
                            f"which is not a season like 2026-27. Row "
                            f"ignored.")

    if path == DEMAND_FILE:
        att = row.get("attendance", "")
        if att and not att.isdigit():
            problems.append(f"{path} line {line}: attendance is {att!r}, "
                            f"not a whole number (no separators). Row "
                            f"ignored.")

    # ---- urls
    for field in ("ticketUrl", "source", "url"):
        value = row.get(field, "")
        if not value:
            continue
        for url in split_urls(value):
            if not url.startswith(("http://", "https://")):
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

        # priceMax: a source that gives a range, "420-440", keeps the
        # range. price is the low end; nothing picks a point inside it.
        pmax = row.get("priceMax", "")
        if pmax:
            try:
                if float(pmax.replace(",", ".")) < float(price.replace(",", ".")):
                    problems.append(f"{path} line {line}: priceMax {pmax!r} "
                                    f"is below price {price!r}. Row ignored.")
            except ValueError:
                problems.append(f"{path} line {line}: priceMax is {pmax!r}, "
                                f"which is not a number. Row ignored.")

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
    sources = None
    for path in FILES:
        rows, problems, notices = read_file(path, today, sources)
        by_file[path] = rows
        all_problems.extend(problems)
        all_notices.extend(notices)
        if path == SOURCES_FILE:
            sources = {r["sourceId"]: r for r in rows}

    # ---- cross-file: a row for a club with no ticket row
    known_clubs = {(r["clubQid"], r.get("team", "")) for r in by_file[TICKETS_FILE]}
    for path in CLUB_FILES:
        if path == TICKETS_FILE:
            continue
        for row in by_file[path]:
            pair = (row["clubQid"], row.get("team", ""))
            if pair not in known_clubs:
                all_notices.append(
                    f"{path} line {row['_line']}: {row.get('club')} "
                    f"({pair[0]}, {pair[1]}) has no row in {TICKETS_FILE}, so "
                    f"nothing says who may buy or how the club allocates. "
                    f"Reported, not rejected.")

    # ---- cross-file: every phase belongs to a window that exists, and
    #      a window's phases run 1, 2, 3 with no gap. A gap is a phase
    #      somebody meant to write and did not, which is exactly the
    #      kind of silent loss this tool is for.
    windows = {(r["clubQid"], r.get("team", ""), r["window"])
               for r in by_file[WINDOWS_FILE]}
    phases_by_window = {}
    for row in by_file[PHASES_FILE]:
        key = (row["clubQid"], row.get("team", ""), row["window"])
        if key not in windows:
            all_problems.append(
                f"{PHASES_FILE} line {row['_line']}: window "
                f"{row['window']!r} for {row.get('club')} has no row in "
                f"{WINDOWS_FILE}. A phase needs the window it belongs to.")
        phases_by_window.setdefault(key, []).append(int(row["phase"]))
    for key, numbers in phases_by_window.items():
        if sorted(numbers) != list(range(1, len(numbers) + 1)):
            all_problems.append(
                f"{PHASES_FILE}: window {key[2]!r} for {key[0]} has phases "
                f"{sorted(numbers)}, which do not run 1, 2, 3... without a "
                f"gap.")

    # ---- cross-file: a cited source nobody cites is worth a line
    if sources:
        used = set()
        for path in CLUB_FILES:
            for row in by_file[path]:
                used.update(s.strip() for s in row.get("sourceRefs", "").split(";"))
        for sid, srow in sources.items():
            if sid not in used:
                all_notices.append(
                    f"{SOURCES_FILE} line {srow['_line']}: {sid} is cited by "
                    f"no row. Kept - it is part of the document's own "
                    f"source list - but nothing rests on it.")

    # ---- the read-back
    print()
    print("READ-BACK - every accepted row, exactly as this tool understood it.")
    if not full:
        print("Notes are shortened; run with --full to print them whole.")
    for path in FILES:
        read_back(path, by_file[path], full)

    # ---- LAYERING. A derby row in club-ticket-rules.csv overrides the
    #      club's general rows on the SAME topic, for that fixture only;
    #      a topic with no derby row falls through to the general rule.
    #      This prints the result for each derby, so what applies to the
    #      match is visible without doing the merge by eye.
    print("=" * 70)
    print("LAYERED - what applies to each derby: its own rows first, then")
    print("every general topic it does not override.")
    rules = by_file[RULES_FILE]
    fixtures = sorted({(r["clubQid"], r.get("team", ""), r["scope"],
                        r["opponentQid"], r.get("club", ""))
                       for r in rules if r.get("scope", "").startswith("derby-")})
    for qid, team, scope, opp, club in fixtures:
        own = [r for r in rules if (r["clubQid"], r.get("team", ""),
               r.get("scope"), r.get("opponentQid")) == (qid, team, scope, opp)]
        overridden = {r["topic"] for r in own}
        general = [r for r in rules if r["clubQid"] == qid
                   and r.get("team", "") == team
                   and r.get("scope", "") in ("", "general")]
        print()
        print(f"  {club} ({qid}), {scope} v {opp}")
        for r in own:
            over = " [overrides general]" if any(g["topic"] == r["topic"]
                                                 for g in general) else ""
            print(f"    {r['topic']:22s} {r['confidence']:10s} "
                  f"{r.get('ref', ''):8s} line {r['_line']} - derby{over}")
        # An AWAY derby does not fall through. A club's general rows
        # describe how it sells its own home games; at the other club's
        # ground the other club's box office, channels and terms apply,
        # and printing this club's as though they did would be wrong.
        if scope == "derby-away":
            print("    (away leg: only the rows above. This club's general "
                  "rules are")
            print("     about its own home sales and are not carried over.)")
            continue
        for r in general:
            if r["topic"] not in overridden:
                print(f"    {r['topic']:22s} {r['confidence']:10s} "
                      f"{r.get('ref', ''):8s} line {r['_line']} - general")

    # ---- LOW CONFIDENCE. Every unverified row, in one place, so an
    #      honest gap cannot hide inside a long read-back.
    low = [(path, r) for path in CLUB_FILES for r in by_file[path]
           if r.get("confidence") == "unverified"]
    print()
    print("=" * 70)
    print(f"UNVERIFIED ({len(low)}) - kept and flagged. Somebody looked and "
          f"could not")
    print("confirm these. Read each as an open question, not a rule.")
    for path, r in low:
        what = r.get("rule") or r.get("buyers") or (
            f"{r.get('category')} {r.get('price')} {r.get('currency')}")
        for i, text in enumerate(_wrap(
                f"{path} line {r['_line']} {r.get('ref', '')}: {what}",
                width=66)):
            print(("  ? " if i == 0 else "    ") + text)

    # ---- the counts
    print("=" * 70)
    for path in FILES:
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
                "Nothing in this tool writes to any of these files. Fix "
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
