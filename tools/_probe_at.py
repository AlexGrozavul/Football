"""TEMPORARY probe #3: sources for the multi-ground clubs, and the Austrian
grounds, reserve sides and VSE St. Poelten. Removed in the same branch."""
import csv, json, re, sys, time, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc

def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

def ents(ids, props="claims|labels|sitelinks"):
    out = {}
    ids = list(dict.fromkeys(ids))
    for i in range(0, len(ids), 45):
        args = {"action": "wbgetentities", "props": props, "languages": "en|de|fr|it|ro",
                "format": "json", "ids": "|".join(ids[i:i+45])}
        d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), "ents")
        out.update((d or {}).get("entities", {}))
        time.sleep(1)
    return out

def lab(ent):
    for l in ("en", "de", "fr", "it", "ro"):
        v = (ent.get("labels", {}).get(l) or {}).get("value")
        if v: return v

def vals(ent, prop):
    out = []
    for c in ent.get("claims", {}).get(prop, []):
        v = c["mainsnak"].get("datavalue", {}).get("value")
        if v is None: v = c["mainsnak"].get("snaktype")
        elif isinstance(v, dict) and "latitude" in v: v = (round(v["latitude"], 6), round(v["longitude"], 6))
        elif isinstance(v, dict) and "amount" in v: v = v["amount"]
        elif isinstance(v, dict) and "id" in v: v = v["id"]
        elif isinstance(v, dict) and "time" in v: v = v["time"][:11]
        out.append((v, c.get("rank")[:4]))
    return out

def search(term, lang="de"):
    args = {"action": "wbsearchentities", "search": term, "language": lang, "format": "json", "limit": 6}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), "search")
    return [(h.get("id"), h.get("label"), h.get("description")) for h in (d or {}).get("search", [])]

def wiki(title, host="en.wikipedia.org", keys="ground|capacity|stadion|kapazität|plätze|liga|league|season|position|dissolved|aufgelöst|gründung|coordinates|breitengrad|längengrad|tenants|opened|eröffnung|verein"):
    qs = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "wikitext", "format": "json",
                                 "formatversion": "2", "redirects": "1", "section": "0"})
    d, e = cr.get_json_with_retry(f"https://{host}/w/api.php?" + qs, title)
    wt = (d or {}).get("parse", {}).get("wikitext", "")
    keep = [l.strip() for l in wt.splitlines() if re.match(r"\s*\|\s*(%s)" % keys, l, re.I)]
    return " || ".join(keep)[:700] if keep else ("(no lines)" if wt else "(no article)")

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": cr.USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as ex:
        return ""

# ---- a. Lyon through CLUB_QUERY itself
tiers = [r["leagueQid"] for r in csv.DictReader(open("data/league-tiers.csv")) if r["country"] == "FR"]
res, err = fc.sparql_with_retry(fc.CLUB_QUERY % {"leagues": " ".join("wd:" + l for l in tiers), "lang": "fr"})
rows = [r for r in (res or {}).get("results", {}).get("bindings", []) if q_(fc.cell(r, "club")) == "Q704"]
p("LYON", err, len(rows), sorted({(q_(fc.cell(r, "venue")), fc.cell(r, "venueLabel")) for r in rows}))
time.sleep(3)

# ---- b. season-article stadium rows
for art, pat in [("2026–27 Liga I", r"Rapid"), ("2026–27 3. Liga", r"Stuttgart"), ("2026–27 Ligue 1", r"Lyon"),
                 ("2026–27 Swiss Super League", r"Lugano|AIL|Cornaredo")]:
    page, real, e = cr.fetch_article(art)
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page or "", re.S):
        t = cr.text_of(tr)
        if re.search(pat, t) and len(t) < 300: p("TABLE", art, "|", t)
    time.sleep(2)

# ---- c. StadiumDB rows
for slug, pat in [("ger", r"Dynamo|Hohensch|Jahn|Rote Erde|Signal|Waldau|Schlienz|Stuttgart|Aspach|Freiburg"),
                  ("rou", r"Rapid|Giule|Regie"), ("fra", r"Lyon|Gerland|Groupama|Décines"),
                  ("sui", r"Lugano|AIL|Cornaredo"), ("aut", r".")]:
    body = get(f"https://stadiumdb.com/stadiums/{slug}")
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S):
        t = cr.text_of(tr)
        if re.search(pat, t): p("SDB", slug, "|", t)
    time.sleep(5)

# ---- d. Austrian grounds and items
for term in ["Untersberg-Arena", "Max Aicher Stadion", "Raiffeisen Arena Linz", "Sportzentrum Maxglan",
             "SK Rapid Wien II", "SK Sturm Graz II", "Austria Wien II", "Sturm Graz Amateure", "Rapid Wien Amateure",
             "Franz Fekete Stadion", "Donauparkstadion", "Hofmann Personal Stadion"]:
    p("SEARCH", term, "|", search(term))
    time.sleep(1)
E = ents(["Q686798", "Q206135", "Q731715", "Q60967849", "Q140038602", "Q671287", "Q1759621",
          "Q489700", "Q671514", "Q119291101", "Q696491", "Q204484", "Q872250", "Q1232645", "Q17310225"])
for q, x in E.items():
    p("ENT", q, "|", lab(x), "| P31", [v[0] for v in vals(x, "P31")][:3], "| P625", vals(x, "P625"),
      "| P1083", vals(x, "P1083"), "| P466", vals(x, "P466")[:6], "| P576", vals(x, "P576"),
      "| P1619", vals(x, "P1619"), "| enwiki", cr.enwiki_title(x),
      "| dewiki", ((x.get("sitelinks") or {}).get("dewiki") or {}).get("title"))
for t, host in [("VSE St. Pölten", "de.wikipedia.org"), ("FC Liefering", "en.wikipedia.org"),
                ("SV Austria Salzburg", "en.wikipedia.org"), ("SK Rapid Wien II", "de.wikipedia.org"),
                ("SK Sturm Graz II", "de.wikipedia.org"), ("FK Austria Wien II", "de.wikipedia.org"),
                ("Untersberg-Arena", "de.wikipedia.org"), ("Max Aicher Stadion", "de.wikipedia.org"),
                ("FC Blau-Weiß Linz", "en.wikipedia.org"), ("SC Austria Lustenau", "en.wikipedia.org"),
                ("LASK", "en.wikipedia.org"), ("Raiffeisen Arena (Linz)", "en.wikipedia.org"),
                ("Stadion Rote Erde", "en.wikipedia.org"), ("Berliner FC Dynamo", "en.wikipedia.org"),
                ("Sportforum Hohenschönhausen", "en.wikipedia.org"), ("VfB Stuttgart II", "de.wikipedia.org"),
                ("FC Rapid București", "ro.wikipedia.org")]:
    p("WIKI", host, t, "|", wiki(t, host))
    time.sleep(1)
p("=== END OF PROBE AT3 ===")
