"""THROWAWAY probe, removed in the same branch (second pass). (1) More
Stadia diagnostics, no real key anywhere. (2) Non-Wikipedia sources for the
grounds of Jong KAA Gent and RSCA Futures."""
import html, json, re, urllib.request, urllib.error, urllib.parse

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
def req(url, headers=None, data=None, method=None, timeout=60):
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
def grep_raw(label, s, pat, width=220, maxn=12):
    n = 0
    for m in re.finditer(pat, s, re.I):
        a = max(0, m.start() - width); print(f"  [{label}] ...{html.unescape(s[a:m.end()+width])!r}"[:2*width+120]); n += 1
        if n >= maxn: break
    if not n: print(f"  [{label}] no match for {pat}")

print("=" * 30, "STADIA 2")
TILE = "https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/7/67/44.png"
GEO = "https://api.stadiamaps.com/geocoding/v1/search?" + urllib.parse.urlencode({"text": "Leonberg", "size": "1"})
def t(label, url, h):
    st, rh, b = req(url, h)
    print(f"  {label:<55} HTTP {st} bytes={len(b)} {b[:80].decode('utf-8','replace') if st != 200 and not b.startswith(bytes([0x89])) else ''}")
for d in ("https://example.com", "https://alexgrozavul.github.io.evil-test.net", "https://someoneelse.github.io", "http://localhost:8000"):
    t(f"tile, Referer {d}, no key", TILE, {"Referer": d + "/"})
t("search, Referer https://example.com, no key", GEO, {"Referer": "https://example.com/", "Origin": "https://example.com"})
BOGUS = "00000000-0000-4000-8000-000000000000"
t("tile, REAL Referer, made-up api_key", TILE + "?api_key=" + BOGUS, {"Referer": "https://alexgrozavul.github.io/Football/"})
t("search, REAL Referer+Origin, made-up api_key", GEO + "&api_key=" + BOGUS, {"Referer": "https://alexgrozavul.github.io/Football/", "Origin": "https://alexgrozavul.github.io"})
t("tile, no headers, made-up api_key", TILE + "?api_key=" + BOGUS, {})

print("\n" + "=" * 30, "BELGIUM 2")
# europlan ground pages
for term in ("Dakota", "Planet Group", "Chillax"):
    st, h, b = req("https://www.europlan-online.de/index.php?s=search&search=" + urllib.parse.quote(term))
    s = b.decode("utf-8", "replace")
    links = sorted(set(re.findall(r'href="([^"]*stadion-\d+\.html)"', s)))
    print(f"\n--- europlan search {term!r}: HTTP {st}, ground links: {links[:10]}")
    for href in links[:3]:
        u = href if href.startswith("http") else "https://www.europlan-online.de" + ("" if href.startswith("/") else "/") + href
        st2, _, b2 = req(u); lines = text(b2.decode("utf-8", "replace"))
        print(f"  ground page {u} HTTP {st2}")
        for k, l in enumerate(lines):
            if re.search(r"Kapazit|Anschrift|Vereine, die|futures|anderlecht|jong|gent|deinze|lat|Liga|Level|Ebene", l, re.I):
                print("    |", " / ".join(lines[k:k+3])[:400])

# kaagent.be page, more context
st, h, b = req("https://www.kaagent.be/nl/jong-kaa-gent"); s = b.decode("utf-8", "replace")
lines = text(s)
print(f"\n--- kaagent.be/nl/jong-kaa-gent HTTP {st}")
for k, l in enumerate(lines):
    if re.search(r"stadion|arena|chillax|planet|thuiswedstrijd|wedstrijd|oostakker", l, re.I):
        print("  |", " / ".join(lines[max(0,k-2):k+4])[:500])
grep_raw("kaagent raw", s, r"planet group|chillax|oostakker|ghelamco", maxn=8)

# proleague.be: sitemap, then club pages and match pages
st, h, b = req("https://www.proleague.be/sitemap.xml"); sm = b.decode("utf-8", "replace")
locs = re.findall(r"<loc>([^<]+)</loc>", sm)
print(f"\n--- proleague sitemap HTTP {st}, {len(locs)} locs; sample: {locs[:5]}")
subs = [l for l in locs if l.endswith(".xml")]
allurls = [l for l in locs if not l.endswith(".xml")]
for sub in subs[:12]:
    st2, _, b2 = req(sub); allurls += re.findall(r"<loc>([^<]+)</loc>", b2.decode("utf-8", "replace"))
print(f"  total urls {len(allurls)}")
cand = [u for u in allurls if re.search(r"gent|futures|anderlecht", u, re.I)]
print("  candidate urls:", cand[:40])
for u in [u for u in cand if re.search(r"jong|futures", u, re.I)][:6]:
    st3, _, b3 = req(u); s3 = b3.decode("utf-8", "replace")
    print(f"\n  page {u} HTTP {st3} bytes={len(s3)}")
    grep_raw("pl", s3, r"dakota|deinze|planet group|chillax|ghelamco|venue|stadium|stadion", maxn=8)

# Internet Archive: the club's own article on Deinze
for q in ({"url": "rsca.be/*", "filter": "original:.*deinze.*"}, {"url": "rsca.be/*", "filter": "original:.*futures.*"}):
    p = dict(q, output="json", limit="20", collapse="urlkey")
    for attempt in range(3):
        st, _, b = req("https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(p), timeout=80)
        if st == 200: break
    rows = []
    try: rows = json.loads(b)[1:]
    except Exception: pass
    print(f"\n--- CDX {q}: HTTP {st}, {len(rows)} rows")
    for r in rows[:20]: print("   ", r[1], r[2], r[4])
    for r in [r for r in rows if re.search(r"deinze|thuisbasis|stadion", r[2], re.I)][:3]:
        for form in (f"https://web.archive.org/web/{r[1]}id_/{r[2]}", f"https://web.archive.org/web/{r[1]}/{r[2]}"):
            st4, _, b4 = req(form, timeout=80)
            if st4 == 200:
                ls = text(b4.decode("utf-8", "replace"))
                print(f"  archived {r[2]} @ {r[1]}")
                for k, l in enumerate(ls):
                    if re.search(r"deinze|dakota|futures|seizoen|stadion", l, re.I): print("    |", l[:400])
                break
