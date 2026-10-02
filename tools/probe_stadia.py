"""THROWAWAY probe, removed in the same branch. Reads Stadia Maps' own
pricing and API documentation pages (blocked from the sandbox), and
makes ONE route request and ONE autocomplete request with the app's key
to see the response shapes and CORS headers."""
import html, json, re, urllib.request, urllib.error

UA = {"User-Agent": "Mozilla/5.0 (football-planner probe)"}
KEY = "ec818681-51dd-4ceb-89c0-6f1124dbc053"
KW = re.compile(r"credit|routing|route|geocod|autocomplete|search|free|non-commercial|"
                r"noncommercial|commercial|tile|per request|per month|domain|cors|origin", re.I)

def get(url, data=None, headers=None):
    h = dict(UA); h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return None, {}, repr(e)

def text(body):
    body = re.sub(r"(?is)<(script|style|svg)[^>]*>.*?</\1>", " ", body)
    body = re.sub(r"(?i)<(br|p|div|li|tr|h\d|td|th)[^>]*>", "\n", body)
    body = html.unescape(re.sub(r"<[^>]+>", " ", body))
    return [re.sub(r"\s+", " ", l).strip() for l in body.split("\n") if l.strip()]


st, hd, body = get("https://stadiamaps.com/pricing/")
lines = text(body)
i = next((k for k,l in enumerate(lines) if "Credit Schedule" in l), 0)
print("===== pricing page, credit schedule section, every line")
for l in lines[i:i+120]: print("  |", l)
# also raw html around the table, in case the cost is in an attribute
m = re.search(r"(?is)Standard Routing.{0,1500}", body)
print("===== raw html after 'Standard Routing' (first hit)"); print(m.group(0)[:1500] if m else None)

for url in ["https://docs.stadiamaps.com/geocoding-search-autocomplete/place-lookup/",
            "https://docs.stadiamaps.com/geocoding-search-autocomplete/place-details/",
            "https://docs.stadiamaps.com/geocoding-search-autocomplete/v2-api-migration-guide/"]:
    st, hd, body = get(url)
    hits = [l for l in text(body) if re.search(r"credit|place|geometry|coordinates|endpoint|api\.stadiamaps", l, re.I) and len(l) < 300] if st == 200 else []
    print(f"\n===== {url} HTTP {st}")
    for l in hits[30:90]: print("  |", l)

print("\n===== one v1 autocomplete request (costs credits)")
st, hd, out = get(f"https://api.stadiamaps.com/geocoding/v1/autocomplete?text=Karlsruhe&size=2&api_key={KEY}")
print("HTTP", st); print(out[:1200])

print("\n===== one raster tile, NO Origin/Referer header (1 credit)")
st, hd, out = get(f"https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/8/134/88.png?api_key={KEY}")
print("HTTP", st, hd.get("Content-Type"), len(out))
print("\n===== one raster tile, Origin https://example.com (1 credit)")
st, hd, out = get(f"https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/8/134/88.png?api_key={KEY}",
                  headers={"Origin": "https://example.com", "Referer": "https://example.com/"})
print("HTTP", st, hd.get("Content-Type"), len(out))
