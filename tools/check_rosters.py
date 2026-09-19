#!/usr/bin/env python3
"""
check_rosters.py -- the pass that asks whether a club that SHOULD be on
the map is missing from it.

Every other accuracy pass in this project runs on what is already there.
crosscheck_capacity.py compares figures for clubs it has;
country-review.csv flags clubs that reached the wrong file;
coordinate-review.csv places clubs it already knows about. A club absent
from the club query leaves no trace anywhere, so nothing could ever find
it. This tool asks the question from the league's side: here is the
division's actual current membership - does the pipeline have all of it.

It READS and never writes to any club file. It writes
data/clubs/roster-review.csv, a row per club with a verdict, in the
column order of data/clubs-manual.csv followed by underscore-prefixed
diagnostics, so a row you accept pastes straight across.


WHY A COUNT IS NOT ENOUGH, AND WHY THERE ARE SEVERAL VERDICTS

Three different things get called "missing" and they want three
different remedies:

  missing-from-wikidata      no P118 at all, or a P118 naming a league
                             that league-tiers.csv does not map. The
                             pipeline cannot see the club.
                             Remedy: an add row in clubs-manual.csv.

  unplaced-no-coordinates    the club query CAN see it; it is dropped at
                             the coordinates gate because neither the
                             club nor its ground has a position. This is
                             the documented case of the 31 Regionalliga
                             clubs.
                             Remedy: coordinate-review.csv, then europlan.

  wrong-tier                 in the file, but not in this division - a
                             stale P118 from a season ago.
                             Remedy: the tier cell in clubs-manual.csv.

and the two that look at it from the other end:

  extra-not-in-roster        on our map at this tier, and the league does
                             not list it.
  ok                         in both, at the same tier.

A bare count cannot tell any of these apart, and worse, a count can come
out RIGHT while the membership is wrong: one club promoted in and one
relegated out, both mistagged, cancel exactly.

Two verdicts past the five were added because the evidence supported
neither of the five and inventing a fit would have been a guess wearing
a checked fact's clothes:

  removed-by-hand            the club query can see it, it has a
                             position, and a skip row in clubs-manual.csv
                             takes it out. That is not the pipeline
                             failing, it is a decision - but a decision
                             about a club that is in the division now is
                             worth re-reading.
  no-wikidata-item           the league article links an article that has
                             no Wikidata item at all, so there is no Q-id
                             to compare with anything.


THE SOURCE, AND WHY IT IS WIKIPEDIA

Wikidata's own P1923 (participant list) was tried first, because it
would have returned Q-ids and needed no name matching whatever. It is
empty: zero participants on the current season item of the Bundesliga,
the Romanian SuperLiga, Liga II, Liga III and five more leagues across
seven countries. It cannot be the roster source for any tier.

League official sites were rejected for the opposite reason: every one is
a different site in a different language with a different layout, several
rendered in the browser, so six countries would mean six brittle parsers -
and a silently broken one looks exactly like "every club is missing".

Wikipedia's season articles are one shape in one language across all of
them. The article title is hand-written in data/league-rosters.csv rather
than derived, because deriving it is what failed on two leagues in the
design pass.

NAME MATCHING IS AVOIDED ENTIRELY. A table row gives an article title;
wbgetentities with sites=enwiki turns that title into a Q-id; the Q-id
joins to the club layer exactly. So the comparison is id-to-id even
though the source is an HTML table, and none of the fuzzy matching that
scored Eutin 08 against FC 08 Homburg is anywhere near this.

Two guards, both from mistakes this project has already made:

  A SOURCE THAT RETURNS NOTHING IS A FAILED FETCH, NOT AN EMPTY LEAGUE.
  If the article is missing or no table parses, the run keeps the last
  good review file and says so - the rule capacity-review.csv and
  unmapped-leagues.csv already follow. A parser silently returning zero
  clubs would otherwise report a whole division as missing, with a green
  tick.

  IT DOES NOT HARDCODE LEAGUE SIZES. The expected membership comes from
  the source. Writing "the 3. Liga has 20 clubs" into this tool would be
  inventing the very fact the check exists to obtain.

Free, no key. football-data.org is read only from the files it has
already written into data/fixtures/, so no token is needed here either.

Usage:  python3 tools/check_rosters.py
"""

import csv
import glob
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------- config

