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
def c1():
    """The Austrian league's own site: team stadium pages, found through its sitemap (robots.txt: Allow /)."""
    st, body, url = fetch("https://www.2liga.at/sitemap.xml")
    p("SITEMAP", st, len(body))
    locs = re.findall(r"<loc>([^<]+)</loc>", body)
    p("SITEMAP-LOCS", len(locs), locs[:8])
    subs = [l for l in locs if l.endswith(".xml")]
    team_urls = [l for l in locs if "/team/" in l]
    for sub in subs[:12]:
        st2, b2, _ = fetch(sub)
        more = re.findall(r"<loc>([^<]+)</loc>", b2)
        team_urls += [l for l in more if "/team/" in l]
        time.sleep(1)
    team_urls = sorted(set(team_urls))
    p("TEAM-URLS", len(team_urls), team_urls[:60])
    wanted = ("liefering", "amstetten", "bregenz", "floridsdorf", "fac-", "voitsberg", "hertha", "rapid", "sturm",
              "wacker")
    bases = sorted({re.sub(r"(/\d+)/.*$", r"\1", u) for u in team_urls if any(k in u.lower() for k in wanted)})
    p("TEAM-BASES", bases)
    for base in bases[:14]:
        st3, b3, u3 = fetch(base.rstrip("/") + "/stadion")
        t = text(b3)
        i = t.find("Stadion")
        p("2LIGA", base, st3, "|", " ## ".join(around(t, [r"Kapazit", r"Fassungs", r"Zuschauer", r"Adresse", r"Sitzpl", r"Stehpl"], 140, 2))[:900])
        time.sleep(2)
    # the Bundesliga's page for WSG Tirol's ground
    st, body, url = fetch("https://www.bundesliga.at/sitemap.xml")
    locs = re.findall(r"<loc>([^<]+)</loc>", body)
    subs = [l for l in locs if l.endswith(".xml")]
    urls = [l for l in locs if "wsg" in l.lower() or "tirol" in l.lower()]
    for sub in subs[:12]:
        st2, b2, _ = fetch(sub)
        urls += [l for l in re.findall(r"<loc>([^<]+)</loc>", b2) if "wsg" in l.lower()]
        time.sleep(1)
    urls = sorted(set(urls))
    p("BL-WSG-URLS", len(urls), urls[:20])
    for u in [x for x in urls if "stadion" in x.lower()][:3] + [x for x in urls if "stadion" not in x.lower()][:1]:
        st4, b4, _ = fetch(u.rstrip("/") + ("" if "stadion" in u.lower() else "/stadion"))
        t = text(b4)
        p("BL-WSG", u, st4, "|", " ## ".join(around(t, [r"Kapazit", r"Fassungs", r"Zuschauer", r"Sitzpl"], 140, 2))[:900])
        time.sleep(2)


