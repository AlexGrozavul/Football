#!/usr/bin/env python3
"""
propose_coordinates.py -- a second chance for the clubs Wikidata cannot
place on the map.

A club only reaches the map if something in Wikidata says where it plays.
When neither the club nor its ground carries a coordinate, the club is
dropped and the map simply does not have it. Most of the missing German
fourth tier is missing for exactly this reason.

This asks OpenStreetMap instead. There is no position to match on - that
is the whole problem - so it has to match on names, which is weaker and
can be wrong. A wrong coordinate is worse than a missing one: the club
sits in the wrong town and looks entirely normal on the map. So this
tool proposes and never applies:

  * it writes data/clubs/coordinate-review.csv and nothing else
  * every club with no coordinates gets a row, including the ones it
    could not match, so nothing disappears quietly
  * a row that is not one clean answer is marked ambiguous, its lat and
    lon are left blank, and the candidates are listed as evidence
  * every row says how the match was made, in words, so you can judge it

Rows you accept go into data/clubs-manual.csv by hand. The file is
written in that file's column order, so an accepted row pastes straight
across. Columns starting with _ are evidence and are ignored there.

How a match is made, strongest first:

  1. OpenStreetMap links the ground to the club's own Wikidata item.
  2. The ground's operator or name in OpenStreetMap carries the club's
     own name.
  3. Wikidata knows the ground's NAME but not where it is, and
     OpenStreetMap has a ground of that name.
  4. A town or village in OpenStreetMap has its name inside the club's
     name, and there is a stadium within 5 km of it.
  5. The same, but the only thing within 5 km is a named football pitch.

A ground OpenStreetMap calls a stadium is treated as better evidence
than a named pitch, which is why 4 and 5 are separate. Everything found
at a weaker level is still listed in the row, so you see what was
passed over.

Two guards against the obvious ways name matching goes wrong:

  * The club's town in Wikidata, if it has one, is used only to throw
    out a candidate in the wrong part of the country. It is never the
    answer itself - a town centre is not a ground.
  * A reserve team ("II", "U21", "Amateure") is never called confident
    on a town match. Its town is the first team's town and says nothing
    about which of the club's grounds it plays on.
  * A place counts only if its WHOLE name is in the club's name. A
    leading part of it is enough only where the rest is a German
    qualifier ('Garching bei München') or sits in brackets. Added
    2026-09-26: 'Periam Port', 'Târgu Jiu', 'Gheorghe Lazăr' and
    'Câmpulung Moldovenesc' had each been read as a club's own town on
    their first word.
  * An object OpenStreetMap tags as a stadium is not a ground if its
    sport tag names only other sports, or its name says hall, pool or
    rink. Added 2026-09-26 after a sports hall was proposed as a
    ground. Athletics counts as possibly football: a ground with a
    running track is often tagged athletics alone. What is left out
    this way is listed in the run summary.

What a person already decided is not asked again. data/coordinate-
reviews.csv, hand-written, records a proposal that was rejected, held
back or is under investigation. A rejected ground never comes back for
that club, a held or open one reads 'held' or 'open' instead of
'confident', and a club rejected as a whole gets no proposal at all.
The finding stays in the row as evidence either way, with the decision
in its _reviewed column, so a reviewed row never reads as new.

Free, no key. Overpass is a volunteer service, so this asks for one
country at a time and waits between requests.

Usage:  python3 tools/propose_coordinates.py
"""

import csv
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_clubs import (                                    # noqa: E402
    CLUB_QUERY, COUNTRIES, COUNTRY_BOX, OVERFLOW, _s, apply_manual, build_clubs, cell,
    load_manual, load_tiers, overflow_problem, qid, sparql_with_retry)

# ---------------------------------------------------------------- config

CLUB_DIR = "data/clubs"
REVIEW_FILE = os.path.join(CLUB_DIR, "coordinate-review.csv")
# Hand-written: what a person already decided about a proposal. Read,
# never written. See load_reviews().
REVIEWED_FILE = "data/coordinate-reviews.csv"
DECISIONS = ("rejected", "held", "open")

OVERPASS = "https://overpass-api.de/api/interpreter"
USER_AGENT = ("football-fixture-planner/1.0 (personal project; "
              "https://github.com/AlexGrozavul/Football)")

# A ground this far from the middle of the town in the club's name still
# counts as that town's ground. Village grounds sit on the edge of the
# village; 5km covers that without reaching the next town.
PLACE_RADIUS_M = 5000

# A candidate further than this from the club's town in Wikidata is
# thrown out. It is a guard against a same-name village in another
# state, not a measurement.
CITY_LIMIT_KM = 30

# Two OpenStreetMap objects this close together are one ground - the
# stadium outline and the building inside it, most often.
SAME_GROUND_M = 200

REQUEST_GAP_SECONDS = 20
TIMEOUT_SECONDS = 180
MAX_RETRIES = 3

# Overpass hands out a couple of slots per caller and a country's worth
# of requests can use them up. The wait after a busy answer is long on
# purpose: giving up loses a whole country, and the rows then say
# "not checked", which helps nobody.
BUSY_WAIT_SECONDS = 60

# Between countries. The second country arrives straight after the first
# one's batches, which is exactly when the slots are gone.
COUNTRY_GAP_SECONDS = 60

# Overpass takes one "around" clause per place, and a country's worth of
# them in one request is neither polite nor reliable. 50 was the figure
# until 2026-09-26, and Romania's pitch lookup - two requests of up to 50
# villages each - failed in every run that reached it (#6, #7, #9, read
# timeouts and 504s) while every other country's single small request
# came back. Same lesson as NAMES_PER_REQUEST below: a smaller request
# is likelier to come back, and losing one loses less.
PLACES_PER_REQUEST = 10

# Place names per lookup. A long list in one request is what failed on
# the second real run: one lost request took a whole stretch of the
# alphabet with it - Bacău, Blaj, Gheorgheni - and those clubs then read
# as though no place of their name existed.
NAMES_PER_REQUEST = 120

# Between the small chunked requests. The country-wide one still waits
# the full gap.
SMALL_GAP_SECONDS = 10

# Strongest first. The order is the whole decision: a club is confident
# only when exactly one ground matches at the best level it reaches.
LEVELS = ("wikidata-link", "club-name", "ground-name", "stadium-in-town",
          "pitch-in-town")

RESERVE_WORDS = {"ii", "u21", "u23", "amateure", "amateur"}

# A place's name may be matched on its leading words alone only where
# what is cut off is a qualifier: 'Garching bei München', 'Rain am
# Lech', 'Frankfurt (Oder)'. Cutting anywhere else matches a DIFFERENT
# place that happens to share a first word - 'Periam Port' is not
# Periam, 'Târgu Jiu' is not Târgu Cărbunești, 'Gheorghe Lazăr' is not
# Gheorghe Doja, 'Câmpulung Moldovenesc' is not Câmpulung Muscel. All
# four came back 'confident' in run #10 before this list existed.
#
# German only, on purpose. In Romanian 'Galda de Jos' and 'Galda de Sus'
# are two villages, and in French 'Bourg-en-Bresse' and 'Bourg-la-Reine'
# two towns: there the words after 'de' or 'en' are part of the name,
# not a qualifier, and the whole name has to match.
QUALIFIER_WORDS = {"bei", "am", "an", "im", "in", "ob", "auf", "vor",
                   "unter", "ueber", "b", "a", "i", "d"}

