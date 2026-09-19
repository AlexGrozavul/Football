#!/usr/bin/env python3
"""
crosscheck_stadiumdb.py -- a THIRD opinion on stadium capacities.

Reads data/clubs/*.json and asks StadiumDB.com for every stadium in the
same country, then compares the two capacity figures. Where
data/clubs/capacity-review.csv already holds an OpenStreetMap figure for
the same club, that is carried across too, so a row can show all three
numbers side by side.

It NEVER changes a club file and it NEVER picks a winner. Where the
sources disagree the row is written with every figure it has and every
source named, and you decide. That is the same contract
crosscheck_capacity.py has - this tool only adds a source.

MATCHING IS BY NAME, AND THAT IS A REAL WEAKNESS.
crosscheck_capacity.py matches a club to a ground by POSITION, within
500m, deliberately not by name, because name matching is what put
Eutin 08 next to FC 08 Homburg on a shared "08". StadiumDB carries no
coordinates on any page - checked across 27 pages in nine countries - so
position matching is not available here and name matching is the only
thing left.

Two things are done about that rather than nothing:

  1. A match needs the club name AND the country. The country comes from
     which country page the stadium was read off, so it is the site's
     own assertion, not an inference.
  2. The ground name is compared as a SECOND signal. A club whose name
     matches and whose ground name also matches is a confident match; a
     club whose name matches while the ground names disagree is written
     out as its own verdict rather than quietly trusted, because that
     disagreement is either our ground being wrong or the club having
     moved, and both are worth your eye.

A club that matches more than one StadiumDB row is reported as ambiguous
and its capacities are NOT compared. Guessing which row was meant is the
exact failure this whole file is trying to avoid.

StadiumDB's robots.txt (33 bytes) disallows only /lay-gfx/, so the pages
this reads carry no crawl restriction. One request per country, with a
gap between, because that is all this needs: a country page is a single
table of every ground the site holds for that country.

Free, no key.

Usage:  python3 tools/crosscheck_stadiumdb.py
"""

import csv
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

# ---------------------------------------------------------------- config

CLUB_DIR = "data/clubs"
REVIEW_FILE = os.path.join(CLUB_DIR, "stadiumdb-review.csv")
OSM_REVIEW_FILE = os.path.join(CLUB_DIR, "capacity-review.csv")

BASE = "https://stadiumdb.com"
USER_AGENT = ("football-fixture-planner/1.0 (personal project; "
              "https://github.com/AlexGrozavul/Football)")

# Which StadiumDB country listing belongs to which of our country files.
# Hand-written, because a slug is not derivable from an ISO code and
# guessing one wrong looks exactly like a country with no stadiums.
COUNTRY_PAGES = {
    "DE": ("ger", "Germany"),
    "RO": ("rou", "Romania"),
}

# Below this the two sources are treated as agreeing. Same threshold
# crosscheck_capacity.py uses, for the same reason: capacities shift by
# a few seats constantly and only real disagreements are worth reading.
AGREE_WITHIN = 0.05

REQUEST_GAP_SECONDS = 10
TIMEOUT_SECONDS = 90
MAX_RETRIES = 3


# ------------------------------------------------------------------ http

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return resp.read().decode("utf-8", "replace")


def fetch_with_retry(url):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fetch(url), None
        except urllib.error.HTTPError as exc:
            # StadiumDB 404s honestly - an 11.5KB error page with a real
            # 404 status - so unlike europlan-online the status code can
            # be trusted here and a 404 is not worth retrying.
            if exc.code == 404:
                return None, "HTTP 404 - no such page"
            if exc.code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
                print(f"    server busy ({exc.code}), waiting 30s")
                time.sleep(30)
                continue
            return None, f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < MAX_RETRIES:
                print(f"    network problem, retrying: {exc}")
                time.sleep(15)
                continue
            return None, f"network error: {exc}"
    return None, "exhausted retries"


# --------------------------------------------------------------- parsing

TAG = re.compile(r"<[^>]+>")


def text_of(fragment):
    """Cell text with the markup taken out and the entities put back."""
    cleaned = TAG.sub(" ", fragment)
    return re.sub(r"\s+", " ", html.unescape(cleaned)).strip()


def parse_country_table(body):
    """
    A StadiumDB country page is one table: Name | City | Clubs | Capacity.
    Returns [{"name", "city", "clubs": [...], "capacity", "url"}].

    The capacity column uses non-breaking spaces as thousands separators
    ("18 482"), so those come out before the number is read.
    """
    grounds = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S | re.I):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(cells) < 4:
            continue
        name = text_of(cells[0])
        city = text_of(cells[1])
        clubs_raw = text_of(cells[2])
        capacity = capacity_of(cells[3])
        if not name:
            continue
        link = re.search(r'href="([^"]+)"', cells[0])
        grounds.append({
            "name": name,
            "city": city,
            "clubs": split_clubs(clubs_raw),
            "clubsRaw": clubs_raw,
            "capacity": capacity,
            "url": (BASE + link.group(1)) if link and link.group(1).startswith("/")
                   else (link.group(1) if link else ""),
        })
    return grounds


