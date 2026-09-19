"""THROWAWAY PROBE - can a roster source actually be had, per country?

Tests the two candidate backbones for the official-roster check:
  1. Wikidata: season item -> P1923 (participating team). Returns Q-ids,
     which join to the club layer with no name matching at all.
  2. Wikipedia: the current-season article's team/stadium table, whose
     club links convert to Q-ids via sitelink - also an exact join.

CLAUDE.md already records that Regionalliga season items carry no P1923.
Nobody has measured tiers 1-2, which is what this does.
"""
import json, re, time, urllib.parse, urllib.request, urllib.error

UA = "football-fixture-planner/1.0 (personal project; https://github.com/AlexGrozavul/Football)"
SPARQL = "https://query.wikidata.org/sparql"

def http(url, hdrs=None, timeout=60):
    h = {"User-Agent": UA}
    if hdrs: h.update(hdrs)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h),
                                    timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, ("ERROR: %s" % e).encode()

def sparql(q, tries=3):
    for a in range(tries):
        u = SPARQL + "?" + urllib.parse.urlencode({"query": q, "format": "json"})
        st, body = http(u, {"Accept": "application/sparql-results+json"}, 70)
        if st == 200:
            try: return json.loads(body)["results"]["bindings"]
            except Exception: pass
        print("    (sparql attempt %d -> HTTP %s)" % (a + 1, st))
        time.sleep(3 * (a + 1))
    return None

# league Q-ids: the 11 already in league-tiers.csv, plus tier 1/2 of the six
# countries under evaluation. The six are looked up BY QUERY, not hardcoded.
KNOWN = {"Q82595":"DE1 Bundesliga","Q152665":"DE2 2.Bundesliga","Q154069":"DE3 3.Liga",
         "Q237753":"RO1 SuperLiga","Q386384":"RO2 Liga II","Q1707697":"RO3 Liga III"}

print("#"*70); print("PART 1  which leagues do the six countries even have?"); print("#"*70)
Q = """
SELECT ?league ?leagueLabel ?countryLabel ?level WHERE {
  VALUES ?country { wd:Q142 wd:Q38 wd:Q39 wd:Q40 wd:Q403 wd:Q41 }
  ?league wdt:P31/wdt:P279* wd:Q15991303 ;
          wdt:P17 ?country ;
          wdt:P3983 ?level .
  FILTER(?level <= 2)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
} ORDER BY ?countryLabel ?level
"""
rows = sparql(Q)
found = {}
if rows is None:
    print("  query failed")
else:
    print("  %d leagues at level 1-2 with P3983 set:" % len(rows))
    for r in rows:
        q = r["league"]["value"].rsplit("/", 1)[-1]
        found[q] = "%s L%s %s" % (r["countryLabel"]["value"][:3].upper(),
                                  r["level"]["value"], r["leagueLabel"]["value"])
        print("    %-10s L%s %-22s %s" % (q, r["level"]["value"],
                                          r["countryLabel"]["value"],
                                          r["leagueLabel"]["value"]))

print("\n"+"#"*70); print("PART 2  do their season items carry P1923 (participants)?")
print("#"*70)
targets = dict(KNOWN); targets.update(found)
vals = " ".join("wd:%s" % q for q in targets)
Q2 = """
SELECT ?league ?season ?start (COUNT(DISTINCT ?team) AS ?teams) WHERE {
  VALUES ?league { %s }
  ?season wdt:P3450 ?league .
  OPTIONAL { ?season wdt:P580 ?start }
  OPTIONAL { ?season wdt:P1923 ?team }
} GROUP BY ?league ?season ?start ORDER BY ?league DESC(?start)
""" % vals
rows = sparql(Q2)
if rows is None:
    print("  query failed")
else:
    best = {}
    for r in rows:
        lq = r["league"]["value"].rsplit("/", 1)[-1]
        st_ = r.get("start", {}).get("value", "")
        n = int(r["teams"]["value"])
        if lq not in best or st_ > best[lq][0]:
            best[lq] = (st_, r["season"]["value"].rsplit("/", 1)[-1], n)
    print("  latest season per league, and how many P1923 teams it lists:")
    print("  %-10s %-34s %-12s %-10s %s" % ("league","name","season","starts","P1923"))
    for lq in targets:
        if lq in best:
            s, sq, n = best[lq]
            print("  %-10s %-34s %-12s %-10s %s" % (lq, targets[lq][:34], sq, s[:10],
                                                    n if n else "*** ZERO ***"))
        else:
            print("  %-10s %-34s %s" % (lq, targets[lq][:34], "no season item at all"))

print("\n"+"#"*70); print("PART 3  the Wikipedia route: does the article exist and parse?")
print("#"*70)
ARTS = ["2026-27 Bundesliga","2026-27 2. Bundesliga","2026-27 Ligue 2",
        "2026-27 Serie B","2026-27 Swiss Challenge League","2026-27 Austrian 2. Liga",
        "2026-27 Serbian First League","2026-27 Super League Greece 2",
        "2026-27 Liga II (Romania)"]
for a in ARTS:
    for dash in ("–", "-"):
        title = a.replace("-", dash, 1) if dash != "-" else a
        u = ("https://en.wikipedia.org/w/api.php?action=parse&format=json&prop=text"
             "&page=" + urllib.parse.quote(title.replace(" ", "_")))
        st, body = http(u)
        try: j = json.loads(body)
        except Exception: j = {}
        if "error" in j:
            continue
        html = j.get("parse", {}).get("text", {}).get("*", "")
        tables = re.findall(r'(?is)<table[^>]*class="[^"]*wikitable[^"]*".*?</table>', html)
        picked = None
        for t in tables:
            head = t[:1400].lower()
            if ("stadium" in head or "venue" in head) and "capacity" in head:
                picked = t; break
        clubs = []
        if picked:
            for row in re.findall(r"(?is)<tr.*?</tr>", picked)[1:]:
                m = re.search(r'(?is)<t[hd][^>]*>.*?<a href="/wiki/([^"#:]+)"', row)
                if m: clubs.append(urllib.parse.unquote(m.group(1)))
        print("  %-36s dash=%s  tables=%-2d  team-table=%s  clubs=%s"
              % (title[:36], "en" if dash != "-" else "hy", len(tables),
                 "yes" if picked else "NO", len(clubs)))
        if clubs:
            print("        first 6: %s" % ", ".join(clubs[:6]))
        break
    else:
        print("  %-36s NO ARTICLE under either dash" % a[:36])
