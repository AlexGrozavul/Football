"""THROWAWAY PROBE 3 - discover structure first, assume nothing.

Probe 2 assumed /stadiums/<iso3> and found nothing. This one reads what
the site actually links and prints the raw evidence.
"""
import re, time, urllib.request, urllib.error
from collections import Counter

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
LAST = [0.0]

def get(url, timeout=45):
    gap = time.time() - LAST[0]
    if gap < 0.7:
        time.sleep(0.7 - gap)
    LAST[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en,pl;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, ("ERROR: %s" % e).encode()

def text_of(html):
    s = re.sub(rb"(?is)<(script|style)[^>]*>.*?</\1>", b" ", html)
    s = re.sub(rb"(?s)<[^>]+>", b" ", s)
    s = s.decode("utf-8", "replace").replace("-->", " ")
    return re.sub(r"\s+", " ", s).strip()

# ============================================ PART 1: legal pages, FULL text
print("#" * 70)
print("PART 1  legal pages - full text this time, not the footer")
print("#" * 70)
for url in ("https://stadiumdb.com/copyrights",
            "https://stadiumdb.com/contact_us",
            "https://stadiumdb.com/faq",
            "https://stadiony.net/prawa_autorskie",
            "https://stadiony.net/o_serwisie"):
    st, body = get(url)
    txt = text_of(body)
    print("\n=== %s  HTTP %s  %d chars" % (url, st, len(txt)))
    print("    FULL: %s" % txt[:2600])

# ============================================ PART 2: real URL structure
print("\n" + "#" * 70)
print("PART 2  what /stadiums actually links to")
print("#" * 70)
st, body = get("https://stadiumdb.com/stadiums")
print("/stadiums HTTP %s  %d bytes" % (st, len(body)))
hrefs = [h.decode("utf-8", "replace")
         for h in re.findall(rb'href="([^"]+)"', body)]
print("total hrefs: %d" % len(hrefs))
pat = Counter()
for h in hrefs:
    parts = [p for p in h.split("?")[0].split("/") if p]
    shape = "/".join(("<%d>" % len(p)) if i and not p.isalpha() else p
                     for i, p in enumerate(parts[:3]))
    pat[shape] += 1
print("\ncommonest path shapes:")
for s, n in pat.most_common(18):
    print("   %-52s %d" % (s, n))
print("\nfirst 30 hrefs verbatim:")
for h in hrefs[:30]:
    print("   %s" % h)
print("\nany href containing 'fra' or 'ita' or 'france' or 'italy':")
for h in hrefs:
    if re.search(r"(fra|ita|france|italy|serbia|greece|austria|switz)", h, re.I):
        print("   %s" % h)

# ============================================ PART 3: the stadium page shape
print("\n" + "#" * 70)
print("PART 3  a real stadium page, to learn the field markup")
print("#" * 70)
cand = [h for h in hrefs if re.match(r"^(https://stadiumdb\.com)?/[a-z]{3}/", h)]
print("hrefs that look like /<iso3>/<slug>: %d, e.g. %s" % (len(cand), cand[:5]))
target = cand[0] if cand else None
if target:
    u = target if target.startswith("http") else "https://stadiumdb.com" + target
    st, body = get(u)
    print("\n%s HTTP %s %d bytes" % (u, st, len(body)))
    txt = text_of(body)
    i = txt.lower().find("capacity")
    print("text around 'capacity': ...%s..." % txt[max(0, i-300):i+300])
    # show the raw markup around capacity so a parser can be written
    m = re.search(rb"(?is).{400}Capacity.{600}", body)
    if m:
        print("\nRAW MARKUP around Capacity:")
        print(m.group(0).decode("utf-8", "replace"))
