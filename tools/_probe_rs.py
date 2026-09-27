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
SL_TEAMS = ["crvena-zvezda", "cukaricki", "imt", "macva", "mladost", "novi-pazar", "ofk-beograd", "partizan",
            "radnicki-1923", "radnicki-nis", "radnik", "vojvodina", "zeleznicar", "zemun"]


def d1():
    """The SuperLiga's own team pages (robots.txt: /tim/ allowed)."""
    for slug in SL_TEAMS:
        st, body, url = fetch(f"https://www.superliga.rs/tim/{slug}/")
        t = text(body)
        hits = around(t, [r"Stadion", r"Kapacitet", r"Стадион", r"Капацитет", r"Adresa"], 110, 3)
        p("SLTEAM", slug, st, "|", " ## ".join(hits)[:800])
        time.sleep(2)


def d2():
    """The First League's own site: sitemap first (robots.txt: all allowed but wp-admin)."""
    st, body, url = fetch("https://www.prvaliga.rs/sitemap_index.xml")
    subs = re.findall(r"<loc>([^<]+)</loc>", body)
    p("PL-SITEMAPS", st, subs[:20])
    urls = []
    for sub in subs[:20]:
        st2, b2, _ = fetch(sub)
        urls += re.findall(r"<loc>([^<]+)</loc>", b2)
        time.sleep(1)
    teamish = sorted({u for u in urls if re.search(r"/(tim|klub|klubovi|team|ekip)", u, re.I)})
    p("PL-TEAMURLS", len(teamish), teamish[:80])
    for u in teamish[:24]:
        st3, b3, _ = fetch(u)
        t = text(b3)
        hits = around(t, [r"Stadion", r"Kapacitet", r"Стадион", r"Капацитет"], 110, 2)
        if hits:
            p("PLTEAM", u, st3, "|", " ## ".join(hits)[:700])
        time.sleep(1.5)


def d3():
    """Wikidata items for the Serbian grounds, by their Serbian Wikipedia titles."""
    for t in ["Градски стадион у Вршцу", "Стадион Драган Џајић", "СРЦ Младост Панчево", "Стадион крај Пирита",
              "Градски стадион у Земуну", "Омладински стадион", "Фудбалски стадион Мачва", "Спортски центар ФСС"]:
        q, x = by_title("srwiki", t)
        p("SRG", t, "->", q, "|", lab(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083")[:3],
          "| P466", [v[0] for v in vals(x, "P466")][:5], "| P131", [v[0] for v in vals(x, "P131")][:1])
        time.sleep(0.5)
    for t in ["Стадион Драган Џајић", "СРЦ Младост Панчево", "Градски стадион у Вршцу"]:
        p("SRGINFO", t, "|", infobox(t, "sr"))


def d4():
    """OpenStreetMap, one small request per town, with a retry."""
    for label, lat, lon in [("Ub", 44.456, 20.074), ("Pancevo", 44.871, 20.640), ("Vrsac", 45.117, 21.303)]:
        q = f"""[out:json][timeout:60];
        nwr["leisure"="stadium"](around:4000,{lat},{lon});
        out center tags;"""
        for attempt in range(3):
            body = urllib.parse.urlencode({"data": q}).encode()
            req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=body,
                                         headers={"User-Agent": cr.USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    d = json.loads(r.read().decode())
                break
            except Exception as ex:
                p("OVERPASS-RETRY", label, ex)
                d = None
                time.sleep(30)
        for el in (d or {}).get("elements", []):
            c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
            t = el.get("tags", {})
            p("RSOSM3", label, f"{el['type']}/{el['id']}", round(c.get("lat") or 0, 6), round(c.get("lon") or 0, 6), "|",
              {k: t[k] for k in ("name", "name:sr-Latn", "sport", "operator", "capacity", "wikidata") if k in t})
        time.sleep(5)


for name, fn in [("D1 SuperLiga site", d1), ("D2 First League site", d2), ("D3 RS grounds by srwiki", d3),
                 ("D4 RS OSM towns", d4)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE RS4 ===")
