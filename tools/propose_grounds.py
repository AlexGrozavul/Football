#!/usr/bin/env python3
"""
propose_grounds.py -- the ground and capacity half of propose_country.py
(`--grounds`). Not run on its own: propose_country.py imports it and passes
itself in (`pc`), so the HTTP politeness (User-Agent, maxlag, one request a
second per host, Retry-After, four tries) and the per-host clock are shared.

For every roster club it reads, and proposes nothing it cannot show:

  (a) the ground the season table gives, and the club's own English article's
      infobox ground;
  (b) the ground item of Wikidata (P115 at best rank, several truthy flagged)
      with its P625, labels, aliases and P1083;
  (c) OpenStreetMap elements named like the ground once legal-form and
      stadium words are set aside - leisure=stadium, leisure=sports_centre, or
      a pitch with sport=soccer - within 3 km of the club's best position,
      asked of the public Overpass API (see OVERPASS BELOW);
  (d) the distances between (b), the ground's English article and (c);
  (e) capacity figures: the table's, Wikidata's, OpenStreetMap's, StadiumDB's
      (crosscheck_stadiumdb.py's parser and matching signals, imported),
      and the UTA Arad rule applied mechanically.

Two kinds of row: ground-proposal and capacity-proposal, one per roster club.
The first word of the detail is the verdict. NOTHING IS WRITTEN ANYWHERE BUT
THE PROPOSAL FILES.

OVERPASS: THE PUBLISHED USAGE POLICY GOVERNS, NOT robots.txt (Alexandru, 2026-10-21)

  https://overpass-api.de/api/interpreter is a documented public API, and the
  operator's documentation tells users to send queries there, although its
  robots.txt disallows /api/ for every agent (a file written for crawlers). So
  this tool follows the published policy: the User-Agent of every other request
  of this tool; ONE request at a time (the loop is sequential); a wait of at
  least 30 s and a retry on HTTP 429 and 504 and, as crosscheck_capacity.py and
  propose_coordinates.py already do, on 502 and 503 (the decision named 429 and
  504; the first live run died on a 502 at its first request, and 5 of the 18
  requests of the last capacity run were 502; a read timeout counts as a 504 -
  anything else, and any other network error, is a failure reported in the row,
  not retried); a failure of the whole OpenStreetMap step does NOT discard the
  proposal: every row says "osm=asked and failed: <reason>", the .md and the log
  say so loudly, and the rest of the evidence is written (OpenStreetMap is a
  supplement, a flaky third party must not take the other sources with it);
  at most 60 requests
  per run (OVERPASS_MAX_REQUESTS, retries included; the run says how many it
  used); and never more than the regular-use guideline of the operator per day
  (about 100 queries and 10 MB; CLAUDE.md, Known open problems, has the count
  of every workflow). robots.txt IS still read first for every other
  non-Wikimedia host (StadiumDB).

THE RULES IT APPLIES (CLAUDE.md, the place-clubs passes)

  A ground is named by two independent places for 2026-27 (the season table,
  the club's own article, Wikidata, StadiumDB); where the names differ, a
  Wikidata alias that equals the table's name is the proof they are one
  ground. A coordinate needs ONE ground-specific source: the ground's own
  Wikipedia article, the ground's Wikidata P625 (only when its name agrees
  with the table's), or an OpenStreetMap element whose name equals the
  ground's. Two sources must agree within 150 m; a position on one source
  says so. An unnamed pitch is never a source.

  A capacity is proposed only where two INDEPENDENT sources agree within 5%.
  The league table and Wikidata are Wikipedia's and count as ONE source
  (CLAUDE.md, Casa Pia: "7,000 appears only in Wikipedia and Wikidata (one
  source)"); StadiumDB and OpenStreetMap are one source each. With no such
  agreement the cell is blank and every figure is listed (contested). The
  map's figure is what the build would show: Wikidata's P1083 on the P115
  ground. Of two agreeing figures the league table's is taken, else
  StadiumDB's, else Wikidata's, else OpenStreetMap's.
"""

import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import crosscheck_stadiumdb as sdb

OVERPASS = "https://overpass-api.de/api/interpreter"
OVERPASS_MAX_REQUESTS = 60          # per run, retries included (Alexandru, 2026-10-21)
OVERPASS_BUSY_CODES = (429, 502, 503, 504)   # busy answers: wait and retry (502/503 as the older tools do)
OVERPASS_WAIT_S = 30                # the operator: pause 30 s after a 429; doubles over the tries (30, 60, 120 s ...)
OVERPASS_MAX_TRIES = 6              # per request; the server's own 502 text asks for exponential backoff
OVERPASS_MAX_WAIT_S = 120
OVERPASS_TIMEOUT_S = 200            # the query says [timeout:180]
OVERPASS_CENTRES_PER_REQUEST = 20   # club positions per request (a smaller request costs less when it is lost)
_overpass_used = [0]                # requests made this run, retries included
RADIUS_M = 3000
AGREE_M = 150
AGREE_PCT = sdb.AGREE_WITHIN

