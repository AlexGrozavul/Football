"""TEMPORARY probe #3 for the Belgium pass. Removed in the same branch."""
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
import crosscheck_capacity as cc


def wikitext(title, lang="en", section="0"):
    args = {"action": "parse", "page": title, "prop": "wikitext", "format": "json",
            "formatversion": "2", "redirects": "1"}
    if section is not None: args["section"] = section
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    return (d or {}).get("parse", {}).get("wikitext", "")


def infobox(title, lang="en", keys=r"capacity|capaciteit|capacité|opened|opening|name|naam|nom|tenants|bespeler|club|clubs|coordinates|coord|location|locatie|ville|adresse|address|former|vroeger|surface|owner|eigenaar|ground|stadion|stade|league|competitie|championnat|opgeheven|dissolved"):
    wt = wikitext(title, lang)
    keep = [re.sub(r"<ref.*?(</ref>|/>)", "", l.strip()) for l in wt.splitlines() if re.match(r"\s*\|\s*(%s)" % keys, l, re.I)]
    return " || ".join(keep)[:1100] if keep else ("(no infobox lines)" if wt else "(no article)")


def intro(title, lang="en", n=900):
    args = {"action": "query", "prop": "extracts", "exintro": "1", "explaintext": "1", "titles": title,
            "redirects": "1", "format": "json", "formatversion": "2"}
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    pages = (d or {}).get("query", {}).get("pages", [])
    return re.sub(r"\s+", " ", (pages[0].get("extract") if pages else "") or "")[:n]


def search(text, lang="en"):
    args = {"action": "wbsearchentities", "search": text, "language": lang, "type": "item", "limit": "7", "format": "json"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), text)
    return [(x["id"], x.get("label"), x.get("description")) for x in (d or {}).get("search", [])]


GROUNDS_EN = ["Planet Group Arena", "Bosuilstadion", "Easi Arena", "Soevereinstadion", "Stade du Pairay", "Daknamstadion",
              "Herman Vanderpoortenstadion", "Stade Yvan Georges", "Kehrwegstadion", "Gemeentelijk Sportparkstadion",
              "Schiervelde Stadion", "Elindus Arena", "Freethiel Stadion", "Stayen", "Den Dreef", "Achter de Kazerne",
              "Dender Football Complex", "Joseph Marien Stadium", "Constant Vanden Stock Stadium", "Stade du Pays de Charleroi",
              "Cegeka Arena", "Stade Maurice Dufrasne", "Het Kuipje", "Jan Breydel Stadium", "Guldensporen Stadion",
              "Olympisch Stadion (Antwerp)", "Stade Leburton"]


def a_grounds():
    got, fails = cr.qids_for_titles(GROUNDS_EN)
    p("GROUND-TITLES", len(got), "of", len(GROUNDS_EN), "fails", fails)
    E = ents(list(got.values()))
    for t in GROUNDS_EN:
        q = got.get(t)
        x = E.get(q, {}) if q else {}
        p("GROUND", t, "->", q, "|", lab(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083"),
          "| P466", [v[0] for v in vals(x, "P466")][:6], "| P576", vals(x, "P576"), "| P131", [v[0] for v in vals(x, "P131")][:2])
        p("   INFOBOX", infobox(t))
        time.sleep(0.5)


def b_search():
    for t in ["Stade Robert Urbain", "Stade de Rocourt", "Stade Vélodrome de Rocourt", "Sportstadion Hasselt",
              "Stedelijk Sportstadion Hasselt", "De Leunen", "Leunenstadion", "Stade du Pairay", "Soevereinstadion",
              "Easi Arena", "Stade du Tivoli", "Burgemeester Van de Wiele", "Jos Van Hoeylandt", "Bosuil", "Planet Group Arena",
              "Gemeentelijk Sportparkstadion", "Patro Eisden"]:
        for lang in ("en", "nl", "fr"):
            r = search(t, lang)
            if r: p("SEARCH", lang, repr(t), r)
            time.sleep(0.3)
    hits = set()
    for line in []: pass


def c_items():
    ids = ["Q1146219", "Q2271005", "Q2117498", "Q3497440", "Q3497457"]
    # filled by search output next time; print whatever is here
    E = ents(ids)
    for q in ids:
        x = E.get(q, {})
        p("ITEM", q, labs(x), "| P31", [v[0] for v in vals(x, "P31")][:3], "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083"),
          "| P466", [v[0] for v in vals(x, "P466")][:6], "| P131", [v[0] for v in vals(x, "P131")][:2])


