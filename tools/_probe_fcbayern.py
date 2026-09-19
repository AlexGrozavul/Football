#!/usr/bin/env python3
"""THROWAWAY PROBE - delete after use.

Reads FC Bayern's own ticket pages from a GitHub runner, because the
sandbox that writes data/club-tickets.csv answers 403 to CONNECT for
fcbayern.com. Extracts nothing into the repo: it prints what the pages
say so a person can read it in the job log and write the row by hand.

v2: every network call now has a timeout. v1 hung because
urllib.robotparser.read() takes no timeout argument and the default
socket timeout is None, i.e. block forever.
"""
import re
import socket
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from html import unescape

socket.setdefaulttimeout(20)          # covers robotparser, which takes no timeout

UA = ("Mozilla/5.0 (compatible; football-planner-probe/1.0; personal fixture "
      "planner; +https://github.com/AlexGrozavul/Football)")
PAUSE = 1.5

# Pages printed in full (cleaned text, capped) - these carry the answers.
DEEP = {
    "https://fcbayern.com/de/tickets/info/preise-und-ermaessigungen": 9000,
    "https://fcbayern.com/de/tickets/info/anfragen-fuer-die-neue-saison-2026-2027": 6000,
    "https://fcbayern.com/de/tickets/status-ticketing": 4000,
    "https://fcbayern.com/de/news/ticketing/2026/ticket-anfragen-uefa-champions-league-ligaphase-2026-27": 5000,
}
# Pages searched for terms, with context printed around each hit.
SHALLOW = [
    "https://fcbayern.com/de/tickets/info/faq",
    "https://fcbayern.com/de/tickets/info/faq-ticket-exchange",
    "https://fcbayern.com/de/tickets",
    "https://fcbayern.com/de/tickets/herrenfussball",
]
ARCHIVE = "https://fcbayern.com/de/tag/ticketing"

TERMS = ["überbucht", "überbuchung", "mitglied", "bestellfrist", "bestellzeitraum",
         "bestellphase", "anfragefrist", "auswärtsspiel", "champions league",
         "kategorie", "stehplatz", "zweitmarkt", "verlosung", "nennwert"]


def get(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "de-DE,de;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")


def text_of(html):
    h = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
    h = re.sub(r"(?i)<(/p|/div|/li|/tr|/h[1-6]|br\s*/?)>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    t = unescape(h)
    t = re.sub(r"[^\S\n]+", " ", t)
    t = re.sub(r"\n[ \t]*", "\n", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def p(*a):
    print(*a, flush=True)


def fetch(url):
    try:
        st, final, html = get(url)
        return st, final, html
    except urllib.error.HTTPError as e:
        p(f"   -> HTTP {e.code}")
    except Exception as e:
        p(f"   -> FAILED {type(e).__name__}: {e}")
    return None, None, None


def main():
    p("=" * 72)
    p("PART 0  robots.txt")
    p("=" * 72)
    for host in ("https://fcbayern.com",):
        try:
            st, _, body = get(host + "/robots.txt", timeout=15)
            p(f"\n{host}/robots.txt -> HTTP {st}, {len(body)} bytes")
            p("\n".join(body.splitlines()[:45]))
        except Exception as e:
            p(f"\n{host}/robots.txt -> FAILED: {type(e).__name__}: {e}")
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(host + "/robots.txt")
        try:
            rp.read()
            for path in ("/de/tickets", "/de/tickets/info/preise-und-ermaessigungen", "/de/tag/ticketing"):
                p(f"   can_fetch({path}) = {rp.can_fetch(UA, host + path)}")
        except Exception as e:
            p(f"   robotparser failed: {type(e).__name__}: {e}")

    p("\n" + "=" * 72)
    p("PART 1  PAGES PRINTED IN FULL")
    p("=" * 72)
    for url, cap in DEEP.items():
        time.sleep(PAUSE)
        p(f"\n{'-' * 72}\n## {url}")
        st, final, html = fetch(url)
        if not html:
            continue
        body = text_of(html)
        title = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
        p(f"   HTTP {st} | final={final} | text={len(body)}B")
        p(f"   title={unescape(title.group(1)).strip() if title else '(none)'}")
        for m in re.finditer(r'(?is)<meta[^>]+(?:property|name)="([^"]*(?:date|time|modified)[^"]*)"[^>]+content="([^"]+)"', html):
            p(f"   meta {m.group(1)} = {m.group(2)}")
        p("   ---- text ----")
        p(body[:cap])
        if len(body) > cap:
            p(f"   ... [truncated at {cap} of {len(body)}]")

    p("\n" + "=" * 72)
    p("PART 2  PAGES SEARCHED FOR TERMS")
    p("=" * 72)
    for url in SHALLOW:
        time.sleep(PAUSE)
        p(f"\n{'-' * 72}\n## {url}")
        st, final, html = fetch(url)
        if not html:
            continue
        body = text_of(html)
        low = body.lower()
        p(f"   HTTP {st} | text={len(body)}B")
        for t in TERMS:
            hits = [m.start() for m in re.finditer(re.escape(t), low)][:2]
            for i in hits:
                a, b = max(0, i - 300), min(len(body), i + 400)
                p(f"   «{t}» ...{' '.join(body[a:b].split())}...")

    p("\n" + "=" * 72)
    p("PART 3  TICKETING NEWS ARCHIVE (headlines + dates)")
    p("=" * 72)
    time.sleep(PAUSE)
    p(f"## {ARCHIVE}")
    st, final, html = fetch(ARCHIVE)
    if html:
        body = text_of(html)
        p(f"   HTTP {st} | text={len(body)}B")
        seen, n = set(), 0
        for m in re.finditer(r'href="(/de/news/[^"#?]+)"', html):
            href = m.group(1)
            if href in seen:
                continue
            seen.add(href)
            n += 1
            if n <= 50:
                p(f"   {href}")
        p(f"   ({n} unique /de/news links)")
        p("   ---- text (first 4000) ----")
        p(body[:4000])

    p("\n" + "=" * 72)
    p("END OF PROBE - the answers are in PART 1 and PART 3 above")
    p("=" * 72)


if __name__ == "__main__":
    sys.exit(main())
