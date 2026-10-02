"""THROWAWAY probe, removed in the same branch. (1) Reads Stadia Maps'
authentication docs. (2) Sends one tile, one route and one place search
with NO API key, as from https://alexgrozavul.github.io, then as from a
made-up domain, then with no Origin/Referer at all. (3) Reads sources on
the grounds of Jong KAA Gent and RSCA Futures. Prints only what it asks."""
import html, json, re, urllib.request, urllib.error, urllib.parse

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def req(url, headers=None, data=None, method=None, timeout=60):
    h = {"User-Agent": UA}
    h.update(headers or {})
    r = urllib.request.Request(url, headers=h, data=data, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return None, {}, repr(e).encode()

def text(body):
    body = re.sub(r"(?is)<(script|style|svg)[^>]*>.*?</\1>", " ", body)
    body = re.sub(r"(?i)<(br|p|div|li|tr|h\d|td|th|section|pre)[^>]*>", "\n", body)
    body = html.unescape(re.sub(r"<[^>]+>", " ", body))
    return [re.sub(r"\s+", " ", l).strip() for l in body.split("\n") if l.strip()]

def show(url, pat, maxl=40, ctx=1):
    st, h, b = req(url)
    s = b.decode("utf-8", "replace")
    lines = text(s) if st == 200 else []
    print(f"\n----- {url}  HTTP {st}  server={h.get('Server') or h.get('server')}  lines={len(lines)}")
    n = 0
    for k, l in enumerate(lines):
        if re.search(pat, l, re.I):
            print("  |", " / ".join(lines[max(0, k-ctx):k+ctx+1])[:700])
            n += 1
            if n >= maxl: break
    return st, s

print("=" * 30, "PART 1: Stadia authentication docs")
DOCS = ["https://docs.stadiamaps.com/authentication/",
        "https://stadiamaps.com/authentication/"]
AUTHPAT = r"domain|referer|referrer|origin|api key|api_key|localhost|subdomain|propagat|mobile|header|browser"
for u in DOCS:
    st, _ = show(u, AUTHPAT, maxl=60, ctx=0)
    if st != 200:
        cdx = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(
            {"url": u, "output": "json", "filter": "statuscode:200", "limit": "-3"})
        for attempt in range(3):
            st2, _, b2 = req(cdx, timeout=70)
            if st2 == 200: break
        print("  CDX", st2, b2[:400])
        try:
            rows = json.loads(b2)[1:]
        except Exception:
            rows = []
        if rows:
            ts = rows[-1][1]
            for form in (f"https://web.archive.org/web/{ts}id_/{u}", f"https://web.archive.org/web/{ts}/{u}"):
                st3, _ = show(form, AUTHPAT, maxl=60, ctx=0)
                if st3 == 200: break

print("\n" + "=" * 30, "PART 2: requests with NO key")
REAL = "https://alexgrozavul.github.io"
FAKE = "https://football-planner-test-q7x2k.example.net"
TILE = "https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/7/67/44.png"
GEO = "https://api.stadiamaps.com/geocoding/v1/search?" + urllib.parse.urlencode({"text": "Leonberg", "size": "5"})
ROUTE = "https://api.stadiamaps.com/route/v1"
BODY = json.dumps({"locations": [{"lat": 48.8001, "lon": 9.0130, "type": "break"},
                                 {"lat": 48.7923, "lon": 9.2320, "type": "break"}],
                   "costing": "auto", "units": "kilometers", "directions_type": "none"}).encode()

def hdrs(origin, mode):
    if origin is None: return {}
    h = {}
    if mode in ("both", "referer"): h["Referer"] = origin + "/Football/"
    if mode in ("both", "origin"): h["Origin"] = origin
    return h

def one(label, origin, mode):
    for name, call in (
        ("tile", lambda h: req(TILE, h)),
        ("route", lambda h: req(ROUTE, dict(h, **{"Content-Type": "application/json"}), data=BODY, method="POST")),
        ("search", lambda h: req(GEO, h)),
    ):
        h = hdrs(origin, mode)
        st, rh, b = call(h)
        ct = rh.get("Content-Type") or rh.get("content-type")
        acao = rh.get("Access-Control-Allow-Origin") or rh.get("access-control-allow-origin")
        detail = ""
        if name == "route" and st == 200:
            try:
                d = json.loads(b); s = d["trip"]["summary"]
                detail = f"legs={len(d['trip']['legs'])} length={s['length']} km shape={'yes' if d['trip']['legs'][0].get('shape') else 'no'}"
            except Exception as e: detail = "unparsed " + repr(e)
        elif name == "search" and st == 200:
            try:
                d = json.loads(b); f = d.get("features") or []
                detail = f"features={len(f)} first={f[0]['properties'].get('label') if f else None} coords={f[0]['geometry']['coordinates'] if f else None}"
            except Exception as e: detail = "unparsed " + repr(e)
        elif name == "tile" and st == 200:
            detail = f"png={b[:4] == bytes([0x89,0x50,0x4e,0x47])}"
        else:
            detail = b[:200].decode("utf-8", "replace").replace("\n", " ")
        print(f"  {label:<28} {name:<6} HTTP {st}  ct={ct}  bytes={len(b)}  acao={acao}  {detail}")

one("REAL domain, Referer+Origin", REAL, "both")
one("REAL domain, Referer only", REAL, "referer")
one("FAKE domain, Referer+Origin", FAKE, "both")
one("FAKE domain, Referer only", FAKE, "referer")
one("no Origin/Referer, no key", None, None)
# CORS preflight the browser sends before the POST route request
for lab, o in (("REAL", REAL), ("FAKE", FAKE)):
    st, rh, b = req(ROUTE, {"Origin": o, "Access-Control-Request-Method": "POST",
                            "Access-Control-Request-Headers": "content-type"}, method="OPTIONS")
    print(f"  preflight {lab}: HTTP {st} acao={rh.get('Access-Control-Allow-Origin') or rh.get('access-control-allow-origin')} "
          f"methods={rh.get('Access-Control-Allow-Methods') or rh.get('access-control-allow-methods')} "
          f"headers={rh.get('Access-Control-Allow-Headers') or rh.get('access-control-allow-headers')}")

print("\n" + "=" * 30, "PART 3: Jong KAA Gent and RSCA Futures")
def wd(qids):
    st, _, b = req("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbgetentities", "ids": "|".join(qids), "props": "labels|claims|sitelinks",
         "languages": "en|nl|fr", "format": "json"}))
    return json.loads(b).get("entities", {}) if st == 200 else {}