CLUB_DIR = "data/clubs"
CONFIG_FILE = "data/league-rosters.csv"
TIERS_FILE = "data/league-tiers.csv"
MANUAL_FILE = "data/clubs-manual.csv"
FIXTURE_DIR = "data/fixtures"
REVIEW_FILE = os.path.join(CLUB_DIR, "roster-review.csv")

CONFIG_REQUIRED = ("country", "tier", "season", "article")
CONFIG_OPTIONAL = ("leagueQid", "note")

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
SPARQL = "https://query.wikidata.org/sparql"
USER_AGENT = ("football-fixture-planner/1.0 (personal project; "
              "https://github.com/AlexGrozavul/Football)")

TIMEOUT_SECONDS = 90
MAX_RETRIES = 3
REQUEST_GAP_SECONDS = 2
TITLE_BATCH = 40          # wbgetentities takes 50; 40 leaves room
QID_BATCH = 40            # VALUES clause size; the query service gives up at 60s

# Which football-data.org competition file confirms which division. Only
# the competitions whose team list this project already holds are here,
# and its free tier reaches the top flights and nothing below them - so
# most rows have one source and say so, rather than being suppressed or
# promoted.
SECOND_SOURCE = {
    ("DE", 1): "BL1.json",
}


# ------------------------------------------------------------- csv safety

# Same guard fetch_clubs.py uses. csv.DictReader hands back any value
# past the last column under one "rest" key; left at its default that key
# is None and a comprehension that skips None throws the values away
# without a word, which is what quietly cut two notes in half the first
# time a comma was typed inside one.
OVERFLOW = object()


def _s(v):
    return (v or "").strip()


def overflow_problem(path, line, columns, extra):
    lost = ", ".join(repr(_s(v)) for v in extra)
    return (f"{path} line {line}: this row has {columns + len(extra)} values but "
            f"the header has {columns} columns, so {lost} would be thrown away. "
            f"A comma inside a cell splits that cell in two - put double quotes "
            f'round the whole cell ("like, this") to keep the comma. Row ignored.')


# ------------------------------------------------------------------ http

def get_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json_with_retry(url, what):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return get_json(url), None
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
                print(f"    {what}: server said {exc.code}, retrying")
                time.sleep(15)
                continue
            return None, f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < MAX_RETRIES:
                print(f"    {what}: network problem, retrying: {exc}")
                time.sleep(10)
                continue
            return None, f"network error: {exc}"
        except ValueError:
            # The query service answers 200 with a half-written body when
            # a query runs past its own limit, so broken JSON means "too
            # slow", not "wrong query".
            if attempt < MAX_RETRIES:
                print(f"    {what}: answer cut off mid-JSON, retrying")
                time.sleep(15)
                continue
            return None, "answer cut off mid-JSON"
    return None, "exhausted retries"


