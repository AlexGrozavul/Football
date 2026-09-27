"""TEMPORARY probe #2 for the Serbia pass and the Austria follow-ups.
Removed in the same branch."""
import csv, json, re, sys, time, traceback, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc


def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

LANGS = "en|de|sr|sr-el|sh"
UA_BROWSER = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def ents(ids, props="claims|labels|sitelinks"):
    out = {}
    ids = list(dict.fromkeys(i for i in ids if i))
    for i in range(0, len(ids), 45):
        args = {"action": "wbgetentities", "props": props, "languages": LANGS,
                "format": "json", "ids": "|".join(ids[i:i + 45])}
        d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), "ents")
        if e: p("ENTS-ERROR", e)
        out.update((d or {}).get("entities", {}))
        time.sleep(1)
    return out


def by_title(site, title):
    args = {"action": "wbgetentities", "sites": site, "titles": title, "props": "claims|labels|sitelinks",
            "languages": LANGS, "format": "json", "normalize": "1", "redirects": "yes"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for q, x in (d or {}).get("entities", {}).items():
        if q.startswith("Q"):
            return q, x
    return None, {}


def search(text, lang="en"):
    args = {"action": "wbsearchentities", "search": text, "language": lang, "limit": "7", "format": "json"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), text)
    return [(r.get("id"), r.get("label"), r.get("description")) for r in (d or {}).get("search", [])]


def lab(ent, order=("en", "de", "sr-el", "sh", "sr")):
    for l in order:
        v = (ent.get("labels", {}).get(l) or {}).get("value")
        if v: return v
    return None


def vals(ent, prop):
    out = []
    for c in ent.get("claims", {}).get(prop, []):
        v = c["mainsnak"].get("datavalue", {}).get("value")
        if v is None: v = c["mainsnak"].get("snaktype")
        elif isinstance(v, dict) and "latitude" in v: v = (round(v["latitude"], 6), round(v["longitude"], 6))
        elif isinstance(v, dict) and "amount" in v: v = v["amount"]
        elif isinstance(v, dict) and "id" in v: v = v["id"]
        elif isinstance(v, dict) and "time" in v: v = v["time"][:11]
        qual = {k: [str(x.get("datavalue", {}).get("value", {}).get("time", ""))[:11] for x in xs]
                for k, xs in c.get("qualifiers", {}).items() if k in ("P580", "P582", "P585")}
        r = c.get("rank")[:4]
        out.append((v, r, qual) if qual else (v, r))
    return out


def sl(ent):
    s = ent.get("sitelinks") or {}
    return len(s), (s.get("enwiki") or {}).get("title"), (s.get("dewiki") or {}).get("title"), (s.get("srwiki") or {}).get("title")


def wikitext(title, lang="en", section="0"):
    args = {"action": "parse", "page": title, "prop": "wikitext", "format": "json",
            "formatversion": "2", "redirects": "1"}
    if section is not None: args["section"] = section
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    return (d or {}).get("parse", {}).get("wikitext", "")


KEYS = (r"dissolved|league|season|position|ground|capacity|coordinates|coord|current|founded|tenants|stadion|plätze|"
        r"aufgelöst|liga|auflösung|kapazität|verein\(e\)|location|stadium|ort|opened|name|лига|стадион|капацитет|сезона|позиција")


def infobox(title, lang="en"):
    wt = wikitext(title, lang)
    keep = [re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", "", l.strip()) for l in wt.splitlines()
            if re.match(r"\s*\|\s*(%s)\b" % KEYS, l, re.I)]
    return " || ".join(keep)[:700] if keep else ("(no infobox lines)" if wt else "(no article)")


def plain(title, lang="en"):
    args = {"action": "query", "prop": "extracts", "explaintext": "1", "titles": title,
            "redirects": "1", "format": "json", "formatversion": "2"}
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    pages = (d or {}).get("query", {}).get("pages", [])
    return re.sub(r"\s+", " ", (pages[0].get("extract") if pages else "") or "")


def fetch(url, browser=False, timeout=45):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA_BROWSER if browser else cr.USER_AGENT,
                                                   "Accept-Language": "de,en"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as ex:
        return ex.code, "", url
    except Exception as ex:
        return str(ex)[:80], "", url


def text(html_):
    html_ = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_, flags=re.S)
    return re.sub(r"\s+", " ", cr.text_of(html_))


def around(t, kws, width=220, most=4):
    out = []
    for kw in kws:
        for m in list(re.finditer(kw, t, re.I))[:most]:
            out.append(t[max(0, m.start() - width):m.end() + width])
    return out


