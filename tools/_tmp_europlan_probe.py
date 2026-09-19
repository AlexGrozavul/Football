#!/usr/bin/env python3
"""TEMPORARY throwaway probe. Delete after the run.

Reads europlan-online.de from a GitHub runner, because this project's
sandbox proxy answers 403 to CONNECT for that host. It answers one
question and builds nothing: what does the site itself say about
automated reading?

It fetches robots.txt, hunts the site for a terms page, and records the
response headers and meta tags that carry robots directives. It reports
verbatim and interprets nothing.
"""

import html
import re
import sys
import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (compatible; europlan-probe/1.0; one-off manual check)"
BASE = "https://europlan-online.de"

# Words that would mean the site has something to say about automated or
# repeated reading, or about reusing what is on the page. German first.
KEYWORDS = [
    "automat", "roboter", "crawl", "scrap", "spider", "bot", "skript",
    "script", "maschinell", "massenhaft", "datenbank", "urheber",
    "vervielf", "nutzungsbedingung", "agb", "genehmigung", "erlaubnis",
    "zustimmung", "kommerziell", "gewerblich", "weiterverwend",
    "weitergabe", "auslesen", "api", "abruf", "zugriff", "lizenz",
    "copyright", "terms", "rechte",
]

pages = {}  # url -> (status, final_url, headers, text)


def get(url, note=""):
    print("=" * 72)
    print("GET", url, note)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "de,en;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read()
            status = r.status
            final = r.geturl()
            headers = dict(r.headers)
    except urllib.error.HTTPError as e:
        raw = e.read()
        status = e.code
        final = e.url if hasattr(e, "url") else url
        headers = dict(e.headers) if e.headers else {}
    except Exception as e:
        print("  FAILED:", type(e).__name__, e)
        print()
        time.sleep(1)
        return None

    print("  status:", status)
    print("  final URL:", final)
    for k in sorted(headers):
        print(f"  header  {k}: {headers[k]}")

    charset = "utf-8"
    ct = headers.get("Content-Type", "")
    m = re.search(r"charset=([\w-]+)", ct, re.I)
    if m:
        charset = m.group(1)
    else:
        m = re.search(rb'charset=["\']?([\w-]+)', raw[:2000], re.I)
        if m:
            charset = m.group(1).decode("ascii", "replace")
    print("  charset used:", charset, f"({len(raw)} bytes)")
    body = raw.decode(charset, errors="replace")
    pages[url] = (status, final, headers, body)
    print()
    time.sleep(1)
    return body


def to_text(htm):
    t = re.sub(r"<script.*?</script>", " ", htm, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</(p|div|tr|li|h\d)>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t\xa0]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip()


print("#" * 72)
print("# 1. robots.txt, verbatim")
print("#" * 72)
for u in (f"{BASE}/robots.txt", "https://www.europlan-online.de/robots.txt"):
    b = get(u)
    if b is not None:
        print("---- BEGIN robots.txt body ----")
        print(b)
        print("---- END robots.txt body ----")
        print("(repr of first 1500 chars, so nothing is lost to whitespace)")
        print(repr(b[:1500]))
        print()

print("#" * 72)
print("# 2. sitemaps")
print("#" * 72)
for u in (f"{BASE}/sitemap.xml", f"{BASE}/sitemap_index.xml"):
    b = get(u)
    if b:
        print(b[:1200])
        print()

