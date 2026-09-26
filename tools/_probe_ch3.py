"""TEMPORARY probe #3 for the Switzerland pass. Removed in the same branch."""
import json, re, sys, time, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc

def p(*a): print(" ".join(str(x) for x in a), flush=True)

# 1. every wikitable on the Super League article: its headers and rows
page, real, e = cr.fetch_article("2026–27 Swiss Super League")
tables = re.findall(r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>.*?</table>', page, re.S)
p("SL tables", len(tables))
for i, t in enumerate(tables):
    heads = [cr.text_of(h) for h in re.findall(r"<th[^>]*>(.*?)</th>", t, re.S)[:10]]
    p("TABLE", i, heads)
    if any("tadi" in h or "apacit" in h for h in heads):
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)[1:]:
            cells = [cr.text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
            p("   ROW", cells)
time.sleep(2)
# the stadia section, whatever its markup
m = re.search(r'id="Stadia_and_locations".*?(<table.*?</table>)', page, re.S)
if m:
    p("STADIA-TABLE-OPEN", m.group(1)[:200])
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(1), re.S):
        p("   SROW", [cr.text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)])

# 2. infoboxes
def wikitext(title):
    qs = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "wikitext",
                                 "format": "json", "formatversion": "2", "redirects": "1", "section": "0"})
    d, e = cr.get_json_with_retry(f"{cr.WIKIPEDIA_API}?{qs}", title)
    return (d or {}).get("parse", {}).get("wikitext", "")
for title in ["FC Lausanne-Sport", "FC Wil 1900", "FC Stade Lausanne-Ouchy", "Stade de la Tuilière",
              "Stade Olympique de la Pontaise", "Stade de Tourbillon", "St. Jakob-Park", "Stadion Kleinfeld",
              "Stade Municipal (Yverdon-les-Bains)", "Stade de la Fontenette", "Stadion Brügglifeld",
              "Rheinpark Stadion", "Stadio Cornaredo", "Stockhorn Arena", "Letzigrund", "Lidl Arena"]:
    wt = wikitext(title)
    keep = [l.strip() for l in wt.splitlines()
            if re.match(r"\s*\|\s*(ground|capacity|league|season|position|stadium_name|coordinates|tenants|opened|record_attendance)\b", l, re.I)]
    p("INFOBOX", title, "|", " || ".join(keep)[:600] if keep else ("(no infobox lines)" if wt else "(no article)"))
    time.sleep(1)

# 3. Wikidata: grounds of the Swiss clubs, and the Tuilière item
Q = """SELECT ?club ?clubLabel ?v ?vLabel ?coord ?cap WHERE {
  VALUES ?club { wd:Q309456 wd:Q869907 wd:Q187091 wd:Q321061 wd:Q671950 wd:Q669130 wd:Q166496 wd:Q603271 }
  OPTIONAL { ?club p:P115 ?st . ?st ps:P115 ?v . OPTIONAL { ?v wdt:P625 ?coord } OPTIONAL { ?v wdt:P1083 ?cap } }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "de,fr,en" }
}"""
res, err = fc.sparql_with_retry(Q)
for r in (res or {}).get("results", {}).get("bindings", []):
    p("GROUND", fc.cell(r, "club"), fc.cell(r, "clubLabel"), "|", fc.cell(r, "v"), fc.cell(r, "vLabel"), "|", fc.cell(r, "coord"), "|", fc.cell(r, "cap"))
time.sleep(2)
Q2 = """SELECT ?s ?sLabel ?coord ?cap ?tenant ?tenantLabel WHERE {
  ?s rdfs:label ?l . FILTER(LANG(?l) IN ("fr","en","de")) FILTER(CONTAINS(?l, "Tuilière"))
  OPTIONAL { ?s wdt:P625 ?coord } OPTIONAL { ?s wdt:P1083 ?cap } OPTIONAL { ?s wdt:P466 ?tenant }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" }
} LIMIT 20"""
res, err = fc.sparql_with_retry(Q2)
p("TUILIERE", err)
for r in (res or {}).get("results", {}).get("bindings", []):
    p("  ", fc.cell(r, "s"), fc.cell(r, "sLabel"), fc.cell(r, "coord"), fc.cell(r, "cap"), fc.cell(r, "tenantLabel"))

# 4. StadiumDB Swiss page: every ground listed
import urllib.request
req = urllib.request.Request("https://stadiumdb.com/stadiums/sui", headers={"User-Agent": cr.USER_AGENT})
body = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S):
    p("SDB", [cr.text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)])
p("=== END OF PROBE 3 ===")
