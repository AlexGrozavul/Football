"""TEMPORARY probe #1 for the Serbia pass and the Austria/roster follow-ups.
Removed in the same branch."""
import csv, json, re, sys, time, traceback, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc


def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

LANGS = "en|de|sr|sr-el|sh|hr"


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


def lab(ent, order=("en", "de", "sr-el", "sh", "sr")):
    for l in order:
        v = (ent.get("labels", {}).get(l) or {}).get("value")
        if v: return v
    return None


def labs(ent):
    return {l: (ent.get("labels", {}).get(l) or {}).get("value") for l in ("en", "sr", "sr-el", "sh")
            if (ent.get("labels", {}).get(l) or {}).get("value")}


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
    return len(s), (s.get("enwiki") or {}).get("title"), (s.get("dewiki") or {}).get("title"), (s.get("srwiki") or {}).get("title")


def wikitext(title, lang="en", section="0"):
    args = {"action": "parse", "page": title, "prop": "wikitext", "format": "json",
            "formatversion": "2", "redirects": "1"}
    if section is not None: args["section"] = section
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    return (d or {}).get("parse", {}).get("wikitext", "")


def infobox(title, lang="en", keys=r"dissolved|league|season|position|ground|capacity|coordinates|coord|current|fullname|founded|tenants|stadion|plätze|aufgelöst|gegründet|liga|verein|auflösung|zuschauer|kapazität|name|opened|location|home|stadium|ort|heimspielstätte|nachfolger|vorgänger|fusion"):
    wt = wikitext(title, lang)
    keep = [l.strip() for l in wt.splitlines() if re.match(r"\s*\|\s*(%s)\b" % keys, l, re.I)]
    return " || ".join(keep)[:900] if keep else ("(no infobox lines)" if wt else "(no article)")


def intro(title, lang="en", n=700):
    args = {"action": "query", "prop": "extracts", "exintro": "1", "explaintext": "1", "titles": title,
            "redirects": "1", "format": "json", "formatversion": "2"}
    d, e = cr.get_json_with_retry(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(args), title)
    pages = (d or {}).get("query", {}).get("pages", [])
    return re.sub(r"\s+", " ", (pages[0].get("extract") if pages else "") or "")[:n]


def section(name, fn):
    p(f"########## {name}")
    try:
        fn()
    except Exception:
        p("SECTION-FAILED", name, traceback.format_exc()[-800:])


# ======================================================================
# 1. Serbia's leagues
RS_LEAGUES = {}


def s1():
    Q = """SELECT ?l ?lLabel ?level ?en ?type WHERE {
      ?l wdt:P17 wd:Q403 ; wdt:P641 wd:Q2736 .
      OPTIONAL { ?l wdt:P3983 ?level }
      OPTIONAL { ?l wdt:P31 ?type }
      OPTIONAL { ?en schema:about ?l ; schema:isPartOf <https://en.wikipedia.org/> }
      ?l rdfs:label ?lab .
      FILTER(CONTAINS(LCASE(?lab), "superli") || CONTAINS(LCASE(?lab), "first league")
             || CONTAINS(LCASE(?lab), "prva liga") || CONTAINS(LCASE(?lab), "суперлига")
             || CONTAINS(LCASE(?lab), "прва лига") || CONTAINS(LCASE(?lab), "second league")
             || CONTAINS(LCASE(?lab), "srpska liga"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,sr" }
    }"""
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("RS-LEAGUES", err, len(rows))
    seen = {}
    for r in rows:
        k = q_(fc.cell(r, "l"))
        s = seen.setdefault(k, [fc.cell(r, "lLabel"), set(), fc.cell(r, "en"), set()])
        if fc.cell(r, "level"): s[1].add(fc.cell(r, "level"))
        if fc.cell(r, "type"): s[3].add(q_(fc.cell(r, "type")))
    for k, (lb, lev, en, ty) in sorted(seen.items(), key=lambda kv: str(sorted(kv[1][1]))):
        p("  ", k, "|", lb, "| level", sorted(lev), "|", en, "|", sorted(ty))
    for k, v in seen.items():
        en = (v[2] or "")
        if en.endswith("/Serbian_SuperLiga"): RS_LEAGUES[k] = 1
        if en.endswith("/Serbian_First_League"): RS_LEAGUES[k] = 2
    p("RS-TOP", RS_LEAGUES)
    e = ents(list(RS_LEAGUES))
    for q, x in e.items():
        p("LEAGUE", q, labs(x), "| P31", vals(x, "P31"), "| P17", vals(x, "P17"), "| P3983", vals(x, "P3983"),
          "| P3450", vals(x, "P3450")[-3:], "| P2094", vals(x, "P2094"), "| sitelinks", sitelinks(x))