print("#" * 72)
print("# 3. homepage, and every link on it that could be a legal page")
print("#" * 72)
home = get(f"{BASE}/", "(homepage)")
candidates = []
if home:
    links = re.findall(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                       home, flags=re.S | re.I)
    print(f"  {len(links)} links on the homepage")
    legal_re = re.compile(
        r"impressum|agb|nutzung|datenschutz|recht|terms|privacy|kontakt|"
        r"contact|info|hilfe|help|faq|about|ueber|über|urheber|copyright|"
        r"disclaimer|haftung|lizenz|licen",
        re.I)
    seen = set()
    print("\n  -- links whose href or text looks legal/informational --")
    for href, txt in links:
        label = re.sub(r"\s+", " ", to_text(txt))[:60]
        if legal_re.search(href) or legal_re.search(label):
            key = (href, label)
            if key in seen:
                continue
            seen.add(key)
            print(f"    {label!r:40} -> {href}")
            candidates.append(href)
    print("\n  -- the site's full distinct href set (first 120) --")
    allh = []
    for href, _ in links:
        if href not in allh:
            allh.append(href)
    for h in allh[:120]:
        print("   ", h)
    print()

    # A real ground page and club page, to read their headers/meta tags.
    m = re.search(r'href=["\']([^"\']*stadion-\d+\.html)["\']', home, re.I)
    if m:
        candidates.append(m.group(1))
        print("  found a ground page link on the homepage:", m.group(1))
    print()

print("#" * 72)
print("# 4. candidate legal / info pages")
print("#" * 72)
guesses = [
    "/index.php?s=impressum",
    "/index.php?s=agb",
    "/index.php?s=nutzungsbedingungen",
    "/index.php?s=datenschutz",
    "/index.php?s=kontakt",
    "/index.php?s=info",
    "/index.php?s=hilfe",
    "/index.php?s=faq",
    "/index.php?s=ueber",
    "/index.php?s=copyright",
    "/index.php?s=disclaimer",
    "/impressum",
    "/agb",
    "/datenschutz",
    "/nutzungsbedingungen",
    "/terms",
]
todo = []
for c in candidates + guesses:
    if c.startswith("http"):
        u = c
    elif c.startswith("/"):
        u = BASE + c
    else:
        u = BASE + "/" + c
    if u not in todo and "europlan-online" in u:
        todo.append(u)

for u in todo:
    b = get(u)
    if b is None:
        continue
    st = pages[u][0]
    txt = to_text(b)
    if st != 200:
        print(f"  -> HTTP {st}; first 300 chars of text: {txt[:300]!r}")
        print()
        continue
    print(f"  -> text ({len(txt)} chars):")
    print(txt[:6000])
    if len(txt) > 6000:
        print(f"  ... [{len(txt)-6000} more chars]")
    print()

print("#" * 72)
print("# 5. robots directives in headers and meta tags, on content pages")
print("#" * 72)
content_urls = [f"{BASE}/", f"{BASE}/index.php?s=land&id=1",
                f"{BASE}/index.php?s=liga&id=1"]
m = re.search(r'href=["\']([^"\']*stadion-\d+\.html)["\']', home or "", re.I)
if m:
    h = m.group(1)
    content_urls.append(h if h.startswith("http") else BASE + "/" + h.lstrip("/"))
for u in content_urls:
    if u not in pages:
        get(u)
for u in content_urls:
    if u not in pages:
        continue
    st, final, hdr, body = pages[u]
    xrt = [f"{k}: {v}" for k, v in hdr.items() if k.lower() == "x-robots-tag"]
    metas = re.findall(r"<meta[^>]+name=[\"']robots[\"'][^>]*>", body, re.I)
    metas += re.findall(r"<meta[^>]+robots[^>]*>", body, re.I)
    print(f"  {u}")
    print(f"    status {st}")
    print(f"    X-Robots-Tag header: {xrt or 'none'}")
    print(f"    <meta robots>: {sorted(set(metas)) or 'none'}")
print()

print("#" * 72)
print("# 6. keyword sweep over every page fetched")
print("#" * 72)
print("Any line, on any page above, mentioning automated access or reuse.")
print()
for u, (st, final, hdr, body) in pages.items():
    txt = body if u.endswith("robots.txt") else to_text(body)
    hits = []
    for line in txt.splitlines():
        low = line.lower()
        for kw in KEYWORDS:
            if kw in low:
                hits.append((kw, line.strip()[:400]))
                break
    if hits:
        print(f"-- {u} ({len(hits)} matching lines)")
        for kw, line in hits[:60]:
            print(f"   [{kw}] {line}")
        if len(hits) > 60:
            print(f"   ... {len(hits)-60} more")
        print()
    else:
        print(f"-- {u}: no keyword matched")
print()
print("PROBE COMPLETE")