def capacity_of(cell):
    raw = text_of(cell).replace(" ", " ")
    digits = re.sub(r"[^\d]", "", raw)
    if not digits:
        return None
    value = int(digits)
    return value if 100 <= value <= 200000 else None


def split_clubs(raw):
    """
    The Clubs cell holds one club, several, or a dash meaning none. A
    comma and a slash both separate; a dash on its own is not a club.
    """
    if not raw or raw.strip() in ("-", "–", "—", ""):
        return []
    parts = re.split(r"\s*[,/;]\s*|\s+–\s+", raw)
    return [p.strip() for p in parts if p.strip() and p.strip() not in ("-", "–")]


# ------------------------------------------------------------- name keys

# Club-name noise this strips for the SECOND, weaker comparison only. It
# is legal form and sporting-society shorthand, nothing that tells two
# clubs apart. Years and squad numbers are deliberately NOT in here:
# "08" is the whole difference between some club names, and this project
# has already been bitten once by treating a shared number as a match.
FORMS = {
    # Germany
    "fc", "fcv", "sc", "sv", "tsv", "tsg", "vfb", "vfl", "vfr", "fsv",
    "ssv", "spvgg", "sg", "sgv", "msv", "bsc", "ksc", "kfc", "bfc",
    "svg", "asv", "dsc", "fsc", "rsv", "tus", "tura", "djk", "eintracht",
    "sportfreunde", "sportverein", "sportclub", "fussballclub",
    "borussia", "werder", "hertha", "arminia", "preussen", "viktoria",
    "germania", "teutonia", "alemannia", "union", "wacker", "kickers",
    "rot", "weiss", "schwarz", "blau",
    # Romania
    "cs", "acs", "afc", "csm", "csu", "cso", "asu", "fcu", "cfr", "fcm",
    "acsm", "scm", "csc", "clubul", "sportiv", "municipal", "asociatia",
    "fotbal", "club",
    # everywhere
    "ii", "2", "b",
}


def fold(text):
    """Lower case, diacritics out, punctuation to spaces, spaces collapsed."""
    if not text:
        return ""
    text = text.replace("ß", "ss")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strict_key(name):
    return fold(name)


def loose_key(name):
    """
    The same name with legal-form words taken out. Used only after a
    strict match has failed, and a match found this way is labelled as
    such in the review file rather than passed off as a clean one.
    """
    words = [w for w in fold(name).split() if w not in FORMS]
    return " ".join(words)


def venue_agrees(ours, theirs):
    """
    Does our ground name and StadiumDB's refer to the same ground? Both
    folded, then one containing the other counts, because sponsors get
    prefixed and dropped constantly ("BBBank Wildpark" / "Wildparkstadion").
    Returns True, False, or None when one side has no name to compare.
    """
    a, b = fold(ours), fold(theirs)
    if not a or not b:
        return None
    a_core = a.replace("stadion", "").replace("stadium", "").replace("arena", "").strip()
    b_core = b.replace("stadion", "").replace("stadium", "").replace("arena", "").strip()
    if a == b:
        return True
    for x, y in ((a, b), (a_core, b_core)):
        if x and y and (x in y or y in x):
            return True
    a_words = {w for w in a_core.split() if len(w) > 3}
    b_words = {w for w in b_core.split() if len(w) > 3}
    if a_words and b_words and (a_words & b_words):
        return True
    return False


# ------------------------------------------------------- the OSM figures

