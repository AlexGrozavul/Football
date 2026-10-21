#!/usr/bin/env python3
"""
propose_country.py -- the repeatable part of adding a country (tiers 1 and 2),
so that a person only decides.

READ-ONLY. It never edits a hand-written file (clubs-manual.csv,
league-tiers.csv, league-rosters.csv, roster-links-manual.csv,
fixture-links-manual.csv, coordinate-reviews.csv, football-rules.json),
never writes a club file, and writes exactly two files:

    data/clubs/proposal-<CC>.csv   one row per piece of evidence
    data/clubs/proposal-<CC>.md    the read-back, the printed wiring patch

Rule 2 applies: a gap is reported, never guessed. A row is EVIDENCE for a
decision, never the decision. Where the tool cannot tell, the cell says so.

WHAT IT READS, IN THIS ORDER

 1. Rosters.   Each season article's stadiums table, with check_rosters.py's
               own reader (imported, not copied): club, Q-id by the sitelink
               hop, ground, capacity. A table that does not resolve, a hop
               that returns nothing, a row the reader cannot read: loud, and
               nothing is written (--write-partial overrides, for probes).
 2. Leagues.   The season article's Wikidata item -> P3450 -> the league item
               (fallback: the infobox's league link). Its P3983 and P17 are
               PRINTED, never used to decide the country. Every item carrying
               either league at ANY rank is listed by SPARQL with rank,
               P580/P582 and P576, and items labelled like the tier but
               dissolved or succeeded by another item are flagged (the "old
               Second Division" trap, Belgium's Q233199).
 3. Candidates (the .csv). kind is one of
               roster-ok  roster-untagged  roster-wrong-tier  roster-unread
               extra-tagged  not-a-club  duplicate  women-candidate
               rank-shape  two-grounds
               (and, with --grounds, ground-proposal  capacity-proposal)
 4. Wiring patch (the .md): league-tiers.csv and league-rosters.csv rows,
               COUNTRY_BOX from P1332-P1335, football-data candidates, and
               the places a person must edit, with line numbers.
 5. Summary: counts per kind and every step's duration.

THE ORDER OF USE FOR A NEW COUNTRY is in CLAUDE.md, "Adding a country".

Usage (from the repo root):
    python3 tools/propose_country.py --country PT --country-qid Q45 \\
        --article "1=2026–27 Primeira Liga" --article "2=2026–27 Liga Portugal 2" \\
        [--langs pt] [--league 1=Q182994] [--write-partial] [--out-dir data/clubs]

Politeness: User-Agent FootballPlannerBot/1.0, maxlag=5 on Wikimedia APIs,
one request a second per host, Retry-After honoured on 429/503, at most 4
tries. No key, no secret.
"""

import argparse
import csv
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import check_rosters as cr                     # noqa: E402  the roster reader
import diagnose_p118_rank as dg                # noqa: E402  the rank queries
import fetch_clubs as fc                       # noqa: E402  the not-a-club net, COUNTRIES
import fetch_fixtures as ff                    # noqa: E402  football-data's list

UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
MIN_GAP = 1.0
MAX_TRIES = 4
TIMEOUT = 90
WDQS = "https://query.wikidata.org/sparql"
WD_API = "https://www.wikidata.org/w/api.php"
WP_API = "https://en.wikipedia.org/w/api.php"

HEADER = ["kind", "tier", "clubQid", "label", "evidenceUrl", "evidenceText", "detail"]
KINDS = ["roster-ok", "roster-untagged", "roster-wrong-tier", "roster-unread",
         "extra-tagged", "not-a-club", "duplicate", "women-candidate",
         "rank-shape", "two-grounds", "ground-proposal", "capacity-proposal"]

WOMEN_WORDS = re.compile(
    r"\b(women|womens|woman|ladies|female|feminine|feminino|feminina|femenino|"
    r"femminile|f[ée]minin|feminin|frauen|damen|vrouwen|dames|femei|kobiet|"
    r"γυναικ\w*|жен\w*)\b|\bW\.?F\.?C\.?\b", re.IGNORECASE)


# =========================================================== http, politely

_last = {}
STEPS = []


class step:
    """Times a named step and prints its duration."""

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.t = time.time()
        print(f"\n[{self.name}]")
        return self

    def __exit__(self, *exc):
        STEPS.append((self.name, round(time.time() - self.t, 1)))
        print(f"[{self.name}] {STEPS[-1][1]} s")
        return False


def _wait(host):
    gap = time.time() - _last.get(host, 0)
    if gap < MIN_GAP:
        time.sleep(MIN_GAP - gap)
    _last[host] = time.time()


def _retry_after(headers):
    try:
        return int((headers or {}).get("Retry-After") or 0)
    except (ValueError, TypeError):
        return 0