ents = wd(["Q117384089", "Q114056326"])
grounds = set()
for q, e in ents.items():
    lab = {k: v["value"] for k, v in e.get("labels", {}).items()}
    sl = {k: v["title"] for k, v in e.get("sitelinks", {}).items()}
    print(f"\n  {q} labels={lab} sitelinks={sl}")
    for p in ("P31", "P115", "P625", "P159", "P118", "P831", "P576", "P17"):
        for c in e.get("claims", {}).get(p, []):
            dv = c["mainsnak"].get("datavalue", {}).get("value")
            v = dv.get("id") if isinstance(dv, dict) and "id" in dv else dv
            qual = {k: [x.get("datavalue", {}).get("value") for x in vs] for k, vs in c.get("qualifiers", {}).items()}
            print(f"    {p} [{c['rank']}] {v} {qual if qual else ''}")
            if p == "P115" and isinstance(v, str): grounds.add(v)
for g, e in wd(sorted(grounds)).items() if grounds else []:
    lab = {k: v["value"] for k, v in e.get("labels", {}).items()}
    p625 = [c["mainsnak"].get("datavalue", {}).get("value") for c in e.get("claims", {}).get("P625", [])]
    p1083 = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("amount") for c in e.get("claims", {}).get("P1083", [])]
    print(f"  ground {g} {lab} P625={p625} P1083={p1083}")

