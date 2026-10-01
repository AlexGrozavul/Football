"""TEMPORARY probe #2 for the Belgium pass. Removed in the same branch."""
import csv, glob, json, os, re, sys, time, traceback, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc


def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

LANGS = "en|nl|fr|de"


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


def lab(ent, order=("en", "nl", "fr", "de")):
    for l in order:
        v = (ent.get("labels", {}).get(l) or {}).get("value")
        if v: return v
    return None


def labs(ent):
    return {l: v["value"] for l, v in ent.get("labels", {}).items()}


def vals(ent, prop):
    out = []
    for c in ent.get("claims", {}).get(prop, []):
        v = c["mainsnak"].get("datavalue", {}).get("value")
        if v is None: v = c["mainsnak"].get("snaktype")
        elif isinstance(v, dict) and "latitude" in v: v = (round(v["latitude"], 6), round(v["longitude"], 6))
        elif isinstance(v, dict) and "amount" in v: v = v["amount"]
        elif isinstance(v, dict) and "id" in v: v = v["id"]
        elif isinstance(v, dict) and "time" in v: v = v["time"][:11]
        qual = {k: [str(x.get("datavalue", {}).get("value", {}).get("time", x.get("datavalue", {}).get("value", "")))[:11]
                    for x in xs]
                for k, xs in c.get("qualifiers", {}).items() if k in ("P580", "P582", "P585")}
        r = c.get("rank")[:4]
        out.append((v, r, qual) if qual else (v, r))
    return out


def sitelinks(ent):
    s = ent.get("sitelinks") or {}
    return len(s), (s.get("enwiki") or {}).get("title")


def section(name, fn):
    p(f"########## {name}")
    try:
        fn()
    except Exception:
        p("SECTION-FAILED", name, traceback.format_exc()[-800:])


def sparql(q, tag):
    res, err = fc.sparql_with_retry(q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p(tag, "err=", err, "rows=", len(rows))
    return rows


def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None


def qid_for(title, lang="en"):
    args = {"action": "wbgetentities", "sites": f"{lang}wiki", "titles": title, "props": "info", "format": "json",
            "normalize": "1"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), title)
    for k in ((d or {}).get("entities") or {}):
        if k.startswith("Q"): return k
    return None



import html as _html
ROSTER = """Q187528 Q732002 Q509170 Q364698 Q19585 Q190916 Q216032 Q18232 Q618620 Q536651 Q1668203 Q113000 Q916199 Q138248 Q190561 Q196160 Q849544 Q376635
Q2268833 Q1065328 Q1423718 Q18001655 Q650917 Q95183770 Q2456491 Q1347229 Q2313985 Q2308515 Q925973 Q101625593 Q113884742 Q117384089""".split()
EXTRA = "Q1053917 Q291937 Q115476719 Q20979061 Q370206 Q2195773 Q221940".split()


def wikitext(title, lang="en", section="0"):
    args = {"action": "parse", "page": title, "prop": "wikitext", "format": "json",
            "formatversion": "2", "redirects": "1"}
    if section is not None: args["section"] = section
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    return (d or {}).get("parse", {}).get("wikitext", "")


def infobox(title, lang="en", keys=r"dissolved|league|season|position|ground|capacity|coordinates|current|fullname|founded|stadium|opened|location|home|tenants|competitie|opgeheven|stadion|opgericht|fusie|merger|defunct|ceased|last|clubname|naam|bijnaam|capaciteit|championnat|stade|fondation|disparition|division|divisie|reeks"):
    wt = wikitext(title, lang)
    keep = [l.strip() for l in wt.splitlines() if re.match(r"\s*\|\s*(%s)" % keys, l, re.I)]
    return " || ".join(keep)[:1300] if keep else ("(no infobox lines)" if wt else "(no article)")


def intro(title, lang="en", n=900):
    args = {"action": "query", "prop": "extracts", "exintro": "1", "explaintext": "1", "titles": title,
            "redirects": "1", "format": "json", "formatversion": "2"}
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    pages = (d or {}).get("query", {}).get("pages", [])
    return re.sub(r"\s+", " ", (pages[0].get("extract") if pages else "") or "")[:n]


