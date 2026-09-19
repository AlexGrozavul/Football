"""TEMPORARY probe. Delete after reading the log.

Two questions:
  A. Does a PUBLIC ARCHIVE hold a copy of the FC Bayern ticket pages?
     fcbayern.com itself answers 403 (AkamaiGHost) to this runner and is
     NOT retried here - that is a bot-management refusal and the rule is
     stop, not evade. An archive snapshot is a third party's public copy.
  B. What do third-party pages say about Champions League prices by round?

Prints a compact recap first and last; detail in between.
"""
import json
import re
import subprocess
import sys

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

recap = []


def get(url, timeout=45):
    try:
        p = subprocess.run(
            ["curl", "-sSL", "-m", str(timeout), "-A", UA,
             "-w", "\n__HTTP__%{http_code}", url],
            capture_output=True, text=True, timeout=timeout + 15)
        body = p.stdout
        m = re.search(r"\n__HTTP__(\d+)$", body)
        code = m.group(1) if m else "?"
        body = body[:m.start()] if m else body
        return code, body
    except Exception as e:
        return "ERR", str(e)[:200]


def text(html):
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    html = (html.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&euro;", "EUR").replace("&#8364;", "EUR")
                .replace("&quot;", '"').replace("&#039;", "'")
                .replace("&uuml;", "ue").replace("&auml;", "ae")
                .replace("&ouml;", "oe").replace("&szlig;", "ss"))
    return re.sub(r"\s+", " ", html).strip()


# ---------------------------------------------------------------- A
FCB = [
    ("season-request", "fcbayern.com/de/tickets/info/anfragen-fuer-die-neue-saison-2026-2027"),
    ("jahreskarten", "fcbayern.com/de/tickets/jahreskarten"),
    ("faq-jahreskarten", "fcbayern.com/de/tickets/faq-jahreskarten"),
    ("preise", "fcbayern.com/de/tickets/info/preise-und-ermaessigungen"),
]

print("=" * 70)
print("A. WAYBACK SNAPSHOTS OF THE FC BAYERN PAGES")
print("=" * 70)

snaps = {}
for label, u in FCB:
    code, body = get("http://web.archive.org/cdx/search/cdx?url=" + u
                     + "&output=json&limit=-6&filter=statuscode:200&collapse=digest")
    print("\n--- %s : cdx HTTP %s" % (label, code))
    rows = []
    try:
        rows = json.loads(body) if body.strip().startswith("[") else []
    except Exception as e:
        print("   cdx parse failed:", str(e)[:120])
    if len(rows) > 1:
        for r in rows[1:]:
            print("   snapshot", r[1])
        snaps[label] = (rows[-1][1], u)
        recap.append("ARCHIVE %s: %d snapshot(s), newest %s"
                     % (label, len(rows) - 1, rows[-1][1]))
    else:
        print("   NO SNAPSHOTS (raw: %s)" % body[:120].replace("\n", " "))
        recap.append("ARCHIVE %s: NONE" % label)

KEYS = ("jahreskart", "dauerkart", "auswaerts", "auswärts", "adk", "einzelkart",
        "anfrag", "verlaenger", "verläng", "frist", "juni", "juli", "mai",
        "ueberbuch", "überbuch", "verlosung", "saison")

for label, (ts, u) in snaps.items():
    print("\n" + "=" * 70)
    print("ARCHIVED TEXT: %s  (captured %s)" % (label, ts))
    print("=" * 70)
    code, body = get("https://web.archive.org/web/%sid_/https://%s" % (ts, u), 60)
    if code != "200":
        print("  fetch HTTP %s" % code)
        continue
    t = text(body)
    # Drop the archive's own banner.
    i = t.lower().find("tickets")
    t = t[max(0, i - 200):]
    sents = re.split(r"(?<=[.!?])\s+", t)
    keep = [s for s in sents if any(k in s.lower() for k in KEYS)]
    out = " ".join(keep) if keep else t
    print(out[:3500])


# ---------------------------------------------------------------- B
print("\n" + "=" * 70)
print("B. THIRD-PARTY CHAMPIONS LEAGUE PRICE PAGES")
print("=" * 70)

SITES = [
    ("fussball-tickets-kaufen", "https://www.fussball-tickets-kaufen.de/fc-bayern-champions-league-tickets/"),
    ("dazn", "https://www.dazn.com/de-DE/news/fussball/fc-bayern-muenchen-wie-viel-kosten-die-tickets-in-der-champions-league/tnbz60uxmtdt18spm016xuhuf"),
    ("ran-achtelfinale", "https://www.ran.de/sports/fussball/champions-league/galerien/fc-bayern-muenchen-fc-liverpool-paris-saint-germain-und-co-die-ticketpreise-im-champions-league-achtelfinale-85523"),
    ("bundesliga-tickets", "https://bundesliga-tickets.com/vereine/fc-bayern-muenchen/"),
]

PRICE_KEYS = ("kategorie", "kat.", "stehplatz", "suedkurve", "südkurve",
              "ligaphase", "gruppenphase", "achtelfinale", "viertelfinale",
              "halbfinale", "champions league", "preis", "euro", "eur")

for label, url in SITES:
    print("\n" + "-" * 70)
    code, body = get(url, 50)
    print("%s -> HTTP %s (%d bytes)" % (label, code, len(body)))
    if code != "200":
        recap.append("PRICES %s: HTTP %s" % (label, code))
        continue
    t = text(body)
    sents = re.split(r"(?<=[.!?;])\s+", t)
    keep = [s for s in sents
            if any(k in s.lower() for k in PRICE_KEYS)
            and re.search(r"\d{2,3}\s*(EUR|€|Euro)", s, re.I)]
    seen, uniq = set(), []
    for s in keep:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    print(" ".join(uniq)[:2500] if uniq else "  no price sentences matched")
    recap.append("PRICES %s: HTTP 200, %d price sentence(s)" % (label, len(uniq)))

print("\n" + "=" * 70)
print("RECAP")
print("=" * 70)
for r in recap:
    print(" ", r)
