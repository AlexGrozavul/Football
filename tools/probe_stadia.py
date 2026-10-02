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

PAGES = [
  "https://stadiamaps.com/pricing/",
  "https://docs.stadiamaps.com/pricing/",
  "https://docs.stadiamaps.com/credits/",
  "https://docs.stadiamaps.com/routing/standard-routing/",
  "https://docs.stadiamaps.com/geocoding-search-autocomplete/autocomplete/",
  "https://docs.stadiamaps.com/geocoding-search-autocomplete/search/",
  "https://docs.stadiamaps.com/authentication/",
  "https://stadiamaps.com/terms-of-service/",
]
for url in PAGES:
    st, hd, body = get(url)
    lines = text(body) if st == 200 else []
    hits = [l for l in lines if KW.search(l) and len(l) < 400]
    print(f"\n===== {url}  HTTP {st}  {len(body)} bytes, {len(hits)} matching lines")
    seen = set()
    for l in hits:
        if l in seen: continue
        seen.add(l); print("  |", l)
        if len(seen) >= 90: print("  | ...cut"); break

print("\n===== API: one route request (costs credits)")
body = json.dumps({"locations": [{"lat": 48.8003, "lon": 9.0167}, {"lat": 48.1351, "lon": 11.5820}],
                   "costing": "auto", "units": "kilometers",
                   "directions_type": "none"}).encode()
st, hd, out = get(f"https://api.stadiamaps.com/route/v1?api_key={KEY}", data=body,
                  headers={"Content-Type": "application/json", "Origin": "https://alexgrozavul.github.io"})
print("HTTP", st, "ACAO:", hd.get("Access-Control-Allow-Origin") or hd.get("access-control-allow-origin"))
print({k: v for k, v in hd.items() if k.lower().startswith(("x-", "ratelimit", "access-control"))})
try:
    j = json.loads(out); tr = j.get("trip", {})
    print("keys:", list(j), "trip keys:", list(tr))
    print("summary:", tr.get("summary"), "units:", tr.get("units"))
    print("legs:", len(tr.get("legs", [])), "shape chars:", len(tr["legs"][0]["shape"]) if tr.get("legs") else None)
    print("leg keys:", list(tr["legs"][0]) if tr.get("legs") else None)
except Exception as e:
    print("not JSON:", e, out[:600])

for path in ["geocoding/v2/autocomplete", "geocoding/v1/autocomplete"]:
    print(f"\n===== API: one {path} request (costs credits)")
    st, hd, out = get(f"https://api.stadiamaps.com/{path}?text=Karlsruhe&size=3&api_key={KEY}",
                      headers={"Origin": "https://alexgrozavul.github.io"})
    print("HTTP", st, "ACAO:", hd.get("Access-Control-Allow-Origin") or hd.get("access-control-allow-origin"))
    print(out[:1500])
    if st == 200: break