# A 'stadium' in OpenStreetMap is not always a football ground. A sports
# hall tagged leisure=stadium was proposed as Flacăra Horezu's ground in
# run #10. A ground is left out when its sport tag names sports and none
# of them is football, or when its name says it is a hall, a pool or a
# rink. A ground with no sport tag at all is kept: most football
# grounds carry none, and dropping them would be the bigger error.
# 'athletics' is kept for the same reason: a town's football ground
# with a running track round it is very often tagged athletics alone,
# and throwing it out can leave a wrong ground as the only candidate -
# worse than proposing nothing.
FOOTBALL_SPORTS = {"soccer", "football", "multi", "association_football",
                   "athletics"}
NOT_A_GROUND_NAME = re.compile(
    r"\b(sala|hala|sporthalle|turnhalle|mehrzweckhalle|palatul|"
    r"patinoar|bazin|schwimm\w*|eishalle|eisstadion|velodrom\w*|"
    r"sports? hall|gymnase|palazzetto|palasport)\b")

# Every stadium in the country, the same net the capacity cross-check
# uses, plus football pitches that carry a name. An unnamed pitch is no
# use here: there would be nothing to match on.
GROUND_QUERY = """
[out:json][timeout:240];
area["ISO3166-1"="%(iso)s"][admin_level=2]->.a;
(
  nwr["leisure"="stadium"](area.a);
  nwr["building"="stadium"](area.a);
);
out tags center;
"""

# Only the places whose names actually occur in a club name. Asking for
# every village in Germany would be a far heavier request for no gain.
#
# Also inside the country's hand-written box from fetch_clubs.py, the
# one the country check uses. Added 2026-09-26 for France: its national
# boundary includes the overseas departments, so the area's bounding box
# spans half the globe and Overpass scans place nodes across all of it.
# France's lookup was ONE request of 19 names and failed in three runs
# running (504s, then read timeouts), while Germany's single request of
# 17 names came back in two minutes - so the size of the request was not
# the problem and splitting it would only have repeated it. The box
# keeps the area filter too, so nothing outside the country is added;
# what it drops is a place outside the box, which for France is the
# overseas departments, where no tracked club plays.
PLACE_QUERY = """
[out:json][timeout:240];
area["ISO3166-1"="%(iso)s"][admin_level=2]->.a;
node["place"~"^(city|town|village|suburb)$"]["name"~"^(%(names)s)([ /,-].*)?$",i](area.a)%(box)s;
out tags center;
"""


def box_filter(code):
    """The Overpass (south,west,north,east) filter for a country's box,
    or nothing where fetch_clubs.py has no box for it."""
    box = COUNTRY_BOX.get(code)
    if not box:
        return ""
    return "(%.2f,%.2f,%.2f,%.2f)" % (box["lat"][0], box["lon"][0],
                                      box["lat"][1], box["lon"][1])

# Named football pitches, but only around the places a club name
# pointed at. Country-wide this would be tens of thousands of objects.
PITCH_QUERY_HEAD = """
[out:json][timeout:240];
(
"""
PITCH_QUERY_TAIL = """
);
out tags center;
"""

NAME_TAGS = ("name", "official_name", "alt_name", "short_name", "operator")
TOWN_TAGS = ("addr:city", "addr:place", "addr:suburb", "addr:town")

# The club's town, and what Wikidata thinks the item actually is. The
# second one matters: a squad list carries a league tag like a club does,
# and arrives here looking like a club with no ground.
CITY_QUERY = """
SELECT ?club ?city ?cityLabel ?coord ?rank ?typeLabel WHERE {
  VALUES ?club { %(clubs)s }
  OPTIONAL { ?club wdt:P31 ?type }
  OPTIONAL {
    { ?club wdt:P159 ?city . BIND(1 AS ?rank) }
    UNION
    { ?club wdt:P131 ?city . BIND(2 AS ?rank) }
    OPTIONAL { ?city wdt:P625 ?coord }
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "%(lang)s,en" }
}
"""

POINT_RE = re.compile(r"Point\(\s*(-?[\d.]+)\s+(-?[\d.]+)\s*\)")


# ------------------------------------------------------------------ http

def overpass(query):
    body = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(
        OVERPASS, data=body,
        headers={"User-Agent": USER_AGENT,
                 "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def overpass_with_retry(query, what):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return overpass(query), None
        except urllib.error.HTTPError as exc:
            # 429 and 504 are Overpass saying it is busy, not that the
            # query is wrong. Waiting is the documented remedy.
            if exc.code in (429, 502, 503, 504) and attempt < MAX_RETRIES:
                print(f"    Overpass busy ({exc.code}) on {what}, waiting "
                      f"{BUSY_WAIT_SECONDS}s")
                time.sleep(BUSY_WAIT_SECONDS)
                continue
            return None, f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < MAX_RETRIES:
                print(f"    network problem on {what}, retrying: {exc}")
                time.sleep(30)
                continue
            return None, f"network error: {exc}"
        except ValueError:
            # Overpass answers 200 with a truncated body when it gives
            # up mid-answer, which arrives here as broken JSON.
            if attempt < MAX_RETRIES:
                print(f"    answer was cut off on {what}, retrying")
                time.sleep(30)
                continue
            return None, "answer was cut off mid-JSON"
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


UMLAUTS = (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "ae"), ("Ö", "oe"),
           ("Ü", "ue"), ("ß", "ss"))


def fold(text):
    """
    One spelling for two sources. Umlauts become ae/oe/ue, every other
    accent is dropped and punctuation becomes a space, so 'Rödinghausen'
    and 'Roedinghausen' both come out as 'roedinghausen'.
    """
    if not text:
        return ""
    for src, dst in UMLAUTS:
        text = text.replace(src, dst)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^0-9a-zA-Z]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def phrase_in(needle, haystack):
    """Whole words only: 'sand' is not inside 'Sandhausen'."""
    if not needle or not haystack:
        return False
    return f" {needle} " in f" {haystack} "


def words(name):
    """The club's name in its own spelling, punctuation dropped."""
    return [w for w in re.split(r"\W+", name, flags=re.UNICODE) if w]


def de_adjective(word):
    """
    German names a club after its town with an -er on the end:
    Torgelower FC Greif plays in Torgelow. Only worth trying on a long
    word, and a wrong guess just asks about a place that does not exist.
    """
    return word[:-2] if len(word) >= 6 and word.lower().endswith("er") else None