def fetch_json(url, what, data=None, headers=None):
    """
    (parsed json, None) or (None, reason). At most MAX_TRIES tries; a 429 or
    503 waits for Retry-After; a Wikimedia API answer of `maxlag` waits and
    retries; an answer cut off mid-JSON is "too slow", not "wrong".
    """
    host = urllib.parse.urlsplit(url).netloc
    if host.endswith(("wikipedia.org", "wikidata.org")) and "/w/api.php" in url \
            and "maxlag=" not in url:
        url += ("&" if "?" in url else "?") + "maxlag=5"
    reason = "no attempt"
    for attempt in range(1, MAX_TRIES + 1):
        _wait(host)
        req = urllib.request.Request(url, data=data, headers={
            "User-Agent": UA, "Accept": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                body = resp.read().decode("utf-8")
                retry_header = resp.headers.get("Retry-After")
            obj = json.loads(body)
        except urllib.error.HTTPError as exc:
            reason = f"HTTP {exc.code}"
            if exc.code in (429, 500, 502, 503, 504) and attempt < MAX_TRIES:
                wait = min(_retry_after(exc.headers) or 15 * attempt, 120)
                print(f"    {what}: {reason}, waiting {wait}s (try {attempt}/{MAX_TRIES})")
                time.sleep(wait)
                continue
            return None, reason
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            reason = f"network error: {getattr(exc, 'reason', exc)}"
            if attempt < MAX_TRIES:
                print(f"    {what}: {reason}, retrying (try {attempt}/{MAX_TRIES})")
                time.sleep(10 * attempt)
                continue
            return None, reason
        except ValueError:
            reason = "answer cut off mid-JSON"
            if attempt < MAX_TRIES:
                print(f"    {what}: {reason}, retrying (try {attempt}/{MAX_TRIES})")
                time.sleep(15)
                continue
            return None, reason
        if isinstance(obj, dict) and (obj.get("error") or {}).get("code") == "maxlag":
            reason = "Wikimedia maxlag"
            wait = min(int(_retry_after({"Retry-After": retry_header}) or 6), 60)
            print(f"    {what}: maxlag, waiting {wait}s (try {attempt}/{MAX_TRIES})")
            time.sleep(wait)
            continue
        return obj, None
    return None, f"gave up after {MAX_TRIES} tries ({reason})"


# check_rosters' own reader makes its HTTP calls through this name: the same
# politeness (User-Agent, maxlag, Retry-After, 4 tries) applies to them.
cr.get_json_with_retry = lambda url, what: fetch_json(url, what)
cr.REQUEST_GAP_SECONDS = 1


def sparql(query, what):
    body = urllib.parse.urlencode({"query": query, "format": "json"}).encode("utf-8")
    data, error = fetch_json(WDQS, what, data=body, headers={
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded"})
    if error:
        return None, error
    return (data.get("results") or {}).get("bindings") or [], None


def bval(row, name):
    item = row.get(name)
    return item.get("value") if item else None


def qid_of(uri):
    return uri.rsplit("/", 1)[-1] if uri else None


# ======================================================= wikidata, as dicts

def fmt_time(value):
    """A Wikidata time value as the precision it was given at."""
    t = (value or {}).get("time", "")
    m = re.match(r"([+-]?)(\d+)-(\d\d)-(\d\d)", t)
    if not m:
        return None
    sign, y, mo, d = m.groups()
    precision = (value or {}).get("precision", 11)
    year = ("-" if sign == "-" else "") + str(int(y))
    if precision <= 9:
        return year
    if precision == 10:
        return f"{year}-{mo}"
    return f"{year}-{mo}-{d}"


def stmt_value(snak):
    dv = (snak or {}).get("datavalue") or {}
    value = dv.get("value")
    if dv.get("type") == "wikibase-entityid":
        return value.get("id")
    if dv.get("type") == "time":
        return fmt_time(value)
    if dv.get("type") == "globecoordinate":
        return (value.get("latitude"), value.get("longitude"))
    if dv.get("type") == "quantity":
        try:
            return int(float(value.get("amount")))
        except (TypeError, ValueError):
            return None
    return value


def qualifier(statement, prop):
    for q in ((statement.get("qualifiers") or {}).get(prop) or []):
        v = stmt_value(q)
        if v:
            return v
    return None


def statements(entity, prop):
    out = []
    for st in (entity.get("claims") or {}).get(prop) or []:
        snak = st.get("mainsnak") or {}
        out.append({"value": stmt_value(snak) if snak.get("snaktype") == "value" else None,
                    "snaktype": snak.get("snaktype") or "?",
                    "rank": st.get("rank") or "normal",
                    "start": qualifier(st, "P580"), "end": qualifier(st, "P582")})
    return out


def truthy(stmts):
    """What `wdt:` yields: the preferred statements if any, else the normal
    ones; never a deprecated one; a no-value statement contributes nothing."""
    ranks = {s["rank"] for s in stmts}
    best = "preferred" if "preferred" in ranks else "normal"
    return [s for s in stmts if s["rank"] == best and s["snaktype"] == "value" and s["value"]]


def labels_of(entity, langs):
    raw = entity.get("labels") or {}
    out = []
    for lang in ["en"] + list(langs):
        v = raw.get(lang)
        v = v.get("value") if isinstance(v, dict) else v
        if v and v not in out:
            out.append(v)
    for v in raw.values():
        v = v.get("value") if isinstance(v, dict) else v
        if v and v not in out:
            out.append(v)
    return out


def sitelinks_of(entity):
    links = entity.get("sitelinks")
    if isinstance(links, list):
        return {l["site"]: l["title"] for l in links if l.get("site")}
    if isinstance(links, dict):
        return {k: (v.get("title") if isinstance(v, dict) else v) for k, v in links.items()}
    return {}


def fetch_entities(qids, langs, props="claims|labels|descriptions|sitelinks"):
    """wbgetentities, 50 ids a call. {qid: entity}, failures. A batch that
    comes back with nothing is a failed call, not items with nothing on them."""
    entities, failures = {}, []
    ordered = list(dict.fromkeys(q for q in qids if q))
    for start in range(0, len(ordered), 50):
        batch = ordered[start:start + 50]
        query = urllib.parse.urlencode({
            "action": "wbgetentities", "ids": "|".join(batch), "props": props,
            "languages": "|".join(["en"] + list(langs)),
            "format": "json", "formatversion": "2"})
        data, error = fetch_json(f"{WD_API}?{query}", f"entities {start}-{start + len(batch)}")
        if error:
            failures.append(f"reading {len(batch)} items failed: {error}")
            continue
        if data.get("error"):
            failures.append(f"reading {len(batch)} items refused: {data['error'].get('code')}")
            continue
        got = {q: e for q, e in (data.get("entities") or {}).items()
               if q.startswith("Q") and not e.get("missing")}
        if not got:
            failures.append(f"no usable entity for any of {len(batch)} items Wikidata had named")
            continue
        entities.update(got)
    return entities, failures


def summarize(entity, tracked, langs):
    """One Wikidata item as the facts the candidates are built from.
    `tracked` is {league qid: tier}."""
    qid = entity.get("id")
    p118 = statements(entity, "P118")
    p118 = [dict(s, league=s.pop("value")) for s in p118]
    visible = dg.truthy_leagues(dg.league_statements(entity))
    tiers = [tracked[q] for q in visible if q in tracked]
    labels = labels_of(entity, langs)
    descs = entity.get("descriptions") or {}
    desc = (descs.get("en") or {}).get("value") if isinstance(descs.get("en"), dict) else None
    grounds = statements(entity, "P115")
    coords = [s["value"] for s in statements(entity, "P625") if s["value"]]
    return {
        "qid": qid, "label": labels[0] if labels else qid, "labels": labels, "desc": desc,
        "sitelinks": sitelinks_of(entity),
        "types": [s["value"] for s in statements(entity, "P31") if s["value"]],
        "p118": p118, "visible": visible,
        "tier": min(tiers) if tiers else None,
        "tracked": [s for s in p118 if s["league"] in tracked],
        "dissolved": dg.dissolved_year(entity),
        "p17": [s["value"] for s in statements(entity, "P17") if s["value"]],
        "grounds_all": grounds, "grounds_truthy": truthy(grounds),
        "coord": coords[0] if coords else None,
        "p831": [s["value"] for s in statements(entity, "P831") if s["value"]],
        "p361": [s["value"] for s in statements(entity, "P361") if s["value"]],
        "p749": [s["value"] for s in statements(entity, "P749") if s["value"]],
        "p2094": [s["value"] for s in statements(entity, "P2094") if s["value"]],
    }


def rank_shape(info):
    """The three ways a tracked league tag can be invisible to the club query.
    None when the club is visible or carries no tracked tag at all."""
    if not info["tracked"] or info["tier"] is not None:
        return None
    stm = info["p118"]
    if any(s["rank"] == "preferred" and s["snaktype"] != "value" for s in stm):
        return "B"       # a preferred novalue / somevalue suppresses them
    if any(s["rank"] == "preferred" and s["snaktype"] == "value"
           and s["league"] not in {t["league"] for t in info["tracked"]} for s in stm) \
            and any(s["rank"] == "normal" for s in info["tracked"]):
        return "C"       # a preferred statement naming ANOTHER league (LR Vicenza)
    if all(s["rank"] == "deprecated" for s in info["tracked"]):
        return "A"       # every tracked statement deprecated (FC Augsburg)
    return "?"


SHAPE_TEXT = {
    "A": "every tracked league statement is deprecated, so the club query cannot see them",
    "B": "a preferred statement asserts no league (novalue/somevalue) and suppresses the tags under it",
    "C": "a preferred statement names a DIFFERENT league over the tracked one at normal rank",
    "?": "tracked tag not truthy for a reason none of A, B, C describes",
}


# ============================================================ small helpers

def wd(q):
    return f"https://www.wikidata.org/wiki/{q}"


def enwiki_url(title):
    return "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))


def one_line(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def kv(**fields):
    return "; ".join(f"{k}={one_line(v)}" for k, v in fields.items() if v not in (None, "", []))


def row(kind, tier, qid, label, url, text, detail):
    return {"kind": kind, "tier": tier if tier is not None else "", "clubQid": qid or "",
            "label": label or "", "evidenceUrl": url or "", "evidenceText": one_line(text),
            "detail": one_line(detail)}


def tag_text(info, lab):
    parts = []
    for s in info["p118"]:
        span = ""
        if s["start"] or s["end"]:
            span = f", {s['start'] or '?'}-{s['end'] or ''}"
        value = lab(s["league"]) if s["snaktype"] == "value" else f"<{s['snaktype']}>"
        parts.append(f"{value} ({s['rank']}{span})")
    return " | ".join(parts) or "no P118"


def first_words(text, n=30):
    words = text.split()
    return text if len(words) <= n else " ".join(words[:n]) + " ..."


def season_of(article):
    m = re.search(r"(\d{4})\s*[–-]\s*(\d{2,4})", article)
    return f"{m.group(1)}-{m.group(2)[-2:]}" if m else ""


# ====================================================== step 1: the rosters

def team_change_links(page_html):
    """{article title: [text, ...]} for every link inside a 'Changes' / 'Team
    changes' / promotion-and-relegation section of a season article. A table's
    caption ("To Liga Portugal 2", "From the Primeira Liga") is kept in the text
    of its rows, because it is what says which way the club moved."""
    out = {}
    m = re.search(r'<h([23])[^>]*id="(?:Team_changes|Changes|Promotion_and_relegation|'
                  r'Club_changes|Team_movements)[^"]*"', page_html)
    if not m:
        return out
    level = int(m.group(1))
    rest = page_html[m.end():]
    end = re.search(r'<div class="mw-heading mw-heading[2-%d]"|<h[2-%d][ >]' % (level, level), rest)
    section = rest[:end.start()] if end else rest
    tables = re.findall(r"<table[^>]*>.*?</table>", section, re.S)
    inner = [t for t in tables if "<table" not in t[6:]] or tables
    for table in inner:
        cap = re.search(r"<caption[^>]*>(.*?)</caption>", table, re.S)
        caption = cr.text_of(cap.group(1)) if cap else ""
        for block in re.findall(r"<tr[^>]*>.*?</tr>", table, re.S):
            text = (caption + ": " if caption else "") + cr.text_of(block)
            for href in re.findall(r'href="/wiki/([^"#:]+)"', block):
                title = urllib.parse.unquote(href).replace("_", " ")
                out.setdefault(title, []).append(text[:200])
    for block in re.findall(r"<li[^>]*>.*?</li>", section, re.S):
        for href in re.findall(r'href="/wiki/([^"#:]+)"', block):
            out.setdefault(urllib.parse.unquote(href).replace("_", " "), []).append(cr.text_of(block)[:200])
    return out


def read_rosters(articles):
    """
    articles: [(tier, title)]. Returns (records, gaps, pages, failures).
    record: tier, article, team, title, qid, ground, ground_title, capacity.
    gaps:   (tier, article, row text, reason) - rows the reader cannot read.
    """
    records, gaps, pages, failures = [], [], {}, []
    for tier, title in articles:
        page, real, error = cr.fetch_article(title)
        if error:
            failures.append(f"tier {tier} {title!r}: {error}")
            continue
        tables, shape = cr.roster_tables(page)
        if not tables:
            failures.append(f"tier {tier} {real!r} parsed, but no table on it looks like a "
                            f"membership list (the page layout has changed?)")
            continue
        n = 0
        for table, headers in tables:
            for r in cr.table_rows(table, headers):
                if r["why"]:
                    gaps.append((tier, real, r["shown"], r["why"]))
                    continue
                if not r["title"]:
                    if r["team"] and re.search(r"[^\W\d_]{3}", r["team"]):
                        gaps.append((tier, real, r["team"], "the row has no link at all"))
                    continue
                records.append({"tier": tier, "article": real, "team": r["team"],
                                "title": r["title"], "qid": None, "ground": r["ground"],
                                "ground_title": r["ground_title"], "capacity": r["capacity"]})
                n += 1
        print(f"    tier {tier}: {real!r}: {len(tables)} {shape} table(s), {n} clubs")
        if not n:
            failures.append(f"tier {tier} {real!r}: tables parsed but no club came out of them")
        pages[tier] = (real, page)
    if records:
        found, hop_failures = cr.qids_for_titles([r["title"] for r in records])
        failures.extend(hop_failures)
        for r in records:
            r["qid"] = found.get(r["title"])
        for title, target in cr.REDIRECT_REFUSED.items():
            for r in [r for r in records if r["title"] == title]:
                gaps.append((r["tier"], r["article"], r["team"],
                             f"a reserve side whose link redirects to {target!r}; the reserve "
                             f"marker does not agree after the redirect"))
                records.remove(r)
        for r in [r for r in records if not r["qid"]]:
            gaps.append((r["tier"], r["article"], r["team"],
                         f"the linked article {r['title']!r} has no Wikidata item"))
            records.remove(r)
    return records, gaps, pages, failures


# ============================================================ step 2: leagues

def find_league(tier, real_title, langs):
    """
    The league's Wikidata item for a season article. Route 1: the article's
    own item, then P3450 (sports season of league). Route 2: the infobox's
    league link, hopped to a Q-id. Returns (qid, via) or (None, reason).
    """
    found, _ = cr.qids_for_titles([real_title])
    season_q = found.get(real_title)
    if season_q:
        ents, _ = fetch_entities([season_q], langs, props="claims|labels")
        e = ents.get(season_q)
        if e:
            for s in statements(e, "P3450"):
                if s["value"]:
                    return s["value"], f"season item {season_q} -> P3450"
    query = urllib.parse.urlencode({
        "action": "parse", "page": real_title, "prop": "wikitext", "section": "0",
        "format": "json", "formatversion": "2", "redirects": "1"})
    data, error = fetch_json(f"{WP_API}?{query}", "infobox")
    if not error and data and not data.get("error"):
        text = (data.get("parse") or {}).get("wikitext") or ""
        m = re.search(r"\|\s*league\s*=\s*\[\[([^\]|#]+)", text)
        if m:
            target = m.group(1).strip()
            hop, _ = cr.qids_for_titles([target])
            if hop.get(target):
                return hop[target], f"infobox league link [[{target}]]"
    return None, ("no P3450 on the season item and no infobox league link; pass "
                  f"--league {tier}=Q... to name the league item")


def league_facts(league_qids, langs):
    ents, failures = fetch_entities(league_qids, langs)
    facts = {}
    for q, e in ents.items():
        facts[q] = {
            "label": labels_of(e, langs)[0], "labels": labels_of(e, langs),
            "desc": ((e.get("descriptions") or {}).get("en") or {}).get("value"),
            "p3983": [s["value"] for s in statements(e, "P3983") if s["value"]],
            "p17": [s["value"] for s in statements(e, "P17") if s["value"]],
            "p576": [s["value"] for s in statements(e, "P576") if s["value"]],
            "p1366": [s["value"] for s in statements(e, "P1366") if s["value"]],
            "p1365": [s["value"] for s in statements(e, "P1365") if s["value"]],
            "types": [s["value"] for s in statements(e, "P31") if s["value"]],
            "sitelinks": sitelinks_of(e)}
    return facts, failures


def tagged_items(tracked, langs):
    """SPARQL: every non-human item carrying either league at ANY rank."""
    values = " ".join(f"wd:{q}" for q in tracked)
    query = f"""
SELECT ?item ?league ?rank ?start ?end ?dissolved WHERE {{
  VALUES ?league {{ {values} }}
  ?item p:P118 ?st . ?st ps:P118 ?league ; wikibase:rank ?rank .
  FILTER NOT EXISTS {{ ?item wdt:P31 wd:Q5 }}
  OPTIONAL {{ ?st pq:P580 ?start }} OPTIONAL {{ ?st pq:P582 ?end }}
  OPTIONAL {{ ?item wdt:P576 ?dissolved }}
}}"""
    rows, error = sparql(query, "every tagged item")
    if error:
        return None, error
    found = {}
    for r in rows:
        q = qid_of(bval(r, "item"))
        if q:
            found.setdefault(q, []).append(
                {"league": qid_of(bval(r, "league")),
                 "rank": (bval(r, "rank") or "").rsplit("#", 1)[-1].replace("Rank", "").lower(),
                 "start": (bval(r, "start") or "")[:10] or None,
                 "end": (bval(r, "end") or "")[:10] or None})
    return found, None


def trap_items(tracked, league_facts_by_q, redirect_titles, langs):
    """Items labelled like a tier (or like a redirect to its article) that are
    not the tier's item, and are used as a league by some club or are
    dissolved/succeeded: the 'old Second Division' trap."""
    labels = set()
    for q in tracked:
        labels.update(league_facts_by_q.get(q, {}).get("labels", []))
    labels.update(redirect_titles)
    lits = " ".join('"%s"@en' % l.replace("\\", "\\\\").replace('"', '\\"') for l in sorted(labels))
    values = " ".join(f"wd:{q}" for q in tracked)
    query = f"""
SELECT ?x ?xLabel ?xDescription ?n ?dis ?succ ?succLabel WHERE {{
  {{ SELECT ?x (COUNT(DISTINCT ?c) AS ?n) (SAMPLE(?d) AS ?dis) (SAMPLE(?s) AS ?succ) WHERE {{
      {{ VALUES ?l {{ {lits} }} ?x rdfs:label ?l }}
      UNION {{ ?x wdt:P1366 ?l1 . VALUES ?l1 {{ {values} }} }}
      UNION {{ ?l2 wdt:P1365 ?x . VALUES ?l2 {{ {values} }} }}
      FILTER(?x NOT IN ({', '.join('wd:' + q for q in tracked)}))
      OPTIONAL {{ ?x wdt:P576 ?d }} OPTIONAL {{ ?x wdt:P1366 ?s }}
      OPTIONAL {{ ?c p:P118/ps:P118 ?x }}
  }} GROUP BY ?x }}
  FILTER(?n > 0 || BOUND(?dis) || BOUND(?succ))
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{','.join(['en'] + list(langs))}". }}
}}"""
    rows, error = sparql(query, "same-label league items")
    if error:
        return None, error
    out = []
    for r in rows:
        out.append({"qid": qid_of(bval(r, "x")), "label": bval(r, "xLabel"),
                    "desc": bval(r, "xDescription"), "clubs": int(bval(r, "n") or 0),
                    "dissolved": (bval(r, "dis") or "")[:10] or None,
                    "succeeded_by": qid_of(bval(r, "succ"))})
    return out, None


def redirects_to(title):
    """English Wikipedia titles that redirect to an article."""
    query = urllib.parse.urlencode({
        "action": "query", "list": "backlinks", "bltitle": title,
        "blfilterredir": "redirects", "bllimit": "50", "blnamespace": "0",
        "format": "json", "formatversion": "2"})
    data, error = fetch_json(f"{WP_API}?{query}", "redirects to the league")
    if error or not data:
        return []
    return [b["title"] for b in (data.get("query") or {}).get("backlinks") or []]


def pointers_at(club_qids, langs):
    """Items that point at a roster/tagged club by P361, P749, P831 or P127,
    with the labels the women's-football angle needs."""
    out = {}
    clubs = sorted(club_qids)
    for start in range(0, len(clubs), 80):
        values = " ".join(f"wd:{q}" for q in clubs[start:start + 80])
        query = f"""
SELECT ?w ?wLabel ?wDescription ?pred ?club ?typeLabel ?classLabel WHERE {{
  VALUES ?club {{ {values} }}
  VALUES ?pred {{ wdt:P361 wdt:P749 wdt:P831 wdt:P127 }}
  ?w ?pred ?club .
  OPTIONAL {{ ?w wdt:P31 ?type }} OPTIONAL {{ ?w wdt:P2094 ?class }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{','.join(['en'] + list(langs))}". }}
}}"""
        rows, error = sparql(query, "items pointing at the clubs")
        if error:
            return None, error
        for r in rows:
            q = qid_of(bval(r, "w"))
            e = out.setdefault(q, {"qid": q, "label": bval(r, "wLabel"),
                                   "desc": bval(r, "wDescription"), "to": set(),
                                   "types": set(), "classes": set()})
            e["to"].add((qid_of(bval(r, "club")), (bval(r, "pred") or "").rsplit("/", 1)[-1]))
            if bval(r, "typeLabel"):
                e["types"].add(bval(r, "typeLabel"))
            if bval(r, "classLabel"):
                e["classes"].add(bval(r, "classLabel"))
    return out, None


def intro_sentences(infos, langs):
    """{qid: (text, url)} - the first intro sentence of the item's article
    that names a league (30 words at most), English first, then the extra
    languages. A gap is returned as (None, reason)."""
    out = {}
    for qid, info in infos.items():
        site, title = None, None
        for lang in ["en"] + list(langs):
            if f"{lang}wiki" in info["sitelinks"]:
                site, title = lang, info["sitelinks"][f"{lang}wiki"]
                break
        out[qid] = (site, title)
    texts = {}
    by_site = {}
    for qid, (site, title) in out.items():
        if site:
            by_site.setdefault(site, []).append((qid, title))
    for site, items in by_site.items():
        for start in range(0, len(items), 20):
            batch = items[start:start + 20]
            query = urllib.parse.urlencode({
                "action": "query", "prop": "extracts", "exintro": "1", "explaintext": "1",
                "exsentences": "4", "exlimit": "20", "redirects": "1",
                "titles": "|".join(t for _q, t in batch),
                "format": "json", "formatversion": "2"})
            data, error = fetch_json(f"https://{site}.wikipedia.org/w/api.php?{query}",
                                     f"intro ({site})")
            if error or not data:
                continue
            q = data.get("query") or {}
            redirected = {r["from"]: r["to"] for r in (q.get("redirects") or [])}
            normalized = {r["from"]: r["to"] for r in (q.get("normalized") or [])}
            pages = {p["title"]: p.get("extract") or "" for p in q.get("pages") or []}
            for qid, title in batch:
                t = normalized.get(title, title)
                t = redirected.get(t, t)
                texts[qid] = (pages.get(t, ""), site, title)
    result = {}
    league_word = re.compile(r"\b(league|division|liga|divis[aã]o|campeonato|tier|"
                             r"championship|compet\w+|plays?|played|currently)\b", re.I)
    for qid, (site, title) in out.items():
        if not site:
            result[qid] = (None, "no article in English or the extra languages")
            continue
        extract, site, title = texts.get(qid, ("", site, title))
        sentences = re.split(r"(?<=[.!?])\s+", one_line(extract))
        pick = next((s for s in sentences if league_word.search(s)), sentences[0] if sentences else "")
        if not pick:
            result[qid] = (None, f"the {site} article has no intro text")
            continue
        url = f"https://{site}.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
        result[qid] = (("[" + site + "] " if site != "en" else "") + first_words(pick), url)
    return result


# =========================================================== country box etc

def country_box(country_qid, langs):
    ents, failures = fetch_entities([country_qid], langs, props="claims|labels")
    e = ents.get(country_qid)
    if not e:
        return None, failures or ["country item not found"]
    edges = {}
    for prop, name in (("P1332", "north"), ("P1333", "south"), ("P1334", "east"), ("P1335", "west")):
        edges[name] = [(s["value"], s["rank"]) for s in statements(e, prop)
                       if s["value"] and s["rank"] != "deprecated"]
    return {"label": labels_of(e, langs)[0], "edges": edges}, failures


def propose_box(box, margin=0.15):
    """Two proposals when a preferred-rank point (an overseas territory, an
    island) is in the way: from the best-rank points, and from the normal-rank
    ones. Wikidata's points are the country's own extremes."""
    def edge(name, ranks):
        pts = [v for v, rk in box["edges"][name] if rk in ranks]
        if not pts:
            return None
        lat_lon = 0 if name in ("north", "south") else 1
        vals = [p[lat_lon] for p in pts]
        return max(vals) if name in ("north", "east") else min(vals)
    out = {}
    for tag, ranks_for in (("best rank", None), ("normal rank only", {"normal"})):
        e = {}
        for name in ("north", "south", "east", "west"):
            pts = box["edges"][name]
            best = "preferred" if any(rk == "preferred" for _v, rk in pts) else "normal"
            e[name] = edge(name, {best} if ranks_for is None else ranks_for)
        if None in e.values():
            continue
        out[tag] = {"lat": (round(e["south"] - margin, 2), round(e["north"] + margin, 2)),
                    "lon": (round(e["west"] - margin, 2), round(e["east"] + margin, 2))}
    return out


def football_data_candidates(country_label, league_labels):
    cands = []
    names = {n.casefold() for n in league_labels} | {country_label.casefold()}
    for code, label in ff.COMPETITIONS:
        low = label.casefold()
        if any(n and (n in low or low in n) for n in names):
            cands.append((code, label, "football-data free tier list (tools/fetch_fixtures.py)"))
    try:
        index = json.load(open("data/fixtures/index.json", encoding="utf-8"))
        for code, meta in (index.get("competitions") or {}).items():
            low = (meta.get("name") or "").casefold()
            if any(n and (n in low or low in n) for n in names) and \
                    not any(c[0] == code for c in cands):
                cands.append((code, meta.get("name"), "data/fixtures/index.json"))
    except (OSError, ValueError):
        pass
    return cands


PLACES = [
    ("data/league-tiers.csv", "append the league-tiers rows printed above", None),
    ("data/league-rosters.csv", "append the league-rosters rows printed above", None),
    ("tools/fetch_clubs.py", "COUNTRIES (code, P17 Q-id, name), COUNTRY_BOX and its comment, "
     "COUNTRY_NAMES, the label languages in the build loop", "tpl"),
    ("tools/diagnose_p118_rank.py", "COUNTRIES (P17 Q-id to code)", "tpl"),
    ("tools/crosscheck_stadiumdb.py", "COUNTRY_PAGES (the slug, found by probe); EXTRA_PAGES if "
     "the pyramid crosses a border", "tpl-slug"),
    ("tools/link_fixtures.py", "CLUB_FILES; FD_COUNTRY if football-data carries a league", "tpl"),
    ("tools/build_calendars.py", "time zone (usually already there)", "tpl"),
    ("index.html", "COUNTRY_FILES; cn.XX in en and ro and COUNTRY_NAME; adj.XX and COUNTRY_ADJ "
     "for a country with no fixtures; noFixturesReason() top map; fx.coverage and LEAGUE_CODES "
     "if football-data carries a league", "tpl"),
    ("tools/test_nearme.js", 'the printed count ("of N country files")', r"of \d+ country"),
    ("docs/ro-review.md", "rows for the new keys (regenerate after the dictionary change)", None),
    ("sw.js", "SHELL_VERSION bump (any change to index.html's shell), history line in CLAUDE.md", r"SHELL_VERSION"),
]

STAYS_MANUAL = [
    "data/clubs-manual.csv: every skip, tier, ground, capacity, hand-named row (decisions)",
    "data/roster-links-manual.csv: identity links for rows the reader refuses",
    "data/fixture-links-manual.csv: abbreviations the fixture matcher refuses",
    "data/coordinate-reviews.csv: open/rejected rows for clubs left unplaced",
    "the pass over the proposals: each skip needs two complete division articles agreeing on the "
    "absence AND an independent statement of the reason (the Hermannstadt standard)",
    "the CLAUDE.md entry for the country, the roster-check, rank-diagnostic, StadiumDB and capacity "
    "dispatches on the branch, and the merge",
]


def places_to_touch(code, country_qid):
    """The places a person must edit, with line numbers - read off the most
    recently added country (the last of fetch_clubs.COUNTRIES that is not this
    one), so the new country is wired beside it."""
    template = [c for c in fc.COUNTRIES if c[0] != code][-1]
    tcode, tqid, tname = template
    token = re.compile(rf'\b{tcode}\b|\b{tqid}\b|\b{re.escape(tname)}\b')
    out = [f"(template country: {tname} {tcode} {tqid}; edit beside its lines)"]
    for path, what, how in PLACES:
        lines = []
        if how and os.path.exists(path):
            pat = token if how in ("tpl", "tpl-slug") else re.compile(how)
            for i, text in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
                if pat.search(text):
                    lines.append(f"{path}:{i}: {text.strip()[:110]}")
        out.append(f"- {path}: {what}")
        out.extend(f"    {l}" for l in lines[:12])
        if len(lines) > 12:
            out.append(f"    ... and {len(lines) - 12} more lines")
    return out


# =============================================== step 3: the candidates

def classify(ctx):
    """
    ctx: country_qid, tracked {league: tier}, league_label (callable),
    roster [rec], infos {qid: info}, tagged {qid: [stmts]}, label (callable),
    intro {qid: (text, url)}, team_changes {qid: [(article, text)]},
    pointers {qid: {...}}, ground_label (callable).
    Returns (rows, notes) - notes holds what is reported but is not a row.
    """
    rows, notes = [], {"dissolved_tagged": [], "hidden_extras": [], "pointer_only": 0}
    infos, lab = ctx["infos"], ctx["label"]
    tracked = ctx["tracked"]
    roster_by_q = {}
    for rec in ctx["roster"]:
        roster_by_q.setdefault(rec["qid"], []).append(rec)

    # The club item / men's team item shape: a tagged team item whose P831 is a
    # roster club with the same reserve markers is that club (one club, not two).
    twin_of, alias = {}, {}
    for t, info in infos.items():
        if t in roster_by_q or not info["tracked"]:
            continue
        for p in info["p831"]:
            if p in roster_by_q and cr.team_markers(info["label"]) == cr.team_markers(infos[p]["label"] if p in infos else info["label"]):
                twin_of.setdefault(p, t)
                alias[t] = p
                break

    def team_changes(q):
        hits = ctx["team_changes"].get(q) or []
        return "; ".join(f"{a}: {first_words(text, 22)}" for a, text in hits[:2])

    # --- the roster side
    for q, recs in sorted(roster_by_q.items(), key=lambda kv: (kv[1][0]["tier"], kv[1][0]["team"])):
        rec = recs[0]
        tier = rec["tier"]
        info = infos.get(q)
        twin = twin_of.get(q)
        url = enwiki_url(rec["title"])
        base = dict(team=rec["team"], ground=rec["ground"], capacity=rec["capacity"],
                    article=rec["article"])
        if not info:
            rows.append(row("roster-untagged", tier, q, rec["team"], wd(q),
                            f"{rec['team']}: roster club, Wikidata entity not readable",
                            kv(**base, why="no entity")))
            continue
        src = info
        via = None
        if info["tier"] is None and twin and infos[twin]["tier"] is not None:
            src, via = infos[twin], twin
        extras = kv(p17="" if info["p17"] == [ctx["country_qid"]] else ",".join(info["p17"]),
                    dissolved=info["dissolved"], via=f"P831 team item {via}" if via else "",
                    tags=tag_text(src, ctx["league_label"]))
        if len(recs) > 1:
            extras += "; also in tier " + ",".join(str(r["tier"]) for r in recs[1:])
        text = f"table row {rec['team']!r} in {rec['article']}"
        if src["tier"] == tier:
            rows.append(row("roster-ok", tier, q, rec["team"], url, text, kv(**base) + "; " + extras))
        elif src["tier"] is not None:
            rows.append(row("roster-wrong-tier", tier, q, rec["team"], url,
                            f"{text}; Wikidata tags it at tier {src['tier']}",
                            kv(**base, roster_tier=tier, tagged_tier=src["tier"],
                               named_in_team_changes=team_changes(q)) + "; " + extras))
        else:
            shape = rank_shape(src) or (rank_shape(infos[twin]) if twin else None)
            if shape:
                rows.append(row("rank-shape", tier, q, rec["team"], url,
                                f"{text}; shape {shape}: {SHAPE_TEXT[shape]}",
                                kv(**base, shape=shape) + "; " + extras))
            else:
                other = [ctx["league_label"](s["league"]) for s in info["p118"] if s["league"]]
                rows.append(row("roster-untagged", tier, q, rec["team"], url,
                                f"{text}; carries no tag of the tracked leagues",
                                kv(**base, other_leagues=" | ".join(other),
                                   fallback=("refused by the hand-named fallback: P576 "
                                             f"{info['dissolved']} (needs allowDissolved yes)"
                                             if info["dissolved"] else "hand-named fallback candidate"))
                                + "; " + extras))
        if len(src["grounds_truthy"]) > 1:
            rows.append(two_grounds_row(tier, q, rec["team"], src, ctx))

    # --- reader gaps
    for tier, article, shown, why in ctx["gaps"]:
        rows.append(row("roster-unread", tier, "", shown, enwiki_url(article),
                        f"{shown!r} in {article}: {why}",
                        "needs a hand link in data/roster-links-manual.csv, or the row is not a club on the map"))

    # --- the extras: tagged, in no roster
    tagged_extras = [q for q in ctx["tagged"] if q not in roster_by_q and q not in alias and q in infos]
    kept = []
    for q in sorted(tagged_extras, key=lambda x: infos[x]["label"]):
        info = infos[q]
        kinds = [ctx["label"](t) for t in info["types"]]
        why = fc.not_a_club(info["label"], kinds)
        if why:
            rows.append(row("not-a-club", info["tier"], q, info["label"], wd(q), why,
                            kv(types=" | ".join(kinds), tags=tag_text(info, ctx["league_label"]))))
            continue
        woman = women_angles(info, ctx)
        if woman:
            rows.append(row("women-candidate", info["tier"], q, info["label"], wd(q),
                            "; ".join(woman), kv(reaches_the_map="yes" if info["tier"] is not None else "no (tag not truthy)",
                                                 tags=tag_text(info, ctx["league_label"]))))
            continue
        if info["dissolved"]:
            notes["dissolved_tagged"].append((q, info["label"], info["dissolved"]))
            continue
        if info["tier"] is None:
            notes["hidden_extras"].append((q, info["label"], rank_shape(info) or "-"))
            continue
        kept.append(q)
        intro_text, intro_url = ctx["intro"].get(q, (None, "not looked up"))
        rows.append(row("extra-tagged", info["tier"], q, info["label"], intro_url if intro_text else wd(q),
                        intro_text or f"no intro sentence: {intro_url}",
                        kv(tags=tag_text(info, ctx["league_label"]), p576=info["dissolved"] or "none",
                           tag_dates=";".join(f"{s['start'] or '?'}-{s['end'] or ''}" for s in info["tracked"]),
                           named_in_team_changes=team_changes(q) or "no", types=" | ".join(kinds),
                           sitelinks=len(info["sitelinks"]),
                           p17="" if info["p17"] == [ctx["country_qid"]] else ",".join(info["p17"]))))
        if len(info["grounds_truthy"]) > 1:
            rows.append(two_grounds_row(info["tier"], q, info["label"], info, ctx))

    # --- duplicates: one folded label or one ground, same reserve markers
    pool = [q for q in infos if (q in roster_by_q or q in kept)]
    groups = {}
    for q in pool:
        for l in {cr.fold(l) for l in infos[q]["labels"] if l}:
            groups.setdefault(("label", l), set()).add(q)
        for s in infos[q]["grounds_truthy"]:
            groups.setdefault(("ground", s["value"]), set()).add(q)
    seen = set()
    n = 0
    for (basis, key), members in sorted(groups.items(), key=lambda kv: str(kv[0])):
        if len(members) < 2:
            continue
        marks = {frozenset(cr.team_markers(infos[m]["label"])) for m in members}
        if len(marks) > 1:
            continue
        sig = (basis, frozenset(members))
        if sig in seen:
            continue
        seen.add(sig)
        n += 1
        ground = ctx["ground_label"](key) if basis == "ground" else key
        desc = " || ".join(
            f"{m} {infos[m]['label']} [{', '.join(ctx['label'](t) for t in infos[m]['types'][:2])}; "
            f"sitelinks {len(infos[m]['sitelinks'])}; tier {infos[m]['tier']}; "
            f"roster {'yes' if m in roster_by_q else 'no'}; P831 {','.join(infos[m]['p831']) or '-'}; "
            f"P576 {infos[m]['dissolved'] or '-'}]" for m in sorted(members))
        for m in sorted(members):
            rows.append(row("duplicate", infos[m]["tier"], m, infos[m]["label"], wd(m),
                            f"group D{n}: {len(members)} items share {basis} {ground!r}",
                            f"group=D{n}; basis={basis}; members: {desc}"))

    # --- women's items that point at a roster/tagged club (no tag: informational)
    tagged_qs = set(ctx["tagged"])
    for w, p in sorted((ctx["pointers"] or {}).items()):
        if w in tagged_qs or w in roster_by_q:
            continue
        text = " ".join([p["label"] or "", p["desc"] or "", " ".join(p["types"]), " ".join(p["classes"])])
        if WOMEN_WORDS.search(text):
            notes["pointer_only"] += 1
            tos = ", ".join(f"{prop}->{lab(c) if c in infos else c}" for c, prop in sorted(p["to"]))
            rows.append(row("women-candidate", "", w, p["label"], wd(w),
                            "angle 4: a women's item points at a roster/tagged club",
                            kv(reaches_the_map="no (carries neither tag)", points=tos,
                               types=" | ".join(sorted(p["types"])), classes=" | ".join(sorted(p["classes"])))))
    return rows, notes


def women_angles(info, ctx):
    found = []
    for t in info["types"]:
        if WOMEN_WORDS.search(ctx["label"](t) or ""):
            found.append(f"angle 1: type {ctx['label'](t)!r}")
    for l in info["labels"]:
        if WOMEN_WORDS.search(l or ""):
            found.append(f"angle 2: label {l!r}")
            break
    if info["desc"] and WOMEN_WORDS.search(info["desc"]):
        found.append(f"angle 2: description {info['desc']!r}")
    for c in info["p2094"]:
        if WOMEN_WORDS.search(ctx["label"](c) or ""):
            found.append(f"angle 3: P2094 {ctx['label'](c)!r}")
    return found


def two_grounds_row(tier, q, label, info, ctx):
    parts = []
    for s in info["grounds_truthy"]:
        span = f" ({s['start'] or '?'}-{s['end'] or ''})" if s["start"] or s["end"] else ""
        parts.append(f"{ctx['ground_label'](s['value'])} {s['value']}{span}")
    return row("two-grounds", tier, q, label, wd(q),
               f"{len(info['grounds_truthy'])} truthy P115 at best rank: " + " | ".join(parts),
               "the club query keeps whichever row arrives first (the SC Freiburg shape); a hand row pins one")


# ======================================================== writing the files

def write_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(HEADER)
        for r in rows:
            w.writerow([r[h] for h in HEADER])


def md_table(headers, body):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for b in body:
        out.append("| " + " | ".join(one_line(c).replace("|", "\\|") for c in b) + " |")
    return out


def build_md(args, ctx, rows, notes, leagues, trap, box, proposals, fd, places, failures, counts):
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = [f"# Proposal for {args.country} ({box['label'] if box else args.country_qid})",
           "", f"Generated {today} by `tools/propose_country.py`. **Read-only evidence, not decisions**: "
           "nothing here was written to a hand-written file or a club file; a gap is a gap.", ""]
    if failures:
        out += ["## FAILURES (this proposal is incomplete)", ""] + [f"- {f}" for f in failures] + [""]
    out += ["## Summary", ""]
    out += md_table(["kind", "rows"], [(k, counts.get(k, 0)) for k in KINDS if counts.get(k)])
    out += ["", f"Tagged but dissolved (not drawn by the build, no row): {len(notes['dissolved_tagged'])}; "
            f"tagged extras whose tag is not truthy (not drawn, no row): {len(notes['hidden_extras'])}; "
            f"women's items pointing at a club, carrying neither tag: {notes['pointer_only']}.", ""]
    if ctx["gaps"]:
        out += [f"**Reader gaps: {len(ctx['gaps'])} roster row(s) the reader cannot read** (kind roster-unread).", ""]
    out += ["Step durations (s): " + ", ".join(f"{n} {d}" for n, d in STEPS), "", "## Leagues", ""]
    out += md_table(["tier", "article", "league item", "label", "found via", "P3983", "P17", "women-word check"],
                    [(t, a, q, l["label"], via, ",".join(l["p3983"]) or "none",
                      ",".join(f"{c} {ctx['label'](c)}" for c in l["p17"]) or "none",
                      "WORDS FOUND" if WOMEN_WORDS.search(" ".join(l["labels"] + [l["desc"] or ""])) else "none")
                     for t, a, q, l, via in leagues])
    out += ["", "P3983 and P17 are printed, not used: the country Q-id given on the command line is "
            f"`{args.country_qid}`.", ""]
    out += ["### Items labelled like a tier, or succeeded by it (the 'old Second Division' trap)", ""]
    if trap is None:
        out += ["The query failed; nothing is claimed.", ""]
    elif not trap:
        out += ["None found.", ""]
    else:
        out += md_table(["item", "label", "description", "clubs carrying it (any rank)", "dissolved", "succeeded by"],
                        [(x["qid"], x["label"], x["desc"] or "", x["clubs"], x["dissolved"] or "",
                          x["succeeded_by"] or "") for x in trap])
        out += ["", "Rows with clubs > 0 and a dissolution or successor are the trap: not to be mapped."]
    out += ["", "## Wiring patch (printed, not applied)", "", "### data/league-tiers.csv — append", "", "```"]
    for t, a, q, l, via in leagues:
        out.append(f"{q},{t},{l['label']},{args.country}")
    out += ["```", "", "### data/league-rosters.csv — append", "", "```"]
    for t, a, q, l, via in leagues:
        out.append(f"{q},{args.country},{t},{season_of(a)},{a},")
    out += ["```", "", "### COUNTRY_BOX (tools/fetch_clubs.py)", ""]
    if box:
        for name in ("north", "south", "east", "west"):
            out.append(f"- {name}: " + (", ".join(f"({v[0]}, {v[1]}) {rk}" for v, rk in box["edges"][name]) or "no point on the item"))
        for tag, b in proposals.items():
            out.append(f'- proposal from {tag}: `"{args.country}": {{"lat": {b["lat"]}, "lon": {b["lon"]}}},`')
        if any(rk == "preferred" for e in box["edges"].values() for _v, rk in e):
            out.append("- NOTE: some point is at preferred rank (an overseas territory or an island); "
                       "compare the two proposals and read the NL/PT comments in fetch_clubs.py.")
        spans = [b for b in proposals.values()]
        if any(b["lat"][1] - b["lat"][0] > 15 or b["lon"][1] - b["lon"][0] > 25 for b in spans):
            out.append("- NOTE: the box is large (an island or overseas territory is in the span).")
        outside = outside_box(ctx, proposals)
        if outside:
            out.append("- NOTE: clubs outside the best-rank proposal (island/overseas?): " + ", ".join(outside))
    out += ["", "### football-data.org code (candidates only)", ""]
    out += [f"- {c} — {n} ({src})" for c, n, src in fd] or ["- none found in the free-tier list or data/fixtures/index.json"]
    out += ["", "### Places to touch (with line numbers)", ""] + places
    out += ["", "### Stays manual", ""] + [f"- {s}" for s in STAYS_MANUAL]
    out += ["", "## Candidates", ""]
    for k in KINDS:
        rs = [r for r in rows if r["kind"] == k]
        if not rs:
            continue
        out += [f"### {k} ({len(rs)})", ""]
        out += md_table(["tier", "club", "label", "evidence", "detail"],
                        [(r["tier"], r["clubQid"], r["label"], r["evidenceText"][:160],
                          r["detail"][:260]) for r in rs])
        out.append("")
    out += ["## Appendix: tagged but dissolved (not drawn)", ""]
    out += [f"- {q} {l} (P576 {y})" for q, l, y in notes["dissolved_tagged"]] or ["- none"]
    out += ["", "## Appendix: tagged extras whose tag is not truthy (not drawn)", ""]
    out += [f"- {q} {l} (shape {s})" for q, l, s in notes["hidden_extras"]] or ["- none"]
    return "\n".join(out) + "\n"


def outside_box(ctx, proposals):
    if not proposals:
        return []
    b = next(iter(proposals.values()))
    out = []
    for q, info in ctx["infos"].items():
        if q not in {r["qid"] for r in ctx["roster"]}:
            continue
        pos = info["coord"] or ctx["ground_coord"](info)
        if pos and not (b["lat"][0] <= pos[0] <= b["lat"][1] and b["lon"][0] <= pos[1] <= b["lon"][1]):
            out.append(f"{info['label']} ({pos[0]:.2f}, {pos[1]:.2f})")
    return out


# ================================================================== main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--country", required=True, help="country code as the club files use it")
    ap.add_argument("--country-qid", required=True)
    ap.add_argument("--article", action="append", default=[], metavar="TIER=TITLE")
    ap.add_argument("--league", action="append", default=[], metavar="TIER=Q...",
                    help="name the league item when it cannot be found from the article")
    ap.add_argument("--langs", default="", help="extra label languages, comma separated")
    ap.add_argument("--out-dir", default="data/clubs")
    ap.add_argument("--write-partial", action="store_true",
                    help="write the files even after a failure (probes only)")
    ap.add_argument("--grounds", action="store_true", help="also propose grounds and capacities")
    args = ap.parse_args(argv)
    langs = [l.strip() for l in args.langs.split(",") if l.strip()]
    articles = []
    for a in args.article:
        t, _, title = a.partition("=")
        if not t.strip().isdigit() or not title.strip():
            ap.error(f"--article wants TIER=TITLE, got {a!r}")
        articles.append((int(t), title.strip()))
    if not articles:
        ap.error("at least one --article TIER=TITLE is needed")
    forced = {}
    for a in args.league:
        t, _, q = a.partition("=")
        forced[int(t)] = q.strip()
    failures = []
    began = time.time()

    with step("1 rosters"):
        records, gaps, pages, f = read_rosters(articles)
        failures += f
        print(f"    {len(records)} roster clubs, {len(gaps)} reader gap(s)")
        for g in gaps:
            print(f"    READER GAP tier {g[0]}: {g[2]!r}: {g[3]}")
    if not records:
        print("\nNo roster could be read: nothing to propose. FAILED.")
        return 1

    with step("2 leagues"):
        league_of = {}     # tier -> (qid, via)
        for tier, title in articles:
            if tier in forced:
                league_of[tier] = (forced[tier], "given with --league")
                continue
            if tier not in pages:
                continue
            q, via = find_league(tier, pages[tier][0], langs)
            if q:
                league_of[tier] = (q, via)
            else:
                failures.append(f"tier {tier}: {via}")
        tracked = {q: t for t, (q, _v) in league_of.items()}
        lfacts, f = league_facts(list(tracked), langs)
        failures += f
        for t, (q, via) in sorted(league_of.items()):
            lf = lfacts.get(q, {})
            print(f"    tier {t}: {q} {lf.get('label')} via {via}; P3983 {lf.get('p3983')}; P17 {lf.get('p17')}")
        tagged, error = tagged_items(tracked, langs)
        if error:
            failures.append(f"the list of tagged items failed: {error}")
            tagged = {}
        print(f"    {len(tagged)} items carry either league at any rank")
        redirect_titles = []
        for t, (q, _v) in league_of.items():
            en = lfacts.get(q, {}).get("sitelinks", {}).get("enwiki")
            if en:
                redirect_titles += redirects_to(en)
        trap, error = trap_items(tracked, lfacts, redirect_titles, langs)
        if error:
            failures.append(f"the same-label league query failed: {error}")
        if trap:
            for x in trap:
                print(f"    LEAGUE-LIKE ITEM {x['qid']} {x['label']}: {x['clubs']} clubs, "
                      f"dissolved {x['dissolved']}, succeeded by {x['succeeded_by']}")

    with step("3 items"):
        roster_q = {r["qid"] for r in records}
        want = sorted(roster_q | set(tagged))
        ents, f = fetch_entities(want, langs)
        failures += f
        infos = {q: summarize(e, tracked, langs) for q, e in ents.items()}
        print(f"    {len(infos)} items read of {len(want)} wanted")
        # grounds and labels the rows need
        ground_qs = {s["value"] for i in infos.values() for s in i["grounds_all"] if s["value"]}
        ground_ents, f = fetch_entities(ground_qs, langs, props="claims|labels")
        failures += f
        label_qs = set()
        for i in infos.values():
            label_qs.update(i["types"] + i["p2094"] + i["p17"])
        for l in lfacts.values():
            label_qs.update(l["p17"] + l["types"] + l["p1366"])
        label_qs -= set(infos) | set(ground_ents) | set(tracked)
        lab_ents, f = fetch_entities(label_qs, langs, props="labels")
        failures += f
        label_cache = {}
        for pool in (ents, ground_ents, lab_ents, {}):
            for q, e in pool.items():
                label_cache[q] = labels_of(e, langs)[0]

    # the cross-check against diagnose_p118_rank's own queries (hidden / stale-preferred)
    with step("4 rank cross-check"):
        values = " ".join(f"wd:{q}" for q in tracked)
        inlist = ", ".join(f"wd:{q}" for q in tracked)
        hidden_rows, e1 = sparql(dg.QUERY_HIDDEN % {"leagues": values}, "diagnose: hidden")
        stale_rows, e2 = sparql(dg.QUERY_STALE_PREFERRED % {"leagues": values, "inlist": inlist},
                                "diagnose: stale preferred")
        for e in (e1, e2):
            if e:
                failures.append(f"rank cross-check query failed: {e}")
        mine_ab = {q for q, i in infos.items() if rank_shape(i) in ("A", "B")}
        mine_c = {q for q, i in infos.items() if rank_shape(i) == "C"}
        theirs_ab = {qid_of(bval(r, "club")) for r in (hidden_rows or [])}
        theirs_c = {qid_of(bval(r, "club")) for r in (stale_rows or [])}
        for name, a, b in (("A/B", mine_ab, theirs_ab), ("C", mine_c, theirs_c)):
            print(f"    shape {name}: from claims {len(a)}, from diagnose_p118_rank's query {len(b)}"
                  + ("" if a == b else f"  DIFFER: only claims {sorted(a - b)}, only query {sorted(b - a)}"))

    with step("5 evidence for extras"):
        ctx_tmp = {"infos": infos}
        extra_qs = [q for q in tagged if q not in roster_q and q in infos and infos[q]["tier"] is not None
                    and not infos[q]["dissolved"]]
        intro = intro_sentences({q: infos[q] for q in extra_qs}, langs)
        titles = {}
        for tier, (real, page) in pages.items():
            for t, texts in team_change_links(page).items():
                for text in texts[:2]:
                    titles.setdefault(t, []).append((real, text))
        tc_found, f = cr.qids_for_titles(list(titles)) if titles else ({}, [])
        failures += f
        team_changes_by_q = {}
        for t, hits in titles.items():
            if tc_found.get(t):
                team_changes_by_q.setdefault(tc_found[t], []).extend(hits)
        pointers, error = pointers_at(roster_q | set(tagged), langs)
        if error:
            failures.append(f"the women's-pointer query failed: {error}")

    ground_by_q = {q: (labels_of(e, langs)[0],
                       next((s["value"] for s in statements(e, "P625") if s["value"]), None))
                   for q, e in ground_ents.items()}

    def lab(q):
        return label_cache.get(q, q)

    def ground_coord(info):
        for s in info["grounds_truthy"] or info["grounds_all"]:
            c = ground_by_q.get(s["value"], (None, None))[1]
            if c:
                return c
        return None

    ctx = {"country_qid": args.country_qid, "tracked": tracked, "roster": records, "gaps": gaps,
           "infos": infos, "tagged": tagged, "label": lab, "ground_coord": ground_coord,
           "league_label": lambda q: lfacts.get(q, {}).get("label") or lab(q),
           "ground_label": lambda q: ground_by_q.get(q, (q, None))[0],
           "intro": intro, "team_changes": team_changes_by_q, "pointers": pointers or {}}

    with step("6 candidates"):
        rows, notes = classify(ctx)
        if args.grounds:
            import propose_grounds                  # PR 2
            rows += propose_grounds.propose(args, ctx, langs)
        counts = {}
        for r in rows:
            counts[r["kind"]] = counts.get(r["kind"], 0) + 1

    with step("7 wiring patch"):
        box, f = country_box(args.country_qid, langs)
        failures += f
        proposals = propose_box(box) if box else {}
        league_labels = [lfacts[q]["label"] for q in tracked if q in lfacts]
        fd = football_data_candidates(box["label"] if box else args.country, league_labels)
        places = places_to_touch(args.country, args.country_qid)
        leagues = [(t, pages[t][0] if t in pages else dict(articles).get(t, ""), q,
                    lfacts.get(q, {"label": q, "p3983": [], "p17": [], "labels": [], "desc": None}), via)
                   for t, (q, via) in sorted(league_of.items())]

    md = build_md(args, ctx, rows, notes, leagues, trap, box, proposals, fd, places, failures, counts)

    print("\n" + "=" * 70)
    print(f"SUMMARY {args.country}: {len(records)} roster clubs, {len(tagged)} tagged items, "
          f"{len(infos)} read")
    for k in KINDS:
        if counts.get(k):
            print(f"  {k:<18} {counts[k]}")
    print(f"  dissolved-tagged (no row) {len(notes['dissolved_tagged'])}; hidden extras (no row) "
          f"{len(notes['hidden_extras'])}; reader gaps {len(gaps)}")
    print("  steps: " + ", ".join(f"{n} {d}s" for n, d in STEPS))
    print(f"  wall clock {round(time.time() - began)} s")
    if failures:
        print("FAILURES:")
        for x in failures:
            print(f"  - {x}")

    if failures and not args.write_partial:
        print("\nNOT WRITTEN: the proposal is incomplete (a failed fetch is not an empty answer).")
        return 1
    os.makedirs(args.out_dir, exist_ok=True)
    csv_path = os.path.join(args.out_dir, f"proposal-{args.country}.csv")
    md_path = os.path.join(args.out_dir, f"proposal-{args.country}.md")
    write_csv(csv_path, rows)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\nwrote {csv_path} ({len(rows)} rows) and {md_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