# 2. season articles, raw rows
RS_ROSTER = {}


def s2():
    for art, tier in [("2026–27 Serbian SuperLiga", 1), ("2026–27 Serbian First League", 2)]:
        page, real, err = cr.fetch_article(art)
        if err:
            p("ARTICLE", art, "ERROR", err); continue
        tables, shape = cr.roster_tables(page)
        p("ARTICLE", art, "->", real, "|", shape, "| tables", len(tables))
        names, caps = [], {}
        for t, h in tables:
            p("  HEAD", h[:8])
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)[1:]:
                cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)
                links = re.findall(r'<a[^>]+href="/wiki/([^"#:]+)"', tr)
                p("  ROW", tier, [cr.text_of(c)[:40] for c in cells][:6], "| links",
                  [urllib.parse.unquote(l) for l in links][:3])
            left = []
            for title, cap in cr.rows_of(t, h, left):
                if title not in names: names.append(title); caps[title] = cap
            for x in left: p("  LEFT-OUT", x)
        got, fails = cr.qids_for_titles(names)
        p("RESOLVED", art, len(got), "of", len(names), "| failures", fails)
        for n in names:
            p("   ", got.get(n, "-"), "|", n, "|", caps.get(n))
            if got.get(n): RS_ROSTER.setdefault(got[n], []).append((tier, n, caps.get(n)))
        plain = cr.text_of(page)
        for kw in ("relegat", "promot", "withdr", "exclu", "dissol", "license", "licence", "merg", "renam"):
            hits = [plain[max(0, m.start() - 160):m.start() + 160] for m in re.finditer(kw, plain, re.I)][:6]
            for h in hits: p("  CHANGE", tier, kw, "...", h)
        time.sleep(2)


# 3. StadiumDB slug and page
def s3():
    for slug in ["srb", "ser", "serbia", "rs", "scg"]:
        try:
            req = urllib.request.Request(f"https://stadiumdb.com/stadiums/{slug}", headers={"User-Agent": cr.USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode("utf-8", "replace"); st = r.status
        except urllib.error.HTTPError as ex:
            st, body = ex.code, ""
        except Exception as ex:
            st, body = str(ex), ""
        p("STADIUMDB", slug, st, len(body), body.count("<tr"))
        if st == 200 and body.count("<tr") > 3:
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S)[:80]:
                p("   SDB", [cr.text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)])
            break
        time.sleep(4)