def name_ngrams(name, longest=3):
    """
    Every run of up to three words in a club's name, which is what gets
    asked of OpenStreetMap's place names. 'TSV Steinbach Haiger' asks
    about Steinbach, Haiger and Steinbach Haiger among others; only the
    ones that are really places come back.
    """
    parts = [w for w in words(name) if not w.isdigit()]
    grams = []
    for size in range(1, longest + 1):
        for start in range(len(parts) - size + 1):
            gram = " ".join(parts[start:start + size])
            least = 3 if size == 1 else 4
            if len(gram.replace(" ", "")) >= least and gram not in grams:
                grams.append(gram)
    for word in parts:
        stem = de_adjective(word)
        if stem and len(stem) >= 3 and stem not in grams:
            grams.append(stem)
    return grams


def club_forms(name):
    """
    The club's name as written, and again with German -er endings taken
    off, so 'Torgelower FC Greif' can also be read as 'Torgelow FC
    Greif'. The second form is marked, because a match on it is a
    slightly longer reach and the row should say so.
    """
    plain = fold(name)
    stemmed = " ".join(
        fold(de_adjective(word) or word) for word in words(name))
    forms = [(plain, "")]
    if stemmed and stemmed != plain:
        forms.append((stemmed, " (the club's name carries it as an "
                               "adjective, the German -er ending)"))
    return forms


def place_cuts(place_name, parts):
    """
    How many leading words of a place's name may stand for the whole
    place: all of them, and a shorter run only where the words cut off
    are a qualifier - they begin with a word like 'bei' or 'am', or sat
    in brackets or after a comma or slash in the name as written.
    """
    sizes = [len(parts)]
    for cut in range(1, len(parts)):
        if parts[cut] in QUALIFIER_WORDS:
            sizes.append(cut)
    head = re.split(r"[(,/]", place_name or "", maxsplit=1)[0]
    if head != place_name:
        size = len(fold(head).split())
        if 0 < size < len(parts):
            sizes.append(size)
    return sorted(set(sizes), reverse=True)


def place_in_club(place_name, forms, parts=None):
    """
    Does this place's name sit inside the club's name? OpenStreetMap
    often carries the long official form - 'Garching bei München' for
    Garching, 'Rain am Lech' for Rain - so a leading run of its words
    counts too, but ONLY where the rest is such a qualifier. Everywhere
    else the whole name has to be in the club's name: a first word
    shared with another town is not the town. Returns what matched and
    any caveat, longest first.
    """
    parts = parts if parts is not None else fold(place_name).split()
    for size in place_cuts(place_name, parts):
        lead = " ".join(parts[:size])
        if len(lead.replace(" ", "")) < 3:
            continue
        for folded, caveat in forms:
            if phrase_in(lead, folded):
                return lead, caveat
    return None, None


def is_reserve(name):
    parts = fold(name).split()
    return bool(parts) and (
        any(p in RESERVE_WORDS for p in parts) or parts[-1] == "2")


def not_a_football_ground(tags):
    """
    Why this OpenStreetMap object is not a football ground, or None.
    Only what the object says about itself is used.
    """
    sports = {s.strip().lower() for s in re.split(r"[;,]", tags.get("sport", ""))
              if s.strip()}
    if sports and not sports & FOOTBALL_SPORTS:
        return f"its sport tag is {tags['sport']!r}"
    for tag in ("name", "official_name"):
        if tags.get(tag) and NOT_A_GROUND_NAME.search(fold(tags[tag])):
            return f"its {tag} {tags[tag]!r} is a hall, pool or rink"
    return None