def a_items():
    ids = ["Q233199", "Q24036298", "Q420970", "Q2441983", "Q98406549", "Q117384089", "Q101625593", "Q113884742",
           "Q115476719", "Q1668203", "Q2313985", "Q95183770", "Q18001655"]
    ids.append(qid_for("RSCA Futures") or "")
    p("RSCA Futures ->", ids[-1])
    E = ents(ids, props="claims|labels|descriptions|sitelinks")
    for q in ids:
        x = E.get(q, {})
        if not x: continue
        p("ITEM", q, labs(x), "| desc", {k: v["value"] for k, v in x.get("descriptions", {}).items() if k in ("en", "nl", "fr")},
          "| sl", sitelinks(x), "| props", sorted(x.get("claims", {}).keys())[:40])
        for pr in ("P31", "P17", "P118", "P571", "P576", "P115", "P625", "P831", "P361", "P1365", "P1366", "P2094", "P3983", "P155", "P156"):
            if pr in x.get("claims", {}): p("    ", q, pr, vals(x, pr)[:8])


def b_pages():
    for t, lang in [("K.S.V. Roeselare", "en"), ("KSV Roeselare", "nl"), ("Royale Union Tubize-Braine", "en"), ("AFC Tubize", "nl"),
                    ("SL16 FC", "en"), ("RWDM Brussels", "en"), ("FCV Dender EH", "en"), ("Lommel SK", "en"),
                    ("Club NXT", "en"), ("RSCA Futures", "en"), ("Jong Genk", "nl"), ("Jong KAA Gent", "nl"),
                    ("RAAL La Louvière", "en"), ("RFC Seraing (1922)", "en"), ("Francs Borains", "en"),
                    ("KSC Lokeren (2025)", "en"), ("Sporting Hasselt", "en"), ("RFC Liège", "en"), ("Lierse SK (2018)", "en"),
                    ("Patro Eisden Maasmechelen", "en"), ("Royal Excelsior Virton", "en"), ("K Beerschot VA", "en"),
                    ("KAS Eupen", "en"), ("Royale Union Saint-Gilloise", "en"), ("KVC Westerlo", "en"),
                    ("KV Oostende", "en"), ("Sportkring Beveren", "en")]:
        p("PAGE", lang, t, "| INFOBOX", infobox(t, lang))
        p("   INTRO", intro(t, lang))
        time.sleep(1)


def c_tables():
    for art in ["2026–27 Challenger Pro League", "2026–27 Belgian Pro League"]:
        page, real, err = cr.fetch_article(art)
        p("TABLES", art, err)
        if not page: continue
        for i, tb in enumerate(re.findall(r'<table class="wikitable[^"]*".*?</table>', page, re.S)):
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S)
            head = [cr.text_of(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", rows[0], re.S)] if rows else []
            p(" TABLE", i, "head", head[:10], "rows", len(rows))
            if i > 3: continue
            for tr in rows[1:30]:
                cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)
                txt = [cr.text_of(c) for c in cells]
                links = [_html.unescape(urllib.parse.unquote(m)).replace("_", " ") for m in re.findall(r'href="/wiki/([^"#?]+)"', tr)]
                p("   ROW", " | ".join(txt)[:220], "|| links", links[:6])
        time.sleep(2)


def d_grounds():
    E = ents(ROSTER + EXTRA)
    gs = {}
    for q in ROSTER + EXTRA:
        x = E.get(q, {})
        for v in vals(x, "P115"):
            gs.setdefault(v[0], []).append(q)
    G = ents(list(gs))
    for g, qs in gs.items():
        x = G.get(g, {})
        p("GROUND", g, lab(x), "| for", qs, "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083"),
          "| P131", vals(x, "P131")[:2], "| P576", vals(x, "P576"), "| P466", [v[0] for v in vals(x, "P466")][:6], "| sl", sitelinks(x))


def e_extras():
    E = ents(EXTRA)
    for q in EXTRA:
        x = E.get(q, {})
        p("EXTRA", q, labs(x), "| P118", vals(x, "P118"), "| P576", vals(x, "P576"), "| P115", vals(x, "P115"),
          "| P1366", vals(x, "P1366"), "| P156", vals(x, "P156"), "| sl", sitelinks(x))


for name, fn in [("a items", a_items), ("c tables", c_tables), ("d grounds", d_grounds), ("e extras", e_extras),
                 ("b pages", b_pages)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE BE2 ===")
