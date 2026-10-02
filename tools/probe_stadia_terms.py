"""THROWAWAY probe, removed in the same branch. Reads Stadia Maps' terms
and docs (blocked from the sandbox) for what they say about caching,
storing and offline use of tiles, routes and geocoding results."""
import html, re, urllib.request, urllib.error

UA = {"User-Agent": "Mozilla/5.0 (football-planner probe)"}
KW = re.compile(r"cach|offline|stor(e|ing|age)|prefetch|pre-fetch|bulk|scrap|download|persist|retain|"
                r"service worker|redistribut|last updated|effective", re.I)

def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return None, repr(e)

def text(body):
    body = re.sub(r"(?is)<(script|style|svg|nav|header|footer)[^>]*>.*?</\1>", " ", body)
    body = re.sub(r"(?i)<(br|p|div|li|tr|h\d|td|th)[^>]*>", "\n", body)
    body = html.unescape(re.sub(r"<[^>]+>", " ", body))
    return [re.sub(r"\s+", " ", l).strip() for l in body.split("\n") if l.strip()]

URLS = ["https://stadiamaps.com/terms-of-service/",
        "https://stadiamaps.com/legal/",
        "https://docs.stadiamaps.com/faq/",
        "https://docs.stadiamaps.com/caching/",
        "https://docs.stadiamaps.com/offline/",
        "https://docs.stadiamaps.com/sdks/offline/",
        "https://docs.stadiamaps.com/native-multiplatform/offline/",
        "https://stadiamaps.com/pricing/"]
for url in URLS:
    st, body = get(url)
    lines = text(body) if st == 200 else []
    print(f"\n===== {url} HTTP {st} lines={len(lines)}")
    for k, l in enumerate(lines):
        if KW.search(l):
            ctx = " ".join(lines[max(0, k-1):k+2])
            print("  |", ctx[:900])
