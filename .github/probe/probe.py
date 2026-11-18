#!/usr/bin/env python3
"""Temporary probe (phase 5, culture rows): reads Wikipedia pages through the MediaWiki
parse API and posts only the matching sentences as PR comments. Removed before merge."""
import html, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request, urllib.error
from html.parser import HTMLParser

UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
REQ = 0
CTX = re.compile(r"rival|derb|feind|freund|amiti|prieten|inimicizia|nemic|enem|"
                 r"reserve|zweite mannschaft|filial|second team|b team|b-team|affiliat|beloften|"
                 r"tradition|ostilit|hostil|antagon|fanfreund|gemellag|amic|twin", re.I)

def api(lang, params):
    global REQ
    params = dict(params, format="json", formatversion="2", maxlag="5")
    url = "https://%s.wikipedia.org/w/api.php?%s" % (lang, urllib.parse.urlencode(params))
    for attempt in range(6):
        REQ += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40) as r:
                data = json.load(r)
            if isinstance(data, dict) and data.get("error", {}).get("code") == "maxlag":
                time.sleep(8); continue
            time.sleep(1)
            return data
        except urllib.error.HTTPError as e:
            wait = int(e.headers.get("Retry-After") or 20)
            time.sleep(min(max(wait, 5), 60))
        except Exception:
            time.sleep(10)
    return None

BLOCK = {"p", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "div", "br", "dd", "dt", "caption", "table", "ul", "ol"}

class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.out = []; self.skip = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.skip or tag in ("style", "script") or (tag == "sup" and "reference" in (a.get("class") or "")) \
                or "mw-editsection" in (a.get("class") or ""):
            if tag not in ("br",):
                self.skip += 1
            return
        if tag in BLOCK: self.out.append("\n")
        if tag in ("td", "th"): self.out.append(" | ")
    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1; return
        if tag in BLOCK: self.out.append("\n")
    def handle_data(self, d):
        if not self.skip: self.out.append(d)

VOID = {"br", "img", "hr", "meta", "link", "input", "wbr", "area", "col", "source"}

def page(url):
    u = urllib.parse.urlparse(url)
    lang = u.netloc.split(".")[0]
    q = urllib.parse.parse_qs(u.query)
    title = q["title"][0] if "title" in q else urllib.parse.unquote(u.path.split("/wiki/", 1)[1])
    params = {"action": "parse", "page": title.replace("_", " "), "prop": "text|revid", "disableeditsection": "1", "disabletoc": "1"}
    if "redirect=no" not in url:
        params["redirects"] = "1"
    d = api(lang, params)
    if not d or "parse" not in d:
        return None, (d or {}).get("error", {}).get("code", "no answer")
    h = d["parse"]["text"]
    h = re.sub(r"<(%s)(\s[^>]*)?/?>" % "|".join(VOID), "\n", h)
    t = Text(); t.feed(h)
    txt = html.unescape("".join(t.out))
    txt = re.sub(r"[ \t ]+", " ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt)
    return (d["parse"]["title"], d["parse"]["revid"], txt), None

def norm(s):
    s = unicodedata.normalize("NFC", s)
    for a, b in (("„", '"'), ("“", '"'), ("”", '"'), ("«", '"'), ("»", '"'), ("’", "'"), ("‘", "'"), ("–", "-"), ("—", "-"), (" ", " ")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s)

def units(txt):
    out = []
    for line in txt.split("\n"):
        line = line.strip()
        if len(line) < 3: continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ÝȘȚĂÎÂ0-9\"„«])", line):
            if s.strip(): out.append(s.strip())
    return out

def snip(u, m, width=300):
    if len(u) <= width: return u
    a = max(0, m.start() - width // 2)
    return ("…" if a else "") + u[a:a + width] + "…"

def main(cfg):
    rows = [l.rstrip("\n").split("\t") for l in open(cfg, encoding="utf-8") if l.strip() and not l.startswith("#")]
    cache, blocks = {}, []
    for r in rows:
        rid, url, ta, tb = r[:4]
        quote = r[4] if len(r) > 4 else ""
        key = url.split("#")[0]
        if key not in cache:
            cache[key] = page(key)
        res, err = cache[key]
        if not res:
            blocks.append("**%s** %s: NOT READ (%s)" % (rid, url, err)); continue
        title, revid, txt = res
        nt = norm(txt)
        ra, rb = re.compile(ta, re.I), re.compile(tb, re.I)
        line = "**%s** %s rev %s | A:%d B:%d" % (rid, title, revid, len(ra.findall(txt)), len(rb.findall(txt)))
        if quote:
            q = norm(quote)
            if q in nt: line += " | quote: ON PAGE"
            elif q.lower() in nt.lower(): line += " | quote: on page (case differs)"
            else:
                line += " | quote: NOT FOUND"
                w = q.split()
                for n in (6, 4, 3):
                    head = " ".join(w[:n]); tail = " ".join(w[-n:])
                    hit = [u for u in units(nt) if head in u or tail in u]
                    if hit:
                        line += "\n> nearest: " + hit[0][:400]; break
        us = units(txt)
        scored = []
        for i, u in enumerate(us):
            m = rb.search(u)
            if not m: continue
            sc = (2 if ra.search(u) else 0) + (1 if CTX.search(u) else 0)
            scored.append((-sc, i, u, m))
        scored.sort(key=lambda x: (x[0], x[1]))
        for sc, i, u, m in scored[:3]:
            line += "\n> [%d] %s" % (-sc, snip(u, m))
        if not scored:
            line += "\n> (other side not named on the page)"
        blocks.append(line)
    blocks.append("requests: %d" % REQ)
    post(blocks)

def post(blocks):
    label = os.environ.get("RUN_LABEL") or "run"
    chunks, cur = [], ""
    for b in blocks:
        if len(cur) + len(b) > 60000:
            chunks.append(cur); cur = ""
        cur += b + "\n\n"
    if cur: chunks.append(cur)
    tok, pr, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("PR"), os.environ.get("REPO")
    for n, c in enumerate(chunks, 1):
        body = "probe %s, part %d/%d\n\n%s" % (label, n, len(chunks), c)
        if not tok:
            print(body); continue
        req = urllib.request.Request("https://api.github.com/repos/%s/issues/%s/comments" % (repo, pr),
                                     data=json.dumps({"body": body}).encode(), method="POST",
                                     headers={"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json", "User-Agent": UA})
        urllib.request.urlopen(req, timeout=30).read()

if __name__ == "__main__":
    main(sys.argv[1])