# Wikidata search for the Deinze ground and Gent's ground
for s in ("Dakota Arena", "Burgemeester Van de Wielestadion", "Planet Group Arena", "Ghelamco Arena"):
    st, _, b = req("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbsearchentities", "search": s, "language": "en", "format": "json", "limit": "4"}))
    hits = json.loads(b).get("search", []) if st == 200 else []
    ids = [h["id"] for h in hits]
    print(f"\n  search '{s}': {[(h['id'], h.get('label'), h.get('description')) for h in hits]}")
    for g, e in (wd(ids).items() if ids else []):
        p625 = [c["mainsnak"].get("datavalue", {}).get("value") for c in e.get("claims", {}).get("P625", [])]
        p1083 = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("amount") for c in e.get("claims", {}).get("P1083", [])]
        occ = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in e.get("claims", {}).get("P466", [])]
        print(f"    {g} P625={p625} P1083={p1083} P466(occupants)={occ}")

PAT = r"futures|jong (kaa )?gent|deinze|dakota|van de wiele|planet group|ghelamco|thuiswedstrijd|stadion|stade|home (games|matches)|ground|venue|speelt"
WIKI = ["https://en.wikipedia.org/wiki/RSCA_Futures",
        "https://nl.wikipedia.org/wiki/RSCA_Futures",
        "https://fr.wikipedia.org/wiki/RSCA_Futures",
        "https://nl.wikipedia.org/wiki/Jong_KAA_Gent",
        "https://en.wikipedia.org/wiki/Jong_KAA_Gent",
        "https://fr.wikipedia.org/wiki/Jong_KAA_Gent",
        "https://nl.wikipedia.org/wiki/Planet_Group_Arena",
        "https://en.wikipedia.org/wiki/Planet_Group_Arena",
        "https://nl.wikipedia.org/wiki/Burgemeester_Van_de_Wielestadion",
        "https://en.wikipedia.org/wiki/Burgemeester_Van_de_Wielestadion",
        "https://en.wikipedia.org/wiki/2026%E2%80%9327_Challenger_Pro_League",
        "https://nl.wikipedia.org/wiki/Challenger_Pro_League_2026/27",
        "https://fr.wikipedia.org/wiki/Challenger_Pro_League_2026-2027"]
for u in WIKI:
    show(u, r"futures|jong (kaa )?gent|deinze|dakota|van de wiele|planet group|ghelamco|bespelers|tenants|thuisbasis|stadion\b|stade\b|home ground", maxl=25)

print("\n----- StadiumDB bel")
show("https://stadiumdb.com/stadiums/bel", r"deinze|dakota|futures|jong|gent|anderlecht|planet|ghelamco", maxl=20, ctx=0)

print("\n----- europlan")
for t in ("Deinze", "Gent"):
    st, s = show("https://www.europlan-online.de/index.php?s=search&search=" + t,
                 r"deinze|dakota|wiele|planet|ghelamco|gent", maxl=20, ctx=0)
    for href in sorted(set(re.findall(r'href="(/[^"]*stadion-\d+\.html)"', s)))[:8]:
        if re.search(r"deinze|dakota|wiele|planet|ghelamco|gent", href, re.I):
            show("https://www.europlan-online.de" + href, r"futures|jong|gent|anderlecht|deinze|kapazit|anschrift|vereine", maxl=20, ctx=0)

print("\n----- club and league sites (robots first)")
for site in ("https://www.rsca.be", "https://www.kaagent.be", "https://www.proleague.be"):
    st, h, b = req(site + "/robots.txt")
    print(f"  {site}/robots.txt HTTP {st} server={h.get('Server') or h.get('server')}")
    print("   ", b[:600].decode("utf-8", "replace").replace("\n", " | "))
for u in ("https://www.rsca.be/nl/rsca-futures", "https://www.rsca.be/fr/rsca-futures", "https://www.rsca.be/en/rsca-futures",
          "https://www.kaagent.be/nl/jong-kaa-gent", "https://www.kaagent.be/jong-kaa-gent",
          "https://www.proleague.be/challenger-pro-league", "https://www.proleague.be/clubs"):
    show(u, r"futures|jong|deinze|dakota|wiele|planet|ghelamco|stadion|stade", maxl=15, ctx=0)

print("\n" + "=" * 30, "PART 2 again (repeat, so the answer is at the end of the log)")
one("REAL domain, Referer+Origin", REAL, "both")
one("FAKE domain, Referer+Origin", FAKE, "both")
