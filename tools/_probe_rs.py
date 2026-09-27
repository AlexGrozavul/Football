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
def e1():
    """Where the home games of 2026-27 were actually played: each league site lists a venue per match."""
    for base, slug, team in [("https://www.superliga.rs", "zemun", "ZEMUN"), ("https://www.superliga.rs", "ofk-beograd", "OFK BEOGRAD"),
                             ("https://www.superliga.rs", "imt", "IMT"), ("https://www.superliga.rs", "zeleznicar", "ŽELEZNIČAR"),
                             ("https://www.superliga.rs", "macva", "MAČVA"),
                             ("https://www.prvaliga.rs", "bor-1919", "BOR 1919"), ("https://www.prvaliga.rs", "jedinstvo", "JEDINSTVO"),
                             ("https://www.prvaliga.rs", "ofk-vrsac", "OFK VRŠAC"), ("https://www.prvaliga.rs", "rfk-graficar", "RFK GRAFIČAR")]:
        st, body, url = fetch(f"{base}/tim/{slug}/")
        t = text(body)
        hits = [t[max(0, m.start() - 170):m.end() + 40] for m in re.finditer(re.escape(team), t)]
        p("VENUES", slug, st, len(hits))
        for h in hits[:10]:
            p("    ", h)
        links = sorted(set(re.findall(r'href="([^"]*(?:utakmic|match|raspored|kolo)[^"]*)"', body, re.I)))[:15]
        p("   LINKS", links)
        time.sleep(2)
    for base in ["https://www.superliga.rs", "https://www.prvaliga.rs"]:
        for path in ["/raspored/", "/rezultati/", "/raspored-i-rezultati/"]:
            st, body, url = fetch(base + path)
            t = text(body)
            p("SCHED", base + path, st, len(t))
            for team in ("ZEMUN", "OFK BEOGRAD", "IMT", "BOR 1919", "Zemun", "OFK Beograd", "Bor 1919"):
                for m in list(re.finditer(re.escape(team), t))[:6]:
                    p("   ", team, "...", t[max(0, m.start() - 150):m.end() + 40])
            time.sleep(2)


def e2():
    """OpenStreetMap around the Ub ground and SRC Mladost in Pancevo, any sports object."""
    for label, lat, lon, r in [("Ub", 44.456, 20.074, 2500), ("SRC Mladost", 44.879086, 20.662633, 600)]:
        q = f"""[out:json][timeout:60];
        nwr["leisure"~"stadium|pitch|sports_centre"](around:{r},{lat},{lon});
        out center tags;"""
        d = None
        for attempt in range(3):
            body = urllib.parse.urlencode({"data": q}).encode()
            req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=body,
                                         headers={"User-Agent": cr.USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=90) as rr:
                    d = json.loads(rr.read().decode())
                break
            except Exception as ex:
                p("OVERPASS-RETRY", label, ex)
                time.sleep(30)
        for el in (d or {}).get("elements", []):
            c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
            t = el.get("tags", {})
            if t.get("sport") and not any(k in t.get("sport") for k in ("soccer", "football", "multi", "athletics")):
                continue
            p("RSOSM4", label, f"{el['type']}/{el['id']}", round(c.get("lat") or 0, 6), round(c.get("lon") or 0, 6), "|",
              {k: t[k] for k in ("name", "name:sr-Latn", "leisure", "sport", "operator", "capacity", "wikidata", "surface") if k in t})
        time.sleep(5)


for name, fn in [("E1 match venues", e1), ("E2 OSM Ub Pancevo", e2)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE RS5 ===")
