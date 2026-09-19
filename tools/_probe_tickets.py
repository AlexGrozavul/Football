"""TEMPORARY probe v3. Delete after reading the log.

fcbayern.com is NOT fetched. It answers 403 (AkamaiGHost); a
bot-management refusal is a stop, not something to work around. These
are public archive copies only.

Target: the archived Tageskarte price page, which is where the
100/80/60/50/19 figures in club-ticket-prices.csv are supposed to come
from.
"""
import re
import subprocess
import time

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")


def get(url, timeout=90):
    try:
        p = subprocess.run(
            ["curl", "-sSL", "-m", str(timeout), "-A", UA,
             "-w", "\n__HTTP__%{http_code}", url],
            capture_output=True, text=True, timeout=timeout + 20)
        b = p.stdout
        m = re.search(r"\n__HTTP__(\d+)$", b)
        return (m.group(1) if m else "?"), (b[:m.start()] if m else b)
    except Exception as e:
        return "ERR", str(e)[:200]


def text(html):
    html = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " | ", html)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&euro;", "EUR"),
                 ("&#8364;", "EUR"), ("&quot;", '"'), ("&#039;", "'")):
        html = html.replace(a, b)
    html = re.sub(r"(\s*\|\s*)+", " | ", html)
    return re.sub(r"[ \t]+", " ", html).strip()


def windows(t, keys, radius=900, cap=14000):
    spans, low = [], t.lower()
    for k in keys:
        s = 0
        while True:
            i = low.find(k, s)
            if i < 0:
                break
            spans.append((max(0, i - radius), min(len(t), i + radius)))
            s = i + 1
    if not spans:
        return ""
    spans.sort()
    merged = [list(spans[0])]
    for a, b in spans[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return "\n   ...\n".join(t[a:b] for a, b in merged)[:cap]


KEYS = ("kategorie 1", "kategorie 5", "ligaphase", "achtelfinale",
        "viertelfinale", "tageskarte", "champions league")

# Snapshots found by probe v2, newest last.
TARGETS = [
    ("preise 2025-09-02", "20250902203843",
     "fcbayern.com/de/tickets/info/preise-und-ermaessigungen"),
    ("preise 2025-05-31", "20250531021605",
     "fcbayern.com/de/tickets/info/preise-und-ermaessigungen"),
    ("jahreskarten 2025-11-11", "20251111223232",
     "fcbayern.com/de/tickets/jahreskarten"),
]

for label, ts, u in TARGETS:
    print("=" * 70)
    print("ARCHIVED: %s (capture %s)" % (label, ts))
    print("=" * 70)
    code, body = get("https://web.archive.org/web/%sid_/https://%s" % (ts, u))
    print("  HTTP %s (%d bytes)" % (code, len(body)))
    if code == "200":
        w = windows(text(body), KEYS)
        print(w if w else "  no keyword hits")
    else:
        print("  retrying once")
        time.sleep(20)
        code, body = get("https://web.archive.org/web/%s/https://%s" % (ts, u))
        print("  retry HTTP %s (%d bytes)" % (code, len(body)))
        if code == "200":
            w = windows(text(body), KEYS)
            print(w if w else "  no keyword hits")
    time.sleep(10)

print("=" * 70)
print("ran.de: every 'N Euro' / 'N EUR' figure near 'Bayern'")
print("=" * 70)
code, body = get("https://www.ran.de/sports/fussball/champions-league/galerien/"
                 "fc-bayern-muenchen-fc-liverpool-paris-saint-germain-und-co-"
                 "die-ticketpreise-im-champions-league-achtelfinale-85523")
print("  HTTP %s (%d bytes)" % (code, len(body)))
if code == "200":
    t = text(body)
    print("  ---- windows round 'Bayern' ----")
    print(windows(t, ("bayern",), 700, 6000) or "  none")
    print("  ---- every price-ish figure ----")
    figs = re.findall(r"[^|]{0,90}\d{2,4}\s*(?:Euro|EUR|€)[^|]{0,90}", t)
    seen, out = set(), []
    for f in figs:
        f = f.strip()
        if f not in seen:
            seen.add(f)
            out.append(f)
    print("\n".join(out[:60]) if out else "  none")
