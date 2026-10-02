"""THROWAWAY probe, removed in the same branch (third pass). (1) Stadia
domain test repeated with made-up domains that are NOT reserved names, all
three request kinds; and the route with a made-up key. (2) The club's own
archived article on Deinze, europlan positions, KAA Gent's Jong calendar."""
import html, json, re, urllib.request, urllib.error, urllib.parse
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
def req(url, headers=None, data=None, method=None, timeout=70):
    h = {"User-Agent": UA}; h.update(headers or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h, data=data, method=method), timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return None, {}, repr(e).encode()
def text(body):
    body = re.sub(r"(?is)<(script|style|svg)[^>]*>.*?</\1>", " ", body)
    body = re.sub(r"(?i)<(br|p|div|li|tr|h\d|td|th|section)[^>]*>", "\n", body)
    body = html.unescape(re.sub(r"<[^>]+>", " ", body))
    return [re.sub(r"\s+", " ", l).strip() for l in body.split("\n") if l.strip()]

print("=" * 30, "STADIA 3")
TILE = "https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/7/67/44.png"
GEO = "https://api.stadiamaps.com/geocoding/v1/search?" + urllib.parse.urlencode({"text": "Leonberg", "size": "1"})
ROUTE = "https://api.stadiamaps.com/route/v1"
BODY = json.dumps({"locations": [{"lat": 48.8001, "lon": 9.0130, "type": "break"}, {"lat": 48.7923, "lon": 9.2320, "type": "break"}],
                   "costing": "auto", "units": "kilometers", "directions_type": "none"}).encode()
BOGUS = "00000000-0000-4000-8000-000000000000"
def three(label, origin, key=None):
    h = {"Referer": origin + "/Football/", "Origin": origin} if origin else {}
    k = ("?api_key=" + key) if key else ""
    out = []
    for name, (st, _, b) in (("tile", req(TILE + k, h)),
                             ("route", req(ROUTE + k, dict(h, **{"Content-Type": "application/json"}), data=BODY, method="POST")),
                             ("search", req(GEO + (("&api_key=" + key) if key else ""), h))):
        out.append(f"{name} {st}")
    print(f"  {label:<62} " + " | ".join(out))
three("REAL https://alexgrozavul.github.io, no key", "https://alexgrozavul.github.io")
three("MADE-UP https://fbplanner-q7x2k-test.net, no key", "https://fbplanner-q7x2k-test.net")
three("MADE-UP https://alexgrozavul.gitlab.io, no key", "https://alexgrozavul.gitlab.io")
three("MADE-UP https://football.alexgrozavul.github.io, no key", "https://football.alexgrozavul.github.io")
three("reserved https://example.org, no key", "https://example.org")
three("REAL https://alexgrozavul.github.io, made-up api_key", "https://alexgrozavul.github.io", BOGUS)
three("no Origin/Referer, made-up api_key", None, BOGUS)

print("\n" + "=" * 30, "BELGIUM 3")
for u, ts in (("https://www.rsca.be/nl/news/het-stadion-van-deinze-blijft-de-thuisbasis-van-rsca-futures", "20260520224926"),
              ("https://www.rsca.be/en/news/deinze-stadium-remains-home-soil-our-rsca-futures", "20260515015856")):
    for form in (f"https://web.archive.org/web/{ts}id_/{u}", f"https://web.archive.org/web/{ts}/{u}"):
        st, _, b = req(form, timeout=90)
        if st == 200:
            s = b.decode("utf-8", "replace")
            m = re.findall(r'(?:article:published_time|datePublished|"date")["\s:=content]*"?([0-9]{4}-[0-9]{2}-[0-9]{2}[^"]*)', s)
            print(f"\n--- archived {u} @ {ts} (dates in page: {m[:4]})")
            for l in text(s):
                if re.search(r"deinze|dakota|futures|seizoen|season|stadion|stadium|thuis|home|202[5-7]", l, re.I) and len(l) > 30:
                    print("   |", l[:600])
            break
        print(f"  {form} -> {st}")

for g in ("burgermeester-van-de-wiele-stadion/stadion-3706.html", "ghelamco-arena/stadion-10086.html"):
    st, _, b = req("https://www.europlan-online.de/" + g); s = b.decode("utf-8", "replace")
    print(f"\n--- europlan {g} HTTP {st}")
    print("   maps:", re.findall(r"maps\.google\.[a-z]+/maps\?q=\(?([-0-9.]+),\s*([-0-9.]+)", s)[:2],
          "umkreis:", re.findall(r"s=umkreis&(?:amp;)?lat=([-0-9.]+)&(?:amp;)?lon=([-0-9.]+)", s)[:1])

for u in ("https://www.kaagent.be/nl/jong-kaa-gent/kalender", "https://www.kaagent.be/nl/jong-kaa-gent/wedstrijdverslagen"):
    st, _, b = req(u); s = b.decode("utf-8", "replace")
    print(f"\n--- {u} HTTP {st}")
    hits = [l for l in text(s) if re.search(r"planet|arena|chillax|stadion|thuis|home|jong", l, re.I)]
    for l in hits[:25]: print("   |", l[:300])
    links = sorted(set(re.findall(r'href="([^"]*jong[^"]*)"', s)))[:15]
    print("   links:", links)
