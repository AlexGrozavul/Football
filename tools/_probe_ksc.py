"""THROWAWAY probe (KSC ticket research, 2026-10-06). Removed in the same branch.
Reads each URL in tools/_probe_urls.txt once, prints status and the page's
text, and lists links worth following. Never writes to the repo."""
import re, subprocess, sys, html, urllib.parse
from html.parser import HTMLParser

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
KEY = re.compile(r"ticket|karte|mitglied|derby|lautern|fck|zweitmarkt|marktplatz|agb|preis|vorverkauf|jugend|kinder|stadionordnung|newsletter|gast|sicherheit", re.I)
MAXC = int(sys.argv[2]) if len(sys.argv) > 2 else 7000

class T(HTMLParser):
    def __init__(s):
        super().__init__(); s.out=[]; s.skip=0; s.links=[]
    def handle_starttag(s, t, a):
        if t in ("script","style","noscript","svg"): s.skip+=1
        if t=="a":
            h=dict(a).get("href")
            if h: s.links.append(h)
        if t in ("p","br","li","h1","h2","h3","h4","tr","div","td","th"): s.out.append("\n")
        if t in ("td","th"): s.out.append(" | ")
    def handle_endtag(s, t):
        if t in ("script","style","noscript","svg") and s.skip: s.skip-=1
    def handle_data(s, d):
        if not s.skip: s.out.append(d)

def fetch(u):
    r = subprocess.run(["curl","-sS","-L","--max-time","40","-A",UA,"-o","/tmp/p.bin","-w","%{http_code} %{content_type} %{url_effective} %{size_download}",u],capture_output=True,text=True)
    return r.stdout.strip(), r.stderr.strip()

for u in [l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]:
    meta, err = fetch(u)
    print("\n" + "="*100 + f"\nURL {u}\nMETA {meta} {err}")
    data = open("/tmp/p.bin","rb").read() if meta else b""
    if b"%PDF" in data[:10]:
        subprocess.run(["pdftotext","-layout","/tmp/p.bin","/tmp/p.txt"])
        txt = open("/tmp/p.txt",errors="replace").read()
        print(re.sub(r"[ \t]+"," ",txt)[:MAXC*2]); continue
    doc = data.decode("utf-8","replace")
    m = re.search(r"<title>(.*?)</title>", doc, re.S|re.I)
    print("TITLE", html.unescape(m.group(1).strip()) if m else None)
    for k in ("article:published_time","datePublished","date"):
        mm = re.search(k + r'["\']?\s*(?:content=|:)\s*["\']([^"\']+)', doc)
        if mm: print("DATE", k, mm.group(1)); break
    body = doc
    mm = re.search(r"<main.*?</main>", doc, re.S|re.I) or re.search(r"<article.*?</article>", doc, re.S|re.I)
    if mm and len(mm.group(0)) > 2000: body = mm.group(0)
    p = T(); p.feed(doc)
    q = T(); q.feed(body)
    txt = re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t\xa0]+"," ","".join(q.out))).strip()
    print(txt[:MAXC])
    seen=set()
    for h in p.links:
        a = urllib.parse.urljoin(u, h)
        if KEY.search(a) and a not in seen and not a.startswith("mailto"):
            seen.add(a)
    print("LINKS", " ".join(sorted(seen))[:3000])
