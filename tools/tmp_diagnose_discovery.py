#!/usr/bin/env python3
"""
tmp_diagnose_discovery.py -- throwaway. Answers one question and is
deleted again once the answer is written down:

    why does the German half of the discovery query in
    tools/fetch_clubs.py never finish, when the Romanian half does?

It measures and prints. It writes no file, and it changes no query that
anything else uses.

Every probe is timed and reported with whatever came back, including
the failures - a query that dies after 61 seconds is a measurement too.

Usage:  python3 tools/tmp_diagnose_discovery.py
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = ("football-fixture-planner/1.0 (personal project; "
              "https://github.com/AlexGrozavul/Football)")
TIMEOUT_SECONDS = 120
GAP_SECONDS = 5

HINT = "PREFIX hint: <http://www.bigdata.com/queryHints#>\n"

# The query as tools/fetch_clubs.py sends it today.
AS_IS = """
SELECT ?club ?league ?leagueLabel WHERE {
  ?club wdt:P17 wd:%(country)s ; wdt:P118 ?league .
  FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
  FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "%(lang)s,en" }
}
"""

PROBES = [
    ("A1", "how many items in Wikidata say country = Germany",
     "SELECT (COUNT(*) AS ?n) WHERE { ?x wdt:P17 wd:Q183 }", 0, ()),

    ("A2", "the same for Romania",
     "SELECT (COUNT(*) AS ?n) WHERE { ?x wdt:P17 wd:Q218 }", 0, ()),

    ("A3", "how many league statements (P118) exist in all of Wikidata",
     "SELECT (COUNT(*) AS ?n) WHERE { ?x wdt:P118 ?l }", 0, ()),

    ("B1", "rows the German discovery query has to produce, counted only",
     """SELECT (COUNT(*) AS ?n) WHERE {
          ?club wdt:P17 wd:Q183 ; wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
          FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
        }""", 0, ()),

    ("B2", "the same for Romania",
     """SELECT (COUNT(*) AS ?n) WHERE {
          ?club wdt:P17 wd:Q218 ; wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
          FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
        }""", 0, ()),

    ("B3", "how many different leagues are in that German answer",
     """SELECT (COUNT(DISTINCT ?league) AS ?n) WHERE {
          ?club wdt:P17 wd:Q183 ; wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
        }""", 0, ()),

    ("B4", "the German join with no filters at all, counted only",
     "SELECT (COUNT(*) AS ?n) WHERE { ?club wdt:P17 wd:Q183 ; wdt:P118 ?league }",
     0, ()),

    ("C1", "the discovery query exactly as fetch_clubs.py sends it, Germany",
     AS_IS % {"country": "Q183", "lang": "de"}, 3, ("league", "leagueLabel")),

    ("C2", "the same, Romania - the half that works",
     AS_IS % {"country": "Q218", "lang": "ro"}, 3, ("league", "leagueLabel")),

    ("C3", "Germany, label service removed, everything else identical",
     """SELECT ?club ?league WHERE {
          ?club wdt:P17 wd:Q183 ; wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
          FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
        }""", 3, ("club", "league")),

    ("C4", "Germany, label service and both filters removed",
     "SELECT ?club ?league WHERE { ?club wdt:P17 wd:Q183 ; wdt:P118 ?league }",
     3, ("club", "league")),

    ("C5", "Germany, one row per league instead of one per club, no labels",
     """SELECT ?league (COUNT(DISTINCT ?club) AS ?clubs) WHERE {
          ?club wdt:P17 wd:Q183 ; wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
        } GROUP BY ?league""", 5, ("league", "clubs")),

    ("C6", "the same, with the label service put back",
     """SELECT ?league ?leagueLabel (COUNT(DISTINCT ?club) AS ?clubs) WHERE {
          ?club wdt:P17 wd:Q183 ; wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en" }
        } GROUP BY ?league ?leagueLabel ORDER BY DESC(?clubs)""",
     12, ("league", "leagueLabel", "clubs")),

    ("C7", "Germany, optimiser switched off so the league statement is read first",
     HINT + """SELECT ?club ?league ?leagueLabel WHERE {
          hint:Query hint:optimizer "None" .
          ?club wdt:P118 ?league .
          ?club wdt:P17 wd:Q183 .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
          FILTER NOT EXISTS { ?club wdt:P576 ?dissolved }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en" }
        }""", 3, ("league", "leagueLabel")),

    ("C8", "Germany, only items that are a football club by type",
     """SELECT ?league ?leagueLabel (COUNT(DISTINCT ?club) AS ?clubs) WHERE {
          ?club wdt:P31/wdt:P279* wd:Q476028 ; wdt:P17 wd:Q183 ; wdt:P118 ?league .
          SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en" }
        } GROUP BY ?league ?leagueLabel ORDER BY DESC(?clubs)""",
     12, ("league", "leagueLabel", "clubs")),

    ("C9", "the question turned round: leagues whose own country is Germany",
     """SELECT ?league ?leagueLabel (COUNT(DISTINCT ?club) AS ?clubs) WHERE {
          ?league wdt:P17 wd:Q183 .
          ?club wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en" }
        } GROUP BY ?league ?leagueLabel ORDER BY DESC(?clubs)""",
     15, ("league", "leagueLabel", "clubs")),

    ("C10", "the same, narrowed to leagues whose sport is football",
     """SELECT ?league ?leagueLabel (COUNT(DISTINCT ?club) AS ?clubs) WHERE {
          ?league wdt:P17 wd:Q183 ; wdt:P641 wd:Q2736 .
          ?club wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en" }
        } GROUP BY ?league ?leagueLabel ORDER BY DESC(?clubs)""",
     15, ("league", "leagueLabel", "clubs")),

    ("C11", "the same turned-round query for Romania, to compare against the 56",
     """SELECT ?league (COUNT(DISTINCT ?club) AS ?clubs) WHERE {
          ?league wdt:P17 wd:Q218 .
          ?club wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
        } GROUP BY ?league""", 5, ("league", "clubs")),

    ("D1", "paging: the German query, first 10000 rows, no order",
     """SELECT ?club ?league WHERE {
          ?club wdt:P17 wd:Q183 ; wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
        } LIMIT 10000""", 2, ("club", "league")),

    ("D2", "paging done properly: the same ordered by club, which is what a "
           "second page would need",
     """SELECT ?club ?league WHERE {
          ?club wdt:P17 wd:Q183 ; wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
        } ORDER BY ?club LIMIT 10000""", 2, ("club", "league")),

    ("D3", "paging, page two: the same with OFFSET 10000",
     """SELECT ?club ?league WHERE {
          ?club wdt:P17 wd:Q183 ; wdt:P118 ?league .
          FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
        } ORDER BY ?club LIMIT 10000 OFFSET 10000""", 2, ("club", "league")),
]


def ask(query):
    body = urllib.parse.urlencode({"query": query, "format": "json"}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"User-Agent": USER_AGENT,
                 "Accept": "application/sparql-results+json",
                 "Content-Type": "application/x-www-form-urlencoded"})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        took = time.time() - started
        try:
            detail = exc.read().decode("utf-8", "replace")
        except Exception:
            detail = ""
        detail = " ".join(detail.split())[:240]
        return took, None, 0, f"HTTP {exc.code} - {detail or 'no body'}"
    except Exception as exc:
        return time.time() - started, None, 0, f"{type(exc).__name__}: {exc}"

    took = time.time() - started
    try:
        rows = json.loads(raw)["results"]["bindings"]
    except ValueError:
        return took, None, len(raw), (f"answer cut off mid-JSON after "
                                      f"{len(raw)} bytes")
    return took, rows, len(raw), None


def main():
    print("=" * 78)
    print("WHY THE GERMAN DISCOVERY QUERY DOES NOT FINISH")
    print(f"client timeout {TIMEOUT_SECONDS}s; the query service gives up on "
          f"its own after 60s")
    print("=" * 78)

    for position, (code, description, query, sample, fields) in enumerate(PROBES):
        if position:
            time.sleep(GAP_SECONDS)
        print()
        print(f"  {code}  {description}")
        took, rows, size, error = ask(query)
        if error:
            print(f"      FAILED after {took:5.1f}s   {error}")
            continue
        print(f"      {took:5.1f}s   {len(rows)} row(s), {size} bytes")
        for row in rows[:sample]:
            values = "  ".join(
                f"{f}={row.get(f, {}).get('value', '')}" for f in fields)
            print(f"        {values[:150]}")

    print()
    print("=" * 78)


if __name__ == "__main__":
    main()
