#!/usr/bin/env python3
"""
crosscheck_stadiumdb.py -- a THIRD opinion on stadium capacities.

Reads data/clubs/*.json and asks StadiumDB.com for every ground it holds
in the same country, then compares the two capacity figures. Where
data/clubs/capacity-review.csv already holds an OpenStreetMap figure for
the same club, that is carried across too, so a row can show all three
numbers side by side.

It NEVER changes a club file and it NEVER picks a winner. Where the
sources disagree the row is written with every figure it has and every
source named, and you decide. That is the same contract
crosscheck_capacity.py has - this tool only adds a source.


WHY THE MATCHING LOOKS THE WAY IT DOES

crosscheck_capacity.py matches a club to a ground by POSITION, within
500m, deliberately not by name, because name matching is what scored
Eutin 08 against FC 08 Homburg on a shared "08". StadiumDB publishes no
coordinates on any page - checked across 27 pages in nine countries - so
position matching is not available here and name matching is all there
is.

Worse, the name it publishes is a SHORT one. A country page is a table
of Name | City | Clubs | Capacity, and the Clubs cell holds "Borussia",
not "Borussia Dortmund"; "Bayern", not "FC Bayern Muenchen". The city is
carrying half the club's identity. And the short name is not unique
either: "Borussia" appears against Dortmund, Moenchengladbach and
Neunkirchen, and "Waldhof" against two different Mannheim grounds.

So a match here needs TWO signals to agree, and the tool says which:

  1. THE CLUB SIGNAL. Every word of the Clubs cell must appear in our
     club's name. "Borussia" matches our "Borussia Dortmund"; "Hoffenheim
     II" does not match our "TSG 1899 Hoffenheim", because "ii" is not in
     it. This is a containment test and not equality, because the short
     name is by design a fragment of the long one.

  2. THE PLACE SIGNAL, which is what stops "Borussia" matching three
     clubs. Either StadiumDB's city appears in our club's name, or our
     ground name and theirs agree. One or the other, not both, because
     the city column is in English - "Munich", "Cologne", "Nuremberg" -
     and our names are not, so the city alone would throw away every
     club in a city with an English exonym.

A club that still matches more than one ground after both signals is
reported as AMBIGUOUS and its capacity is NOT compared. Guessing which
row was meant is the exact failure this file exists to avoid.

A club that matches on the club signal, and on the city, while the two
ground names disagree, is written out under its own verdict rather than
quietly trusted. That disagreement means either our ground is wrong or
the club has moved, and both are worth your eye - and if they are two
different grounds then the two capacities were never about the same
thing.

StadiumDB's robots.txt (33 bytes) disallows only /lay-gfx/, so nothing
this reads carries a crawl restriction. It is one request per country,
because a country page is the whole country in one table.

Free, no key.

Usage:  python3 tools/crosscheck_stadiumdb.py
        python3 tools/crosscheck_stadiumdb.py --offline DE=path.tsv
            reads a saved Name/City/Clubs/Capacity TSV instead of the
            network, which is how the matching was developed from a
            sandbox that cannot reach the site.
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
# Hand-written, because a slug is not derivable from an ISO code and a
# wrong guess looks exactly like a country with no grounds in it. Both
# of these were confirmed against the site: /stadiums/germany,
# /stadiums/de, /stadiums/rom, /stadiums/romania and /stadiums/ro are
# all genuine 404s. France's "fra" was confirmed the same way on
# 2026-09-25, from a runner: /stadiums/fra answers 200 with the country
# table, and /stadiums/france, /stadiums/fr and /stadiums/fre are 404s.
# Italy's "ita" likewise on 2026-09-25: /stadiums/ita answers 200,
# /stadiums/italy and /stadiums/it are 404s.
# Switzerland's "sui" on 2026-09-26: /stadiums/sui answers 200, and
# /stadiums/swi, /stadiums/che, /stadiums/switzerland and /stadiums/ch
# are 404s. The page is THIN - under twenty grounds for a country whose
# top two divisions field 22 clubs - so a Swiss club with no StadiumDB
# match is the expected case, not a finding, and it is never agreement.
COUNTRY_PAGES = {
    "DE": ("ger", "Germany"),
    "RO": ("rou", "Romania"),
    "FR": ("fra", "France"),
    "IT": ("ita", "Italy"),
    "CH": ("sui", "Switzerland"),
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
            # StadiumDB 404s honestly - a real 404 status with an 11.5KB
            # error page - so unlike europlan-online the status code can
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


def capacity_of(raw):
    """
    The capacity column separates thousands with a space ("18 482"), so
    every non-digit comes out before the number is read. A figure outside
    the plausible range is treated as no figure rather than as a number.
    """
    digits = re.sub(r"[^\d]", "", raw.replace(" ", " "))
    if not digits:
        return None
    value = int(digits)
    return value if 100 <= value <= 200000 else None


def split_clubs(raw):
    """
    The Clubs cell holds one club, several separated by commas, or a
    dash meaning the site records no club there.
    """
    if not raw or raw.strip() in ("-", "–", "—"):
        return []
    parts = re.split(r"\s*[,/;]\s*", raw)
    return [p.strip() for p in parts if p.strip() and p.strip() not in ("-", "–")]


def parse_country_table(body):
    """
    A StadiumDB country page is a table of
    Name | City | Clubs | Capacity, with the ground's own page linked
    from the first cell. Returns a list of ground dicts.
    """
    grounds = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S | re.I):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(cells) < 4:
            continue
        name = text_of(cells[0])
        if not name:
            continue
        link = re.search(r'href="([^"]+)"', cells[0])
        url = link.group(1) if link else ""
        if url.startswith("/"):
            url = BASE + url
        grounds.append(ground(name, text_of(cells[1]), text_of(cells[2]),
                              capacity_of(text_of(cells[3])), url))
    return grounds


def ground(name, city, clubs_raw, capacity, url=""):
    return {"name": name, "city": city, "clubs": split_clubs(clubs_raw),
            "clubsRaw": clubs_raw, "capacity": capacity, "url": url}


def read_offline(path):
    """A saved Name/City/Clubs/Capacity TSV, for developing the matching."""
    grounds = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            grounds.append(ground(parts[0], parts[1], parts[2],
                                  capacity_of(parts[3])))
    return grounds


# ------------------------------------------------------------- name keys

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


def words(text):
    return [w for w in fold(text).split() if w]


# Words that say what kind of organisation a club is rather than which
# club it is. Dropped from the CLUB signal only, and only from our side,
# so that StadiumDB's "Bayern" can be found inside our "FC Bayern
# Muenchen". Years and squad numbers are deliberately absent: "08" is the
# whole difference between some club names and this project has already
# been bitten once by treating a shared number as a match.
CLUB_FORMS = {
    "fc", "sc", "sv", "tsv", "tsg", "vfb", "vfl", "vfr", "fsv", "ssv",
    "spvgg", "sg", "msv", "bsc", "ksc", "kfc", "bfc", "asv", "dsc",
    "tus", "djk", "rsv", "wsv", "sgv", "svg", "fsc", "tv",
    "cs", "acs", "afc", "csm", "csu", "cso", "fcu", "fcm", "acsm", "scm",
    "csc", "asu", "cf", "as",
}

# Words that say what kind of place a ground is rather than which ground
# it is. Two grounds sharing only one of these have nothing in common -
# "Stadionul Municipal Sibiu" and "Stadionul Municipal Botosani" are not
# the same ground and must never be treated as agreeing.
GROUND_FORMS = {
    "stadion", "stadionul", "stadium", "stadio", "stadien", "arena",
    "arena", "park", "sportpark", "sport", "sports", "sportanlage",
    "sportplatz", "sportzentrum", "platz", "municipal", "municipala",
    "orasenesc", "oraseneasca", "central", "centrala", "city", "der",
    "am", "an", "die", "das", "des", "von", "de", "la", "dem", "und",
}


# The marker that says a name is a club's RESERVE side rather than its
# first team. It has to agree on both sides of a match, and it is the one
# word that a containment test must not be allowed to ignore: StadiumDB
# writes "Borussia" and "Borussia II" as two separate grounds, and
# without this every reserve side in the file matched its first team's
# stadium and inherited a capacity ten times too big.
TEAM_MARKERS = {"ii", "2", "b", "iii", "3", "u21", "u23", "u19", "amateure"}


def team_marker(name):
    return {w for w in words(name) if w in TEAM_MARKERS}


def club_signal(our_name, their_club, town_words):
    """
    Does StadiumDB's short club name sit inside ours? Every word of
    theirs has to be one of ours, with the legal-form words on our side
    allowed to go unmatched - the site publishes "Bayern" where we hold
    "FC Bayern Muenchen". Returns the match label, or None.

    Two things the leniency must not swallow.

    The RESERVE MARKER has to match exactly, in both directions. The site
    lists "Borussia" and "Borussia II" as two grounds, and without this
    every reserve side matched its first team's stadium and took on a
    capacity ten times too big.

    A SHORT NAME THAT IS ONLY THE TOWN names the town's main club and
    nobody else. StadiumDB writes VfL Wolfsburg as "Wolfsburg", and
    "Wolfsburg" is inside "Lupo Martini Wolfsburg" too - so where the
    short name says nothing but the town, our club may not say anything
    beyond the town either, bar its legal form and a founding year.
    """
    theirs = [w for w in words(their_club) if w not in CLUB_FORMS]
    if not theirs:
        return None
    ours = set(words(our_name))
    if not ours:
        return None
    if team_marker(our_name) != team_marker(their_club):
        return None
    if all(w in town_words for w in theirs):
        distinctive = {w for w in ours
                       if w not in CLUB_FORMS and w not in town_words
                       and not w.isdigit()}
        if distinctive:
            return None
    if set(words(their_club)) == ours:
        return "name-exact"
    if all(w in ours for w in theirs):
        return "name-contained"
    return None


def ground_signal(our_venue, their_ground):
    """
    Do our ground name and theirs refer to the same ground?

    True, False, or None when one side has no name to compare with.
    Sponsors are prefixed and dropped constantly - "BBBank Wildpark" is
    the "Wildparkstadion" - so containment counts, and a shared
    distinctive word counts. A shared GROUND_FORMS word never does.
    """
    a, b = fold(our_venue), fold(their_ground)
    if not a or not b:
        return None
    if a == b:
        return True
    a_words = [w for w in a.split() if w not in GROUND_FORMS]
    b_words = [w for w in b.split() if w not in GROUND_FORMS]
    if not a_words or not b_words:
        # Nothing distinctive on one side: "Stadionul Municipal" alone
        # cannot confirm or deny anything.
        return None
    a_core, b_core = " ".join(a_words), " ".join(b_words)
    if a_core in b_core or b_core in a_core:
        return True
    # A German ground name is often one long compound word against the
    # other side's two - "Grenzlandstadion" against "Grenzland-Stadion",
    # "Volksparkstadion" against "Volkspark Stadion".
    a_join, b_join = "".join(a.split()), "".join(b.split())
    if a_join == b_join or a_join in b_join or b_join in a_join:
        return True
    shared = {w for w in a_words if len(w) >= 5} & {w for w in b_words if len(w) >= 5}
    return bool(shared)


def place_signal(club, gr, town_words):
    """
    Does anything but the club's name tie it to this ground? Returns
    "city", or "ground", or None.

    The city is compared against our club's NAME, because the club layer
    carries no city of its own - CLUB_QUERY in fetch_clubs.py selects
    cityLabel but never binds a city, so every club in data/clubs/ has
    "city": null. That is a known open problem, not something assumed
    here, and when it is fixed this check gets stronger for free.

    town_words is every town StadiumDB names anywhere in this country. It
    is what stops the ground signal on its own from crossing the map:
    "AFC Metalul Buzau" matched the "Stadionul Metalul" in AIUD on the
    ground name alone, 300km away, because both grounds are called after
    the same works. If our club's own name carries a town, the ground has
    to be in that town - and when it carries none, as German club names
    mostly do not, the rule simply does not apply.
    """
    ours = set(words(club.get("name")))
    city_words = [w for w in words(gr["city"]) if w not in GROUND_FORMS]

    town_in_our_name = ours & town_words
    if town_in_our_name and not (town_in_our_name & set(city_words)):
        return None

    if city_words and all(w in ours for w in city_words):
        return "city"
    if ground_signal(club.get("venue"), gr["name"]) is True:
        return "ground"
    return None


# ------------------------------------------------------- the OSM figures

def load_osm_figures():
    """
    capacity-review.csv is where the OpenStreetMap figures already live.
    It holds only the clubs the two sources DISAGREED about, or where
    just one of them had a number - an agreement is left out of that file
    by design. So a blank here means "those two agreed, or OSM had
    nothing", not "OSM was not asked". The summary says so every run,
    because a blank column meaning two different things is exactly the
    kind of quiet ambiguity this project keeps tripping over.
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