def load_osm_figures():
    """
    capacity-review.csv is where the OpenStreetMap figures already live.
    It only holds clubs the two sources DISAGREED about, or where only
    one of them had a number - an agreement is left out of that file by
    design. So a blank here means "the two agreed, or OSM had nothing",
    not "OSM was not asked". The summary says so every run, because a
    blank column that means two different things is exactly the kind of
    quiet ambiguity this project keeps tripping over.
    """
    figures = {}
    if not os.path.exists(OSM_REVIEW_FILE):
        return figures, False
    with open(OSM_REVIEW_FILE, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            qid = (row.get("clubQid") or "").strip()
            osm = (row.get("_osm") or "").strip()
            if qid and osm.isdigit():
                figures[qid] = int(osm)
    return figures, True


# ------------------------------------------------------------------ main

def main():
    if not os.path.isdir(CLUB_DIR):
        sys.exit(f"{CLUB_DIR} does not exist - run the club layer first")

    files = sorted(f for f in os.listdir(CLUB_DIR)
                   if f.endswith(".json") and f != "index.json")
    if not files:
        sys.exit(f"no country files in {CLUB_DIR}")

    osm_figures, osm_file_present = load_osm_figures()

    rows, summary, failures, readback = [], [], [], []

    # Anything that makes this run less than the whole picture. While
    # this stays empty the run may replace the review file; once it is
    # not, the file is left exactly as the last good run left it.
    incomplete = []

    for position, filename in enumerate(files):
        code = filename[:-5]
        with open(os.path.join(CLUB_DIR, filename), encoding="utf-8") as fh:
            data = json.load(fh)
        clubs = data.get("clubs", [])
        if not clubs:
            continue

        if code not in COUNTRY_PAGES:
            failures.append(
                f"{code}: no StadiumDB country page is configured for it. "
                f"Add a slug to COUNTRY_PAGES in this tool - a wrong guess "
                f"looks exactly like a country with no stadiums")
            incomplete.append(f"{code}: no country page configured")
            continue

        slug, label = COUNTRY_PAGES[code]
        if position:
            time.sleep(REQUEST_GAP_SECONDS)
        url = f"{BASE}/stadiums/{slug}"
        print(f"  {code}  asking StadiumDB for {label} -- {url}")
        body, error = fetch_with_retry(url)
        if error:
            failures.append(f"{code}: {error} - no cross-check done for this country")
            incomplete.append(f"{code}: {error}")
            continue

        grounds = parse_country_table(body)
        if not grounds:
            # A page that parses to nothing is a changed layout, not an
            # empty country, and reporting a whole country as unchecked
            # is better than reporting every club in it as missing.
            failures.append(
                f"{code}: the {label} page returned {len(body)} bytes but no table "
                f"rows parsed out of it - the layout has probably changed")
            incomplete.append(f"{code}: country page did not parse")
            continue

        with_cap = sum(1 for g in grounds if g["capacity"])
        named = sum(1 for g in grounds if g["clubs"])
        print(f"      {len(grounds)} grounds, {with_cap} with a capacity, "
              f"{named} naming at least one club")

        # Index every club name StadiumDB gives, both ways.
        strict, loose = {}, {}
        for ground in grounds:
            for club_name in ground["clubs"]:
                strict.setdefault(strict_key(club_name), []).append((club_name, ground))
                lk = loose_key(club_name)
                if lk:
                    loose.setdefault(lk, []).append((club_name, ground))

        agree = differ = only_sdb = only_ours = ambiguous = 0
        venue_clash = unmatched = 0

        for club in clubs:
            name = club.get("name") or ""
            hits = strict.get(strict_key(name)) or []
            how = "name"
            if not hits:
                lk = loose_key(name)
                hits = loose.get(lk) or [] if lk else []
                how = "name-without-club-prefix"

            if not hits:
                unmatched += 1
                continue

            # More than one ground claims this club. The ground name can
            # break the tie, and when it cannot the row says ambiguous
            # and no capacity is compared.
            if len(hits) > 1:
                narrowed = [h for h in hits
                            if venue_agrees(club.get("venue"), h[1]["name"]) is True]
                if len(narrowed) == 1:
                    hits = narrowed
                    how += "+ground"
                else:
                    ambiguous += 1
                    rows.append(review_row(
                        club, code, None, osm_figures,
                        how=how,
                        verdict=f"{len(hits)} StadiumDB grounds name this club - "
                                f"nothing here says which, so no figure was compared",
                        candidates="; ".join(
                            f"{g['name']} ({g['city']}, {g['capacity'] or 'no capacity'})"
                            for _, g in hits[:5])))
                    continue

            sdb_name, ground = hits[0]
            ours = club.get("capacity")
            theirs = ground["capacity"]
            same_ground = venue_agrees(club.get("venue"), ground["name"])

            readback.append(
                f"{code} {name[:30]:30s} -> {ground['name'][:30]:30s} "
                f"{ground['city'][:16]:16s} "
                f"ours {ours if ours is not None else '-':>7} "
                f"sdb {theirs if theirs is not None else '-':>7}  ({how})")

            # The ground names disagreeing is its own finding and it
            # outranks the capacity comparison, because if these are two
            # different grounds then the two capacities were never about
            # the same thing in the first place.
            if same_ground is False:
                venue_clash += 1
                rows.append(review_row(
                    club, code, ground, osm_figures, how=how,
                    verdict="club names match but the ground names do not - either "
                            "our ground is wrong or the club has moved"))
                continue

            if ours is not None and theirs is not None:
                spread = abs(ours - theirs) / max(ours, theirs)
                if spread <= AGREE_WITHIN:
                    agree += 1
                    continue
                differ += 1
                rows.append(review_row(
                    club, code, ground, osm_figures, how=how,
                    verdict=f"sources differ by {round(spread * 100)}%"))
            elif ours is None and theirs is not None:
                only_sdb += 1
                rows.append(review_row(
                    club, code, ground, osm_figures, how=how,
                    verdict="only StadiumDB has a figure"))
            elif ours is not None and theirs is None:
                only_ours += 1      # one source, nothing to check it against
            # neither has one: nothing to say that the club file does not
            # already say by being blank.

        summary.append(
            f"{code}  {len(clubs)} clubs vs {len(grounds)} StadiumDB grounds  |  "
            f"{agree} agree  |  {differ} differ  |  {venue_clash} ground name clash  |  "
            f"{only_sdb} StadiumDB only  |  {only_ours} ours only  |  "
            f"{ambiguous} ambiguous  |  {unmatched} not in StadiumDB")

    header = ["clubQid", "name", "country", "tier", "venue", "capacity",
              "lat", "lon", "ticketUrl", "source", "note",
              "_ours", "_stadiumdb", "_osm", "_sdbGround", "_sdbCity",
              "_sdbClub", "_sdbUrl", "_match", "_candidates", "_verdict"]

    rows.sort(key=lambda r: (r["country"], r["_verdict"], r["name"]))

    # Same rule the other review files follow: a country that could not
    # be read contributes no rows, and writing the file anyway would
    # delete work nobody has acted on yet, with a green tick.
    existing = os.path.exists(REVIEW_FILE)
    kept = bool(incomplete) and existing
    if not kept:
        with open(REVIEW_FILE, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=header)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    print()
    print("=" * 74)
    print("STADIUMDB CROSS-CHECK  (third opinion, alongside Wikidata and OSM)")
    print("=" * 74)
    for line in summary:
        print("  " + line)
    print()
    if readback:
        print(f"  Read back - the {len(readback)} clubs StadiumDB could be matched to:")
        for line in readback:
            print("    " + line)
        print()
    if kept:
        print("  StadiumDB unreachable for at least one country, review file")
        print(f"  unchanged from the last successful run. {REVIEW_FILE}")
        print("  was NOT rewritten. Not checked this time:")
        for reason in incomplete:
            print(f"    {reason}")
    else:
        if incomplete:
            print(f"  {REVIEW_FILE} did not exist yet, so a partial list was")
            print("  written. It is missing the countries listed at the bottom.")
        print(f"  {len(rows)} club(s) need your eye - written to {REVIEW_FILE}")
        print("  Columns starting with _ are evidence and are ignored by the")
        print("  club builder. Nothing here picks a winner: put the figure you")
        print("  trust in the capacity column, name where it came from in")
        print("  source, record the figure you did NOT take in note, then paste")
        print("  the row into data/clubs-manual.csv.")
    print()
    print("  _ours is what data/clubs/ currently holds, which is Wikidata")
    print("  unless a hand correction has already replaced it.")
    if osm_file_present:
        print(f"  _osm is carried across from {OSM_REVIEW_FILE}, which only")
        print("  holds clubs where Wikidata and OpenStreetMap DISAGREED or where")
        print("  only one of them had a figure. So a blank _osm means the two")
        print("  agreed or OSM had nothing - it does not mean OSM was not asked.")
    else:
        print(f"  _osm is blank on every row: {OSM_REVIEW_FILE} does not")
        print("  exist, so no OpenStreetMap figure was available to carry across.")
    print()
    print("  Matching here is by NAME, not by position - StadiumDB publishes no")
    print("  coordinates. A _match of 'name' is the club's name exactly; anything")
    print("  else is a weaker match and deserves a harder look.")
    if failures:
        print()
        for f in failures:
            print("  ! " + f)
    print("=" * 74)


def review_row(club, code, ground, osm_figures, how, verdict, candidates=""):
    qid = club.get("id", "")
    return {
        "clubQid": qid,
        "name": club.get("name", ""),
        "country": code,
        "tier": "",
        "venue": "",
        "capacity": "",
        "lat": "", "lon": "",
        "ticketUrl": "", "source": "",
        "note": "",
        "_ours": club.get("capacity") if club.get("capacity") is not None else "",
        "_stadiumdb": (ground or {}).get("capacity") or "",
        "_osm": osm_figures.get(qid, ""),
        "_sdbGround": (ground or {}).get("name", ""),
        "_sdbCity": (ground or {}).get("city", ""),
        "_sdbClub": (ground or {}).get("clubsRaw", ""),
        "_sdbUrl": (ground or {}).get("url", ""),
        "_match": how,
        "_candidates": candidates,
        "_verdict": verdict,
    }


if __name__ == "__main__":
    main()