def c2():
    """German Wikipedia on where Sturm II and Rapid II play, and Liefering's move."""
    for t, kws in [("SK Sturm Graz II", [r"Gleisdorf", r"Donawitz", r"Merkur", r"Heimspiel", r"Stadion"]),
                   ("SK Rapid Wien II", [r"Allianz", r"Heimspiel", r"Stadion", r"Hütteldorf"]),
                   ("FC Liefering", [r"Red Bull Arena", r"Untersberg", r"MGG", r"Grödig", r"Heimspiel"]),
                   ("FC Hertha Wels", [r"Stadion", r"Mauth", r"eww", r"Huber", r"Heimspiel"]),
                   ("ASK Voitsberg", [r"Stadion", r"Sportpark", r"Blümel", r"Münzer", r"Heimspiel"])]:
        tx = plain(t, "de")
        p("DETEXT", t, len(tx), "|", " ## ".join(around(tx, kws, 160, 2))[:1600])
        time.sleep(0.5)
    E = ents(["Q140456746", "Q65167618", "Q38244305", "Q85760247", "Q3280007", "Q13567334"])
    for q, x in E.items():
        p("ITEMC", q, lab(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083"), "| P131", [v[0] for v in vals(x, "P131")][:2],
          "| P466", [v[0] for v in vals(x, "P466")][:4], "| P31", [v[0] for v in vals(x, "P31")][:3], "| sl", sl(x))


def c3():
    """Serbia: the country's extreme points, for the country box."""
    E = ents(["Q403"])
    x = E.get("Q403", {})
    for prop in ("P1332", "P1333", "P1334", "P1335"):
        for c in x.get("claims", {}).get(prop, []):
            v = c["mainsnak"].get("datavalue", {}).get("value", {})
            quals = c.get("qualifiers", {})
            coord = [q.get("datavalue", {}).get("value") for q in quals.get("P625", [])]
            p("EXTREME", prop, v, coord[:1], "| rank", c.get("rank"))


def c4():
    """Serbia: grounds in Ub, Pancevo and Vrsac, from OpenStreetMap, whatever they are called."""
    q = """[out:json][timeout:150];
    ( nwr["leisure"~"stadium|pitch"](around:3500,44.456,20.074);
      nwr["leisure"~"stadium|pitch"](around:4500,44.871,20.640);
      nwr["leisure"~"stadium|pitch"](around:3500,45.117,21.303); );
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
        if t.get("sport") not in (None, "soccer", "football", "athletics;soccer", "soccer;athletics", "multi") and t.get("leisure") == "pitch":
            continue
        if t.get("leisure") == "pitch" and not t.get("name"):
            continue
        p("RSOSM2", f"{el['type']}/{el['id']}", round(c.get("lat") or 0, 6), round(c.get("lon") or 0, 6), "|",
          {k: t[k] for k in ("name", "name:sr-Latn", "leisure", "sport", "operator", "capacity", "wikidata") if k in t})


def c5():
    """Serbia: the leagues' own sites, robots first, then the clubs whose ground is in question."""
    for base in ["https://www.superliga.rs", "https://superliga.rs", "https://www.prvaliga.rs", "https://prvaliga.rs",
                 "https://www.fss.rs"]:
        st, body, url = fetch(base + "/robots.txt")
        p("RSROBOTS", base, st, url, "|", body[:300].replace("\n", " / "))
        time.sleep(1)
    st, body, url = fetch("https://www.superliga.rs/")
    p("SUPERLIGA-HOME", st, url, len(body))
    links = sorted(set(re.findall(r'href="([^"]*(?:klub|club|tim|team)[^"]*)"', body, re.I)))
    p("SUPERLIGA-LINKS", len(links), links[:60])


def c6():
    """Serbian Wikipedia infoboxes for the clubs whose ground is in question."""
    E = ents(["Q2123289", "Q1323373", "Q209619", "Q12760457", "Q1388917", "Q61130291", "Q3063273", "Q2614598"])
    for q, x in E.items():
        s = x.get("sitelinks") or {}
        t = (s.get("srwiki") or {}).get("title")
        if t:
            p("SRINFO", q, t, "|", infobox(t, "sr"))
            tx = plain(t, "sr")
            p("SRTEXT", q, "|", " ## ".join(around(tx, [r"стадион", r"Стадион", r"игра", r"домаћ"], 150, 3))[:1200])
        time.sleep(0.5)
    for t in ["2026–27 Serbian SuperLiga", "2026–27 Serbian First League"]:
        tx = plain(t, "en")
        p("RSART", t, "|", " ## ".join(around(tx, [r"temporar", r"reconstruct", r"renovat", r" Ub\b", r"FSS", r"Kruševac"], 200, 4))[:2000])


for name, fn in [("C1 AT league site", c1), ("C2 AT de text + items", c2), ("C3 RS extremes", c3),
                 ("C4 RS OSM", c4), ("C5 RS league sites", c5), ("C6 RS sr infoboxes", c6)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE RS3 ===")
