#!/usr/bin/env python3
"""Temporary probe (phase 5b, quote-less other rivalry rows): reads Wikipedia pages through the MediaWiki
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
        if tag in ("h2", "h3", "h4"): self.out.append("\u0001%s " % tag[1])
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

CLS = re.compile(r"local derb|city derb|lokalderb|stadtderb|derby local|derbi local|derby cittadin|derby locale|derbiul local|lokalni derbi|"
                 r"main rival|biggest rival|greatest rival|fiercest|arch-?rival|archrival|hauptrival|erzrival|principal|rivale principal|"
                 r"local rival|bitter rival|traditional rival|most important", re.I)

def sections(txt, frag):
    """[(heading, line)] for the page or for the section the fragment names."""
    out, head, lvl_in, keep = [], "(lead)", None, frag is None
    want = norm(urllib.parse.unquote(frag or "").replace("_", " ")).lower()
    for line in txt.split("\n"):
        line = line.strip()
        if line.startswith("\u0001"):
            lvl, h = int(line[1]), line[2:].strip()
            head = h
            if frag is not None:
                if keep and lvl <= lvl_in: keep = False
                if not keep and norm(h).lower() == want: keep, lvl_in = True, lvl
            continue
        if keep and len(line) >= 3: out.append((head, line))
    return out

def sents(secs):
    out = []
    for head, line in secs:
        for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ÝȘȚĂÎÂ0-9\"„«])", line):
            if s.strip(): out.append((head, s.strip()))
    return out

def main(cfg):
    rows = [l.rstrip("\n").split("\t") for l in open(cfg, encoding="utf-8") if l.strip() and not l.startswith("#")]
    cache, blocks, seen = {}, [], {}
    for r in rows:
        rid, url, ta, tb = r[:4]
        key = url.split("#")[0]
        frag = url.split("#", 1)[1] if "#" in url else None
        if key not in cache:
            cache[key] = page(key)
        res, err = cache[key]
        if not res:
            blocks.append("**%s** %s: NOT READ (%s)" % (rid, url, err)); continue
        title, revid, txt = res
        secs = sections(txt, frag)
        ss = sents(secs)
        ra, rb = re.compile(ta, re.I), re.compile(tb, re.I)
        both = [(h, u) for h, u in ss if ra.search(u) and rb.search(u)]
        one = [(h, u) for h, u in ss if (ra.search(u) or rb.search(u)) and CLS.search(u) and (h, u) not in both]
        lead = []
        if frag is None and not title.lower().startswith(("list", "german football")):
            lead = [(h, u) for h, u in ss if CLS.search(u) and (h, u) not in both and (h, u) not in one][:2]
        sig = (key, frag, tuple(both), tuple(one))
        line = "**%s** %s%s rev %s | sec lines %d | both %d" % (rid, title, ("#" + frag) if frag else "", revid, len(secs), len(both))
        if sig in seen:
            blocks.append(line + " | same sentences as " + seen[sig]); continue
        seen[sig] = rid
        for h, u in both[:5]:
            line += "\n> [both | %s] %s" % (h[:50], u[:420])
        for h, u in one[:3]:
            line += "\n> [one+class | %s] %s" % (h[:50], u[:300])
        for h, u in lead:
            line += "\n> [class | %s] %s" % (h[:50], u[:300])
        if not both:
            line += "\n> (no sentence names both clubs)"
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
