#!/usr/bin/env python3
"""TEMPORARY throwaway probe, second pass. Delete after the run.

The first pass drowned in the homepage's link dump and the log lost the
robots.txt body. This one prints robots.txt first and last, prints no
link dumps, and proves which index.php?s=... pages are real pages rather
than the site's fallback, by comparing each body against the homepage.

It reports verbatim and interprets nothing. It fetches no club or ground
data and builds nothing.
"""

import hashlib
import html
import re
import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (compatible; europlan-probe/1.0; one-off manual check)"
BASE = "https://europlan-online.de"
pages = {}


def get(url, quiet=False):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "*/*", "Accept-Language": "de,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw, status, final, hdr = r.read(), r.status, r.geturl(), dict(r.headers)
    except urllib.error.HTTPError as e:
        raw, status = e.read(), e.code
        final = getattr(e, "url", url)
        hdr = dict(e.headers) if e.headers else {}
    except Exception as e:
        print(f"  FAILED {url}: {type(e).__name__} {e}")
        time.sleep(1)
        return None
    cs = "utf-8"
    m = re.search(r"charset=([\w-]+)", hdr.get("Content-Type", ""), re.I)
    if m:
        cs = m.group(1)
    body = raw.decode(cs, errors="replace")
    pages[url] = (status, final, hdr, body)
    if not quiet:
        print(f"  status {status}  final {final}  {len(raw)} bytes")
    time.sleep(1)
    return body


def text(h):
    t = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</(p|div|tr|li|h\d)>", "\n", t, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t).strip()


def robots_block(tag):
    print("#" * 70)
    print(f"# ROBOTS.TXT VERBATIM ({tag})")
    print("#" * 70)
    for u in (f"{BASE}/robots.txt", "https://www.europlan-online.de/robots.txt"):
        print(f"--- {u}")
        b = get(u, quiet=(tag == "repeat"))
        if b is None:
            continue
        st, final, hdr, _ = pages[u]
        if tag != "repeat":
            for k in sorted(hdr):
                print(f"    header {k}: {hdr[k]}")
        print(f"    HTTP {st}, {len(b)} chars")
        print("    >>>>>>>>>> BEGIN BODY")
        for line in b.splitlines():
            print("    |" + line)
        print("    <<<<<<<<<< END BODY")
        print("    repr:", repr(b[:2000]))
        print()


robots_block("first")

print("#" * 70)
print("# WHICH index.php?s=... PAGES ARE REAL, AND WHICH ARE THE FALLBACK")
print("#" * 70)
home = get(f"{BASE}/", quiet=True)
home_h = hashlib.sha1((home or "").encode()).hexdigest()[:12]
home_t = text(home or "")
print(f"homepage: {len(home or '')} chars, sha1 {home_h}, text {len(home_t)} chars")
print()

slugs = ["impressum", "datenschutz", "faq", "kontakt", "agb",
         "nutzungsbedingungen", "info", "hilfe", "ueber", "copyright",
         "disclaimer", "terms", "nutzung", "regeln", "lizenz",
         "thisdefinitelydoesnotexist"]
real = []
for s in slugs:
    u = f"{BASE}/index.php?s={s}"
    b = get(u, quiet=True)
    if b is None:
        continue
    st, final, hdr, _ = pages[u]
    t = text(b)
    same = "SAME AS HOMEPAGE (fallback)" if t == home_t else "distinct page"
    ttl = re.search(r"<title>(.*?)</title>", b, re.S | re.I)
    ttl = re.sub(r"\s+", " ", html.unescape(ttl.group(1))).strip() if ttl else "(no title)"
    print(f"  s={s:28} HTTP {st}  text {len(t):6} chars  {same}")
    print(f"      <title> {ttl}")
    if t != home_t:
        real.append((s, u, t))
print()

print("#" * 70)
print("# FULL TEXT OF EVERY DISTINCT PAGE FOUND")
print("#" * 70)
for s, u, t in real:
    print("=" * 70)
    print(f"PAGE s={s}  ({u})  {len(t)} chars")
    print("=" * 70)
    print(t[:9000])
    if len(t) > 9000:
        print(f"... [{len(t)-9000} more chars omitted]")
    print()

print("#" * 70)
print("# DOES THE SITE LINK TO A TERMS PAGE ANYWHERE ON THE HOMEPAGE?")
print("#" * 70)
print("Searching the homepage HTML for the words themselves, links or not.")
for w in ["agb", "nutzungsbedingung", "nutzungsbeding", "terms", "impressum",
          "datenschutz", "urheber", "copyright", "lizenz", "disclaimer",
          "haftung", "api", "robots"]:
    hits = [m.start() for m in re.finditer(w, home or "", re.I)]
    print(f"  {w:20} {len(hits)} occurrence(s)")
    for p in hits[:3]:
        frag = re.sub(r"\s+", " ", (home or "")[max(0, p - 120):p + 120])
        print(f"      ...{frag}...")
print()

print("#" * 70)
print("# SITEMAP")
print("#" * 70)
for u in (f"{BASE}/sitemap.xml", f"{BASE}/sitemap_index.xml",
          f"{BASE}/sitemap.xml.gz"):
    print(f"--- {u}")
    b = get(u, quiet=False)
    if b:
        print("    first 600 chars:", repr(b[:600]))
print()

robots_block("repeat")
print("PROBE COMPLETE")