def post_sparql(query):
    body = urllib.parse.urlencode({"query": query, "format": "json"}).encode("utf-8")
    req = urllib.request.Request(SPARQL, data=body, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sparql_with_retry(query):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return post_sparql(query), None
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
                print(f"    query service said {exc.code}, retrying")
                time.sleep(15)
                continue
            return None, f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < MAX_RETRIES:
                print(f"    network problem, retrying: {exc}")
                time.sleep(10)
                continue
            return None, f"network error: {exc}"
        except ValueError:
            if attempt < MAX_RETRIES:
                print("    answer cut off mid-JSON, retrying")
                time.sleep(15)
                continue
            return None, "answer cut off mid-JSON"
    return None, "exhausted retries"


# ---------------------------------------------------------- the config

def load_config():
    """
    data/league-rosters.csv -- one hand-written line per league.

    leagueQid is documentation of which league the article is about; the
    comparison is driven by country and tier, because a single article
    can cover a whole level (the Regionalliga's five divisions are one
    page, and league-tiers.csv maps all five to tier 4).
    """
    rows, problems = [], []
    if not os.path.exists(CONFIG_FILE):
        problems.append(f"{CONFIG_FILE} does not exist - there is nothing to check")
        return rows, problems

    with open(CONFIG_FILE, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, restkey=OVERFLOW)
        if not reader.fieldnames:
            problems.append(f"{CONFIG_FILE} is empty - it needs a header row")
            return rows, problems
        headers = [_s(h) for h in reader.fieldnames]
        for need in CONFIG_REQUIRED:
            if need not in headers:
                problems.append(f"{CONFIG_FILE} line 1: missing required column {need!r}")
                return rows, problems
        for h in headers:
            if h and h not in CONFIG_REQUIRED + CONFIG_OPTIONAL:
                problems.append(f"{CONFIG_FILE} line 1: column {h!r} not recognised, ignored")

        for raw in reader:
            line = reader.line_num
            extra = raw.pop(OVERFLOW, None)
            if extra:
                problems.append(overflow_problem(
                    CONFIG_FILE, line, len(reader.fieldnames), extra))
                continue
            row = {_s(k): _s(v) for k, v in raw.items()}
            if not any(row.values()):
                continue

            qid = row.get("leagueQid", "")
            if qid and not re.match(r"^Q\d+$", qid):
                problems.append(f"{CONFIG_FILE} line {line}: leagueQid {qid!r} is not a Q-id")
                continue
            if not row.get("article"):
                problems.append(f"{CONFIG_FILE} line {line}: article is required")
                continue
            if not row.get("country"):
                problems.append(f"{CONFIG_FILE} line {line}: country is required")
                continue
            if not row.get("tier", "").isdigit():
                problems.append(
                    f"{CONFIG_FILE} line {line}: tier {row.get('tier')!r} must be a "
                    f"whole number")
                continue
            if not re.match(r"^\d{4}-\d{2}$", row.get("season", "")):
                problems.append(
                    f"{CONFIG_FILE} line {line}: season {row.get('season')!r} must be a "
                    f"cycle like 2026-27")
                continue
            # The article titles use an EN DASH and it is not optional -
            # "2026-27 Bundesliga" with a hyphen does not resolve.
            if re.search(r"^\d{4}-\d{2}\s", row["article"]):
                problems.append(
                    f"{CONFIG_FILE} line {line}: article {row['article']!r} starts with a "
                    f"HYPHEN. Wikipedia's season articles use an en dash (2026–27); a "
                    f"hyphen does not resolve. Row ignored")
                continue
            row["_line"] = line
            rows.append(row)
    return rows, problems


def load_tiers():
    """leagueQid -> (tier, country), so a stale P118 can be given a tier."""
    tiers = {}
    if not os.path.exists(TIERS_FILE):
        return tiers
    with open(TIERS_FILE, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            qid = _s(row.get("leagueQid"))
            tier = _s(row.get("tier"))
            if qid and tier.isdigit():
                tiers[qid] = (int(tier), _s(row.get("country")), _s(row.get("label")))
    return tiers


def load_skips():
    """The clubs a hand-written skip row removes from the map."""
    skips = {}
    if not os.path.exists(MANUAL_FILE):
        return skips
    with open(MANUAL_FILE, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, restkey=OVERFLOW):
            row.pop(OVERFLOW, None)
            if _s(row.get("tier")).lower() == "skip" and _s(row.get("clubQid")):
                skips[_s(row["clubQid"])] = _s(row.get("name"))
    return skips


# ------------------------------------------------------ wikipedia tables

TAG = re.compile(r"<[^>]+>")


def text_of(fragment):
    return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", fragment))).strip()


def roster_tables(page_html):
    """
    Which tables on a season article carry the division's membership.

    TWO SHAPES, because the top divisions and the lower ones do not write
    the page the same way:

      "Stadiums and locations" - a header naming a stadium/venue/ground
      AND a capacity. This is the better one: it carries a capacity per
      club, which is a free second opinion on the ground.

      the league table - a header with Pos and Team and Pld. This is all
      the Regionalliga and Liga III pages have; neither carries a
      stadiums table at all, and without this shape both came back with
      zero clubs, which the guard above would rightly have called a
      failed fetch.

    Where the first shape is present it is used alone, because on a page
    that has both, the standings table is the same clubs with more ways
    to go wrong. Where it is absent, EVERY table of the second shape is
    used and the clubs unioned - the Regionalliga's five divisions and
    Liga III's series and play-off groups are separate tables on one page,
    and the groups are subsets of the series, so the union is the level's
    membership.
    """
    tables = re.findall(
        r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>.*?</table>', page_html, re.S)
    venue_shaped, table_shaped = [], []
    for table in tables:
        headers = [text_of(h).lower()
                   for h in re.findall(r"<th[^>]*>(.*?)</th>", table, re.S)[:14]]
        joined = " ".join(headers)
        has_place = any(k in joined for k in ("stadium", "venue", "ground", "arena"))
        if has_place and "capacit" in joined:
            venue_shaped.append((table, headers))
        elif ("pos" in headers and "pld" in headers
              and ("team" in headers or "club" in headers)):
            table_shaped.append((table, headers))
    if venue_shaped:
        return venue_shaped, "stadiums-and-locations"
    return table_shaped, "league-table"


def rows_of(table, headers):
    """
    (article title, capacity) for each row: the FIRST linked article in
    the row is the club, and the capacity is whichever cell sits under a
    capacity header, when there is one.
    """
    cap_index = None
    for i, h in enumerate(headers):
        if "capacit" in h:
            cap_index = i
            break

    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S)[1:]:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)
        if not cells:
            continue
        title = None
        for cell in cells:
            link = re.search(r'<a[^>]+href="/wiki/([^"#:]+)"', cell)
            if link:
                title = urllib.parse.unquote(link.group(1)).replace("_", " ")
                break
        if not title:
            continue
        capacity = None
        if cap_index is not None and cap_index < len(cells):
            digits = re.sub(r"[^\d]", "", text_of(cells[cap_index]).replace(" ", ""))
            if digits and 100 <= int(digits) <= 200000:
                capacity = int(digits)
        out.append((title, capacity))
    return out


def fetch_article(title):
    query = urllib.parse.urlencode({
        "action": "parse", "page": title, "prop": "text",
        "format": "json", "formatversion": "2", "redirects": "1"})
    data, error = get_json_with_retry(f"{WIKIPEDIA_API}?{query}", title)
    if error:
        return None, None, error
    if "error" in data:
        return None, None, (
            f"no such article ({data['error'].get('code')}) - check the title in "
            f"{CONFIG_FILE}, and remember the season articles use an en dash")
    return data["parse"]["text"], data["parse"]["title"], None


# ------------------------------------------------------- title -> Q-id

def qids_for_titles(titles):
    """
    The sitelink hop. wbgetentities with sites=enwiki turns an English
    Wikipedia title into a Q-id, so the comparison downstream is id to
    id and no club name is ever matched against another.
    """
    found, failures = {}, []
    ordered = list(dict.fromkeys(titles))
    for start in range(0, len(ordered), TITLE_BATCH):
        batch = ordered[start:start + TITLE_BATCH]
        query = urllib.parse.urlencode({
            "action": "wbgetentities", "sites": "enwiki",
            "titles": "|".join(batch), "props": "sitelinks",
            "sitefilter": "enwiki", "normalize": "1",
            "format": "json", "formatversion": "2"})
        data, error = get_json_with_retry(f"{WIKIDATA_API}?{query}", "sitelinks")
        if error:
            failures.append(f"sitelink lookup failed for {len(batch)} titles: {error}")
            continue

        # The answer comes back keyed by Q-id, not by the title that was
        # sent, so it is read back through the sitelink each item
        # actually carries. Wikidata also normalises titles on the way in
        # (underscores, capitalisation), so its own normalisation table
        # is followed rather than a pairing being guessed - a guessed
        # pairing here would put one club's Q-id on another club's row,
        # which is precisely the error the sitelink hop exists to avoid.
        normalised = {n.get("to"): n.get("from")
                      for n in (data.get("normalized") or [])}
        for qid, entity in (data.get("entities") or {}).items():
            if not qid.startswith("Q"):
                continue
            sitelink = ((entity.get("sitelinks") or {}).get("enwiki") or {}).get("title")
            if not sitelink:
                continue
            found[sitelink] = qid
            if sitelink in normalised:
                found[normalised[sitelink]] = qid
        time.sleep(REQUEST_GAP_SECONDS)
    return found, failures


# ------------------------------------------------------ wikidata diagnosis

DIAGNOSIS_QUERY = """
SELECT ?club ?clubLabel ?league ?venue ?coord ?type ?dissolved
WHERE {
  VALUES ?club { %(clubs)s }
  OPTIONAL { ?club wdt:P118 ?league }
  OPTIONAL { ?club wdt:P31 ?type }
  OPTIONAL { ?club wdt:P576 ?dissolved }
  OPTIONAL {
    ?club wdt:P115 ?venue .
    OPTIONAL { ?venue wdt:P625 ?venueCoord }
  }
  OPTIONAL { ?club wdt:P625 ?clubCoord }
  BIND(COALESCE(?venueCoord, ?clubCoord) AS ?coord)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,de,ro" }
}
"""


def qid_of(uri):
    return uri.rsplit("/", 1)[-1] if uri else None


def diagnose(qids):
    """
    What Wikidata says about each club, in the same terms the club query
    asks in - which leagues it claims, whether anything gives it a
    position, whether it is typed as a person or marked dissolved. Those
    last two are the gates CLUB_QUERY applies, so a club failing one of
    them is invisible to the pipeline for a reason this tool can name.
    """
    facts, failures = {}, []
    ordered = list(dict.fromkeys(qids))
    for start in range(0, len(ordered), QID_BATCH):
        batch = ordered[start:start + QID_BATCH]
        query = DIAGNOSIS_QUERY % {"clubs": " ".join(f"wd:{q}" for q in batch)}
        began = time.time()
        data, error = sparql_with_retry(query)
        if error:
            failures.append(f"diagnosis failed for {len(batch)} clubs: {error}")
            continue
        print(f"    diagnosed {len(batch)} clubs in {round(time.time() - began, 1)}s")
        for row in data["results"]["bindings"]:
            qid = qid_of((row.get("club") or {}).get("value"))
            if not qid:
                continue
            fact = facts.setdefault(qid, {
                "label": "", "leagues": set(), "venue": None,
                "coord": False, "types": set(), "dissolved": False})
            if row.get("clubLabel"):
                fact["label"] = row["clubLabel"]["value"]
            if row.get("league"):
                fact["leagues"].add(qid_of(row["league"]["value"]))
            if row.get("type"):
                fact["types"].add(qid_of(row["type"]["value"]))
            if row.get("venue"):
                fact["venue"] = qid_of(row["venue"]["value"])
            if row.get("coord"):
                fact["coord"] = True
            if row.get("dissolved"):
                fact["dissolved"] = True
        time.sleep(REQUEST_GAP_SECONDS)
    return facts, failures


# ------------------------------------------------------- the second source

def fold(text):
    if not text:
        return ""
    text = text.replace("ß", "ss")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def load_second_source(country, tier):
    """
    football-data.org's own team list for this division, read from the
    file it has already written into data/fixtures/. Its free tier
    reaches the top flights and nothing below them, so most divisions
    have no second source and the review row says so rather than being
    suppressed or promoted.

    The comparison here IS by name, unavoidably - football-data.org has
    its own ids and they do not join to Wikidata. That is why this is
    only ever a CONFIRMATION of something the roster already said, never
    a finding of its own.
    """
    filename = SECOND_SOURCE.get((country, tier))
    if not filename:
        return None, None
    path = os.path.join(FIXTURE_DIR, filename)
    if not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    names = set()
    for team in (data.get("teams") or {}).values():
        for key in ("name", "shortName"):
            if team.get(key):
                names.add(fold(team[key]))
    return names, data.get("name") or filename


def second_source_says(names, *candidates):
    if not names:
        return ""
    for candidate in candidates:
        folded = fold(candidate)
        if not folded:
            continue
        if folded in names:
            return "confirms"
        for name in names:
            if folded in name or name in folded:
                return "confirms"
    return "silent"


# ---------------------------------------------------------------- output

HEADER = ["clubQid", "name", "country", "tier", "venue", "capacity",
          "lat", "lon", "ticketUrl", "source", "note",
          "_league", "_season", "_article", "_rosterCapacity", "_ourTier",
          "_wikidataLeagues", "_hasCoordinates", "_secondSource", "_why",
          "_verdict"]


def main():
    if not os.path.isdir(CLUB_DIR):
        sys.exit(f"{CLUB_DIR} does not exist - run the club layer first")

    config, config_problems = load_config()
    tiers = load_tiers()
    skips = load_skips()

    # The club layer, indexed by Q-id and by (country, tier).
    layer, by_country_tier = {}, {}
    for path in sorted(glob.glob(os.path.join(CLUB_DIR, "*.json"))):
        if os.path.basename(path) == "index.json":
            continue
        code = os.path.basename(path)[:-5]
        with open(path, encoding="utf-8") as fh:
            for club in json.load(fh).get("clubs", []):
                club["_country"] = code
                layer[club["id"]] = club
                by_country_tier.setdefault((code, club.get("tier")), set()).add(club["id"])

    rows, summary, failures, readback, skipped = [], [], [], [], []
    incomplete = []

    # One row per league, but one article may serve several - the
    # Regionalliga's five divisions are a single page - so the articles
    # are fetched once each and grouped by the (country, tier) they are
    # compared against.
    groups = {}
    for entry in config:
        country, tier = entry["country"], int(entry["tier"])
        if not os.path.exists(os.path.join(CLUB_DIR, f"{country}.json")):
            skipped.append(
                f"{CONFIG_FILE} line {entry['_line']}: {entry['article']} is about "
                f"{country}, which has no country file in {CLUB_DIR}, so there is "
                f"nothing to compare it against. Row read and skipped")
            continue
        if entry.get("leagueQid") and entry["leagueQid"] not in tiers:
            skipped.append(
                f"{CONFIG_FILE} line {entry['_line']}: {entry['leagueQid']} is not in "
                f"{TIERS_FILE}, so no club reaches the map through it. Row read "
                f"and skipped")
            continue
        group = groups.setdefault((country, tier), {"articles": {}, "leagues": []})
        group["articles"].setdefault(entry["article"], entry["season"])
        if entry.get("leagueQid"):
            group["leagues"].append(entry["leagueQid"])

    # ---- read every article first, so a failure is known before anything
    #      is written
    rosters = {}
    for (country, tier), group in sorted(groups.items()):
        clubs_here, capacities, sources = {}, {}, []
        failed = False
        for article, season in group["articles"].items():
            print(f"  {country} tier {tier}  reading {article!r}")
            page, real_title, error = fetch_article(article)
            if error:
                failures.append(f"{country} tier {tier}: {article!r} - {error}")
                incomplete.append(f"{country} tier {tier}: {article!r} could not be read")
                failed = True
                break
            tables, shape = roster_tables(page)
            if not tables:
                # Zero tables is a changed page, not an empty division.
                failures.append(
                    f"{country} tier {tier}: {real_title!r} parsed, but no table on it "
                    f"looks like a membership list - neither a stadiums-and-locations "
                    f"table nor a league table. The page layout has probably changed")
                incomplete.append(f"{country} tier {tier}: no membership table on {article!r}")
                failed = True
                break
            for table, headers in tables:
                for title, capacity in rows_of(table, headers):
                    clubs_here.setdefault(title, capacity)
                    if capacity is not None and capacities.get(title) is None:
                        capacities[title] = capacity
            print(f"      {len(tables)} {shape} table(s), {len(clubs_here)} clubs so far")
            sources.append((real_title, season, shape))
            time.sleep(REQUEST_GAP_SECONDS)
        if failed:
            continue
        if not clubs_here:
            failures.append(
                f"{country} tier {tier}: the tables parsed but no club came out of "
                f"them. That is a failed parse, not an empty division")
            incomplete.append(f"{country} tier {tier}: no clubs parsed")
            continue
        rosters[(country, tier)] = {
            "clubs": clubs_here, "capacities": capacities,
            "sources": sources, "leagues": group["leagues"]}

    # ---- one sitelink hop and one diagnosis for everything
    all_titles = [t for r in rosters.values() for t in r["clubs"]]
    qid_by_title, hop_failures = ({}, [])
    if all_titles:
        print(f"  turning {len(set(all_titles))} article titles into Q-ids")
        qid_by_title, hop_failures = qids_for_titles(all_titles)
        failures.extend(hop_failures)
        if hop_failures:
            incomplete.append("at least one sitelink lookup failed")

    needed = sorted(set(qid_by_title.values()))
    facts, diag_failures = ({}, [])
    if needed:
        print(f"  asking Wikidata about {len(needed)} clubs")
        facts, diag_failures = diagnose(needed)
        failures.extend(diag_failures)
        if diag_failures:
            incomplete.append("at least one Wikidata diagnosis failed")

    # ---- the verdicts
    for (country, tier), roster in sorted(rosters.items()):
        second_names, second_label = load_second_source(country, tier)
        article_names = ", ".join(s[0] for s in roster["sources"])
        season = roster["sources"][0][1]
        league_label = ", ".join(
            tiers.get(q, (None, None, q))[2] or q for q in roster["leagues"]) or f"tier {tier}"

        counts = {}
        seen_qids = set()

        for title in sorted(roster["clubs"]):
            qid = qid_by_title.get(title)
            capacity = roster["capacities"].get(title)
            confirm = second_source_says(second_names, title,
                                         (facts.get(qid) or {}).get("label", ""))
            base = {
                "clubQid": qid or "", "name": title, "country": country,
                "tier": "", "venue": "", "capacity": "", "lat": "", "lon": "",
                "ticketUrl": "", "source": f"https://en.wikipedia.org/wiki/"
                                           f"{urllib.parse.quote(title.replace(' ', '_'))}",
                "note": "",
                "_league": league_label, "_season": season, "_article": article_names,
                "_rosterCapacity": capacity if capacity is not None else "",
                "_ourTier": "", "_wikidataLeagues": "", "_hasCoordinates": "",
                "_secondSource": (f"{second_label}: {confirm}" if second_names
                                  else "no second source for this division"),
                "_why": "", "_verdict": "",
            }

            if not qid:
                base["_verdict"] = "no-wikidata-item"
                base["_why"] = ("this article has no Wikidata item, so there is no Q-id "
                                "to compare against the club layer. It may also not be a "
                                "club at all - a stadium or a town linked first in its row")
                rows.append(base)
                counts["no-wikidata-item"] = counts.get("no-wikidata-item", 0) + 1
                continue

            seen_qids.add(qid)
            fact = facts.get(qid, {})
            leagues = sorted(fact.get("leagues") or [])
            base["name"] = fact.get("label") or title
            base["_wikidataLeagues"] = " ".join(leagues) or "none"
            base["_hasCoordinates"] = "yes" if fact.get("coord") else "no"

            mapped = [q for q in leagues if q in tiers]
            mapped_here = [q for q in mapped if tiers[q][0] == tier
                           and tiers[q][1] == country]

            club = layer.get(qid)
            if club is not None:
                base["_ourTier"] = club.get("tier") or ""

            if club is not None and club.get("tier") == tier and club["_country"] == country:
                base["_verdict"] = "ok"
                base["_why"] = "in the division and on the map at this tier"
            elif club is not None:
                base["_verdict"] = "wrong-tier"
                base["_why"] = (
                    f"the league lists it at tier {tier} and the map has it at tier "
                    f"{club.get('tier')} in {club['_country']} - most likely a P118 left "
                    f"over from last season. Put {tier} in the tier cell of "
                    f"{MANUAL_FILE}")
            elif qid in skips:
                base["_verdict"] = "removed-by-hand"
                base["_why"] = (
                    f"a skip row in {MANUAL_FILE} removes this club, but the league "
                    f"lists it in the division now. Re-read that decision")
            elif fact.get("dissolved"):
                base["_verdict"] = "missing-from-wikidata"
                base["_why"] = (
                    "Wikidata marks this club dissolved (P576) and the club query "
                    "excludes dissolved clubs, so it can never reach the map. Either "
                    "Wikidata is wrong or the league article is")
            elif not mapped_here and not mapped:
                base["_verdict"] = "missing-from-wikidata"
                base["_why"] = (
                    f"Wikidata gives it {'no league at all' if not leagues else 'only leagues ' + ' '.join(leagues)}"
                    f", none of them in {TIERS_FILE}, so the club query never sees it. "
                    f"Add a row to {MANUAL_FILE}")
            elif not mapped_here:
                where = ", ".join(f"{q} = tier {tiers[q][0]} {tiers[q][1]}" for q in mapped)
                base["_verdict"] = "wrong-tier"
                base["_why"] = (
                    f"Wikidata puts it in {where}, not in this division, and it is not "
                    f"on the map at all. Both the tier and the absence need a hand row "
                    f"in {MANUAL_FILE}")
            elif not fact.get("coord"):
                base["_verdict"] = "unplaced-no-coordinates"
                base["_why"] = (
                    "the club query can see this club - its league is mapped - but "
                    "neither it nor its ground has a position, so it is dropped at the "
                    "coordinates gate. This is the route coordinate-review.csv and "
                    "europlan-online already exist for")
            else:
                base["_verdict"] = "missing-from-wikidata"
                base["_why"] = (
                    "Wikidata has the right league and a position for this club, and it "
                    "is still not on the map. Nothing here explains that - read the club "
                    "layer run summary for this Q-id")

            rows.append(base)
            counts[base["_verdict"]] = counts.get(base["_verdict"], 0) + 1

        # ---- the other direction
        ours = by_country_tier.get((country, tier), set())
        for qid in sorted(ours - seen_qids):
            club = layer[qid]
            rows.append({
                "clubQid": qid, "name": club.get("name", ""), "country": country,
                "tier": "", "venue": "", "capacity": "", "lat": "", "lon": "",
                "ticketUrl": "", "source": "", "note": "",
                "_league": league_label, "_season": season, "_article": article_names,
                "_rosterCapacity": "", "_ourTier": club.get("tier") or "",
                "_wikidataLeagues": " ".join(club.get("leagues") or []) or "none",
                "_hasCoordinates": "yes" if club.get("lat") is not None else "no",
                "_secondSource": (f"{second_label}: "
                                  f"{second_source_says(second_names, club.get('name'))}"
                                  if second_names else "no second source for this division"),
                "_why": ("the map has this club at this tier and the league does not list "
                         "it. Either its P118 is stale and it belongs at another tier, or "
                         "the league article links it under a title the sitelink hop did "
                         "not resolve"),
                "_verdict": "extra-not-in-roster",
            })
            counts["extra-not-in-roster"] = counts.get("extra-not-in-roster", 0) + 1

        summary.append(
            f"{country} tier {tier}  {league_label}  |  roster {len(roster['clubs'])}  |  "
            f"map {len(ours)}  |  " +
            "  ".join(f"{v} {k}" for k, v in sorted(counts.items())))
        readback.append(
            f"{country} tier {tier}  {season}  {article_names}  "
            f"({roster['sources'][0][2]})")

    order = {"missing-from-wikidata": 0, "unplaced-no-coordinates": 1,
             "wrong-tier": 2, "removed-by-hand": 3, "no-wikidata-item": 4,
             "extra-not-in-roster": 5, "ok": 6}
    rows.sort(key=lambda r: (r["country"], r["_league"],
                             order.get(r["_verdict"], 9), r["name"]))

    # Same rule the other review files follow. A league that could not be
    # read contributes no rows, and writing the file anyway would delete
    # work nobody has acted on yet, with a green tick.
    existing = os.path.exists(REVIEW_FILE)
    kept = bool(incomplete) and existing
    if not kept:
        with open(REVIEW_FILE, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=HEADER)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    print()
    print("=" * 74)
    print("ROSTER CHECK  (is a club that should be on the map missing from it)")
    print("=" * 74)
    if readback:
        print("  Read back - the leagues checked, exactly as understood:")
        for line in readback:
            print("    " + line)
        print()
    for line in summary:
        print("  " + line)
    print()
    if skipped:
        print("  Read and skipped:")
        for line in skipped:
            print("    " + line)
        print()
    if config_problems:
        print(f"  Problems in {CONFIG_FILE}:")
        for line in config_problems:
            print("    ! " + line)
        print()
    if kept:
        print("  At least one league could not be read, so the review file is")
        print(f"  unchanged from the last successful run. {REVIEW_FILE}")
        print("  was NOT rewritten - a league that returns nothing is a failed fetch,")
        print("  not an empty division, and writing it would report a whole division")
        print("  as missing with a green tick. Not checked this time:")
        for reason in incomplete:
            print(f"    {reason}")
    else:
        if incomplete:
            print(f"  {REVIEW_FILE} did not exist yet, so a partial list was")
            print("  written. It is missing the leagues listed at the bottom.")
        print(f"  {len(rows)} row(s) written to {REVIEW_FILE}")
        print("  Columns starting with _ are evidence and are ignored by the club")
        print("  builder. _verdict says WHICH KIND of missing each club is, because")
        print("  the three kinds want three different remedies and a count cannot")
        print("  tell them apart - a count can even come out right while the")
        print("  membership is wrong, if one club promoted in and one relegated out")
        print("  are both mistagged.")
    print()
    print("  Nothing here is corrected automatically. Which remedy applies is a")
    print("  judgement: the SSV Ulm case is the standing proof that two items on")
    print("  one ground can want opposite answers.")
    print()
    print("  Where a division has no second source the row says so. football-data.org")
    print("  reaches the top flights and nothing below them, so it confirms tier 1")
    print("  and stays silent underneath - and a silent second source is not a")
    print("  second source disagreeing.")
    if failures:
        print()
        for f in failures:
            print("  ! " + f)
    print("=" * 74)

    if config_problems:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