# 4. every item carrying a Serbian tier 1/2 tag at any rank
def s4():
    if not RS_LEAGUES:
        p("NO RS LEAGUES"); return
    Q = """SELECT ?club ?league ?rank WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
    }""" % " ".join("wd:" + l for l in RS_LEAGUES)
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("TAGGED", err, len(rows))
    tags = {}
    for r in rows:
        tags.setdefault(q_(fc.cell(r, "club")), set()).add(
            (RS_LEAGUES.get(q_(fc.cell(r, "league"))), q_(fc.cell(r, "rank")).split("#")[-1][:4]))
    allq = set(tags) | set(RS_ROSTER)
    E = ents(sorted(allq))
    venues = []
    for q in sorted(allq, key=lambda q: lab(E.get(q, {})) or q):
        x = E.get(q, {})
        types = [v[0] for v in vals(x, "P31")]
        if "Q5" in types: continue
        venues += [v[0] for v in vals(x, "P115") if isinstance(v[0], str) and v[0].startswith("Q")]
        p("ITEM", q, "|", labs(x), "| tags", sorted(tags.get(q, []), key=str), "| roster", RS_ROSTER.get(q),
          "| P118", vals(x, "P118")[:8], "| P576", vals(x, "P576") or "-", "| P17", [v[0] for v in vals(x, "P17")],
          "| P115", vals(x, "P115"), "| P625", vals(x, "P625"), "| P31", types[:4], "| sl", sitelinks(x))
    G = ents(venues)
    for q, x in G.items():
        p("GROUND", q, "|", labs(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083")[:4],
          "| P131", [v[0] for v in vals(x, "P131")][:2], "| sl", sitelinks(x)[:2])


# ======================================================================
# 5. Austria: the seven clubs, Tivoli, Liefering, old Vienna clubs
AT7 = ["Q2206406", "Q699686", "Q696474", "Q297832", "Q63168427", "Q98228613", "Q98217947"]
REL = ["P361", "P527", "P749", "P355", "P127", "P1830", "P1365", "P1366", "P155", "P156", "P710", "P466"]


def s5():
    E = ents(AT7 + ["Q60967849", "Q131215", "Q124007617", "Q131209"])
    venues = []
    for q in AT7 + ["Q60967849"]:
        x = E.get(q, {})
        venues += [v[0] for v in vals(x, "P115") if isinstance(v[0], str) and v[0].startswith("Q")]
        p("ATCLUB", q, "|", lab(x), "| P118", vals(x, "P118")[:6], "| P115", vals(x, "P115"),
          "| P625", vals(x, "P625"), "| P576", vals(x, "P576") or "-", "| P17", [v[0] for v in vals(x, "P17")],
          "| P31", [v[0] for v in vals(x, "P31")][:4], "| rel", {k: vals(x, k) for k in REL if vals(x, k)},
          "| sl", sitelinks(x))
    for q in ("Q131215", "Q124007617", "Q131209"):
        x = E.get(q, {})
        p("PARENT", q, lab(x), "| rel", {k: vals(x, k) for k in REL if vals(x, k)})
    G = ents(venues)
    for q, x in G.items():
        p("ATGROUND", q, "|", lab(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083")[:4],
          "| P466", [v[0] for v in vals(x, "P466")][:6], "| sl", sitelinks(x))


def s6():
    page, real, err = cr.fetch_article("2026–27 Austrian Football Second League")
    if err: p("AT2 ERROR", err); return
    tables, shape = cr.roster_tables(page)
    for t, h in tables:
        p("AT2 HEAD", h[:8])
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)[1:]:
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)
            links = re.findall(r'<a[^>]+href="/wiki/([^"#:]+)"', tr)
            p("  AT2ROW", [cr.text_of(c)[:45] for c in cells][:6], "| links", [urllib.parse.unquote(l) for l in links][:4])
    plain = cr.text_of(page)
    for kw in ("Amstetten", "Bregenz", "Floridsdorf", "Voitsberg", "Hertha", "Rapid II", "Sturm Graz II", "Liefering"):
        hits = [plain[max(0, m.start() - 140):m.start() + 180] for m in re.finditer(kw, plain)][:3]
        for h in hits: p("  AT2MENTION", kw, "...", h)


def s7():
    for t in ["SKU Amstetten", "SC Schwarz-Weiß Bregenz", "Floridsdorfer AC", "ASK Voitsberg", "WSC Hertha Wels",
              "SK Rapid Wien II", "SK Sturm Graz II", "FC Liefering", "FC Wacker Innsbruck", "WSG Tirol",
              "Tivoli Stadion Tirol", "Untersberg-Arena", "Red Bull Arena (Salzburg)"]:
        for lang in ("en", "de"):
            p("INFOBOX", lang, t, "|", infobox(t, lang))
            time.sleep(0.5)
    for t in ["FC Juniors OÖ", "SKU Amstetten", "SC Schwarz-Weiß Bregenz", "Floridsdorfer AC", "ASK Voitsberg",
              "WSC Hertha Wels", "SK Sturm Graz II", "SK Rapid Wien II"]:
        p("DEINTRO", t, "|", intro(t, "de", 500))


