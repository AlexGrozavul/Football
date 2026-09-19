"""THROWAWAY PROBE - access and terms only. Delete after reading the log.

Answers, for stadiumdb.com and its Polish parent stadiony.net:
  1. Is there a robots.txt, and what exactly does it say?
  2. Is there a sitemap?
  3. Which non-content pages exist (terms, privacy, about, contact)?
  4. Does the full text of those pages say anything about automated access?
  5. Does an unknown URL 404 honestly, or silently serve a fallback page?

Reads no stadium data. Prints the answer first and again last, because a
long log gets truncated from the top - see CLAUDE.md on the europlan runs.
"""
import re, sys, time, urllib.request, urllib.error

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en,pl;q=0.8"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return (r.status, dict(r.headers), body, r.geturl(), time.time() - t0)
    except urllib.error.HTTPError as e:
        return (e.code, dict(e.headers), e.read(), url, 0.0)
    except Exception as e:
        return (None, {}, ("ERROR: %s" % e).encode(), url, 0.0)

def text_of(html):
    s = re.sub(rb"(?is)<(script|style)[^>]*>.*?</\1>", b" ", html)
    s = re.sub(rb"(?s)<[^>]+>", b" ", s)
    s = s.decode("utf-8", "replace")
    return re.sub(r"\s+", " ", s).strip()

# ---------------------------------------------------------------- robots
print("=" * 72)
print("SECTION 1  robots.txt and sitemap - the gate")
print("=" * 72)
robots_verdict = {}
for host in ("stadiumdb.com", "www.stadiumdb.com", "stadiony.net", "www.stadiony.net"):
    url = "https://%s/robots.txt" % host
    st, hdr, body, final, el = get(url)
    ct = hdr.get("Content-Type", "?")
    print("\n--- %s -> HTTP %s  %s  %d bytes  final=%s" % (url, st, ct, len(body), final))
    if st == 200 and len(body) < 6000:
        txt = body.decode("utf-8", "replace")
        looks_html = "<html" in txt.lower() or "<!doctype" in txt.lower()
        print("    looks like HTML (i.e. NOT a real robots.txt): %s" % looks_html)
        print("    ----- VERBATIM BODY BEGIN -----")
        for line in txt.splitlines():
            print("    | " + line)
        print("    ----- VERBATIM BODY END -----")
        robots_verdict[host] = ("html-fallback" if looks_html else "real", txt)
    else:
        robots_verdict[host] = ("http-%s" % st, "")

for host in ("stadiumdb.com", "stadiony.net"):
    for path in ("/sitemap.xml", "/sitemap_index.xml"):
        st, hdr, body, final, el = get("https://%s%s" % (host, path))
        print("sitemap %s%s -> HTTP %s  %d bytes  ct=%s"
              % (host, path, st, len(body), hdr.get("Content-Type", "?")))

# ------------------------------------------------- 404 honesty (europlan trap)
print("\n" + "=" * 72)
print("SECTION 2  does an unknown URL 404 honestly?")
print("=" * 72)
st_real, _, body_real, _, _ = get("https://stadiumdb.com/")
print("homepage                              -> HTTP %s  %d bytes" % (st_real, len(body_real)))
for bogus in ("https://stadiumdb.com/thisdefinitelydoesnotexist_probe_xyz",
              "https://stadiumdb.com/stadiums/thisdefinitelydoesnotexist_probe_xyz"):
    st, _, body, final, _ = get(bogus)
    same = abs(len(body) - len(body_real)) < 500
    print("%-38s -> HTTP %s  %d bytes  same-size-as-homepage=%s  final=%s"
          % (bogus.replace("https://stadiumdb.com", ""), st, len(body), same, final))

# --------------------------------------------------- robots meta / X-Robots-Tag
print("\n" + "=" * 72)
print("SECTION 3  meta robots and X-Robots-Tag")
print("=" * 72)
for url in ("https://stadiumdb.com/", "https://stadiumdb.com/stadiums",
            "https://stadiumdb.com/about_us"):
    st, hdr, body, final, _ = get(url)
    metas = re.findall(rb'(?i)<meta[^>]+name=["\']robots["\'][^>]*>', body)
    print("%-42s HTTP %s  X-Robots-Tag=%r  meta=%s"
          % (url, st, hdr.get("X-Robots-Tag"),
             [m.decode("utf-8", "replace") for m in metas] or "none"))