# IOC / FIFA-style three-letter codes for European countries: the candidates
# StadiumDB's slug is probed from, after the first three letters of the
# country's English name and its two-letter code. A wrong guess is a 404, so
# the slug is never assumed (CLAUDE.md: "a wrong guess looks exactly like a
# country with no grounds in it").
IOC = {"AL": "alb", "AD": "and", "AM": "arm", "AT": "aut", "AZ": "aze", "BY": "blr", "BE": "bel",
       "BA": "bih", "BG": "bul", "HR": "cro", "CY": "cyp", "CZ": "cze", "DK": "den", "EE": "est",
       "FI": "fin", "FR": "fra", "GE": "geo", "DE": "ger", "GB": "eng", "GR": "gre", "HU": "hun",
       "IS": "isl", "IE": "irl", "IT": "ita", "XK": "kos", "LV": "lat", "LI": "lie", "LT": "ltu",
       "LU": "lux", "MT": "mlt", "MD": "mda", "ME": "mne", "NL": "ned", "MK": "mkd", "NO": "nor",
       "PL": "pol", "PT": "por", "RO": "rou", "RU": "rus", "SM": "smr", "RS": "ser", "SK": "svk",
       "SI": "slo", "ES": "esp", "SE": "swe", "CH": "sui", "TR": "tur", "UA": "ukr"}

# Words that say what kind of club or place a name is, not which one: the
# union of the StadiumDB matcher's two lists and the stadium words of the
# languages the project has met. Digits are kept ("Estadio 1 de Maio").
SET_ASIDE = set(sdb.CLUB_FORMS) | set(sdb.GROUND_FORMS) | {
    "clube", "club", "clubes", "futebol", "football", "soccer", "sad", "sporting", "desportivo",
    "desportiva", "desportos", "estadio", "complexo", "campo", "campos", "do", "da", "de", "dos",
    "das", "e", "the", "of", "a", "o", "os", "as", "sports", "centre", "center", "centro",
    "complex", "terrain", "stade", "stadionul", "municipale", "municipal", "comunal", "comunale",
    "youth", "academy", "academia", "cidade", "ciudad", "city", "nacional", "national", "b", "ii",
    "pitch", "field", "ground", "grounds", "est", "estadi"}


# =========================================================== pure helpers