def s8():
    # StadiumDB Austria, every row
    req = urllib.request.Request("https://stadiumdb.com/stadiums/aut", headers={"User-Agent": cr.USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode("utf-8", "replace")
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S):
        p("   SDB-AT", [cr.text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)])


def s9():
    # Tivoli, Liefering grounds, BFC Dynamo's ground
    E = ents(["Q204484", "Q1387293", "Q261813", "Q686659", "Q551837", "Q159930", "Q656063"])
    for q, x in E.items():
        p("ITEM9", q, lab(x), "| P1083", vals(x, "P1083"), "| P625", vals(x, "P625"), "| P115", vals(x, "P115"),
          "| P466", [v[0] for v in vals(x, "P466")][:8], "| sl", sitelinks(x))
    # the Untersberg-Arena item, by its dewiki title
    args = {"action": "wbgetentities", "sites": "dewiki", "titles": "Untersberg-Arena", "props": "claims|labels|sitelinks",
            "languages": "en|de", "format": "json"}
    d, e = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(args), "ua")
    for q, x in (d or {}).get("entities", {}).items():
        p("UNTERSBERG", q, lab(x), "| P1083", vals(x, "P1083"), "| P625", vals(x, "P625"),
          "| P466", vals(x, "P466"), "| sl", sitelinks(x))
    for t in ["Berliner FC Dynamo", "Sportforum Hohenschönhausen"]:
        for lang in ("en", "de"):
            p("INFOBOX", lang, t, "|", infobox(t, lang))


def s10():
    # the five old Vienna clubs
    V = ["Q461162", "Q683981", "Q684205", "Q459929", "Q430940"]
    E = ents(V, props="claims|labels|sitelinks")
    for q in V:
        x = E.get(q, {})
        p("VIENNA", q, lab(x), "| P118", vals(x, "P118"), "| P576", vals(x, "P576") or "-", "| P571", vals(x, "P571"),
          "| P31", [v[0] for v in vals(x, "P31")], "| rel", {k: vals(x, k) for k in REL if vals(x, k)},
          "| P115", vals(x, "P115"), "| sl", sitelinks(x))
        s = x.get("sitelinks") or {}
        for lang in ("en", "de"):
            t = (s.get(f"{lang}wiki") or {}).get("title")
            if t:
                p("   ", lang, t, "| INFOBOX", infobox(t, lang))
                p("   ", lang, t, "| INTRO", intro(t, lang, 900))
        time.sleep(1)


def s11():
    # shape 5: do the club item and the men's team item point at each other?
    pairs = [("Q15755", "Q97905916"), ("Q141882", "Q97927365"), ("Q571553", "Q97927380")]
    E = ents([q for pr in pairs for q in pr])
    for a, b in pairs:
        for q, other in ((a, b), (b, a)):
            x = E.get(q, {})
            hits = {}
            for prop, sts in (x.get("claims") or {}).items():
                for v in vals(x, prop):
                    if v[0] == other: hits.setdefault(prop, []).append(v)
            p("SHAPE5", q, lab(x), "-> mentions", other, ":", hits or "NOTHING",
              "| P31", [v[0] for v in vals(x, "P31")], "| rel", {k: vals(x, k) for k in REL if vals(x, k)})


for name, fn in [("1 RS leagues", s1), ("2 RS articles", s2), ("3 RS StadiumDB", s3), ("4 RS items", s4),
                 ("5 AT seven", s5), ("6 AT 2.Liga rows", s6), ("7 AT infoboxes", s7), ("8 SDB AT", s8),
                 ("9 Tivoli/Liefering/BFC", s9), ("10 Vienna", s10), ("11 shape5", s11)]:
    section(name, fn)
    time.sleep(2)
p("RS-TOP again", RS_LEAGUES)
p("=== END OF PROBE RS1 ===")
