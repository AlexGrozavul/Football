#!/usr/bin/env python3
"""
diagnose_p118_rank.py -- which clubs does the club query's `wdt:P118`
join hide, and why.

CLUB_QUERY in fetch_clubs.py joins on `wdt:P118`. The `wdt:` prefix
yields only TRUTHY statements: the preferred-rank ones if the item has
any, otherwise the normal-rank ones, and NEVER a deprecated one. So a
club can carry exactly the right league on exactly the right item and
still never reach the map, and it leaves no trace anywhere downstream -
not in data/clubs/, so no review file mentions it, and not in the club
query's answer, so nothing counts it. That is a shape of invisibility
that no other pass in this project can see.

Two statement shapes cause it, and this tool asks about both:

  a PREFERRED-rank statement carrying NO VALUE.  Wikidata's <novalue>
      is an assertion - "this item has no league" - and at preferred
      rank it suppresses every normal-rank statement underneath it.
      SSC Farul Constanta's Q368104 is the case this was written from:
      Liga II and Liga III at normal rank, both true, both invisible.

  EVERY statement DEPRECATED.  Nothing is left for `wdt:` to yield.
      FC Augsburg's Q15755 is the case: one statement, P118 =
      Q82595 Bundesliga, deprecated, and the club reaches the map not
      at all through that item.

IT READS AND WRITES NOTHING. Not a club file, not a review file, not a
seed list. It prints what it found and exits 1 if any call failed,
because a diagnostic that answers "nothing found" after a failed fetch
is worse than one that does not answer at all.

WHAT IT DOES NOT DO is decide what a hidden league means. Reading rank
properly in CLUB_QUERY would mean deciding what a deprecated league tag
is for - a club that left the league in 1994 carries one too, and that
is exactly the problem league-tiers.csv and the truthy join exist to
avoid. This tool finds the clubs; which of them is an error and which
is history is a judgement, and it is Alexandru's.
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TIERS_FILE = ROOT / "data" / "league-tiers.csv"

ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = ("football-fixture-planner/1.0 (personal project; "
              "https://github.com/AlexGrozavul/Football)")

TIMEOUT_SECONDS = 90
MAX_RETRIES = 3
REQUEST_GAP_SECONDS = 2
ENTITY_BATCH = 50

# The two countries the map covers. A club is counted as one of ours if
# its P17 says so OR if a hidden statement names a league that
# league-tiers.csv maps to that country - because P17 is exactly the
# field the missing clubs already lack, and a census that trusted it
# alone would miss the clubs it is meant to find.
COUNTRIES = {"Q183": "DE", "Q218": "RO"}

P_LEAGUE = "P118"
P_VENUE = "P115"
P_COORD = "P625"
P_COUNTRY = "P17"
P_TYPE = "P31"


# QUERY A - the census. Every item ANYWHERE with a preferred-rank P118
# carrying no value. It is deliberately not bounded by country: the
# question asked was "every instance, not just Farul", and an item with
# no P17 - which is the common shape on exactly the clubs that go
# missing - would fall straight through a country filter. The class is
# narrow enough that the whole world is cheaper than a join.
#
# `?st a wdno:P118` is how Wikidata's RDF export writes <novalue>: the
# statement node is typed into the property's "no value" class and
# carries no ps:P118 triple at all. A <somevalue> is written the other
# way round - a ps:P118 pointing at a blank node - and it suppresses
# lower ranks just the same, so both are asked for.
QUERY_NOVALUE = """
SELECT ?club ?clubLabel ?country ?countryLabel ?shape
WHERE {
  {
    ?club p:P118 ?st .
    ?st a wdno:P118 .
    ?st wikibase:rank wikibase:PreferredRank .
    BIND("novalue" AS ?shape)
  } UNION {
    ?club p:P118 ?st .
    ?st wikibase:rank wikibase:PreferredRank .
    ?st ps:P118 ?someValue .
    FILTER(isBlank(?someValue))
    BIND("somevalue" AS ?shape)
  }
  FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
  OPTIONAL { ?club wdt:P17 ?country }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,de,ro" }
}
LIMIT 2000
"""

# QUERY B - the cost, to this project specifically. Clubs carrying one
# of the leagues league-tiers.csv maps, on a statement `wdt:` will not
# yield, for any reason: a deprecated rank, or a preferred <novalue>
# sitting on top of it. Bounded by the twelve mapped leagues, so it is
# small and fast, and it needs no P17 at all - the league IS the country
# signal here.
QUERY_HIDDEN = """
SELECT ?club ?clubLabel ?league ?rank ?venue ?coord
WHERE {
  VALUES ?league { %(leagues)s }
  ?club p:P118 ?st .
  ?st ps:P118 ?league .
  ?st wikibase:rank ?rank .
  FILTER NOT EXISTS { ?club wdt:P118 ?anyTruthy }
  FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
  OPTIONAL { ?club wdt:P115 ?venue }
  OPTIONAL { ?club wdt:P625 ?coord }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,de,ro" }
}
"""


# ------------------------------------------------------------------ http

def sparql_with_retry(query, what):
    body = urllib.parse.urlencode({"query": query, "format": "json"}).encode("utf-8")
    for attempt in range(1, MAX_RETRIES + 1):
        req = urllib.request.Request(
            ENDPOINT, data=body,
            headers={"User-Agent": USER_AGENT,
                     "Accept": "application/sparql-results+json",
                     "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                return json.loads(resp.read().decode("utf-8")), None
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
                print(f"    {what}: HTTP {exc.code}, retrying")
                time.sleep(15)
                continue
            return None, f"HTTP {exc.code}"
        except urllib.error.URLError as exc:
            if attempt < MAX_RETRIES:
                print(f"    {what}: network error, retrying: {exc.reason}")
                time.sleep(15)
                continue
            return None, f"network error: {exc.reason}"
        except TimeoutError:
            if attempt < MAX_RETRIES:
                print(f"    {what}: timed out, retrying")
                continue
            return None, "query timed out"
        except ValueError:
            # The query service answers 200 with a half-written body when
            # it gives up at its own 60-second ceiling, so broken JSON
            # means "too slow", not "wrong query".
            if attempt < MAX_RETRIES:
                print(f"    {what}: answer cut off mid-JSON, retrying")
                time.sleep(15)
                continue
            return None, "answer cut off mid-JSON - the query service gave up (60s limit)"
    return None, "exhausted retries"


def api_with_retry(url, what):
    for attempt in range(1, MAX_RETRIES + 1):
        req = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                return json.loads(resp.read().decode("utf-8")), None
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                ValueError) as exc:
            if attempt < MAX_RETRIES:
                print(f"    {what}: {exc}, retrying")
                time.sleep(10)
                continue
            return None, str(exc)
    return None, "exhausted retries"


def qid(uri):
    return uri.rsplit("/", 1)[-1] if uri else None


def cell(row, name):
    value = (row.get(name) or {}).get("value")
    return value if value not in ("", None) else None


# ------------------------------------------------------------ tier table

def load_tiers():
    """leagueQid -> (tier, country, label). `skip` rows are left out."""
    tiers = {}
    with TIERS_FILE.open(encoding="utf-8") as handle:
        header = handle.readline()
        if not header:
            return tiers
        for line in handle:
            parts = [p.strip() for p in line.rstrip("\n").split(",")]
            if len(parts) < 4 or not parts[0]:
                continue
            league, tier, label, country = parts[0], parts[1], parts[2], parts[3]
            if tier == "skip":
                continue
            try:
                tiers[league] = (int(tier), country, label)
            except ValueError:
                continue
    return tiers


# ------------------------------------------------------- entity reading

def fetch_entities(qids):
    """
    wbgetentities, 50 ids a call, claims and labels and sitelinks.

    A batch that comes back with nothing usable is a FAILED CALL, not a
    fact about those items - the same guard the roster check needed
    after a refusal read as "Wikidata has never heard of any of these".
    An API that answers 200 with an error object gets that object read
    and printed, for the same reason.
    """
    entities, failures = {}, []
    ordered = list(dict.fromkeys(qids))
    for start in range(0, len(ordered), ENTITY_BATCH):
        batch = ordered[start:start + ENTITY_BATCH]
        query = urllib.parse.urlencode({
            "action": "wbgetentities", "ids": "|".join(batch),
            "props": "claims|labels|sitelinks", "languages": "en|de|ro",
            "format": "json", "formatversion": "2"})
        data, error = api_with_retry(f"{WIKIDATA_API}?{query}", "entities")
        if error:
            failures.append(f"reading {len(batch)} items from Wikidata failed: {error}")
            continue
        if data.get("error"):
            failures.append(
                f"reading {len(batch)} items was refused: "
                f"{data['error'].get('code')} - {data['error'].get('info')}")
            continue
        got = {q: e for q, e in (data.get("entities") or {}).items()
               if q.startswith("Q") and not e.get("missing")}
        if not got:
            failures.append(
                f"Wikidata answered with no usable entity for any of {len(batch)} "
                f"items it had just named itself. That is a failed call, not "
                f"{len(batch)} items with nothing on them")
            continue
        entities.update(got)
        time.sleep(REQUEST_GAP_SECONDS)
    return entities, failures


def label_of(entity):
    labels = entity.get("labels") or {}
    for lang in ("en", "de", "ro"):
        value = labels.get(lang)
        if isinstance(value, dict):
            value = value.get("value")
        if value:
            return value
    return entity.get("id") or "?"


def sitelink_count(entity):
    """
    formatversion=2 hands sitelinks back as a LIST of {site, title}; the
    default hands back a dict keyed by site. Both shapes are read,
    because assuming one of them is what made the roster check report
    all 246 roster clubs as having no Wikidata item, with a green tick.
    """
    links = entity.get("sitelinks")
    if isinstance(links, list):
        return len(links)
    if isinstance(links, dict):
        return len(links)
    return 0


def league_statements(entity):
    """
    Every P118 statement on the item, as (value-qid-or-None, rank,
    snaktype). Rank and snaktype are kept because they are the whole
    subject of this tool - a statement's value alone cannot say why the
    club is invisible.
    """
    out = []
    for statement in (entity.get("claims") or {}).get(P_LEAGUE) or []:
        snak = statement.get("mainsnak") or {}
        snaktype = snak.get("snaktype") or "?"
        value = (snak.get("datavalue") or {}).get("value") or {}
        vid = value.get("id") if isinstance(value, dict) else None
        out.append((vid, statement.get("rank") or "?", snaktype))
    return out


def truthy_leagues(statements):
    """
    Exactly what `wdt:P118` yields, worked out here rather than asked
    for separately, so the report can show the statements and the
    consequence side by side and neither can drift from the other.

    The rule: if any statement is preferred, the truthy set is the
    preferred ones; otherwise the normal ones. Deprecated is never
    truthy, and a statement with no value contributes nothing - which
    is how a preferred <novalue> empties the set.
    """
    ranks = {rank for _vid, rank, _snak in statements}
    best = "preferred" if "preferred" in ranks else "normal"
    return [vid for vid, rank, snaktype in statements
            if rank == best and snaktype == "value" and vid]


def first_qid(entity, prop):
    for statement in (entity.get("claims") or {}).get(prop) or []:
        value = (((statement.get("mainsnak") or {}).get("datavalue") or {})
                 .get("value") or {})
        if isinstance(value, dict) and value.get("id"):
            return value["id"]
    return None


def has_claim(entity, prop):
    return bool((entity.get("claims") or {}).get(prop))


# ---------------------------------------------------------------- report

def describe(entity, tiers, placed_grounds):
    """One club's whole story, in the terms CLUB_QUERY asks in."""
    statements = league_statements(entity)
    truthy = truthy_leagues(statements)
    country = first_qid(entity, P_COUNTRY)
    venue = first_qid(entity, P_VENUE)
    hidden = []
    for vid, rank, snaktype in statements:
        if snaktype != "value" or not vid or vid in truthy:
            continue
        if vid in tiers:
            tier, code, label = tiers[vid]
            hidden.append((vid, rank, f"{label} = tier {tier} {code}, MAPPED"))
        else:
            hidden.append((vid, rank, "not in league-tiers.csv"))
    return {
        "qid": entity.get("id"),
        "label": label_of(entity),
        "sitelinks": sitelink_count(entity),
        "statements": statements,
        "truthy": truthy,
        "hidden": hidden,
        "country": country,
        "countryCode": COUNTRIES.get(country or ""),
        "venue": venue,
        "coord": has_claim(entity, P_COORD) or (venue in placed_grounds),
        "type": first_qid(entity, P_TYPE),
    }


