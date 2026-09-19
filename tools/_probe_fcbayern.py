#!/usr/bin/env python3
"""THROWAWAY PROBE - delete after use.

Reads FC Bayern's own ticket pages from a GitHub runner, because the
sandbox that writes data/club-tickets.csv answers 403 to CONNECT for
fcbayern.com. Extracts nothing into the repo: it prints what the pages
say so a person can read it in the job log and write the row by hand.

Output is kept small on purpose - a previous probe in this repo dumped
a site's whole link list and the log no longer reached the answer.
"""
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from html import unescape

UA = "Mozilla/5.0 (compatible; football-planner-probe/1.0; personal fixture planner; +https://github.com/AlexGrozavul/Football)"
PAUSE = 2.0

PAGES = [
    "https://fcbayern.com/de/tickets",
    "https://fcbayern.com/de/tickets/status-ticketing",
    "https://fcbayern.com/de/tickets/info/faq-ticket-exchange",
    "https://fcbayern.com/de/tickets/info/ticketpreise",
    "https://fcbayern.com/de/tickets/info",
    "https://fcbayern.com/de/tickets/bundesliga",
    "https://tickets.fcbayern.com/",
]

TERMS = [
    "überbucht", "überbuchung", "mitglied", "bestellfrist", "bestellzeitraum",
    "bestellphase", "ticketanfrage", "auswärtsspiel", "champions league",
    "kategorie", "stehplatz", "zweitmarkt", "verlosung", "bestellung",
]


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "de-DE,de;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")


def text_of(html):
    h = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"[ \t\r\f\v]*\n\s*", "\n", re.sub(r"[^\S\n]+", " ", unescape(h))).strip()


def show(label, body, terms, width=260, cap=3):
    low = body.lower()
    for t in terms:
        hits = [m.start() for m in re.finditer(re.escape(t), low)][:cap]
        if not hits:
            continue
        for i in hits:
            a, b = max(0, i - width // 2), min(len(body), i + width // 2)
            snippet = " ".join(body[a:b].split())
            print(f"  [{label}] «{t}» ...{snippet}...")


def main():
    print("=" * 72)
    print("ANSWER BLOCK (top) - filled in below, repeated at the end")
    print("=" * 72)

    for host in ("https://fcbayern.com", "https://tickets.fcbayern.com"):
        try:
            st, _, body = get(host + "/robots.txt", timeout=20)
            print(f"\n### robots.txt {host} -> HTTP {st}, {len(body)} bytes")
            print("\n".join(body.splitlines()[:40]))
        except Exception as e:
            print(f"\n### robots.txt {host} -> FAILED: {type(e).__name__}: {e}")

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(host + "/robots.txt")
        try:
            rp.read()
            print(f"    can_fetch('{host}/de/tickets') = {rp.can_fetch(UA, host + '/de/tickets')}")
        except Exception as e:
            print(f"    robotparser failed: {e}")
        time.sleep(PAUSE)

    print("\n" + "=" * 72)
    print("PAGES")
    print("=" * 72)
    fetched = {}
    for url in PAGES:
        time.sleep(PAUSE)
        try:
            st, final, html = get(url)
        except urllib.error.HTTPError as e:
            print(f"\n## {url} -> HTTP {e.code}")
            continue
        except Exception as e:
            print(f"\n## {url} -> FAILED {type(e).__name__}: {e}")
            continue
        body = text_of(html)
        fetched[url] = (final, html, body)
        title = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
        print(f"\n## {url}")
        print(f"   HTTP {st} | final={final} | html={len(html)}B | text={len(body)}B")
        print(f"   title={unescape(title.group(1)).strip() if title else '(none)'}")
        present = [t for t in TERMS if t in body.lower()]
        print(f"   terms present: {', '.join(present) if present else '(none)'}")
        show(url.rsplit('/', 1)[-1] or "root", body, present)

    print("\n" + "=" * 72)
    print("LINKS under /de/tickets (paths only, deduped, capped)")
    print("=" * 72)
    if "https://fcbayern.com/de/tickets" in fetched:
        html = fetched["https://fcbayern.com/de/tickets"][1]
        paths = sorted({m for m in re.findall(r'href="([^"#?]*(?:ticket|preis|mitglied)[^"#?]*)"', html, re.I)})
        for p in paths[:60]:
            print("  ", p)
        print(f"   ({len(paths)} unique)")
    else:
        print("   /de/tickets was not fetched")

    print("\n" + "=" * 72)
    print("ANSWER BLOCK (repeated at the end) - see PAGES section above")
    print("=" * 72)


if __name__ == "__main__":
    sys.exit(main())
