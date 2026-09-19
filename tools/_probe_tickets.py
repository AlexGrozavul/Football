"""TEMPORARY probe v2. Delete after reading the log.

fcbayern.com is NOT fetched here. It answers 403 (AkamaiGHost) to this
runner, which is a bot-management refusal, and the rule is stop, not
evade. Only public archives and third-party pages are read.
"""
import json
import re
import subprocess
import time

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
recap = []


def get(url, timeout=60):
    try:
        p = subprocess.run(
            ["curl", "-sSL", "-m", str(timeout), "-A", UA,
             "-w", "\n__HTTP__%{http_code}", url],
            capture_output=True, text=True, timeout=timeout + 20)
        body = p.stdout
        m = re.search(r"\n__HTTP__(\d+)$", body)
        code = m.group(1) if m else "?"
        return code, (body[:m.start()] if m else body)
    except Exception as e:
        return "ERR", str(e)[:200]


def text(html):
    html = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " | ", html)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&euro;", "EUR"),
                 ("&#8364;", "EUR"), ("&quot;", '"'), ("&#039;", "'"),
                 ("&uuml;", "ue"), ("&auml;", "ae"), ("&ouml;", "oe"),
                 ("&szlig;", "ss"), ("&Uuml;", "Ue")):
        html = html.replace(a, b)
    html = re.sub(r"(\s*\|\s*)+", " | ", html)
    return re.sub(r"[ \t]+", " ", html).strip()


def windows(t, keys, radius=260, cap=9000):
    """Text around each keyword hit, merged and deduplicated."""
    spans = []
    low = t.lower()
    for k in keys:
        start = 0
        while True:
            i = low.find(k, start)
            if i < 0:
                break
            spans.append((max(0, i - radius), min(len(t), i + radius)))
            start = i + 1
    if not spans:
        return ""
    spans.sort()
    merged = [list(spans[0])]
    for s, e in spans[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    out = "\n   ...\n".join(t[s:e] for s, e in merged)
    return out[:cap]


# ------------------------------------------------- A. archive snapshots
print("=" * 70)
print("A. PUBLIC ARCHIVE - does a snapshot of the FC Bayern pages exist?")
print("=" * 70)

FCB = [
    ("season-request", "fcbayern.com/de/tickets/info/anfragen-fuer-die-neue-saison-2026-2027"),
    ("jahreskarten", "fcbayern.com/de/tickets/jahreskarten"),
    ("faq-jahreskarten", "fcbayern.com/de/tickets/faq-jahreskarten"),
    ("preise", "fcbayern.com/de/tickets/info/preise-und-ermaessigungen"),
    ("adk", "fcbayern.com/de/tickets/auswaerts-dauerkarte"),
]

snaps = {}
for label, u in FCB:
    ok = False
    for attempt in (1, 2, 3):
        code, body = get("https://web.archive.org/cdx/search/cdx?url="
                         + u + "&output=json&limit=-4"
                         + "&filter=statuscode:200&collapse=digest", 70)
        if code == "200":
            ok = True
            break
        time.sleep(15)
    if not ok:
        print("\n--- %s : cdx unreachable (HTTP %s after 3 tries)" % (label, code))
        recap.append("ARCHIVE %s: cdx unreachable" % label)
        time.sleep(8)
        continue
    rows = []
    try:
        rows = json.loads(body) if body.strip().startswith("[") else []
    except Exception:
        pass
    if len(rows) > 1:
        stamps = [r[1] for r in rows[1:]]
        print("\n--- %s : %d snapshot(s): %s" % (label, len(stamps), ", ".join(stamps)))
        snaps[label] = (stamps[-1], u)
        recap.append("ARCHIVE %s: newest %s" % (label, stamps[-1]))
    else:
        print("\n--- %s : NO SNAPSHOTS (cdx answered 200 with an empty list)" % label)
        recap.append("ARCHIVE %s: NONE (conclusive)" % label)
    time.sleep(8)

AKEYS = ("jahreskart", "dauerkart", "auswaerts", "adk", "einzelkart", "anfrag",
         "verlaeng", "frist", "juni", "juli", "verlos", "ueberbuch", "saison")

for label, (ts, u) in snaps.items():
    print("\n" + "=" * 70)
    print("ARCHIVED TEXT: %s (captured %s)" % (label, ts))
    print("=" * 70)
    code, body = get("https://web.archive.org/web/%sid_/https://%s" % (ts, u), 90)
    print("  fetch HTTP %s (%d bytes)" % (code, len(body)))
    if code == "200":
        print(windows(text(body), AKEYS, 300, 7000))
    time.sleep(6)

# ------------------------------------------------- B. price pages
print("\n" + "=" * 70)
print("B. THIRD-PARTY CHAMPIONS LEAGUE PRICE PAGES")
print("=" * 70)

SITES = [
    ("fussball-tickets-kaufen", "https://www.fussball-tickets-kaufen.de/fc-bayern-champions-league-tickets/"),
    ("ran-achtelfinale", "https://www.ran.de/sports/fussball/champions-league/galerien/fc-bayern-muenchen-fc-liverpool-paris-saint-germain-und-co-die-ticketpreise-im-champions-league-achtelfinale-85523"),
    ("goal-bodoglimt", "https://www.goal.com/en/news/bayern-munich-bodoe-glimt-tickets/blt9880df56bba4aef8"),
    ("tickets-aktuell", "https://www.tickets-aktuell.de/fussball/fc-bayern-tickets/"),
    ("event-com-de", "https://event.com.de/bayern-muenchen-tickets.html"),
]

PKEYS = ("kategorie", "stehplatz", "suedkurve", "ligaphase", "gruppenphase",
         "achtelfinale", "viertelfinale", "halbfinale", "preiskategorie")

for label, url in SITES:
    print("\n" + "-" * 70)
    code, body = get(url, 60)
    print("%s -> HTTP %s (%d bytes)" % (label, code, len(body)))
    if code != "200":
        recap.append("PRICES %s: HTTP %s" % (label, code))
        continue
    w = windows(text(body), PKEYS, 300, 8000)
    print(w if w else "  no keyword hits")
    recap.append("PRICES %s: HTTP 200, %d chars extracted" % (label, len(w)))
    time.sleep(3)

print("\n" + "=" * 70)
print("RECAP")
print("=" * 70)
for r in recap:
    print(" ", r)
