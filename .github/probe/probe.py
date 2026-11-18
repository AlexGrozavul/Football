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

ABBR = re.compile(r"(\b(St|Nr|Dr|ca|bzw|vs|v|No|Jr|Mr|Inc|e\.V|z\.B)|\b\d{1,2})\.$")

def sents(secs):
    out = []
    for head, line in secs:
        parts = [p for p in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ÝȘȚĂÎÂ0-9\"„«])", line) if p.strip()]
        merged = []
        for p in parts:
            if merged and ABBR.search(merged[-1]): merged[-1] += " " + p
            else: merged.append(p)
        out += [(head, m.strip()) for m in merged]
    return out

CLS2 = re.compile(r"local derb|city derb|lokalderb|stadtderb|derby cittadin|derby local|main rival|arch-?rival|archrival|biggest rival|greatest rival|"
                  r"hauptrival|erzrival|principal rival|fiercest|most important rival|ewig", re.I)

def paths(txt, frag):
    """[(heading path, line)] for the page or the fragment's section."""
    out, stack, keep, lvl_in = [], {}, frag is None, None
    want = norm(urllib.parse.unquote(frag or "").replace("_", " ")).lower()
    for line in txt.split("\n"):
        line = line.strip()
        if line.startswith("\u0001"):
            lvl, h = int(line[1]), line[2:].strip()
            stack = {k: v for k, v in stack.items() if k < lvl}; stack[lvl] = h
            if frag is not None:
                if keep and lvl <= lvl_in: keep = False
                if not keep and norm(h).lower() == want: keep, lvl_in = True, lvl
            continue
        if keep and len(line) >= 3: out.append((" > ".join(stack[k] for k in sorted(stack)) or "(lead)", line))
    return out

def main(cfg):
    rows = [l.rstrip("\n").split("\t") for l in open(cfg, encoding="utf-8") if l.strip() and not l.startswith("#")]
    cache, blocks, seen = {}, [], {}
    for r in rows:
        rid, url, ta, tb, mode = r[:5]
        key = url.split("#")[0]
        frag = url.split("#", 1)[1] if "#" in url else None
        if key not in cache:
            cache[key] = page(key)
        res, err = cache[key]
        if not res:
            blocks.append("**%s** %s: NOT READ (%s)" % (rid, url, err)); continue
        title, revid, txt = res
        ra, rb = re.compile(ta, re.I), re.compile(tb, re.I)
        ps = paths(txt, frag)
        out = []
        if mode == "ctx":
            ls = [(h, l) for h, l in ps if not h.startswith(("References", "Notes", "Further", "External", "See also"))]
            n = 0
            for i, (h, l) in enumerate(ls):
                if not rb.search(l) or n >= 2: continue
                win = ls[max(0, i - 4):i + 5]
                if not any(ra.search(x) for _, x in win): continue
                n += 1
                out.append("[%s] window:" % h[:80] + "".join("\n>   %s%s" % ("=> " if j == i - max(0, i - 4) else "", x[:140]) for j, (_, x) in enumerate(win)))
            if not n: out.append("(no window of 9 lines names both)")
        elif mode == "list":
            hit = [(h, l) for h, l in ps if (rb.search(l) or rb.search(h.split(" > ")[-1])) and (ra.search(l) or ra.search(h))
                   and not h.startswith(("References", "Notes", "Further", "External", "See also"))]
            for h, l in hit[:6]: out.append("[%s] %s" % (h[:80], l[:300]))
            if not hit:
                out.append("(no line names both; lines naming B:)")
                for h, l in [(h, l) for h, l in ps if rb.search(l) and not h.startswith("References")][:3]:
                    out.append("[%s] %s" % (h[:80], l[:200]))
        else:
            ss = sents([(h, l) for h, l in ps if not l.startswith("|") and not h.startswith(("References", "Notes", "Further", "External", "See also"))])
            prose = [(h, u) for h, u in ss if len(u) > 70]
            lead = [(h, u) for h, u in prose if h == "(lead)"][:3]
            both = [(h, u) for h, u in prose if ra.search(u) and rb.search(u) and (h, u) not in lead][:3]
            cls = [(h, u) for h, u in ss if CLS2.search(u) and (h, u) not in lead + both][:4]
            for tag, lst in (("lead", lead), ("both", both), ("class", cls)):
                for h, u in lst: out.append("[%s | %s] %s" % (tag, h[:50], u[:450]))
        sig = (key, frag, tuple(out))
        line = "**%s** %s%s rev %s" % (rid, title, ("#" + frag) if frag else "", revid)
        if sig in seen:
            blocks.append(line + " | same as " + seen[sig]); continue
        seen[sig] = rid
        blocks.append(line + "".join("\n> " + o for o in out))
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