# ------------------------------------------------- discover non-content pages
print("\n" + "=" * 72)
print("SECTION 4  every non-stadium link the site itself offers")
print("=" * 72)
CAND = ("terms", "tos", "legal", "privacy", "policy", "polic", "copyright",
        "disclaimer", "about", "contact", "cookie", "gdpr", "rodo",
        "regulamin", "polityka", "kontakt", "prawa", "api", "rss", "licen")
for home in ("https://stadiumdb.com/", "https://stadiony.net/"):
    st, hdr, body, final, _ = get(home)
    hrefs = set()
    for m in re.finditer(rb'href=["\']([^"\'#?]+)["\']', body):
        h = m.group(1).decode("utf-8", "replace")
        low = h.lower()
        if any(c in low for c in CAND):
            hrefs.add(h)
    print("\n%s  (HTTP %s, %d bytes) candidate non-content links:" % (home, st, len(body)))
    for h in sorted(hrefs)[:40]:
        print("    %s" % h)
    if not hrefs:
        print("    (none matched)")

# -------------------------------------------------------- sweep the legal text
print("\n" + "=" * 72)
print("SECTION 5  full-text sweep of the legal/informational pages")
print("=" * 72)
TERMS = [
    # English
    "prohibit", "forbidden", "not permitted", "not allowed", "may not", "must not",
    "automated", "automatic", "scrap", "scrape", "crawl", "spider", "bot ", "robot",
    "harvest", "data mining", "text and data mining", "systematic", "bulk",
    "rate limit", "throttl", "personal use", "non-commercial", "noncommercial",
    "commercial use", "reproduce", "reproduction", "redistribut", "republish",
    "database right", "sui generis", "extract", "written permission",
    "prior consent", "all rights reserved", "copyright",
    # Polish
    "zabron", "zabrani", "niedozwolon", "nie wolno", "zakaz", "automatyczn",
    "zautomatyzowan", "skanowanie", "kopiowanie", "powielanie", "rozpowszechnian",
    "masow", "systematyczn", "komercyjn", "użytek osobisty", "użytku osobistego",
    "prawa autorskie", "baza danych", "bazy danych", "zgodą pisemn", "pisemnej zgody",
]
PAGES = [
    "https://stadiumdb.com/about_us",
    "https://stadiumdb.com/contact",
    "https://stadiumdb.com/privacy_policy",
    "https://stadiumdb.com/terms",
    "https://stadiumdb.com/terms_of_use",
    "https://stadiony.net/o_nas",
    "https://stadiony.net/kontakt",
    "https://stadiony.net/regulamin",
    "https://stadiony.net/polityka_prywatnosci",
]
found_any = []
for url in PAGES:
    st, hdr, body, final, _ = get(url)
    same_as_home = abs(len(body) - len(body_real)) < 500
    txt = text_of(body)
    print("\n--- %s" % url)
    print("    HTTP %s  %d bytes  %d chars of text  looks-like-homepage-fallback=%s"
          % (st, len(body), len(txt), same_as_home))
    if st != 200 or same_as_home:
        print("    -> treated as NOT A REAL PAGE")
        continue
    hits = []
    low = txt.lower()
    for t in TERMS:
        i = low.find(t)
        if i >= 0:
            hits.append((t, txt[max(0, i - 90):i + 110].strip()))
    print("    terms matched: %d" % len(hits))
    for t, ctx in hits[:14]:
        print("      [%s] ...%s..." % (t, ctx))
    if hits:
        found_any.append((url, len(hits)))

print("\n" + "=" * 72)
print("REPEAT OF THE HEADLINE ANSWERS (log reads from the bottom)")
print("=" * 72)
for host, (kind, txt) in robots_verdict.items():
    print("robots %-20s : %s" % (host, kind))
    if kind == "real":
        for line in txt.splitlines():
            if line.strip():
                print("        | %s" % line)
print("legal pages with any matched term: %s" % (found_any or "NONE"))
