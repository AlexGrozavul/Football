#!/usr/bin/env python3
"""TEMPORARY throwaway probe, third pass. Delete after the run.

Pass two printed only the first 9,000 characters of the 43,000-character
Datenschutzerklaerung, so the sweep for prohibition wording did not cover
all of it. This pass sweeps the COMPLETE text of every real page and
prints only the headings and the hits, so the answer is not capped.

It reports verbatim and interprets nothing. It builds nothing.
"""

import html
import re
import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (compatible; europlan-probe/1.0; one-off manual check)"
BASE = "https://europlan-online.de"

# Anything that would amount to a restriction on reading the site, or a
# permission to. German first, then English.
WORDS = [
    "untersagt", "verboten", "nicht gestattet", "unzulässig", "dürfen nicht",
    "darf nicht", "nicht erlaubt", "keine automat", "automatisiert",
    "automatisch", "systematisch", "massenhaft", "crawl", "scrap", "spider",
    "harvest", "data mining", "data-mining", "text und data", "roboter",
    "bot ", "bots", "skript", "rate limit", "zugriffsbeschränk",
    "nur für den persönlichen", "private nutzung", "gewerblich",
    "kommerziell", "vervielfält", "verwertung", "weiterverwend",
    "datenbank", "schnittstelle", "api", "download", "herunterladen",
    "einwilligung", "zustimmung", "genehmigung", "erlaubnis", "lizenz",
    "nutzungsbedingung", "agb", "terms of use",
]

PAGES = {
    "impressum": f"{BASE}/index.php?s=impressum",
    "datenschutz": f"{BASE}/index.php?s=datenschutz",
    "faq": f"{BASE}/index.php?s=faq",
    "kontakt": f"{BASE}/index.php?s=kontakt",
}


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "*/*", "Accept-Language": "de,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw, hdr, st = r.read(), dict(r.headers), r.status
    except urllib.error.HTTPError as e:
        raw, hdr, st = e.read(), dict(e.headers) if e.headers else {}, e.code
    except Exception as e:
        print(f"  FAILED {url}: {type(e).__name__} {e}")
        return None, None
    cs = "utf-8"
    m = re.search(r"charset=([\w-]+)", hdr.get("Content-Type", ""), re.I)
    if m:
        cs = m.group(1)
    time.sleep(1)
    return st, raw.decode(cs, errors="replace")


def text(h):
    t = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</(p|div|tr|li|h\d)>", "\n", t, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t).strip()


print("Sweeping the COMPLETE text of every real page. Nothing is capped.")
print()
for name, url in PAGES.items():
    st, body = fetch(url)
    if body is None:
        continue
    t = text(body)
    print("=" * 70)
    print(f"PAGE {name}  HTTP {st}  full text {len(t)} chars")
    print("=" * 70)

    heads = re.findall(r"<h([1-4])[^>]*>(.*?)</h\1>", body, re.S | re.I)
    print("  headings:")
    for lvl, htxt in heads:
        clean = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", htxt))).strip()
        if clean:
            print(f"    h{lvl}: {clean[:110]}")

    print("  sweep over the whole page:")
    total = 0
    for w in WORDS:
        hits = [m.start() for m in re.finditer(re.escape(w), t, re.I)]
        if not hits:
            continue
        total += len(hits)
        print(f"    [{w}] {len(hits)} hit(s)")
        for p in hits[:3]:
            frag = re.sub(r"\s+", " ", t[max(0, p - 200):p + 260])
            print(f"        ...{frag}...")
    if total == 0:
        print("    nothing matched on this page")
    print()

print("PROBE COMPLETE")