def haversine_m(a, b):
    """Metres between two (lat, lon) points."""
    (la1, lo1), (la2, lo2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = p2 - p1, math.radians(lo2 - lo1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def clean_ground(text):
    """A table's ground cell without footnote marks and the ', at Town' tail."""
    if not text:
        return ""
    text = re.sub(r"\[[^\]]{0,6}\]", "", text)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r",\s*at\s+.*$", "", text)
    return re.sub(r"\s+", " ", text).strip()


NUMBER_MARK = re.compile(r"\bn\s*\.?\s*[°º]?\s*\d+\b", re.IGNORECASE)


def core(name):
    """The words that say WHICH ground a name is. A pitch number ("Campo n.° 1")
    says which pitch of a complex, not which ground, and is set aside."""
    return [w for w in sdb.words(NUMBER_MARK.sub(" ", name or "")) if w not in SET_ASIDE]


def name_strength(a, b, club_words=()):
    """exact / contained / None between two ground names, with the words that
    only say what kind of place it is set aside - and the club's own name
    words too: "Benfica Campus" and "Benfica Stadium" share only the club,
    which says nothing about the ground. Exact equality is tried first,
    before the club's words are dropped."""
    ca, cb = core(a), core(b)
    if not ca or not cb:
        return None
    if set(ca) == set(cb) or "".join(ca) == "".join(cb):
        return "exact"
    drop = set(club_words)
    ca, cb = [w for w in ca if w not in drop], [w for w in cb if w not in drop]
    if not ca or not cb:
        return None
    if set(ca) == set(cb):
        return "exact"
    if set(ca) <= set(cb) or set(cb) <= set(ca):
        return "contained"
    return None


def best_strength(name, others, club_words=()):
    """The strongest of name_strength over several names, with the one that gave it."""
    order = {"exact": 2, "contained": 1}
    best = (None, None)
    for o in others:
        s = name_strength(name, o, club_words)
        if s and order[s] > order.get(best[0], 0):
            best = (s, o)
    return best


def within(a, b, pct=AGREE_PCT):
    return abs(a - b) / max(a, b) <= pct


def capacity_rule(table, wikidata, osm, stadiumdb):
    """
    The UTA Arad rule, mechanically. Each argument is an int or None.
    Returns (verdict, proposed, taken_from, note):
      verdict   agreed | contested | single-source | none
      proposed  the figure, or None (blank)
      taken_from  which source's figure is proposed
    Independent groups: Wikipedia (the table AND Wikidata), StadiumDB, OSM.
    """
    groups = {"wikipedia": [("table", table), ("wikidata", wikidata)],
              "stadiumdb": [("stadiumdb", stadiumdb)], "osm": [("osm", osm)]}
    have = {g: [(s, v) for s, v in members if v] for g, members in groups.items()}
    have = {g: m for g, m in have.items() if m}
    if not have:
        return "none", None, None, "no source has a figure"
    best = None
    names = list(have)
    for i, g1 in enumerate(names):
        for g2 in names[i + 1:]:
            for s1, v1 in have[g1]:
                for s2, v2 in have[g2]:
                    if within(v1, v2):
                        cluster = {s1: v1, s2: v2}
                        for g3 in names:
                            for s3, v3 in have[g3]:
                                if s3 not in cluster and within(v3, v1) and within(v3, v2):
                                    cluster[s3] = v3
                        if best is None or len(cluster) > len(best):
                            best = cluster
    if best:
        for pick in ("table", "stadiumdb", "wikidata", "osm"):
            if pick in best:
                others = ", ".join(f"{s} {v}" for s, v in best.items() if s != pick)
                return "agreed", best[pick], pick, f"{pick} {best[pick]} agrees within 5% with {others}"
    if len(have) == 1:
        only = ", ".join(f"{s} {v}" for g in have.values() for s, v in g)
        return "single-source", None, None, (
            f"one independent source only ({only}); the table and Wikidata are both Wikipedia's")
    return "contested", None, None, "no two independent sources agree within 5%"


def cr_markers(name):
    """The reserve-side marker words of a team name (II, B, U23, Jong ...)."""
    return {w for w in sdb.words(name) if w in sdb.TEAM_MARKERS}


def pick_centre(candidates):
    """The first available (label, (lat, lon)) of an ordered list."""
    for label, pos in candidates:
        if pos:
            return label, pos
    return None, None


# ============================================================= network

def robots_allows(pc, base, path):
    """robots.txt of a non-Wikimedia host, read before any request to it. 404
    means no rules; any other failure is a stop. Returns (ok, text)."""
    body, error = fetch_text(pc, base + "/robots.txt", "robots.txt")
    if error and "404" in error:
        return True, f"{base}/robots.txt: 404, no rules"
    if error:
        return False, f"{base}/robots.txt could not be read ({error}): treated as a stop"
    disallow, applies = [], False
    for line in body.splitlines():
        line = line.split("#")[0].strip()
        if line.lower().startswith("user-agent:"):
            applies = line.split(":", 1)[1].strip() == "*"
        elif applies and line.lower().startswith("disallow:"):
            rule = line.split(":", 1)[1].strip()
            if rule:
                disallow.append(rule)
    blocked = [r for r in disallow if path.startswith(r)]
    if blocked:
        return False, f"{base}/robots.txt disallows {blocked} for {path}"
    return True, f"{base}/robots.txt read ({len(disallow)} disallow rule(s)); {path} is allowed"


def fetch_text(pc, url, what, data=None, headers=None):
    """Like pc.fetch_json, for a page that is not JSON: (text, None) or (None, reason)."""
    import time
    import urllib.error
    import urllib.request
    host = urllib.parse.urlsplit(url).netloc
    reason = "no attempt"
    for attempt in range(1, pc.MAX_TRIES + 1):
        pc._wait(host)
        req = urllib.request.Request(url, data=data, headers={"User-Agent": pc.UA, **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=pc.TIMEOUT) as resp:
                return resp.read().decode("utf-8", "replace"), None
        except urllib.error.HTTPError as exc:
            reason = f"HTTP {exc.code}"
            if exc.code in (429, 500, 502, 503, 504) and attempt < pc.MAX_TRIES:
                wait = min(pc._retry_after(exc.headers) or 15 * attempt, 120)
                print(f"    {what}: {reason}, waiting {wait}s (try {attempt}/{pc.MAX_TRIES})")
                time.sleep(wait)
                continue
            return None, reason
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            reason = f"network error: {getattr(exc, 'reason', exc)}"
            if attempt < pc.MAX_TRIES:
                print(f"    {what}: {reason}, retrying (try {attempt}/{pc.MAX_TRIES})")
                time.sleep(10 * attempt)
                continue
            return None, reason
    return None, f"gave up after {pc.MAX_TRIES} tries ({reason})"


def article_coordinates(pc, titles):
    """{title as given: (lat, lon)} from the English Wikipedia's primary
    coordinates of the ground articles."""
    out = {}
    titles = sorted(set(t for t in titles if t))
    for start in range(0, len(titles), 40):
        batch = titles[start:start + 40]
        query = urllib.parse.urlencode({
            "action": "query", "prop": "coordinates", "coprimary": "primary", "colimit": "max",
            "redirects": "1", "titles": "|".join(batch), "format": "json", "formatversion": "2"})
        data, error = pc.fetch_json(f"{pc.WP_API}?{query}", "ground article coordinates")
        if error or not data:
            continue
        q = data.get("query") or {}
        moved = {}
        for key in ("normalized", "redirects"):
            for r in q.get(key) or []:
                moved[r["from"]] = r["to"]
        by_title = {}
        for p in q.get("pages") or []:
            if p.get("coordinates"):
                c = p["coordinates"][0]
                by_title[p["title"]] = (c["lat"], c["lon"])
        for t in batch:
            end = t
            for _ in range(3):
                end = moved.get(end, end)
            if end in by_title:
                out[t] = by_title[end]
    return out


def club_infobox_grounds(pc, titles):
    """{club article title: ground text} from the infobox of each club's English
    article (the `ground` / `stadium` parameter, links resolved to their text)."""
    out = {}
    titles = sorted(set(t for t in titles if t))
    for start in range(0, len(titles), 40):
        batch = titles[start:start + 40]
        query = urllib.parse.urlencode({
            "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "rvsection": "0", "redirects": "1", "titles": "|".join(batch),
            "format": "json", "formatversion": "2"})
        data, error = pc.fetch_json(f"{pc.WP_API}?{query}", "club infoboxes")
        if error or not data:
            continue
        q = data.get("query") or {}
        moved = {}
        for key in ("normalized", "redirects"):
            for r in q.get(key) or []:
                moved[r["from"]] = r["to"]
        text_by_title = {}
        for p in q.get("pages") or []:
            revs = p.get("revisions") or []
            if revs:
                text_by_title[p["title"]] = ((revs[0].get("slots") or {}).get("main") or {}).get("content", "")
        for t in batch:
            end = t
            for _ in range(3):
                end = moved.get(end, end)
            text = text_by_title.get(end, "")
            m = re.search(r"\|\s*(?:ground|stadium)\s*=\s*([^\n|]+)", text)
            if m:
                value = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", m.group(1))
                value = re.sub(r"<[^>]+>|\{\{[^}]*\}\}", " ", value)
                value = re.sub(r"\s+", " ", value).strip(" ,;")
                if value:
                    out[t] = value
    return out


def ground_search(pc, wanted, langs, club_words_of):
    """The Wikidata items labelled like a ground, found by searching for its
    name - the route the hand rows used when the club has no P115 (Alverca:
    'the ground's own Wikidata item'). wanted: [(club qid, ground name)].
    Only an item whose label EQUALS the ground's name (club words and stadium
    words set aside) with a P625 counts. {club qid: [{qid,label,coord,cap}]}"""
    found = {}
    for club_q, name in wanted:
        if not name:
            continue
        query = urllib.parse.urlencode({
            "action": "wbsearchentities", "search": name, "language": "en",
            "uselang": "en", "type": "item", "limit": "7", "format": "json"})
        data, error = pc.fetch_json(f"{pc.WD_API}?{query}", "search the ground's name")
        if error or not data:
            continue
        for hit in data.get("search") or []:
            label = hit.get("label") or ""
            if name_strength(name, label, club_words_of[club_q]) == "exact":
                found.setdefault(club_q, []).append(hit["id"])
    qids = sorted({q for qs in found.values() for q in qs})
    ents, _f = pc.fetch_entities(qids, langs, props="claims|labels|descriptions") if qids else ({}, [])
    out = {}
    for club_q, qs in found.items():
        for q in qs:
            e = ents.get(q)
            if not e:
                continue
            coords = [x["value"] for x in pc.statements(e, "P625") if x["value"]]
            caps = [x["value"] for x in pc.truthy(pc.statements(e, "P1083")) if x["value"]]
            if coords:
                out.setdefault(club_q, []).append({
                    "qid": q, "label": pc.labels_of(e, langs)[0], "coord": coords[0],
                    "cap": caps[0] if caps else None,
                    "desc": ((e.get("descriptions") or {}).get("en") or {}).get("value")})
    return out


def overpass_wait(attempt, retry_after=0):
    """Seconds to wait after try number `attempt`: 30, 60, 120, 120 ... (exponential backoff,
    which is what the server's own '502 ... at capacity' page asks for), or Retry-After."""
    return min(max(retry_after, OVERPASS_WAIT_S * 2 ** (attempt - 1)), OVERPASS_MAX_WAIT_S)


def overpass_post(pc, body):
    """One POST to Overpass: (text, None) or (None, reason). One request at a time; a busy
    answer (429, 502, 503, 504, or a read timeout) waits (overpass_wait) and asks again, up to
    OVERPASS_MAX_TRIES; every request, retries included, counts against OVERPASS_MAX_REQUESTS."""
    reason = "no attempt"
    for attempt in range(1, OVERPASS_MAX_TRIES + 1):
        if _overpass_used[0] >= OVERPASS_MAX_REQUESTS:
            return None, f"the cap of {OVERPASS_MAX_REQUESTS} Overpass requests per run was reached"
        pc._wait("overpass-api.de")
        _overpass_used[0] += 1
        req = urllib.request.Request(OVERPASS, data=body, headers={
            "User-Agent": pc.UA, "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=OVERPASS_TIMEOUT_S) as resp:
                return resp.read().decode("utf-8", "replace"), None
        except urllib.error.HTTPError as exc:
            reason = f"HTTP {exc.code}"
            if exc.code in OVERPASS_BUSY_CODES and attempt < OVERPASS_MAX_TRIES:
                wait = overpass_wait(attempt, pc._retry_after(exc.headers))
                print(f"    Overpass: {reason}, waiting {wait}s (try {attempt}/{OVERPASS_MAX_TRIES})")
                time.sleep(wait)
                continue
            return None, reason
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            # A read timeout is what a gateway timeout (504) looks like from the client:
            # Overpass held the request in its queue. It waits and retries like a 504; any
            # other network error (DNS, refused, reset) is a failure, not retried.
            reason = f"network error: {getattr(exc, 'reason', exc)}"
            if "timed out" in str(reason).lower() and attempt < OVERPASS_MAX_TRIES:
                wait = overpass_wait(attempt)
                print(f"    Overpass: {reason}, waiting {wait}s (try {attempt}/{OVERPASS_MAX_TRIES})")
                time.sleep(wait)
                continue
            return None, reason
    return None, f"gave up after {OVERPASS_MAX_TRIES} tries ({reason})"


def overpass_elements(pc, centres):
    """Overpass requests for every centre (OVERPASS_CENTRES_PER_REQUEST at a
    time): named stadiums, sports centres and soccer pitches within RADIUS_M
    of it. ({(type, id): element}, None) or (None, reason); one failed
    request fails the whole step, a partial map is not a map."""
    uniq = list(dict.fromkeys((round(lat, 6), round(lon, 6)) for lat, lon in centres))
    out = {}
    for i in range(0, len(uniq), OVERPASS_CENTRES_PER_REQUEST):
        parts = []
        for lat, lon in uniq[i:i + OVERPASS_CENTRES_PER_REQUEST]:
            around = f"(around:{RADIUS_M},{lat:.6f},{lon:.6f})"
            parts.append(f'nwr{around}["name"]["leisure"~"^(stadium|sports_centre)$"];')
            parts.append(f'nwr{around}["name"]["leisure"="pitch"]["sport"~"soccer|football"];')
        query = "[out:json][timeout:180];(" + "".join(parts) + ");out tags center;"
        text, error = overpass_post(pc, urllib.parse.urlencode({"data": query}).encode("utf-8"))
        if error:
            return None, error
        try:
            data = json.loads(text)
        except ValueError:
            return None, "Overpass answered with something that is not JSON (a busy-server page?)"
        if data.get("remark") and "error" in str(data["remark"]).lower():
            return None, f"Overpass remark: {data['remark']}"
        for e in data.get("elements") or []:
            pos = (e.get("lat"), e.get("lon")) if e.get("type") == "node" else \
                ((e.get("center") or {}).get("lat"), (e.get("center") or {}).get("lon"))
            if pos[0] is None:
                continue
            out[(e["type"], e["id"])] = {"ref": f"{e['type']}/{e['id']}", "pos": pos,
                                         "tags": e.get("tags") or {}}
    return out, None


def stadiumdb_grounds(pc, args, country_label, probe):
    """The country's StadiumDB page, as crosscheck_stadiumdb.parse_country_table
    reads it. The slug is the configured one unless `probe`; probing tries the
    first three letters of the country's name, its two-letter code and its IOC
    code, and says which answered a table. Returns (grounds, slug, notes, failures)."""
    notes, failures = [], []
    ok, robots = robots_allows(pc, sdb.BASE, "/stadiums/")
    notes.append(robots)
    if not ok:
        return [], None, notes, [robots]
    candidates = []
    if not probe and args.country in sdb.COUNTRY_PAGES:
        candidates.append(sdb.COUNTRY_PAGES[args.country][0])
    else:
        name = re.sub(r"[^a-z]", "", (country_label or "").lower())
        for c in [name[:3], args.country.lower(), IOC.get(args.country, "")]:
            if c and c not in candidates:
                candidates.append(c)
    tried = []
    for slug in candidates:
        body, error = fetch_text(pc, f"{sdb.BASE}/stadiums/{slug}", f"StadiumDB /stadiums/{slug}")
        tried.append(f"{slug}: {error or 'answered'}")
        if error:
            continue
        grounds = sdb.parse_country_table(body)
        if grounds:
            notes.append(f"StadiumDB slug {slug!r} answered a table of {len(grounds)} grounds "
                         f"({sum(1 for g in grounds if g['capacity'])} with a capacity); tried: "
                         + "; ".join(tried)
                         + ("" if probe or args.country not in sdb.COUNTRY_PAGES
                            else " (configured in crosscheck_stadiumdb.COUNTRY_PAGES)"))
            return grounds, slug, notes, failures
        tried[-1] = f"{slug}: answered but no table rows parsed"
    notes.append("no StadiumDB page answered a table; tried: " + "; ".join(tried))
    return [], None, notes, failures


# ============================================================ the proposal

def match_stadiumdb(label, venue, grounds):
    """crosscheck_stadiumdb's own signals, per club: the ground, or 'ambiguous',
    or None. Returns (ground dict | None, note)."""
    town_words = set()
    for gr in grounds:
        town_words.update(w for w in sdb.words(gr["city"]) if w not in sdb.GROUND_FORMS)
    club = {"name": label, "venue": venue}
    hits = []
    for gr in grounds:
        for their in gr["clubs"]:
            sig = sdb.club_signal(label, their, town_words)
            if sig and sdb.place_signal(club, gr, town_words):
                hits.append((sig, their, gr))
                break
    if not hits:
        return None, "no StadiumDB ground carries this club's name"
    if len(hits) > 1:
        narrowed = [h for h in hits if sdb.ground_signal(venue, h[2]["name"]) is True]
        if len(narrowed) != 1:
            return None, "ambiguous: " + "; ".join(f"{h[2]['name']} ({h[2]['city']})" for h in hits[:4])
        hits = narrowed
    sig, their, gr = hits[0]
    return gr, f"{sig} via {their!r}"


def propose(pc, args, ctx, langs, failures):
    """The rows of kinds ground-proposal and capacity-proposal, one pair per
    roster club; sets ctx['grounds_md'] with the read-back."""
    infos, roster = ctx["infos"], ctx["roster"]
    twin_of = ctx.get("twin_of", {})
    md = []

    # --- Wikidata ground items (P115 of the club, or of its men's team item)
    def src_of(rec):
        info = infos.get(rec["qid"])
        twin = twin_of.get(rec["qid"])
        if info and not info["grounds_all"] and twin and twin in infos:
            return infos[twin]
        return info

    ground_qs = set()
    for rec in roster:
        src = src_of(rec)
        if src:
            ground_qs.update(s["value"] for s in src["grounds_all"] if s["value"])
    gents, f = pc.fetch_entities(ground_qs, langs, props="claims|labels|aliases")
    failures += f
    gdata = {}
    for q, e in gents.items():
        aliases = []
        for lang_aliases in (e.get("aliases") or {}).values():
            for a in lang_aliases if isinstance(lang_aliases, list) else []:
                aliases.append(a.get("value") if isinstance(a, dict) else a)
        caps = pc.truthy(pc.statements(e, "P1083"))
        coords = [s["value"] for s in pc.statements(e, "P625") if s["value"]]
        gdata[q] = {"qid": q, "label": pc.labels_of(e, langs)[0], "labels": pc.labels_of(e, langs),
                    "aliases": [a for a in aliases if a], "coord": coords[0] if coords else None,
                    "capacities": [s["value"] for s in caps if s["value"]]}

    # --- the grounds' own English articles, and the clubs' infoboxes
    article_pos = article_coordinates(pc, [r["ground_title"] for r in roster])
    infobox = club_infobox_grounds(pc, [r["title"] for r in roster])

    # --- the best position of each club, for the OpenStreetMap search
    def wd_ground(rec):
        src = src_of(rec)
        gs = [s["value"] for s in (src["grounds_truthy"] if src else [])]
        return [gdata[g] for g in gs if g in gdata]

    # Every position that could be the ground, the table's ground first: a
    # Wikidata ground is only the table's ground if its name agrees with it,
    # so when it does not, the search is centred on the ground's own article
    # first (Farense: Wikidata names the Estadio Algarve, the table Sao Luis).
    centres, centre_of, need_search = [], {}, {}
    for rec in roster:
        src = src_of(rec)
        wg = wd_ground(rec)
        table_ground = clean_ground(rec["ground"])
        wd_names = [n for g in wg for n in g["labels"] + g["aliases"]]
        cw = set(sdb.words(src["label"])) | set(sdb.words(rec["team"]))
        wd_same = bool(wg) and best_strength(table_ground, wd_names, cw)[0] is not None
        need_search[rec["qid"]] = (not wd_same and not article_pos.get(rec["ground_title"]), table_ground, cw)
        wd_pos = ("Wikidata ground P625" + ("" if wd_same else " (a ground whose name differs)"),
                  wg[0]["coord"] if wg else None)
        art_pos = ("the ground's English article", article_pos.get(rec["ground_title"]))
        club_pos = ("the club's P625", src["coord"] if src else None)
        ordered = [wd_pos, art_pos, club_pos] if wd_same else [art_pos, wd_pos, club_pos]
        found = []
        for label, pos in ordered:
            if pos and all(haversine_m(pos, q) > 100 for _l, q in found):
                found.append((label, pos))
        centre_of[rec["qid"]] = found
        centres.extend(pos for _l, pos in found)
    # a ground nothing else gave a position for: look for its own Wikidata item by name
    wanted = [(q, name) for q, (need, name, _cw) in need_search.items() if need]
    search_hits = ground_search(pc, wanted, langs, {q: cw for q, (_n, _g, cw) in need_search.items()}) if wanted else {}
    for q, hits in search_hits.items():
        for h in hits:
            centres.append(h["coord"])
            centre_of[q] = centre_of.get(q, []) + [(f"Wikidata item {h['qid']} found by name", h["coord"])]
    md.append(f"- Wikidata name search for {len(wanted)} ground(s) with no other position: "
              f"{sum(1 for q in search_hits)} found an item with a position")

    # Overpass: the published usage policy governs, not robots.txt (module docstring);
    # robots.txt is still read for every other non-Wikimedia host (StadiumDB, below).
    osm, osm_status = {}, "not queried: no club position to search around"
    if centres:
        osm, error = overpass_elements(pc, centres)
        if error:
            # Not a run failure (module docstring): said in the log, the .md and every row.
            osm, osm_status = {}, f"asked and failed: {error}"
            print(f"    WARNING: OpenStreetMap (Overpass) did not answer ({error}); the proposal is "
                  f"written WITHOUT it and every row says so")
            md.append(f"- **WARNING: OpenStreetMap (Overpass) did not answer ({error}). The grounds below "
                      f"were proposed WITHOUT it; run the tool again to ask it.**")
        else:
            osm_status = "queried"
    md.append(f"- OpenStreetMap: {osm_status}" + (f"; {len(osm)} named stadium / sports centre / "
              f"soccer pitch elements within {RADIUS_M} m of {len(centres)} club position(s)" if osm_status == "queried" else "")
              + f" [Overpass requests this run: {_overpass_used[0]} of the cap {OVERPASS_MAX_REQUESTS}]")

    # --- StadiumDB
    country_label = ctx.get("country_label") or args.country
    sgrounds, slug, notes, f = stadiumdb_grounds(pc, args, country_label, getattr(args, "probe_slug", False))
    failures += f
    md += [f"- {n}" for n in notes]

    # grounds shared by several roster clubs (a copied first-team ground?)
    shared = {}
    for rec in roster:
        for g in wd_ground(rec):
            shared.setdefault(g["qid"], []).append(rec["team"])

    rows, attention = [], []
    for rec in roster:
        q, tier, team = rec["qid"], rec["tier"], rec["team"]
        src = src_of(rec)
        if not src:
            continue
        table_ground = clean_ground(rec["ground"])
        wg = wd_ground(rec)
        wd_names = [n for g in wg for n in g["labels"] + g["aliases"]]
        box = infobox.get(rec["title"], "")
        url = pc.enwiki_url(rec["ground_title"]) if rec["ground_title"] else pc.wd(q)

        # (a)+(b) the names, and which of them agree with each other
        club_words = set(sdb.words(src["label"])) | set(sdb.words(team))
        sdb_gr, sdb_note = (match_stadiumdb(src["label"], table_ground, sgrounds) if sgrounds else (None, "no StadiumDB page"))
        places = {"table": [table_ground]}
        if box:
            places["club article infobox"] = [box]
        if wg:
            places["Wikidata P115"] = wd_names
        if sdb_gr:
            places["StadiumDB"] = [sdb_gr["name"]]

        def agree(x, y):
            return any(name_strength(nx, ny, club_words) for nx in places[x] for ny in places[y])
        # connected groups of places that name the same ground
        left, groups = list(places), []
        while left:
            group, todo = [], [left.pop(0)]
            while todo:
                cur = todo.pop()
                group.append(cur)
                for other in [o for o in left if agree(cur, o)]:
                    left.remove(other)
                    todo.append(other)
            groups.append(group)
        table_group = next(g for g in groups if "table" in g)
        other_groups = [g for g in groups if "table" not in g]
        named_by = len(table_group)
        agree_with_table = [x for x in table_group if x != "table"]
        wd_agrees = "Wikidata P115" in table_group
        odd_table = named_by < 2 and any(len(g) >= 2 for g in other_groups)

        # (c) OSM elements named like the ground, within 3 km of the centre
        found = centre_of[q]
        c_label, c_pos = (found[0] if found else (None, None))
        osm_hits = []
        for el in osm.values():
            near = min((haversine_m(pos, el["pos"]) for _l, pos in found), default=None)
            if near is None or near > RADIUS_M:
                continue
            strength, _via = best_strength(el["tags"].get("name", ""), [table_ground] + (wd_names if wd_agrees else []), club_words)
            if strength:
                osm_hits.append(dict(el, strength=strength, near=near))
        osm_hits.sort(key=lambda e: (e["strength"] != "exact", e["near"]))
        exact = [e for e in osm_hits if e["strength"] == "exact"]

        # (b)+(d) coordinates, ground-specific only
        coord_sources = []
        if wg and wg[0]["coord"] and wd_agrees:
            coord_sources.append(("Wikidata ground P625 " + wg[0]["qid"], wg[0]["coord"]))
        if article_pos.get(rec["ground_title"]):
            coord_sources.append(("the ground's English article", article_pos[rec["ground_title"]]))
        hits_here = search_hits.get(q, [])
        for h in hits_here[:2]:
            coord_sources.append((f"Wikidata item {h['qid']} ({h['label']}) found by searching the ground's name",
                                  h["coord"]))
        if exact:
            coord_sources.append((f"OpenStreetMap {exact[0]['ref']} (name equal)", exact[0]["pos"]))
        proposed_pos, agree_text = None, ""
        if coord_sources:
            proposed_pos = coord_sources[0][1]
            if len(coord_sources) > 1:
                ds = [haversine_m(proposed_pos, p) for _l, p in coord_sources[1:]]
                agree_text = "; ".join(f"{coord_sources[i + 1][0]} {round(d)} m" for i, d in enumerate(ds))
                agree_text = ("AGREE within 150 m: " if all(d <= AGREE_M for d in ds) else "DISAGREE (over 150 m): ") + agree_text
            else:
                agree_text = "single ground-specific source"

        # what the build would do
        build_pos = src["coord"] or next((g["coord"] for g in wg if g["coord"]), None)
        if build_pos:
            build_note = ("club P625" if src["coord"] else "P625 of its P115 ground")
        else:
            reasons = []
            if not src["grounds_all"]:
                reasons.append("no P115 on the club" + (" or its men's team item" if q in twin_of else ""))
            else:
                reasons.append("the P115 ground(s) " + ", ".join(
                    f"{gdata[s['value']]['label']} {s['value']}" for s in src["grounds_all"]
                    if s["value"] in gdata) + " carry no P625")
            reasons.append("the club has no P625")
            build_note = "UNPLACED (unplaced-no-coordinates): " + "; ".join(reasons)

        problems, notes_ = [], []
        if len(wg) > 1:
            problems.append(f"TWO TRUTHY GROUNDS ({', '.join(g['label'] for g in wg)})")
        if wg:
            others = [t for t in shared.get(wg[0]["qid"], []) if t != team]
            if others:
                mine = bool(cr_markers(team))
                theirs = [bool(cr_markers(o)) for o in others]
                if mine and not all(theirs):
                    problems.append("P115 is the first team's ground (" + ", ".join(others)
                                    + ") - copied onto a reserve side unless the table agrees")
                elif not mine and all(theirs):
                    notes_.append("its P115 is also its reserve side's (" + ", ".join(others) + ")")
                else:
                    problems.append("P115 shared with " + ", ".join(others))
        if wg and not wd_agrees:
            (notes_ if odd_table else problems).append(
                f"Wikidata names {wg[0]['label']!r}, the table {table_ground!r}"
                + (" - the table is the odd one out (three places agree with each other)" if odd_table else ""))
        elif not wg:
            notes_.append("Wikidata names no ground")
        if build_pos and proposed_pos and haversine_m(build_pos, proposed_pos) > AGREE_M:
            problems.append(f"THE MAP WOULD BE {round(haversine_m(build_pos, proposed_pos))} m FROM THE PROPOSAL")
        if not build_pos:
            problems.append("UNPLACED by the build")
        if named_by < 2 and not odd_table:
            problems.append("the ground is named by ONE place only (rule: two independent places)")
        if not proposed_pos:
            problems.append("NO ground-specific position found" + ("" if osm_status == "queried"
                                                                    else f" (OpenStreetMap: {osm_status})"))
        flags = problems
        verdict = "ok" if not problems else ("unplaced" if not build_pos else "attention")
        detail = pc.kv(
            verdict=verdict, flags=" | ".join(problems), notes=" | ".join(notes_),
            ground_table=table_ground, named_by=f"{named_by} place(s): table" + "".join(f", {a}" for a in agree_with_table),
            other_names="; ".join(f"{k}={' / '.join(v[:2])}" for k, v in places.items() if k != "table"),
            proposed_venue=table_ground,
            proposed_position=(f"{proposed_pos[0]:.6f} / {proposed_pos[1]:.6f}" if proposed_pos else ""),
            position_sources="; ".join(f"{l} {p[0]:.6f}/{p[1]:.6f}" for l, p in coord_sources),
            position_check=agree_text, build_position=(build_note if not build_pos else
                                                       f"{build_pos[0]:.6f} / {build_pos[1]:.6f} ({build_note})"),
            osm_candidates="; ".join(
                f"{e['ref']} {e['tags'].get('name')!r} [{e['tags'].get('leisure')}"
                f"{'/' + e['tags']['sport'] if e['tags'].get('sport') else ''}] {e['strength']}, "
                f"{round(e['near'])} m from the nearest search centre" for e in osm_hits[:4]),
            osm=osm_status if osm_status != "queried" else "queried",
            osm_search_centres="; ".join(l for l, _p in found) or "NONE: no position to search around")
        rows.append(pc.row("ground-proposal", tier, q, team, url,
                           f"{team}: ground {table_ground!r} - {verdict}", detail))
        if verdict != "ok":
            attention.append((verdict, team, table_ground, flags))

        # (e) capacity - a figure counts only when it is about the TABLE's ground
        wd_cap = wg[0]["capacities"][0] if wg and wg[0]["capacities"] else None
        big_other = max(other_groups, key=len) if other_groups else []
        sdb_same = bool(sdb_gr) and (name_strength(table_ground, sdb_gr["name"], club_words) is not None
                                     or (odd_table and "StadiumDB" in big_other))
        hit_caps = [h["cap"] for h in search_hits.get(q, []) if h.get("cap")]
        osm_caps = sorted({int(re.sub(r"\D", "", e["tags"]["capacity"])) for e in exact
                           if re.fullmatch(r"\s*\d[\d ,.]*", e["tags"].get("capacity", ""))})
        osm_cap = osm_caps[0] if len(osm_caps) == 1 else None
        wd_for_rule = wd_cap if (wd_agrees or not wg or (odd_table and "Wikidata P115" in big_other)) else None
        if not wg and hit_caps:
            wd_for_rule = hit_caps[0]
        sdb_for_rule = sdb_gr["capacity"] if sdb_same else None
        verdict_c, proposed, taken, note = capacity_rule(rec["capacity"], wd_for_rule, osm_cap, sdb_for_rule)
        not_used = []
        if wd_cap and not wd_for_rule:
            not_used.append(f"Wikidata's {wd_cap} is the capacity of {wg[0]['label']}, not of the table's ground")
        if sdb_gr and not sdb_same:
            not_used.append(f"StadiumDB's {sdb_gr['capacity']} is for {sdb_gr['name']}, a different ground")
        action = ""
        if verdict_c == "agreed":
            action = "keep (the map's figure is in the agreement)" if wd_cap and within(wd_cap, proposed) \
                else ("add (the map has no figure)" if not wd_cap else f"REPLACE the map's {wd_cap}")
        elif wd_cap and not wd_for_rule:
            action = (f"CLEAR the map's {wd_cap}: it is the capacity of another ground ({wg[0]['label']}), "
                      f"unless the two names are one ground")
        elif wd_cap:
            action = (f"no change proposed: the map's {wd_cap} has no independent agreement "
                      f"(it rests on Wikipedia/Wikidata alone)")
        detail_c = pc.kv(
            verdict=verdict_c, proposed=proposed if proposed is not None else "BLANK",
            action=action, rule=note,
            figures=f"table {rec['capacity']}; Wikidata {wd_cap} (map's figure); OpenStreetMap "
                    f"{osm_cap if osm_cap else (str(osm_caps) if osm_caps else None)}; StadiumDB "
                    f"{sdb_gr['capacity'] if sdb_gr else None}"
                    + (f"; Wikidata item found by name {hit_caps[0]}" if hit_caps else ""),
            not_used=" | ".join(not_used),
            wikidata_ground_capacities=",".join(str(c) for g in wg for c in g["capacities"]) if len(wg) > 1 or (wg and len(wg[0]["capacities"]) > 1) else "",
            stadiumdb=f"{sdb_gr['name']} ({sdb_gr['city']}) - {sdb_note}" if sdb_gr else sdb_note)
        rows.append(pc.row("capacity-proposal", tier, q, team, url,
                           f"{team}: {verdict_c}" + (f", proposed {proposed}" if proposed else ", blank"), detail_c))

    md_rows = [(v, t, g, " | ".join(f)) for v, t, g, f in attention]
    ctx["grounds_md"] = ["## Grounds and capacities", ""] + md + [""] + \
        [f"{len([r for r in rows if r['kind'] == 'ground-proposal' and 'verdict=ok' in r['detail']])} ground(s) "
         f"agree everywhere and need nothing; {len(attention)} need a look:", ""] + \
        pc.md_table(["verdict", "club", "table's ground", "flags"], md_rows) + [""]
    return rows