def elements(payload, default_kind, excluded=None):
    """
    Flatten an Overpass answer into ground records. Objects that say they
    are not football grounds are left out, and named in `excluded` if a
    dict is passed, so the summary can say what was passed over.
    """
    out = {}
    for el in payload.get("elements", []):
        tags = el.get("tags") or {}
        reason = not_a_football_ground(tags)
        if reason:
            if excluded is not None:
                ref = f"{el.get('type')}/{el.get('id')}"
                excluded[ref] = f"{tags.get('name') or 'unnamed'} [{ref}]: {reason}"
            continue
        lat = el.get("lat") if el.get("lat") is not None else (el.get("center") or {}).get("lat")
        lon = el.get("lon") if el.get("lon") is not None else (el.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        ref = f"{el.get('type')}/{el.get('id')}"
        stadium = tags.get("leisure") == "stadium" or tags.get("building") == "stadium"
        out[ref] = {
            "ref": ref, "lat": lat, "lon": lon, "tags": tags,
            "name": tags.get("name") or tags.get("official_name") or "",
            "kind": "stadium" if stadium else default_kind,
            "town": next((tags[t] for t in TOWN_TAGS if tags.get(t)), ""),
            # folded once here: this gets compared against every club
            "folded": {tag: fold(tags[tag]) for tag in NAME_TAGS if tags.get(tag)},
        }
    return out


def places(payload):
    out = []
    for el in payload.get("elements", []):
        tags = el.get("tags") or {}
        lat = el.get("lat") if el.get("lat") is not None else (el.get("center") or {}).get("lat")
        lon = el.get("lon") if el.get("lon") is not None else (el.get("center") or {}).get("lon")
        if lat is None or lon is None or not tags.get("name"):
            continue
        out.append({"name": tags["name"], "kind": tags.get("place", "place"),
                    "lat": lat, "lon": lon, "parts": fold(tags["name"]).split()})
    return out


def km(distance_m):
    return round(distance_m / 1000.0, 1)


# ------------------------------------------------------ reviewed before

REVIEW_COLUMNS = ["clubQid", "name", "country", "decision", "osmRef",
                  "reviewed", "reason"]


def load_reviews():
    """
    data/coordinate-reviews.csv -- what a person already decided about a
    proposal, so it does not come back next month looking brand new.
    Hand-written; this tool reads it and never writes it.

    One row per club per decision:
      rejected + osmRef   that ground is wrong for that club. It is taken
                          out of the club's candidates, so it can never be
                          proposed again; any OTHER ground is still judged
                          on its merits and the row says a ground was
                          rejected before.
      rejected, no osmRef the club itself is not to be placed - dissolved,
                          or not a club. Nothing is proposed for it while
                          the row stands; what would have been proposed
                          is still listed as evidence.
      held + osmRef       the ground looks right and is being kept back on
                          purpose (no roster behind the club, say). If the
                          tool proposes that same ground again the row
                          reads 'held', not 'confident'. If it proposes a
                          different one, the row stays as the tool says
                          and notes that the held ground was another.
      open (osmRef optional) a question is being worked on; the proposal
                          is kept as evidence and reads 'open'.

    Returns ({clubQid: [review, ...]}, readback lines, problems).
    """
    reviews, readback, problems = {}, [], []
    if not os.path.exists(REVIEWED_FILE):
        readback.append(f"{REVIEWED_FILE} does not exist - no proposal has "
                        f"been reviewed before")
        return reviews, readback, problems
    seen = set()
    with open(REVIEWED_FILE, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, restkey=OVERFLOW)
        headers = [_s(h) for h in (reader.fieldnames or [])]
        missing = [c for c in REVIEW_COLUMNS if c not in headers]
        if missing:
            problems.append(f"{REVIEWED_FILE} line 1: missing column(s) "
                            f"{', '.join(missing)} - the file was not read")
            return reviews, readback, problems
        for raw in reader:
            line = reader.line_num
            extra = raw.pop(OVERFLOW, None)
            if extra:
                problems.append(overflow_problem(
                    REVIEWED_FILE, line, len(reader.fieldnames), extra))
                continue
            row = {_s(k): _s(v) for k, v in raw.items()}
            if not any(row.values()):
                continue
            why = None
            if not re.match(r"^Q\d+$", row["clubQid"]):
                why = f"clubQid {row['clubQid']!r} is not a Q-id"
            elif row["decision"] not in DECISIONS:
                why = (f"decision {row['decision']!r} is not one of "
                       f"{', '.join(DECISIONS)}")
            elif row["osmRef"] and not re.match(r"^(node|way|relation)/\d+$",
                                                row["osmRef"]):
                why = f"osmRef {row['osmRef']!r} is not node/, way/ or relation/<id>"
            elif row["decision"] == "held" and not row["osmRef"]:
                why = "a 'held' row needs the osmRef of the ground being held"
            elif not re.match(r"^\d{4}-\d{2}-\d{2}$", row["reviewed"]):
                why = f"reviewed {row['reviewed']!r} is not a date like 2026-09-26"
            elif not row["reason"]:
                why = "reason is empty - a decision nobody can read back is not kept"
            elif (row["clubQid"], row["osmRef"]) in seen:
                why = (f"{row['clubQid']} {row['osmRef'] or '(whole club)'} is "
                       f"already decided on an earlier line")
            if why:
                problems.append(f"{REVIEWED_FILE} line {line}: {why} - row ignored")
                continue
            seen.add((row["clubQid"], row["osmRef"]))
            row["line"] = line
            reviews.setdefault(row["clubQid"], []).append(row)
            readback.append(
                f"line {line:3d}  {row['country']:2s} {row['clubQid']:11s} "
                f"{row['name'][:28]:28s} {row['decision']:8s} "
                f"{row['osmRef'] or '(whole club)':18s} {row['reviewed']}")
    return reviews, readback, problems


def review_note(review):
    return (f"{review['decision']} {review['reviewed']}"
            f"{' ' + review['osmRef'] if review['osmRef'] else ''}: "
            f"{review['reason']}")


# ------------------------------------------------------------- proposing

def add_candidate(found, ground, level, how, town=""):
    """
    One ground can be reached by several routes, and one ground can be
    two OpenStreetMap objects a few metres apart. Both collapse here, and
    the strongest reason wins.
    """
    for existing in found:
        near = metres(existing["ground"]["lat"], existing["ground"]["lon"],
                      ground["lat"], ground["lon"]) <= SAME_GROUND_M
        if existing["ground"]["ref"] == ground["ref"] or near:
            if LEVELS.index(level) < LEVELS.index(existing["level"]):
                existing["level"] = level
                existing["how"] = how
                if ground.get("name") and ground["kind"] == "stadium":
                    existing["ground"] = ground
            if town and not existing["town"]:
                existing["town"] = town
            return
    found.append({"ground": ground, "level": level, "how": how,
                  "town": town or ground.get("town", "")})


def candidates_for(club, grounds, place_list):
    """Everything OpenStreetMap offers for one club, with its reason."""
    name = club.get("name") or club["id"]
    forms = club_forms(name)
    folded = forms[0][0]
    venue = fold(club.get("venue") or "")
    found = []

    for ground in grounds.values():
        tags = ground["tags"]

        if club["id"].startswith("Q") and club["id"] in (
                tags.get("wikidata"), tags.get("operator:wikidata"),
                tags.get("subject:wikidata")):
            add_candidate(found, ground, "wikidata-link",
                          "OpenStreetMap links this ground to the club's own "
                          f"Wikidata item ({club['id']})")
            continue

        if len(folded) >= 6:
            hit = next((tag for tag, value in ground["folded"].items()
                        if phrase_in(folded, value)), None)
            if hit:
                add_candidate(found, ground, "club-name",
                              f"the ground's {hit} in OpenStreetMap is "
                              f"{tags[hit]!r}, which carries the club's name")
                continue

        if venue and len(venue) >= 6 and venue in ground["folded"].values():
            add_candidate(found, ground, "ground-name",
                          f"Wikidata knows the club's ground as "
                          f"{club['venue']!r} but not where it is; this "
                          f"OpenStreetMap ground has that name")

    for place in place_list:
        lead, caveat = place_in_club(place["name"], forms, place["parts"])
        if not lead:
            continue
        for ground in grounds.values():
            away = metres(place["lat"], place["lon"], ground["lat"], ground["lon"])
            if away > PLACE_RADIUS_M:
                continue
            level = "stadium-in-town" if ground["kind"] == "stadium" else "pitch-in-town"
            what = "stadium" if ground["kind"] == "stadium" else "named football pitch"
            add_candidate(found, ground, level,
                          f"{place['name']!r} in the club's name is a "
                          f"{place['kind']} in OpenStreetMap{caveat}, and this "
                          f"{what} is {km(away)} km from the middle of it",
                          town=place["name"])
    return found


def describe(candidate):
    ground = candidate["ground"]
    label = ground["name"] or "unnamed " + ground["kind"]
    where = f" ({candidate['town']})" if candidate["town"] else ""
    return f"{label}{where} [{ground['ref']}]"


def propose(club, grounds, place_list, reviews=()):
    """Returns the review row for one club with no coordinates."""
    row = propose_unreviewed(club, grounds, place_list, reviews)
    return apply_reviews(row, reviews)


def apply_reviews(row, reviews):
    """
    Lay what a person already decided over what the tool found. The tool's
    own finding stays in the row as evidence; only the verdict says the
    decision, so a reviewed row never reads as new.
    """
    if not reviews:
        return row
    row["_reviewed"] = " | ".join(review_note(r) for r in reviews)
    whole = next((r for r in reviews
                  if r["decision"] == "rejected" and not r["osmRef"]), None)
    if whole:
        found = row["_osmRef"] or row["_alternatives"]
        row["_alternatives"] = "; ".join(filter(None, [
            (f"would have proposed {row['_osmName'] or 'a ground'} "
             f"[{row['_osmRef']}]") if row["_osmRef"] else "",
            row["_alternatives"]]))
        row["_verdict"] = (f"rejected - the club itself was rejected on "
                           f"{whole['reviewed']}, nothing is proposed while "
                           f"{REVIEWED_FILE} line {whole['line']} stands"
                           + ("" if found else "; the tool found nothing anyway"))
        row["venue"] = row["lat"] = row["lon"] = row["source"] = ""
        return row
    if row["_verdict"] != "confident":
        return row
    for review in reviews:
        if review["decision"] == "rejected":
            continue
        if review["osmRef"] and review["osmRef"] != row["_osmRef"]:
            row["_reviewed"] += (f" | NOTE: the {review['decision']} ground was "
                                 f"{review['osmRef']}; this proposal "
                                 f"({row['_osmRef']}) is new")
            continue
        word = "held" if review["decision"] == "held" else "open"
        row["_verdict"] = (f"{word} - reviewed {review['reviewed']}, "
                           f"{REVIEWED_FILE} line {review['line']}: do not "
                           f"paste this row while that line stands")
        return row
    return row


def propose_unreviewed(club, grounds, place_list, reviews=()):
    name = club.get("name") or club["id"]
    city = club.get("_city") or {}
    found = candidates_for(club, grounds, place_list)
    # A ground somebody already rejected for this club never comes back.
    rejected = {r["osmRef"] for r in reviews
                if r["decision"] == "rejected" and r["osmRef"]}
    if rejected:
        found = [c for c in found if c["ground"]["ref"] not in rejected]

    too_far = []
    if city.get("lat") is not None:
        near = []
        for candidate in found:
            away = km(metres(city["lat"], city["lon"],
                             candidate["ground"]["lat"], candidate["ground"]["lon"]))
            candidate["cityKm"] = away
            (near if away <= CITY_LIMIT_KM else too_far).append(candidate)
        found = near

    row = {
        "name": name,
        "_reviewed": "",
        "_city": city.get("name", ""),
        "_cityKm": "",
        "_osmName": "", "_osmTown": "", "_osmRef": "",
        "_how": "", "_alternatives": "",
        "venue": "", "lat": "", "lon": "", "source": "",
    }

    if club.get("_unchecked"):
        caveat = ("part of the place lookup did not come back, so there may be "
                  "candidates this row never saw")
        row["_alternatives"] = caveat

    if not found:
        if too_far:
            row["_alternatives"] = "; ".join(
                [row["_alternatives"]] * bool(row["_alternatives"])
                + [describe(c) for c in too_far[:5]])
            row["_verdict"] = (
                f"no match - every candidate is more than {CITY_LIMIT_KM} km from "
                f"{city['name']}, the club's town in Wikidata, so each one is some "
                f"other place of the same name")
        elif club.get("_unchecked"):
            row["_verdict"] = (
                "not checked - part of the place lookup did not come back, and it "
                "covered this club's name, so nothing was really tested for it")
        elif any(place_in_club(p["name"], club_forms(name), p["parts"])[0]
                 for p in place_list):
            row["_verdict"] = ("no match - a place in the club's name was found, but "
                               f"OpenStreetMap has no named ground within "
                               f"{PLACE_RADIUS_M // 1000} km of it")
        else:
            row["_verdict"] = ("no match - nothing in the club's name is the name of "
                               "a place OpenStreetMap knows, and no ground names "
                               "the club")
        return row

    best = min(LEVELS.index(c["level"]) for c in found)
    shortlist = [c for c in found if LEVELS.index(c["level"]) == best]
    others = [c for c in found if LEVELS.index(c["level"]) != best]
    pick = shortlist[0]
    reserve = is_reserve(name) and pick["level"].endswith("in-town")

    if len(shortlist) == 1 and not reserve:
        # One answer at the best evidence there is. Fill it in, and still
        # say what was passed over on the way.
        row["_osmName"] = pick["ground"]["name"] or ""
        row["_osmTown"] = pick["town"] or pick["ground"].get("town", "")
        row["_osmRef"] = pick["ground"]["ref"]
        row["_how"] = pick["how"]
        if pick.get("cityKm") is not None:
            row["_cityKm"] = pick["cityKm"]
        row["_alternatives"] = "; ".join(
            [row["_alternatives"]] * bool(row["_alternatives"])
            + [describe(c) for c in others[:5]])
        row["_verdict"] = "confident"
        row["venue"] = pick["ground"]["name"] or ""
        row["lat"] = round(pick["ground"]["lat"], 6)
        row["lon"] = round(pick["ground"]["lon"], 6)
        row["source"] = "https://www.openstreetmap.org/" + pick["ground"]["ref"]
        return row

    # Ambiguous. No ground is named in the OpenStreetMap columns, because
    # naming one of several would read as a choice. They all go in the
    # alternatives column instead, strongest first.
    row["_how"] = why_several(shortlist)
    row["_alternatives"] = "; ".join(
        [row["_alternatives"]] * bool(row["_alternatives"])
        + [describe(c) for c in (shortlist + others)[:6]])
    if reserve:
        row["_verdict"] = ("ambiguous - reserve team, so the town in the name is the "
                           "first team's town and says nothing about which of the "
                           "club's grounds this side plays on")
    else:
        row["_verdict"] = (f"ambiguous - {len(shortlist)} grounds match equally "
                           f"well, nothing here can choose between them")
    return row


def why_several(shortlist):
    """One sentence covering a whole shortlist, not one ground of it."""
    level = shortlist[0]["level"]
    count = len(shortlist)
    if level == "wikidata-link":
        return f"{count} OpenStreetMap grounds are linked to the club's Wikidata item"
    if level == "club-name":
        return f"{count} OpenStreetMap grounds carry the club's name"
    if level == "ground-name":
        return (f"{count} OpenStreetMap grounds have the name Wikidata gives "
                f"the club's ground")
    town = shortlist[0]["town"] or "the town in the club's name"
    what = "stadiums" if level == "stadium-in-town" else "named football pitches"
    if count == 1:
        return (f"{town!r} in the club's name is a place in OpenStreetMap, and "
                f"there is one of its {what} within "
                f"{PLACE_RADIUS_M // 1000} km")
    return (f"{town!r} in the club's name is a place in OpenStreetMap, and "
            f"{count} {what} lie within {PLACE_RADIUS_M // 1000} km of it")


def flag_shared_grounds(rows):
    """
    Two clubs proposed at one ground would put two pins on one spot, the
    thing that has already gone wrong here with duplicate Wikidata items.
    Sometimes it is simply true - a town's clubs share the municipal
    ground - so this does not throw either row away. It says so on both.
    """
    by_ground, shared = {}, []
    for row in rows:
        if row["_verdict"].split(" ")[0] == "confident" and row["_osmRef"]:
            by_ground.setdefault(row["_osmRef"], []).append(row)
    for ref, group in sorted(by_ground.items()):
        if len(group) < 2:
            continue
        names = [row["name"] for row in group]
        shared.append(f"{ref}  {' / '.join(names)}")
        for row in group:
            others = [n for n in names if n != row["name"]]
            note = "the same ground is proposed for " + ", ".join(others)
            row["_alternatives"] = (
                f"{row['_alternatives']}; {note}" if row["_alternatives"] else note)
    return shared


# --------------------------------------------------------------- country

def missing_clubs(code, lang, tiers, labels, manual_rows, failures, incomplete,
                  summary=None):
    """The clubs fetch_clubs.py drops: they have a tier but no position."""
    wanted = [lid for lid, t in tiers.items()
              if t != "skip" and labels.get(lid, {}).get("country", code) == code]
    if not wanted:
        failures.append(f"{code}: no leagues mapped for this country yet")
        incomplete.append(f"{code}: no leagues mapped, so no club was looked at")
        return []
    values = " ".join("wd:" + lid for lid in wanted)
    data, error = sparql_with_retry(CLUB_QUERY % {"leagues": values, "lang": lang})
    if error:
        failures.append(f"{code} clubs from Wikidata: {error}")
        incomplete.append(f"{code} clubs from Wikidata: {error}")
        return []
    clubs, _leagues, _ambiguous, dropped, _countries = build_clubs(
        data.get("results", {}).get("bindings", []), tiers)
    # The items that carry a league tag and are not clubs - squad lists,
    # most often - used to arrive here and take up a row each in the
    # review file, asking you to find a ground for a list. They are named
    # rather than removed quietly.
    if summary is not None:
        for note in dropped:
            summary.append(f"{code}  left out, not a club: {note}")
    apply_manual(clubs, manual_rows, code)
    return [c for c in clubs.values()
            if c["tier"] is not None and c["lat"] is None]


def add_cities(clubs, lang, failures, code, incomplete):
    """
    The club's town from Wikidata, used only to throw out a candidate in
    the wrong part of the country, and what Wikidata says the item is.
    """
    ids = [c["id"] for c in clubs if c["id"].startswith("Q")]
    if not ids:
        return
    values = " ".join("wd:" + i for i in ids)
    data, error = sparql_with_retry(CITY_QUERY % {"clubs": values, "lang": lang})
    if error:
        failures.append(f"{code} club towns from Wikidata: {error} - "
                        f"no candidate could be checked against a town")
        # Without the town the wrong-village guard is gone, so a candidate
        # that would have been thrown out can come back as confident. That
        # is a worse answer, not a shorter one, and it must not replace a
        # good file either.
        incomplete.append(f"{code} club towns from Wikidata: {error} - "
                          f"the wrong-town guard was off for this country")
        return
    best, kinds = {}, {}
    for row in data.get("results", {}).get("bindings", []):
        cid = qid(cell(row, "club"))

        kind = cell(row, "typeLabel") or ""
        if kind and not kind.startswith("Q"):
            seen = kinds.setdefault(cid, [])
            if kind not in seen:
                seen.append(kind)

        rank_raw = cell(row, "rank")
        if rank_raw is None:
            continue
        rank = int(rank_raw)
        label = cell(row, "cityLabel") or ""
        if label.startswith("Q"):
            label = ""
        entry = {"name": label, "lat": None, "lon": None, "rank": rank}
        coord = cell(row, "coord")
        if coord:
            match = POINT_RE.match(coord)
            if match:
                entry["lon"] = float(match.group(1))
                entry["lat"] = float(match.group(2))
        if cid not in best or rank < best[cid]["rank"] or (
                rank == best[cid]["rank"] and entry["lat"] is not None
                and best[cid]["lat"] is None):
            best[cid] = entry
    for club in clubs:
        if club["id"] in best:
            club["_city"] = best[club["id"]]
        if club["id"] in kinds:
            club["_isA"] = "; ".join(kinds[club["id"]][:3])


def fetch_places(code, names, failures):
    """
    Ask OpenStreetMap which of these names are really places, in small
    batches. Returns what came back and, separately, the names that were
    never looked up - those are not the same as names that came back
    empty, and the difference decides whether a club can be told it has
    no match.
    """
    found, missing = [], []
    batches = [names[i:i + NAMES_PER_REQUEST]
               for i in range(0, len(names), NAMES_PER_REQUEST)]
    for position, batch in enumerate(batches):
        if position:
            time.sleep(SMALL_GAP_SECONDS)
        pattern = "|".join(re.escape(gram) for gram in batch)
        payload, error = overpass_with_retry(
            PLACE_QUERY % {"iso": code, "names": pattern,
                           "box": box_filter(code)}, "places")
        if error:
            failures.append(f"{code} places: {error} - {len(batch)} name(s) in "
                            f"this batch were not looked up")
            missing.extend(batch)
            continue
        found.extend(places(payload))
    return found, missing


def fetch_pitches(code, place_list, failures, excluded=None):
    """
    Named football pitches around these places, in small batches. Returns
    the pitches found and, separately, the places whose batch never came
    back - the same split fetch_places makes, for the same reason: a
    place nobody asked about is not a place with no pitch.
    """
    found, missing = {}, []
    batches = [place_list[i:i + PLACES_PER_REQUEST]
               for i in range(0, len(place_list), PLACES_PER_REQUEST)]
    for number, batch in enumerate(batches, 1):
        time.sleep(SMALL_GAP_SECONDS)
        payload, error = overpass_with_retry(
            pitch_query(batch), f"pitches {number}/{len(batches)}")
        if error:
            failures.append(f"{code} pitches: {error} - {len(batch)} place(s) "
                            f"in this batch were not asked about")
            missing.extend(batch)
            continue
        found.update(elements(payload, "pitch", excluded))
    return found, missing


def pitch_query(place_list):
    around = "\n".join(
        '  nwr["leisure"="pitch"]["sport"="soccer"]["name"]'
        '(around:%d,%.6f,%.6f);' % (PLACE_RADIUS_M, p["lat"], p["lon"])
        for p in place_list)
    return PITCH_QUERY_HEAD + around + PITCH_QUERY_TAIL


# ------------------------------------------------------------------ main

def main():
    # Line by line, so a long run shows where it has got to instead of
    # arriving in one block at the end.
    sys.stdout.reconfigure(line_buffering=True)

    if not os.path.isdir("data"):
        sys.exit("run this from the top of the repository: "
                 "python3 tools/propose_coordinates.py")
    os.makedirs(CLUB_DIR, exist_ok=True)

    tiers, labels, problems = load_tiers()
    manual_rows, manual_problems = load_manual()
    problems.extend(manual_problems)
    reviews, review_readback, review_problems = load_reviews()
    problems.extend(review_problems)
    print(f"  {REVIEWED_FILE}, read back:")
    for line in review_readback:
        print("    " + line)
    reviews_used = set()
    excluded_all = {}

    summary, failures, readback = [], [], []

    # One entry per country: its rows, and anything that made this run's
    # answer for THAT country less than the whole picture. The decision
    # whether to replace a country's rows is taken per country, from its
    # own list - see write_review(). Registered before any work is done,
    # so a country that stops half-way still has an entry saying why.
    results = {}

    for position, (code, _country_qid, country_name) in enumerate(COUNTRIES):
        if position:
            time.sleep(COUNTRY_GAP_SECONDS)
        lang = {"DE": "de", "RO": "ro", "FR": "fr", "IT": "it", "CH": "de,fr,it", "AT": "de"}.get(code, "en")
        print(f"  {code}  {country_name}")
        rows, incomplete = [], []
        results[code] = {"rows": rows, "incomplete": incomplete}

        clubs = missing_clubs(code, lang, tiers, labels, manual_rows, failures,
                              incomplete, summary)
        if not clubs:
            if incomplete:
                summary.append(f"{code}  the club list could not be fetched")
            else:
                summary.append(f"{code}  no club is missing its coordinates")
            continue
        print(f"      {len(clubs)} club(s) have a tier but no coordinates")

        time.sleep(REQUEST_GAP_SECONDS)
        add_cities(clubs, lang, failures, code, incomplete)

        time.sleep(REQUEST_GAP_SECONDS)
        print("      asking OpenStreetMap for every stadium in the country")
        payload, error = overpass_with_retry(GROUND_QUERY % {"iso": code}, "stadiums")
        if error:
            failures.append(f"{code}: {error} - OpenStreetMap was not asked, so "
                            f"no coordinate was proposed for this country")
            incomplete.append(f"{code}: OpenStreetMap unreachable ({error})")
            for club in clubs:
                rows.append(review_row(club, code, {
                    "_verdict": "not checked - OpenStreetMap could not be reached",
                    "name": club.get("name") or club["id"],
                    "_city": (club.get("_city") or {}).get("name", "")}))
            continue
        excluded = {}
        grounds = elements(payload, "stadium", excluded)
        print(f"      {len(grounds)} stadiums, and {len(excluded)} object(s) "
              f"tagged as a stadium left out as not a football ground")

        grams = {club["id"]: name_ngrams(club.get("name") or "") for club in clubs}
        asked = sorted({gram for one in grams.values() for gram in one})
        time.sleep(REQUEST_GAP_SECONDS)
        print(f"      looking up {len(asked)} name(s) from the club names"
              + (f", inside the box {box_filter(code)}" if box_filter(code)
                 else ", with no box for this country"))
        place_list, missing = fetch_places(code, asked, failures)
        if missing:
            print(f"      {len(missing)} name(s) did not come back, asking again")
            time.sleep(REQUEST_GAP_SECONDS)
            second, missing = fetch_places(code, missing, failures)
            place_list.extend(second)
        if missing:
            # A lost request takes a whole stretch of the alphabet with
            # it. Those clubs must not be told nothing matched, because
            # nothing was asked.
            failures.append(
                f"{code}: {len(missing)} name(s) were never looked up, so the "
                f"clubs carrying them say 'not checked' instead of 'no match'")
            incomplete.append(f"{code}: {len(missing)} place name(s) were never "
                              f"looked up")
            for club in clubs:
                if any(gram in missing for gram in grams[club["id"]]):
                    club["_unchecked"] = True
        print(f"      {len(place_list)} place(s) in OpenStreetMap carry a name "
              f"that appears in a club's name")

        forms = {c["id"]: club_forms(c.get("name") or "") for c in clubs}
        # Pitches only where no stadium matched at all. Everywhere else
        # they add candidates without settling anything, and the request
        # is not free.
        needy = [c for c in clubs if not candidates_for(c, grounds, place_list)]
        wanted_places = [p for p in place_list
                         if any(place_in_club(p["name"], forms[c["id"]], p["parts"])[0]
                                for c in needy)]
        if needy:
            print(f"      {len(needy)} club(s) matched no stadium at all")
        pitch_count = 0
        if wanted_places:
            requests = -(-len(wanted_places) // PLACES_PER_REQUEST)
            print(f"      asking for named football pitches around "
                  f"{len(wanted_places)} place(s), {requests} request(s) of up "
                  f"to {PLACES_PER_REQUEST}")
            pitches, lost = fetch_pitches(code, wanted_places, failures, excluded)
            if lost:
                print(f"      {len(lost)} place(s) did not come back, asking again")
                time.sleep(REQUEST_GAP_SECONDS)
                second, lost = fetch_pitches(code, lost, failures, excluded)
                pitches.update(second)
            if lost:
                incomplete.append(
                    f"{code} pitches: {len(lost)} of {len(wanted_places)} place(s) "
                    f"were never asked about - a club whose only ground is a "
                    f"pitch could read as 'no match'")
            else:
                print(f"      every pitch request came back")
            for ref, ground in pitches.items():
                if ref not in grounds:
                    grounds[ref] = ground
                    pitch_count += 1
            print(f"      {pitch_count} named football pitch(es) nearby")

        excluded_all[code] = excluded
        counts = {w: 0 for w in VERDICT_ORDER}
        for club in sorted(clubs, key=lambda c: (c.get("name") or c["id"]).lower()):
            mine = reviews.get(club["id"], [])
            if mine:
                reviews_used.add(club["id"])
            result = propose(club, grounds, place_list, mine)
            counts[result["_verdict"].split(" ")[0]] += 1
            rows.append(review_row(club, code, result))
            readback.append((code, result))

        by_tier = {}
        for club in clubs:
            by_tier[club["tier"]] = by_tier.get(club["tier"], 0) + 1
        tiers_seen = ", ".join(f"tier {t}: {n}" for t, n in sorted(by_tier.items()))

        summary.append(
            f"{code}  {len(clubs)} club(s) with no coordinates  |  "
            f"{counts['confident']} confident  |  {counts['ambiguous']} ambiguous  |  "
            f"{counts['no'] + counts['not']} nothing  |  already reviewed: "
            f"{counts['held']} held, {counts['open']} open, "
            f"{counts['rejected']} rejected")
        summary.append(
            f"    {tiers_seen}  |  asked OpenStreetMap about {len(grounds)} "
            f"ground(s) and {len(place_list)} place name(s)")

    shared = {code: flag_shared_grounds(result["rows"])
              for code, result in results.items()}

    written, kept, partial, others = write_review(results)
    shared = [line for code in written + partial for line in shared[code]]

    print()
    print("=" * 74)
    print("COORDINATE PROPOSALS")
    print("=" * 74)
    for line in summary:
        print("  " + line)
    print()
    # Country by country, because that is how the file is now decided. A
    # green tick on this workflow says only that the tool ran; these lines
    # say which countries in the file are this run's and which are not.
    for code in results:
        count = len(results[code]["rows"])
        if code in written:
            print(f"  {code}  WRITTEN - complete answer, {count} row(s) replace "
                  f"this country's rows")
        elif code in partial:
            print(f"  {code}  WRITTEN AS PARTIAL - {REVIEW_FILE} did not exist, so "
                  f"there was nothing to protect; {count} row(s), missing "
                  f"whatever is listed below")
        else:
            print(f"  {code}  UNCHANGED - Overpass or Wikidata did not answer "
                  f"everything for this country, so its rows are exactly as the "
                  f"last successful run for {code} left them ({kept[code]} "
                  f"row(s)). This run's {count} row(s) for it were thrown away.")
        for reason in results[code]["incomplete"]:
            print(f"        did not come back: {reason}")
    if others:
        print(f"  Rows for countries this run does not cover were kept as they "
              f"were: {', '.join(others)}")
    print()
    looked_at = {code for code in results if code in written + partial}
    inert = [r for q, rs in reviews.items() if q not in reviews_used
             for r in rs if r["country"] in looked_at]
    if inert:
        print(f"  {REVIEWED_FILE}: {len(inert)} row(s) matched no club this run "
              f"left without coordinates - placed since, or no longer tracked. "
              f"They did nothing; delete them when you are sure:")
        for r in inert:
            print(f"    line {r['line']:3d}  {r['clubQid']} {r['name']}")
        print()
    for code, excluded in sorted(excluded_all.items()):
        if not excluded:
            continue
        print(f"  {code}  {len(excluded)} object(s) left out as not a football "
              f"ground:")
        for line in sorted(excluded.values())[:15]:
            print("    " + line)
        if len(excluded) > 15:
            print(f"    ... and {len(excluded) - 15} more")
    print()
    if not written and not partial:
        print(f"  No country came back complete. {REVIEW_FILE} was NOT rewritten.")
        print("=" * 74)
        return
    fresh = sum(len(results[c]["rows"]) for c in written + partial)
    print(f"  {fresh} club(s) written to {REVIEW_FILE} for "
          f"{', '.join(written + partial)}")
    print("  Nothing was applied. A confident row carries a ground, a lat and a")
    print("  lon and can be pasted into data/clubs-manual.csv once you agree with")
    print("  it; an ambiguous one is deliberately left blank for you to settle.")

    for title, wanted in (("Confident - read these back before you use them",
                           ("confident",)),
                          ("Already reviewed and kept back - not to be pasted",
                           ("held", "open", "rejected")),
                          ("Ambiguous - nothing was filled in", ("ambiguous",)),
                          ("Nothing found", ("no", "not"))):
        chosen = [(code, r) for code, r in readback
                  if code in written + partial
                  and r["_verdict"].split(" ")[0] in wanted]
        if not chosen:
            continue
        print()
        print(f"  {title}:")
        for code, result in chosen:
            head = f"    {code} {result['name'][:32]:32s}"
            if result["_verdict"] == "confident":
                print(f"{head} -> {result['_osmName'] or 'unnamed ground'} "
                      f"[{result['_osmRef']}]")
                print(f"         {result['_how']}")
                if result["_cityKm"] != "":
                    print(f"         {result['_cityKm']} km from {result['_city']}, "
                          f"the club's town in Wikidata")
                if result["_alternatives"]:
                    print(f"         passed over: {result['_alternatives']}")
            else:
                print(f"{head} {result['_verdict']}")
                if result["_alternatives"]:
                    print(f"         candidates: {result['_alternatives']}")
            if result.get("_reviewed"):
                print(f"         reviewed before: {result['_reviewed']}")

    if shared:
        print()
        print("  Careful - one ground proposed for more than one club, which")
        print("  would put two pins on one spot. Sometimes a town's clubs really")
        print("  do share a ground; check before accepting both:")
        for line in shared:
            print("    " + line)

    for problem in problems:
        print("  ! " + problem)
    if failures:
        print()
        for failure in failures:
            print("  ! " + failure)
    print("=" * 74)


HEADER = ["clubQid", "name", "country", "tier", "venue", "capacity",
          "lat", "lon", "ticketUrl", "source", "note",
          "_tier", "_isA", "_city", "_cityKm", "_osmName", "_osmTown",
          "_osmRef", "_how", "_alternatives", "_verdict", "_reviewed"]

VERDICT_ORDER = {"confident": 0, "open": 1, "held": 2, "ambiguous": 3,
                 "rejected": 4, "no": 5, "not": 6}


def write_review(results):
    """
    Decide, COUNTRY BY COUNTRY, whose rows this run may replace, and write
    the file. Returns (written, kept, partial, others).

    The rule is the one this file always had, applied to one country at a
    time instead of to the whole run: a request that did not come back
    turns real proposals into rows that read "not checked" or "no match",
    and writing that over a country's rows would delete evidence nobody
    has worked through yet - with a green tick. So a country whose answer
    is incomplete keeps exactly the rows the last good run for it left,
    byte for byte, and a country whose answer is complete replaces its own
    rows and nobody else's. Until 2026-09-26 one country's failed step
    threw away every country's answer; Germany, France and Italy came back
    whole in run #9 and were discarded because Romania's pitches did not.

    The first run is still the one exception, and still for the whole
    file: with no file there is nothing to protect, so a partial list is
    written and the summary says so. It is NOT extended to "a country
    with no rows yet": an incomplete country is never written into an
    existing file, even where that file has nothing for it.
    """
    existing = os.path.exists(REVIEW_FILE)
    old = {}
    if existing:
        with open(REVIEW_FILE, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                old.setdefault(row.get("country", ""), []).append(row)

    written, partial, kept = [], [], {}
    out = {}
    for code, result in results.items():
        if not result["incomplete"]:
            written.append(code)
            out[code] = result["rows"]
        elif not existing:
            partial.append(code)
            out[code] = result["rows"]
        else:
            kept[code] = len(old.get(code, []))
            out[code] = old.get(code, [])
    # A country in the file that this run did not look at at all - one
    # taken out of COUNTRIES - is not this run's to delete either.
    others = sorted(c for c in old if c not in results)
    for code in others:
        out[code] = old[code]

    if not written and not partial:
        return written, kept, partial, others

    with open(REVIEW_FILE, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADER)
        writer.writeheader()
        for code in sorted(out):
            rows = out[code]
            if code in written or code in partial:
                rows = sorted(rows, key=lambda r: (
                    VERDICT_ORDER.get(r["_verdict"].split(" ")[0], 9),
                    r["name"].lower()))
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in HEADER})
    return written, kept, partial, others


def review_row(club, code, result):
    """One row, in the column order of data/clubs-manual.csv."""
    return {
        "clubQid": club["id"] if club["id"].startswith("Q") else "",
        "name": result.get("name") or club.get("name") or club["id"],
        "country": code,
        "tier": "", "capacity": "", "ticketUrl": "", "note": "",
        "_tier": club.get("tier") if club.get("tier") is not None else "",
        "_isA": club.get("_isA", ""),
        "venue": result.get("venue", ""),
        "lat": result.get("lat", ""),
        "lon": result.get("lon", ""),
        "source": result.get("source", ""),
        "_city": result.get("_city", ""),
        "_cityKm": result.get("_cityKm", ""),
        "_osmName": result.get("_osmName", ""),
        "_osmTown": result.get("_osmTown", ""),
        "_osmRef": result.get("_osmRef", ""),
        "_how": result.get("_how", ""),
        "_alternatives": result.get("_alternatives", ""),
        "_verdict": result["_verdict"],
        "_reviewed": result.get("_reviewed", ""),
    }


if __name__ == "__main__":
    main()