def print_club(fact, tiers):
    print(f"  {fact['qid']}  {fact['label']}")
    print(f"      country P17: {fact['country'] or 'none'}"
          f"{'  (' + fact['countryCode'] + ')' if fact['countryCode'] else ''}"
          f"   sitelinks: {fact['sitelinks']}")
    for vid, rank, snaktype in fact["statements"]:
        if snaktype == "value" and vid:
            meta = tiers.get(vid)
            note = (f"{meta[2]} = tier {meta[0]} {meta[1]}, MAPPED" if meta
                    else "not in league-tiers.csv")
            print(f"      P118 {rank:<10} {vid:<12} {note}")
        else:
            print(f"      P118 {rank:<10} <{snaktype}>   asserts no league")
    if fact["truthy"]:
        print(f"      wdt:P118 yields: {' '.join(fact['truthy'])}")
    else:
        print("      wdt:P118 yields: NOTHING - the club query cannot see this item")
    if fact["coord"]:
        print("      position: yes")
    else:
        print("      position: NO - it would be dropped at the coordinates "
              "gate even if the tier were read")
    print()


def main():
    tiers = load_tiers()
    mapped = sorted(tiers)
    print(f"league-tiers.csv read back: {len(mapped)} mapped leagues - "
          + ", ".join(f"{q}={tiers[q][0]}{tiers[q][1]}" for q in mapped))
    print()

    failures = []

    # ---------------------------------------------------- query A
    print("QUERY A - every item anywhere with a preferred-rank P118 that "
          "asserts no league")
    began = time.time()
    data, error = sparql_with_retry(QUERY_NOVALUE, "novalue census")
    if error:
        failures.append(f"the novalue census failed: {error}")
        census = []
    else:
        census = data.get("results", {}).get("bindings", [])
        print(f"  answered in {round(time.time() - began, 1)}s with "
              f"{len(census)} statements")
    census_qids = []
    census_shape = {}
    for row in census:
        club = qid(cell(row, "club"))
        if club:
            census_qids.append(club)
            census_shape.setdefault(club, set()).add(cell(row, "shape"))
    print(f"  {len(set(census_qids))} distinct items")
    print()

    # ---------------------------------------------------- query B
    print("QUERY B - clubs carrying a league league-tiers.csv maps, on a "
          "statement wdt:P118 will not yield")
    values = " ".join(f"wd:{q}" for q in mapped)
    began = time.time()
    data, error = sparql_with_retry(QUERY_HIDDEN % {"leagues": values},
                                    "hidden clubs")
    if error:
        failures.append(f"the hidden-club query failed: {error}")
        hidden_rows = []
    else:
        hidden_rows = data.get("results", {}).get("bindings", [])
        print(f"  answered in {round(time.time() - began, 1)}s with "
              f"{len(hidden_rows)} statements")
    hidden_qids = [qid(cell(row, "club")) for row in hidden_rows]
    hidden_qids = [q for q in hidden_qids if q]
    print(f"  {len(set(hidden_qids))} distinct clubs")
    print()

    if failures:
        print("A QUERY FAILED. Nothing below is a finding - a diagnostic that "
              "answers 'nothing found' after a failed fetch is worse than one "
              "that does not answer at all.")
        for line in failures:
            print(f"  {line}")
        return 1

    # -------------------------------------------------- the entities
    wanted = sorted(set(census_qids) | set(hidden_qids))
    print(f"reading {len(wanted)} items from Wikidata")
    entities, entity_failures = fetch_entities(wanted)
    failures.extend(entity_failures)

    grounds_wanted = set()
    for entity in entities.values():
        if not has_claim(entity, P_COORD):
            ground = first_qid(entity, P_VENUE)
            if ground:
                grounds_wanted.add(ground)
    placed_grounds = set()
    if grounds_wanted:
        print(f"reading {len(grounds_wanted)} grounds, for the clubs that "
              f"carry no position themselves")
        grounds, ground_failures = fetch_entities(sorted(grounds_wanted))
        failures.extend(ground_failures)
        placed_grounds = {q for q, e in grounds.items() if has_claim(e, P_COORD)}

    if failures:
        print()
        print("A FETCH FAILED. Treat this run as incomplete.")
        for line in failures:
            print(f"  {line}")
        return 1

    facts = {q: describe(entities[q], tiers, placed_grounds)
             for q in wanted if q in entities}
    print()

    # ------------------------------------------------------- report
    ours, elsewhere = [], []
    for q, fact in facts.items():
        mine = fact["countryCode"] in COUNTRIES.values()
        if not mine:
            mine = any(vid in tiers for vid, _r, _n in fact["hidden"])
        (ours if mine else elsewhere).append(fact)

    ours.sort(key=lambda f: (f["countryCode"] or "zz", f["label"]))

    print("=" * 74)
    print("GERMANY AND ROMANIA - every club hidden from the club query by rank")
    print("=" * 74)
    print()
    if not ours:
        print("  none")
    for fact in ours:
        print_club(fact, tiers)

    novalue_ours = [f for f in ours if f["qid"] in census_shape]
    print("-" * 74)
    print(f"of those, {len(novalue_ours)} are hidden by a preferred-rank "
          f"statement asserting no league:")
    for fact in novalue_ours:
        shapes = "/".join(sorted(census_shape[fact["qid"]]))
        print(f"  {fact['qid']}  {fact['label']}  <{shapes}>  "
              f"suppressing {len(fact['hidden'])} statement(s)")
    print()

    print("-" * 74)
    print(f"the same census outside Germany and Romania: "
          f"{len(elsewhere)} items, not this project's business and listed "
          f"only so the number is not mistaken for zero")
    for fact in sorted(elsewhere, key=lambda f: f["qid"])[:40]:
        print(f"  {fact['qid']}  {fact['label']}  "
              f"(P17 {fact['country'] or 'none'})")
    if len(elsewhere) > 40:
        print(f"  ... and {len(elsewhere) - 40} more")
    print()

    # The answer again, at the bottom. A long job log is read from the
    # end, and the first europlan probe taught this project that the
    # readable part of a log may not reach as far as the top of it.
    print("=" * 74)
    print("SUMMARY, repeated so it is at both ends of the log")
    print("=" * 74)
    print(f"  preferred-rank no-league statements, worldwide: "
          f"{len(set(census_qids))} items")
    print(f"  clubs hidden from the club query in DE/RO:      {len(ours)}")
    for fact in ours:
        why = ("preferred <novalue>" if fact["qid"] in census_shape
               else "every statement deprecated")
        mappable = [f"{vid} ({note})" for vid, _r, note in fact["hidden"]
                    if "MAPPED" in note]
        print(f"    {fact['qid']:<12} {fact['label']:<28} {why}")
        for line in mappable:
            print(f"                 hides {line}")
        if not fact["coord"]:
            print("                 and has no position, so reading the rank "
                  "alone would not place it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
