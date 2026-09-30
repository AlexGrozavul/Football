"""TEMPORARY probe #2 for the England pass. Removed in the same branch."""
import re, sys, time, traceback, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc


def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]


def section(name, fn):
    p(f"########## {name}")
    try:
        fn()
    except Exception:
        p("SECTION-FAILED", name, traceback.format_exc()[-800:])


def w1():
    # rule 6, second angle: an item carrying either league at ANY rank whose competition class (P2094)
    # or English description says women - a women's club typed only as a club would slip past a type check
    Q = """SELECT DISTINCT ?club ?clubLabel ?desc ?cls ?clsLabel WHERE {
      VALUES ?league { wd:Q9448 wd:Q19510 }
      ?club p:P118/ps:P118 ?league .
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
      OPTIONAL { ?club schema:description ?desc . FILTER(LANG(?desc) = "en") }
      OPTIONAL { ?club wdt:P2094 ?cls }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }"""
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("W1", err, len(rows))
    for r in rows:
        d = (fc.cell(r, "desc") or "") + " " + (fc.cell(r, "clsLabel") or "")
        if re.search(r"women|ladies|female|girls", d, re.I) or fc.cell(r, "cls"):
            p("W1-ROW", q_(fc.cell(r, "club")), fc.cell(r, "clubLabel"), "| desc", fc.cell(r, "desc"),
              "| P2094", q_(fc.cell(r, "cls")), fc.cell(r, "clsLabel"))
    # and every item that names one of the 44 roster clubs as its P831/P361 parent and carries a women's type
    Q2 = """SELECT DISTINCT ?t ?tLabel ?club ?clubLabel ?lg WHERE {
      VALUES ?club { wd:Q9617 wd:Q9616 wd:Q18656 wd:Q50602 wd:Q1130849 wd:Q18741 wd:Q5794 wd:Q18747 wd:Q18529 wd:Q18659 wd:Q18662 }
      ?t wdt:P831|wdt:P361 ?club ; wdt:P31 ?ty . ?ty rdfs:label ?tyl . FILTER(LANG(?tyl)="en")
      FILTER(CONTAINS(LCASE(?tyl), "women"))
      OPTIONAL { ?t wdt:P118 ?lg }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }"""
    res, err = fc.sparql_with_retry(Q2)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("W2", err, len(rows))
    for r in rows:
        p("W2-ROW", q_(fc.cell(r, "t")), fc.cell(r, "tLabel"), "| parent", fc.cell(r, "clubLabel"), "| P118", q_(fc.cell(r, "lg")))


def w2():
    for slug in ["wal", "wales"]:
        try:
            req = urllib.request.Request(f"https://stadiumdb.com/stadiums/{slug}", headers={"User-Agent": cr.USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode("utf-8", "replace"); st = r.status
        except urllib.error.HTTPError as ex:
            st, body = ex.code, ""
        except Exception as ex:
            st, body = str(ex), ""
        p("STADIUMDB", slug, st, len(body), body.count("<tr"))
        if st == 200:
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S)[:40]:
                p("   SDB", " | ".join(cr.text_of(x) for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)))
            break
        time.sleep(4)


for name, fn in [("w1 women", w1), ("w2 wales stadiumdb", w2)]:
    section(name, fn)
p("=== END OF PROBE EN2 ===")