def d_pages():
    for t, lang in [("SL16 FC", "fr"), ("SL16 FC", "nl"), ("Standard Luik", "nl"), ("Club NXT", "nl"), ("RSCA Futures", "nl"),
                    ("Jong Genk", "nl"), ("Lommel SK", "nl"), ("RAAL La Louvière", "fr"), ("RFC Liège", "fr"),
                    ("Royal Francs Borains", "fr"), ("Francs Borains", "nl"), ("Sporting Hasselt", "nl"), ("KSK Hasselt", "nl"),
                    ("Stade de Rocourt", "fr"), ("Stade Robert Urbain", "fr"), ("Stade du Pairay", "fr"), ("Leunenstadion", "nl"),
                    ("Soevereinstadion", "nl"), ("Stade du Tivoli", "fr"), ("Easi Arena", "fr"), ("Sportpark Hasselt", "nl"),
                    ("Royale Union Tubize-Braine", "fr"), ("KV Mechelen", "en"), ("Bosuilstadion", "nl"), ("Planet Group Arena", "nl"),
                    ("Stade Joseph Marien", "fr"), ("FCV Dender EH", "nl"), ("Dender Football Complex", "en")]:
        p("PAGE", lang, t, "| INFOBOX", infobox(t, lang))
        p("   INTRO", intro(t, lang, 700))
        time.sleep(0.7)


def e_prev_season():
    for art in ["2025–26 Challenger Pro League", "2025–26 Belgian Pro League"]:
        page, real, err = cr.fetch_article(art)
        p("PREV", art, real, err)
        if not page: continue
        plain = cr.text_of(page)
        i = plain.find("Team changes")
        p("  TEAMCHANGES", plain[i:i + 1500] if i >= 0 else "(none)")
        for kw in ("SL16", "Standard", "U23", "withdr"):
            for m in list(re.finditer(kw, plain))[:4]:
                p("  KW", kw, "...", plain[max(0, m.start() - 200):m.start() + 200])
        time.sleep(2)


def f_osm():
    clubs = json.load(open("data/clubs/BE.json"))["clubs"]
    payload, err = cc.overpass_with_retry("BE")
    p("OVERPASS", err, len((payload or {}).get("elements", [])))
    st = cc.stadium_points(payload or {})
    p("OSM stadiums", len(st), "with capacity", sum(1 for s in st if s.get("capacity")))
    for c in sorted(clubs, key=lambda c: c["name"]):
        best, bd = None, None
        for s in st:
            d = cc.metres(c["lat"], c["lon"], s["lat"], s["lon"])
            if bd is None or d < bd: best, bd = s, d
        p("OSM", c["name"], "| ours", c["venue"], c["capacity"], "| nearest", (best or {}).get("name"), "| osm cap",
          (best or {}).get("capacity"), "| metres", round(bd) if bd is not None else None)
    rx = re.compile(r"urbain|rocourt|pairay|sportstadion|soeverein|easi|tivoli|leunen|sportpark|bosuil|planet|ghelamco|"
                    r"daknam|vanderpoorten|kehrweg|yvan|schiervelde|deinze|wiele|machtens|marien|mambourg|olympisch", re.I)
    for s in st:
        if rx.search(s.get("name") or ""):
            p("OSM-NAMED", s.get("name"), s["lat"], s["lon"], "cap", s.get("capacity"), s.get("tag"))


for name, fn in [("a grounds", a_grounds), ("b search", b_search), ("e prev season", e_prev_season),
                 ("d pages", d_pages), ("f osm", f_osm)]:
    section(name, fn)
    time.sleep(2)
p("=== END OF PROBE BE3 ===")
