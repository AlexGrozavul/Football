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
    CLUB_QUERY, COUNTRIES, apply_manual, build_clubs, cell,
    load_manual, load_tiers, qid, sparql_with_retry)

# ---------------------------------------------------------------- config

CLUB_DIR = "data/clubs"
REVIEW_FILE = os.path.join(CLUB_DIR, "coordinate-review.csv")

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
MAX_RETRIES = 2

# Overpass takes one "around" clause per place, and a country's worth of
# them in one request is neither polite nor reliable.
PLACES_PER_REQUEST = 50

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
PLACE_QUERY = """
[out:json][timeout:240];
area["ISO3166-1"="%(iso)s"][admin_level=2]->.a;
node["place"~"^(city|town|village|suburb)$"]["name"~"^(%(names)s)([ /,-].*)?$",i](area.a);
out tags center;
"""

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
                print(f"    Overpass busy ({exc.code}) on {what}, waiting 30s")
                time.sleep(30)
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


def place_in_club(place_name, forms, parts=None):
    """
    Does this place's name sit inside the club's name? OpenStreetMap
    often carries the long official form - 'Garching bei München' for
    Garching, 'Rain am Lech' for Rain - so a leading run of its words
    counts too. Returns what matched and any caveat, longest first.
    """
    parts = parts if parts is not None else fold(place_name).split()
    for size in range(len(parts), 0, -1):
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


def elements(payload, default_kind):
    """Flatten an Overpass answer into ground records."""
    out = {}
    for el in payload.get("elements", []):
        tags = el.get("tags") or {}
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


def propose(club, grounds, place_list):
    """Returns the review row for one club with no coordinates."""
    name = club.get("name") or club["id"]
    city = club.get("_city") or {}
    found = candidates_for(club, grounds, place_list)

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

def missing_clubs(code, lang, tiers, labels, manual_rows, failures):
    """The clubs fetch_clubs.py drops: they have a tier but no position."""
    wanted = [lid for lid, t in tiers.items()
              if t != "skip" and labels.get(lid, {}).get("country", code) == code]
    if not wanted:
        failures.append(f"{code}: no leagues mapped for this country yet")
        return []
    values = " ".join("wd:" + lid for lid in wanted)
    data, error = sparql_with_retry(CLUB_QUERY % {"leagues": values, "lang": lang})
    if error:
        failures.append(f"{code} clubs from Wikidata: {error}")
        return []
    clubs, _leagues, _ambiguous = build_clubs(
        data.get("results", {}).get("bindings", []), tiers)
    apply_manual(clubs, manual_rows, code)
    return [c for c in clubs.values()
            if c["tier"] is not None and c["lat"] is None]


def add_cities(clubs, lang, failures, code):
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
            PLACE_QUERY % {"iso": code, "names": pattern}, "places")
        if error:
            failures.append(f"{code} places: {error} - {len(batch)} name(s) in "
                            f"this batch were not looked up")
            missing.extend(batch)
            continue
        found.extend(places(payload))
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

    rows, summary, failures, readback = [], [], [], []

    for position, (code, _country_qid, country_name) in enumerate(COUNTRIES):
        if position:
            time.sleep(REQUEST_GAP_SECONDS)
        lang = {"DE": "de", "RO": "ro"}.get(code, "en")
        print(f"  {code}  {country_name}")

        clubs = missing_clubs(code, lang, tiers, labels, manual_rows, failures)
        if not clubs:
            summary.append(f"{code}  no club is missing its coordinates, "
                           f"or the club list could not be fetched")
            continue
        print(f"      {len(clubs)} club(s) have a tier but no coordinates")

        time.sleep(REQUEST_GAP_SECONDS)
        add_cities(clubs, lang, failures, code)

        time.sleep(REQUEST_GAP_SECONDS)
        print("      asking OpenStreetMap for every stadium in the country")
        payload, error = overpass_with_retry(GROUND_QUERY % {"iso": code}, "stadiums")
        if error:
            failures.append(f"{code}: {error} - OpenStreetMap was not asked, so "
                            f"no coordinate was proposed for this country")
            for club in clubs:
                rows.append(review_row(club, code, {
                    "_verdict": "not checked - OpenStreetMap could not be reached",
                    "name": club.get("name") or club["id"],
                    "_city": (club.get("_city") or {}).get("name", "")}))
            continue
        grounds = elements(payload, "stadium")
        print(f"      {len(grounds)} stadiums")

        grams = {club["id"]: name_ngrams(club.get("name") or "") for club in clubs}
        asked = sorted({gram for one in grams.values() for gram in one})
        time.sleep(REQUEST_GAP_SECONDS)
        print(f"      looking up {len(asked)} name(s) from the club names")
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
        batches = [wanted_places[i:i + PLACES_PER_REQUEST]
                   for i in range(0, len(wanted_places), PLACES_PER_REQUEST)]
        if batches:
            print(f"      asking for named football pitches around those places, "
                  f"{len(batches)} request(s)")
        for batch in batches:
            time.sleep(SMALL_GAP_SECONDS)
            payload, error = overpass_with_retry(pitch_query(batch), "pitches")
            if error:
                failures.append(f"{code} pitches: {error} - some of the country's "
                                f"named pitches were not considered")
                continue
            pitches = elements(payload, "pitch")
            for ref, ground in pitches.items():
                if ref not in grounds:
                    grounds[ref] = ground
                    pitch_count += 1
        if batches:
            print(f"      {pitch_count} named football pitch(es) nearby")

        counts = {"confident": 0, "ambiguous": 0, "no": 0, "not": 0}
        for club in sorted(clubs, key=lambda c: (c.get("name") or c["id"]).lower()):
            result = propose(club, grounds, place_list)
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
            f"{counts['no'] + counts['not']} nothing")
        summary.append(
            f"    {tiers_seen}  |  asked OpenStreetMap about {len(grounds)} "
            f"ground(s) and {len(place_list)} place name(s)")

    header = ["clubQid", "name", "country", "tier", "venue", "capacity",
              "lat", "lon", "ticketUrl", "source", "note",
              "_tier", "_isA", "_city", "_cityKm", "_osmName", "_osmTown",
              "_osmRef", "_how", "_alternatives", "_verdict"]
    shared = flag_shared_grounds(rows)
    order = {"confident": 0, "ambiguous": 1, "no": 2, "not": 3}
    rows.sort(key=lambda r: (r["country"], order.get(r["_verdict"].split(" ")[0], 9),
                             r["name"].lower()))
    with open(REVIEW_FILE, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print()
    print("=" * 74)
    print("COORDINATE PROPOSALS")
    print("=" * 74)
    for line in summary:
        print("  " + line)
    print()
    print(f"  {len(rows)} club(s) written to {REVIEW_FILE}")
    print("  Nothing was applied. A confident row carries a ground, a lat and a")
    print("  lon and can be pasted into data/clubs-manual.csv once you agree with")
    print("  it; an ambiguous one is deliberately left blank for you to settle.")

    for title, wanted in (("Confident - read these back before you use them",
                           ("confident",)),
                          ("Ambiguous - nothing was filled in", ("ambiguous",)),
                          ("Nothing found", ("no", "not"))):
        chosen = [(code, r) for code, r in readback
                  if r["_verdict"].split(" ")[0] in wanted]
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
    }


if __name__ == "__main__":
    main()
