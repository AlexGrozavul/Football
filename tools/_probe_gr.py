"""TEMPORARY probe #1 for the Greece pass and the league-tag end-date (P582)
measurement. Removed in the same branch."""
import csv, glob, json, os, re, sys, time, traceback, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "tools")
import check_rosters as cr
import fetch_clubs as fc

TODAY = "2026-09-27"


def p(*a): print(" ".join(str(x) for x in a), flush=True)
def q_(uri): return (uri or "").rsplit("/", 1)[-1]

LANGS = "en|el|de"


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


def lab(ent, order=("en", "el", "de")):
    for l in order:
        v = (ent.get("labels", {}).get(l) or {}).get("value")
        if v: return v
    return None


def labs(ent):
    return {l: (ent.get("labels", {}).get(l) or {}).get("value") for l in ("en", "el")
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
    return len(s), (s.get("enwiki") or {}).get("title"), (s.get("elwiki") or {}).get("title")


def section(name, fn):
    p(f"########## {name}")
    try:
        fn()
    except Exception:
        p("SECTION-FAILED", name, traceback.format_exc()[-800:])


# ======================================================================
GR_LEAGUES = {}


def s1():
    Q = """SELECT ?l ?lLabel ?level ?en ?type WHERE {
      ?l wdt:P17 wd:Q41 ; wdt:P641 wd:Q2736 .
      OPTIONAL { ?l wdt:P3983 ?level }
      OPTIONAL { ?l wdt:P31 ?type }
      OPTIONAL { ?en schema:about ?l ; schema:isPartOf <https://en.wikipedia.org/> }
      ?l rdfs:label ?lab .
      FILTER(CONTAINS(LCASE(?lab), "super league") || CONTAINS(LCASE(?lab), "σούπερ λίγκ")
             || CONTAINS(LCASE(?lab), "football league") || CONTAINS(LCASE(?lab), "gamma ethniki")
             || CONTAINS(LCASE(?lab), "beta ethniki") || CONTAINS(LCASE(?lab), "alpha ethniki")
             || CONTAINS(LCASE(?lab), "εθνική"))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,el" }
    }"""
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("GR-LEAGUES", err, len(rows))
    seen = {}
    for r in rows:
        k = q_(fc.cell(r, "l"))
        s = seen.setdefault(k, [fc.cell(r, "lLabel"), set(), fc.cell(r, "en"), set()])
        if fc.cell(r, "level"): s[1].add(fc.cell(r, "level"))
        if fc.cell(r, "type"): s[3].add(q_(fc.cell(r, "type")))
    for k, (lb, lev, en, ty) in sorted(seen.items(), key=lambda kv: str(sorted(kv[1][1]))):
        p("  ", k, "|", lb, "| level", sorted(lev), "|", en, "|", sorted(ty))
    for k, v in seen.items():
        en = urllib.parse.unquote(v[2] or "")
        if en.endswith("/Super_League_Greece"): GR_LEAGUES[k] = 1
        if en.endswith("/Super_League_Greece_2"): GR_LEAGUES[k] = 2
    p("GR-TOP", GR_LEAGUES)
    e = ents(list(GR_LEAGUES))
    for q, x in e.items():
        p("LEAGUE", q, labs(x), "| P31", vals(x, "P31"), "| P17", vals(x, "P17"), "| P3983", vals(x, "P3983"),
          "| P3450", vals(x, "P3450")[-3:], "| P1132", vals(x, "P1132"), "| sitelinks", sitelinks(x))


GR_ROSTER = {}


def s2():
    for art, tier in [("2026–27 Super League Greece", 1), ("2026–27 Super League Greece 2", 2)]:
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
            if got.get(n): GR_ROSTER.setdefault(got[n], []).append((tier, n, caps.get(n)))
        plain = cr.text_of(page)
        for kw in ("relegat", "promot", "withdr", "exclu", "dissol", "licen", "merg", "renam", "group", "deduct"):
            hits = [plain[max(0, m.start() - 160):m.start() + 160] for m in re.finditer(kw, plain, re.I)][:6]
            for h in hits: p("  CHANGE", tier, kw, "...", h)
        time.sleep(2)


def s3():
    for slug in ["gre", "grc", "greece", "gr", "hel"]:
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


def s4():
    if not GR_LEAGUES:
        p("NO GR LEAGUES"); return
    Q = """SELECT ?club ?league ?rank WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
    }""" % " ".join("wd:" + l for l in GR_LEAGUES)
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("TAGGED", err, len(rows))
    tags = {}
    for r in rows:
        tags.setdefault(q_(fc.cell(r, "club")), set()).add(
            (GR_LEAGUES.get(q_(fc.cell(r, "league"))), q_(fc.cell(r, "rank")).split("#")[-1][:4]))
    allq = set(tags) | set(GR_ROSTER)
    E = ents(sorted(allq))
    venues = []
    for q in sorted(allq, key=lambda q: lab(E.get(q, {})) or q):
        x = E.get(q, {})
        types = [v[0] for v in vals(x, "P31")]
        if "Q5" in types: continue
        venues += [v[0] for v in vals(x, "P115") if isinstance(v[0], str) and v[0].startswith("Q")]
        p("ITEM", q, "|", labs(x), "| tags", sorted(tags.get(q, []), key=str), "| roster", GR_ROSTER.get(q),
          "| P118", vals(x, "P118")[:8], "| P576", vals(x, "P576") or "-", "| P17", [v[0] for v in vals(x, "P17")],
          "| P115", vals(x, "P115"), "| P625", vals(x, "P625"), "| P31", types[:4],
          "| P831", vals(x, "P831"), "| P361", vals(x, "P361")[:3], "| sl", sitelinks(x))
    G = ents(venues)
    for q, x in G.items():
        p("GROUND", q, "|", labs(x), "| P625", vals(x, "P625"), "| P1083", vals(x, "P1083")[:4],
          "| P131", [v[0] for v in vals(x, "P131")][:2], "| sl", sitelinks(x)[:2])


# ======================================================================
# 5. the P582 measurement across every mapped country (and Greece's two)
def load_tiers():
    out = {}
    with open("data/league-tiers.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["tier"].strip().isdigit():
                out[r["leagueQid"].strip()] = (int(r["tier"]), r["country"].strip())
    return out


def s5():
    tiers = load_tiers()
    for q, t in GR_LEAGUES.items():
        tiers[q] = (t, "GR")
    Q = """SELECT ?club ?league ?end ?endPrec ?start WHERE {
      VALUES ?league { %s }
      ?club p:P118 ?st . ?st ps:P118 ?league ; a wikibase:BestRank .
      OPTIONAL { ?st pqv:P582 ?ev . ?ev wikibase:timeValue ?end ; wikibase:timePrecision ?endPrec }
      OPTIONAL { ?st pq:P580 ?start }
      FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }
      FILTER NOT EXISTS { ?club wdt:P576 ?d }
    }""" % " ".join("wd:" + l for l in tiers)
    t0 = time.time()
    res, err = fc.sparql_with_retry(Q)
    rows = (res or {}).get("results", {}).get("bindings", [])
    p("P582-QUERY", err, len(rows), "rows in", round(time.time() - t0, 1), "s")
    stm = {}
    for r in rows:
        club, lg = q_(fc.cell(r, "club")), q_(fc.cell(r, "league"))
        end = fc.cell(r, "end"); prec = fc.cell(r, "endPrec")
        stm.setdefault(club, []).append((lg, (end or "")[:10], int(prec) if prec else None,
                                         (fc.cell(r, "start") or "")[:4]))

    def ended(end, prec):
        if not end: return False
        if prec is not None and prec <= 9:  # year precision or coarser
            return end[:4] < TODAY[:4]
        return end < TODAY

    # the map and the hand rows
    onmap = {}
    for f in glob.glob("data/clubs/[A-Z][A-Z].json"):
        d = json.load(open(f, encoding="utf-8"))
        for c in d.get("clubs", []):
            onmap[c["id"]] = (c.get("tier"), c.get("name"), os.path.basename(f)[:2])
    manual = {}
    with open("data/clubs-manual.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r.get("clubQid") or "").strip():
                manual[r["clubQid"].strip()] = (r.get("tier") or "").strip()
    rejected = set()
    with open("data/coordinate-reviews.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["decision"] == "rejected" and not r["osmRef"]:
                rejected.add(r["clubQid"])
    verdicts = {}
    with open("data/clubs/roster-review.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            verdicts.setdefault(r["clubQid"], []).append(r["_verdict"])

    E = {}
    counts = {}
    detail = []
    for club, ss in stm.items():
        mapped = [(tiers[lg][0], tiers[lg][1], lg, end, prec, st) for lg, end, prec, st in ss if lg in tiers]
        if not mapped: continue
        country = sorted({m[1] for m in mapped})[0]
        tier_all = min(m[0] for m in mapped)
        live = [m for m in mapped if not ended(m[3], m[4])]
        tier_live = min((m[0] for m in live), default=None)
        anyend = any(m[3] for m in mapped)
        c = counts.setdefault(country, {"clubs": 0, "withEnd": 0, "tierByEnded": 0})
        c["clubs"] += 1
        if anyend: c["withEnd"] += 1
        if tier_live == tier_all: continue
        c["tierByEnded"] += 1
        # where does this club stand today
        hand = manual.get(club)
        if club in onmap:
            if hand == "skip":
                state = "skip-row-but-on-map?"
            elif hand and hand.isdigit():
                state = f"on-map-tier{onmap[club][0]}-HAND-TIER"
            else:
                state = f"on-map-tier{onmap[club][0]}-UNCORRECTED"
        elif hand == "skip":
            state = "skipped-by-hand"
        elif club in rejected:
            state = "off-map-whole-club-rejected"
        elif hand and hand.isdigit():
            state = f"off-map-hand-tier{hand}"
        else:
            state = "off-map-no-coords-NOT-REJECTED"
        key = f"{country}:{state.split('-tier')[0] if state.startswith('on-map') else state}"
        detail.append((country, state, club, tier_all, tier_live,
                       [(m[0], m[3] or "-", m[5] or "-") for m in mapped], verdicts.get(club, [])))
    for k, v in sorted(counts.items()):
        p("P582-COUNTS", k, v)
    need = [d[2] for d in detail]
    E = ents(need, props="labels")
    agg = {}
    for d in sorted(detail):
        agg.setdefault((d[0], d[1].replace("tier1", "tierN").replace("tier2", "tierN").replace("tier3", "tierN").replace("tier4", "tierN")), 0)
        agg[(d[0], d[1].replace("tier1", "tierN").replace("tier2", "tierN").replace("tier3", "tierN").replace("tier4", "tierN"))] += 1
        p("P582-CLUB", d[0], "|", d[1], "|", d[2], lab(E.get(d[2], {})), "| tierAll", d[3], "tierLive", d[4],
          "| tags", d[5], "| roster", d[6])
    for k, v in sorted(agg.items()):
        p("P582-STATE", k, v)


for name, fn in [("1 GR leagues", s1), ("2 GR articles", s2), ("3 GR StadiumDB", s3), ("4 GR items", s4),
                 ("5 P582", s5)]:
    section(name, fn)
    time.sleep(2)
p("GR-TOP again", GR_LEAGUES)
p("=== END OF PROBE GR1 ===")