# ---------------------------------------------------------------- output

HEADER = ["clubQid", "name", "country", "tier", "venue", "capacity",
          "lat", "lon", "ticketUrl", "source", "note",
          "_ours", "_stadiumdb", "_osm", "_sdbGround", "_sdbCity",
          "_sdbClub", "_sdbUrl", "_match", "_candidates", "_verdict"]


def review_row(club, code, gr, osm_figures, match, verdict, candidates=""):
    qid = club.get("id", "")
    return {
        "clubQid": qid,
        "name": club.get("name", ""),
        "country": code,
        "tier": "", "venue": "", "capacity": "", "lat": "", "lon": "",
        "ticketUrl": "", "source": "", "note": "",
        "_ours": club.get("capacity") if club.get("capacity") is not None else "",
        "_stadiumdb": (gr or {}).get("capacity") or "",
        "_osm": osm_figures.get(qid, ""),
        "_sdbGround": (gr or {}).get("name", ""),
        "_sdbCity": (gr or {}).get("city", ""),
        "_sdbClub": (gr or {}).get("clubsRaw", ""),
        "_sdbUrl": (gr or {}).get("url", ""),
        "_match": match,
        "_candidates": candidates,
        "_verdict": verdict,
    }


# ------------------------------------------------------------------ main

def main():
    offline = {}
    for arg in sys.argv[1:]:
        if arg == "--offline":
            continue
        if "=" in arg:
            code, path = arg.split("=", 1)
            offline[code] = path

    if not os.path.isdir(CLUB_DIR):
        sys.exit(f"{CLUB_DIR} does not exist - run the club layer first")

    # A country file is named by its two-letter code. fixture-links.json
    # lives in the same folder and is not one - reading it as a country
    # file crashed this tool on 2026-09-25.
    files = sorted(f for f in os.listdir(CLUB_DIR)
                   if re.match(r"^[A-Z]{2}\.json$", f))
    if not files:
        sys.exit(f"no country files in {CLUB_DIR}")

    osm_figures, osm_file_present = load_osm_figures()
    rows, summary, failures, readback = [], [], [], []
    incomplete = []          # anything that makes this less than the whole picture

    for position, filename in enumerate(files):
        code = filename[:-5]
        with open(os.path.join(CLUB_DIR, filename), encoding="utf-8") as fh:
            clubs = json.load(fh).get("clubs", [])
        if not clubs:
            continue

        if code in offline:
            grounds = read_offline(offline[code])
            print(f"  {code}  {len(grounds)} grounds read from {offline[code]} (offline)")
        else:
            if code not in COUNTRY_PAGES:
                failures.append(
                    f"{code}: no StadiumDB country page is configured. Add a slug to "
                    f"COUNTRY_PAGES in this tool - a wrong guess looks exactly like a "
                    f"country with no grounds in it")
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
                # A page that parses to nothing is a changed layout, not
                # an empty country. Reporting the country as unchecked is
                # right; reporting every club in it as missing is not.
                failures.append(
                    f"{code}: the {label} page returned {len(body)} bytes but no table "
                    f"rows parsed out of it - the layout has probably changed")
                incomplete.append(f"{code}: country page did not parse")
                continue
            with_cap = sum(1 for g in grounds if g["capacity"])
            named = sum(1 for g in grounds if g["clubs"])
            print(f"      {len(grounds)} grounds, {with_cap} with a capacity, "
                  f"{named} naming at least one club")

        agree = differ = only_sdb = only_ours = 0
        ambiguous = clash = unmatched = neither = 0

        # Every town this country page names, which is what the place
        # signal uses to refuse a match that crosses the country.
        town_words = set()
        for gr in grounds:
            town_words.update(w for w in words(gr["city"]) if w not in GROUND_FORMS)

        for club in clubs:
            hits = []
            for gr in grounds:
                for their_club in gr["clubs"]:
                    label = club_signal(club.get("name"), their_club, town_words)
                    if not label:
                        continue
                    place = place_signal(club, gr, town_words)
                    if not place:
                        continue
                    # A ground name that could neither confirm nor deny
                    # says so, because a match resting on the city alone
                    # has not been checked against a ground at all.
                    if ground_signal(club.get("venue"), gr["name"]) is None:
                        label += "?ground-unchecked"
                    hits.append((f"{label}+{place}", their_club, gr))
                    break

            if not hits:
                unmatched += 1
                continue

            if len(hits) > 1:
                # The ground name is the last thing that can break a tie,
                # and when it cannot, nothing here says which row was
                # meant, so no figure is compared.
                narrowed = [h for h in hits
                            if ground_signal(club.get("venue"), h[2]["name"]) is True]
                if len(narrowed) == 1:
                    hits = narrowed
                else:
                    ambiguous += 1
                    rows.append(review_row(
                        club, code, None, osm_figures,
                        match="ambiguous",
                        verdict=f"{len(hits)} StadiumDB grounds fit this club and nothing "
                                f"here says which, so no figure was compared",
                        candidates="; ".join(
                            f"{g['name']} ({g['city']}, "
                            f"{g['capacity'] if g['capacity'] else 'no capacity'})"
                            for _, _, g in hits[:6])))
                    continue

            match, their_club, gr = hits[0]
            ours, theirs = club.get("capacity"), gr["capacity"]
            same_ground = ground_signal(club.get("venue"), gr["name"])

            readback.append(
                f"{code} {(club.get('name') or '')[:29]:29s} -> "
                f"{gr['name'][:31]:31s} {gr['city'][:14]:14s} "
                f"ours {ours if ours is not None else '-':>7} "
                f"sdb {theirs if theirs is not None else '-':>7}  ({match})")

            # Two different grounds would mean the two capacities were
            # never about the same thing, so this outranks the
            # comparison. What the names disagreeing does NOT establish
            # is that the grounds are different: half the German ones in
            # this file are a sponsor's name against the old one. So the
            # figures get a say in the verdict rather than the row
            # claiming more than it knows.
            if same_ground is False:
                clash += 1
                figures_agree = (
                    ours is not None and theirs is not None
                    and abs(ours - theirs) / max(ours, theirs) <= AGREE_WITHIN)
                rows.append(review_row(
                    club, code, gr, osm_figures, match,
                    verdict=("the two ground names do not match but the two figures do "
                             "- most likely one ground under a sponsor's name and its "
                             "old one, worth confirming"
                             if figures_agree else
                             "the two ground names do not match AND the two figures do "
                             "not either - check which ground each source means before "
                             "trusting either number")))
                continue

            if ours is not None and theirs is not None:
                spread = abs(ours - theirs) / max(ours, theirs)
                if spread <= AGREE_WITHIN:
                    agree += 1
                    continue
                differ += 1
                rows.append(review_row(
                    club, code, gr, osm_figures, match,
                    verdict=f"sources differ by {round(spread * 100)}%"))
            elif ours is None and theirs is not None:
                only_sdb += 1
                rows.append(review_row(
                    club, code, gr, osm_figures, match,
                    verdict="only StadiumDB has a figure"))
            elif ours is not None and theirs is None:
                only_ours += 1       # one source, nothing to check it against
            else:
                neither += 1

        summary.append(
            f"{code}  {len(clubs)} clubs vs {len(grounds)} StadiumDB grounds  |  "
            f"{agree} agree  |  {differ} differ  |  {clash} ground clash  |  "
            f"{only_sdb} StadiumDB only  |  {only_ours} ours only  |  "
            f"{neither} neither  |  {ambiguous} ambiguous  |  "
            f"{unmatched} not matched")

    rows.sort(key=lambda r: (r["country"], r["_verdict"], r["name"]))

    # Same rule the other review files follow: a country that could not
    # be read contributes no rows, and writing the file anyway would
    # delete work nobody has acted on yet, with a green tick.
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
    print("STADIUMDB CROSS-CHECK  (third opinion, beside Wikidata and OpenStreetMap)")
    print("=" * 74)
    for line in summary:
        print("  " + line)
    print()
    if readback:
        print(f"  Read back - the {len(readback)} clubs StadiumDB could be matched to,")
        print("  exactly as understood:")
        for line in sorted(readback):
            print("    " + line)
        print()
    if kept:
        print("  StadiumDB could not be read for at least one country, so the")
        print(f"  review file is unchanged from the last successful run.")
        print(f"  {REVIEW_FILE} was NOT rewritten. Not checked this time:")
        for reason in incomplete:
            print(f"    {reason}")
    else:
        if incomplete:
            print(f"  {REVIEW_FILE} did not exist yet, so a partial list was")
            print("  written. It is missing the countries listed at the bottom.")
        print(f"  {len(rows)} club(s) need your eye - written to {REVIEW_FILE}")
        print("  Columns starting with _ are evidence and are ignored by the club")
        print("  builder. NOTHING HERE PICKS A WINNER: put the figure you trust in")
        print("  the capacity column, name where it came from in source, record the")
        print("  figure you did NOT take in note, then paste the row into")
        print("  data/clubs-manual.csv.")
    print()
    print("  _ours is what data/clubs/ holds now - Wikidata, unless a hand")
    print("  correction has already replaced it.")
    if osm_file_present:
        print(f"  _osm is carried across from {OSM_REVIEW_FILE}, which holds")
        print("  only the clubs where Wikidata and OpenStreetMap disagreed or where")
        print("  just one of them had a figure. A blank _osm therefore means those")
        print("  two agreed or OSM had nothing - not that OSM went unasked.")
    else:
        print(f"  _osm is blank on every row: {OSM_REVIEW_FILE} does not")
        print("  exist, so there was no OpenStreetMap figure to carry across.")
    print()
    print("  Matching is by NAME and CITY, not by position - StadiumDB publishes no")
    print("  coordinates. _match says which two signals agreed. 'name-exact' is our")
    print("  club's whole name; 'name-contained' is StadiumDB's short name sitting")
    print("  inside ours, which is the ordinary case and is weaker.")
    if failures:
        print()
        for f in failures:
            print("  ! " + f)
    print("=" * 74)


if __name__ == "__main__":
    main()