def section(name, fn):
    p(f"########## {name}")
    try:
        fn()
    except Exception:
        p("SECTION-FAILED", name, traceback.format_exc()[-900:])


# ======================================================================
def a1():
    """Brigittenauer AC: how did it end."""
    t = plain("Brigittenauer AC", "de")
    for h in around(t, [r"aufgel", r"Auflösung", r"eingestellt", r"Fusion", r"fusion", r"existiert"], 260, 3):
        p("BAC ...", h)
    p("BAC-TAIL", t[-900:])


def a2():
    """Austrian grounds, by title and by search."""
    for site, title in [("enwiki", "Ertl Glas Stadion"), ("enwiki", "Union-Platz"), ("dewiki", "Ertl-Glas-Stadion"),
                        ("dewiki", "FAC-Platz"), ("enwiki", "FAC-Platz"), ("dewiki", "eww Stadion"),
                        ("dewiki", "Solarstadion Gleisdorf"), ("dewiki", "Stadion Donawitz"),
                        ("enwiki", "Allianz Stadion"), ("enwiki", "Untersberg-Arena"), ("dewiki", "MGG Arena"),
                        ("enwiki", "Liebenauer Stadium"), ("dewiki", "Hans-Blümel-Stadion"),
                        ("dewiki", "Casino-Stadion (Bregenz)")]:
        q, x = by_title(site, title)
        p("GTITLE", site, title, "->", q, "|", lab(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083")[:3],
          "| P466", [v[0] for v in vals(x, "P466")][:6], "| P131", [v[0] for v in vals(x, "P131")][:2])
        time.sleep(0.5)
    for s in ["Münzer Bioindustrie Sportpark", "Hans Blümel Stadion", "Huber Arena", "eww Stadion", "FAC-Platz",
              "Ertl Glas Stadion", "Solarstadion Gleisdorf", "Stadion Donawitz", "Sportplatz Voitsberg"]:
        p("GSEARCH", s, search(s, "de"))
        time.sleep(0.5)
    for t in ["Ertl-Glas-Stadion", "FAC-Platz", "eww Stadion", "Solarstadion Gleisdorf", "MGG Arena"]:
        p("GINFO de", t, "|", infobox(t, "de"))
    for t in ["Ertl-Glas-Stadion", "FAC-Platz", "eww Stadion"]:
        p("GTEXT de", t, "|", plain(t, "de")[:500])


def a3():
    """OpenStreetMap objects for the Austrian grounds with no Wikidata position."""
    q = """[out:json][timeout:120];
    area["ISO3166-1"="AT"][admin_level=2]->.a;
    ( nwr["leisure"~"stadium|pitch|sports_centre"]["name"~"Blümel|Münzer|Huber|eww|FAC|Ertl|Solarstadion|Hertha|Mauth|Union-Platz|Voitsberg|Floridsdorf|Donawitz|Gleisdorf",i](area.a); );
    out center tags;"""
    body = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=body,
                                 headers={"User-Agent": cr.USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.loads(r.read().decode())
    except Exception as ex:
        p("OVERPASS-ERROR", ex); return
    for el in d.get("elements", []):
        c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        t = el.get("tags", {})
        p("OSM", f"{el['type']}/{el['id']}", round(c.get("lat") or 0, 6), round(c.get("lon") or 0, 6), "|",
          {k: t[k] for k in ("name", "leisure", "sport", "operator", "capacity", "addr:city", "wikidata", "club") if k in t})


def a4():
    """The league's own site and the clubs' own sites: robots first."""
    for base in ["https://www.2liga.at", "https://www.bundesliga.at", "https://www.wsg-fussball.at",
                 "https://www.fcliefering.at"]:
        st, body, url = fetch(base + "/robots.txt")
        p("ROBOTS", base, st, "|", body[:400].replace("\n", " / "))
        time.sleep(1)
    st, body, url = fetch("https://www.2liga.at/de/")
    p("2LIGA-HOME", st, url, len(body))
    links = sorted(set(re.findall(r'href="(/de/team/[^"]+)"', body)))
    p("2LIGA-TEAMLINKS", len(links), links[:40])
    for path in links:
        if not any(k in path for k in ("liefering", "amstetten", "bregenz", "floridsdorf", "fac", "voitsberg",
                                       "hertha", "rapid", "sturm", "wacker")):
            continue
        base = re.sub(r"/(kader|spielplan|stadion|news|statistik)?$", "", path.rstrip("/"))
        st, body2, url2 = fetch("https://www.2liga.at" + base + "/stadion")
        t = text(body2)
        hits = around(t, [r"Kapazit", r"Stadion", r"Fassungs", r"Plätze", r"Adresse", r"Zuschauer"], 120, 2)
        p("2LIGA-STADION", base, st, "|", " ## ".join(hits)[:900])
        time.sleep(2)
    for url in ["https://www.wsg-fussball.at/de/verein/stadion/", "https://www.wsg-fussball.at/en/club/stadium/"]:
        st, body, u = fetch(url)
        t = text(body)
        p("WSG", url, st, "|", " ## ".join(around(t, [r"Kapazit", r"capacity", r"Plätze", r"seats", r"Sitzpl", r"Zuschauer"], 150, 3))[:1200])
        time.sleep(2)
    st, body, u = fetch("https://www.fcliefering.at/")
    t = text(body)
    p("LIEFERING-HOME", st, "|", " ## ".join(around(t, [r"Untersberg", r"MGG", r"Grödig", r"Red Bull Arena", r"Heimspiel"], 120, 3))[:1200])


def a5():
    """Liefering: the Untersberg-Arena item and German article."""
    for t in ["MGG Arena", "FC Liefering"]:
        tx = plain(t, "de")
        p("LIEF-DE", t, "|", " ## ".join(around(tx, [r"Liefering", r"Heimspiel", r"Grödig", r"Red Bull Arena", r"Saison 2025", r"Saison 2026"], 180, 3))[:1800])
    q, x = by_title("enwiki", "Untersberg-Arena")
    p("UA", q, lab(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083"), "| P466", vals(x, "P466"), "| sl", sl(x))


# ======================================================================
RS = {
    # extras (tier 1 or 2 by tags, in neither article)
    "Q651198": "FK BSK Borča", "Q2407113": "OFK Bečej 1918", "Q953621": "FK Bežanija", "Q5426069": "FK Bačinci",
    "Q2513289": "FK Budućnost Banatski Dvor", "Q591746": "FK Inđija", "Q5426189": "FK Jedinstvo Putevi",
    "Q2662732": "FK Kolubara", "Q5426249": "FK Mladost Novi Sad", "Q2505780": "FK Proleter Novi Sad",
    "Q2561958": "FK Proleter Zrenjanin", "Q757098": "FK Rad", "Q5426363": "FK Radnički Nova Pazova",
    "Q995113": "FK Sloboda Užice", "Q2335020": "FK Sloga Kraljevo", "Q9257379": "FK Sloga 33",
    "Q2505672": "FK Srem", "Q9257386": "FK Tekstilac Odžaci", "Q3544941": "FK Timok", "Q5426474": "FK Zlatibor Čajetina",
    "Q284077": "OFK Bačka", "Q749049": "OFK Mladenovac", "Q2523663": "RFK Novi Sad 1921",
    # at the wrong tier by tags
    "Q218724": "FK Javor Ivanjica", "Q843210": "FK Napredak Kruševac", "Q421940": "FK Smederevo 1924",
    "Q94605": "FK Spartak Subotica", "Q828297": "FK TSC", "Q2614598": "FK Mačva Šabac",
    # missing
    "Q2123289": "FK Bor 1919", "Q4863629": "FK Loznica", "Q140302346": "FK Proleter 023", "Q1323373": "FK Zemun",
    "Q5426131": "GFK Dubočica", "Q61130291": "OFK Vršac", "Q3063273": "RFK Grafičar Beograd",
    # on the map but unplaced, or with no ground on Wikidata
    "Q31181880": "FK IMT", "Q12760457": "FK Železničar Pančevo", "Q1388917": "FK Jedinstvo Ub",
}


def b1():
    E = ents(list(RS))
    for q, title in RS.items():
        x = E.get(q, {})
        s = x.get("sitelinks") or {}
        en = (s.get("enwiki") or {}).get("title")
        p("RSCLUB", q, title, "| P576", vals(x, "P576") or "-", "| P1366", vals(x, "P1366"), "| P31", [v[0] for v in vals(x, "P31")][:3])
        if en:
            p("   EN", en, "|", infobox(en, "en"))
        else:
            srt = (s.get("srwiki") or {}).get("title")
            if srt: p("   SR", srt, "|", infobox(srt, "sr"))
        time.sleep(0.4)


def b2():
    for art in ["2026–27 Serbian SuperLiga", "2026–27 Serbian First League"]:
        page, real, err = cr.fetch_article(art)
        if err: p("ART", art, err); continue
        m = re.search(r'id="Team_changes".*?(<table.*?</table>)', page, re.S)
        if m:
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(1), re.S):
                p("  CHANGES", art[:14], [cr.text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)])
        t = cr.text_of(page)
        for h in around(t, [r"withdr", r"expell", r"exclu", r"licen", r"dissol", r"merged", r"replac"], 200, 3):
            p("  NOTE", art[:14], "...", h)


def b3():
    """Serbian grounds for the clubs that will need a position."""
    for site, title in [("enwiki", "Lagator Stadium"), ("enwiki", "Zemun Stadium"), ("enwiki", "Dubočica Stadium"),
                        ("enwiki", "Stadion Karađorđev park"), ("enwiki", "TSC Arena"), ("enwiki", "Mladost Stadium (Kruševac)"),
                        ("enwiki", "Stadion Bor"), ("enwiki", "Rajko Mitić Stadium"), ("enwiki", "Serbian FA Sports Center"),
                        ("enwiki", "Javor Stadium"), ("enwiki", "Čačak Stadium"), ("enwiki", "Metalac Stadium"),
                        ("enwiki", "Smederevo Stadium"), ("enwiki", "Subotica City Stadium"), ("enwiki", "SC Partizan-Teleoptik"),
                        ("enwiki", "Voždovac Stadium"), ("enwiki", "Čukarički Stadium"), ("enwiki", "Novi Pazar City Stadium"),
                        ("enwiki", "Surdulica City Stadium"), ("enwiki", "Karađorđe Stadium"), ("enwiki", "Partizan Stadium"),
                        ("enwiki", "Čair Stadium"), ("enwiki", "Čika Dača Stadium"), ("enwiki", "Omladinski Stadium")]:
        q, x = by_title(site, title)
        p("RSG", title, "->", q, "|", lab(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083")[:3],
          "| P466", [v[0] for v in vals(x, "P466")][:6], "| P131", [v[0] for v in vals(x, "P131")][:1])
        time.sleep(0.4)
    for s, lang in [("Stadion FK Mačva", "sr"), ("Mačva Šabac stadium", "en"), ("Gradski stadion Vršac", "sr"),
                    ("Stadion Mladost Pančevo", "sr"), ("Stadion Dragan Džajić Ub", "sr"), ("Gradski stadion Bor", "sr"),
                    ("Stadion Dragan Džajić", "en"), ("SRC Mr Radoš Milovanović", "en")]:
        p("RSGSEARCH", s, search(s, lang))
        time.sleep(0.4)
    for t in ["FK Mačva Šabac", "FK Železničar Pančevo", "FK Jedinstvo Ub", "OFK Vršac", "FK Bor 1919", "FK IMT",
              "FK Loznica", "RFK Grafičar Beograd", "GFK Dubočica", "FK Proleter 023", "FK Zemun", "OFK Beograd",
              "FK Mladost Lučani", "FK TSC"]:
        p("RSINFO", t, "|", infobox(t, "en"))
        time.sleep(0.3)


def b4():
    """OpenStreetMap: named football grounds in the Serbian towns that need one."""
    q = """[out:json][timeout:150];
    area["ISO3166-1"="RS"][admin_level=2]->.a;
    ( nwr["leisure"~"stadium|pitch"]["name"~"Мачв|Mačv|Вршац|Vršac|Младост|Mladost|Џајић|Džajić|Бор|Лагатор|Lagator|Дубочиц|Dubočic|ТСЦ|TSC|Железничар|Železničar|Пролетер|Proleter|Карађорђев|Земун|Zemun|Графичар|Grafičar",i](area.a); );
    out center tags;"""
    body = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=body, headers={"User-Agent": cr.USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=200) as r:
            d = json.loads(r.read().decode())
    except Exception as ex:
        p("OVERPASS-ERROR", ex); return
    for el in d.get("elements", []):
        c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        t = el.get("tags", {})
        if t.get("leisure") == "pitch" and not t.get("name"):
            continue
        p("RSOSM", f"{el['type']}/{el['id']}", round(c.get("lat") or 0, 6), round(c.get("lon") or 0, 6), "|",
          {k: t[k] for k in ("name", "name:sr-Latn", "leisure", "sport", "operator", "capacity", "addr:city", "wikidata") if k in t})


for name, fn in [("A1 BAC", a1), ("A2 AT grounds", a2), ("A3 AT OSM", a3), ("A4 AT sites", a4), ("A5 Liefering", a5),
                 ("B1 RS clubs", b1), ("B2 RS changes", b2), ("B3 RS grounds", b3), ("B4 RS OSM", b4)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE RS2 ===")
