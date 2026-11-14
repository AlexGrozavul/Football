#!/usr/bin/env python3
"""TEMPORARY: derby audit, phase 3a. Reads the Wikipedia article each
sampled derbies.csv row names as its source (the MediaWiki API, wikitext)
and prints, per row, only the lines that name the pair. Removed before
the merge."""
import json, re, sys, time, unicodedata, urllib.parse, urllib.request

UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
REQUESTS = 0


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().replace("–", "-").replace("’", "'")


def has(text_n, needles):
    return any(norm(n) in text_n for n in needles)


def count(text_n, needles):
    return max([text_n.count(norm(n)) for n in needles] or [0])


def fetch(lang, title):
    """One page's wikitext. maxlag=5; on a lag refusal wait and retry."""
    global REQUESTS
    q = urllib.parse.urlencode({
        "action": "query", "prop": "revisions", "rvprop": "ids|timestamp|content",
        "rvslots": "main", "redirects": "1", "titles": title, "format": "json",
        "formatversion": "2", "maxlag": "5"})
    url = f"https://{lang}.wikipedia.org/w/api.php?{q}"
    for attempt in range(8):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        REQUESTS += 1
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.load(r)
                retry = r.headers.get("Retry-After")
        except urllib.error.HTTPError as e:
            retry = e.headers.get("Retry-After")
            if e.code in (429, 503):
                time.sleep(min(int(retry or 10), 120))
                continue
            return {"error": f"HTTP {e.code}"}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}
        if "error" in d:
            if d["error"].get("code") == "maxlag":
                time.sleep(min(int(retry or 5), 120) + 1)
                continue
            return {"error": json.dumps(d["error"])[:200]}
        qd = d.get("query", {})
        pg = (qd.get("pages") or [{}])[0]
        if pg.get("missing"):
            return {"error": "page missing", "title": pg.get("title")}
        rev = (pg.get("revisions") or [{}])[0]
        return {"title": pg.get("title"),
                "redirects": [f"{x['from']} -> {x['to']}" for x in qd.get("redirects", [])],
                "revid": rev.get("revid"), "ts": rev.get("timestamp"),
                "text": rev.get("slots", {}).get("main", {}).get("content", "")}
    return {"error": "still lagged after 8 tries"}


# ---------------------------------------------------------- wikitext
KEEP_LAST = re.compile(r"^\s*(lang|langx|lang-\w+|nowrap|transl|native name|nobr|small|fb team|football team)\s*\|", re.I)


def ref_summary(body):
    host = re.search(r"https?://([^/\s|\]}]+)", body)
    bits = [host.group(1) if host else "no url"]
    for k in ("work", "website", "newspaper", "publisher", "date", "title"):
        m = re.search(r"\|\s*" + k + r"\s*=\s*([^|}]+)", body)
        if m and m.group(1).strip():
            bits.append(f"{k}={m.group(1).strip()[:60]}")
    if len(bits) == 1 and not host:
        bits.append(re.sub(r"\s+", " ", body)[:80])
    return "[ref: " + "; ".join(bits) + "]"


def strip_templates(t):
    for _ in range(12):
        def rep(m):
            inner = m.group(1)
            if KEEP_LAST.match(inner):
                parts = [p for p in inner.split("|")[1:] if "=" not in p]
                return parts[-1] if parts else ""
            return ""
        new = re.sub(r"\{\{([^{}]*)\}\}", rep, t)
        if new == t:
            break
        t = new
    return t


def clean(t, named=None, refs=True):
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)

    def full(m):
        return (" " + ref_summary(m.group(2))) if refs else ""

    def short(m):
        if not refs:
            return ""
        nm = m.group(1).strip().strip('"').strip("'")
        return " " + (named or {}).get(nm, f"[ref name={nm}]")
    t = re.sub(r"<ref([^>/]*)>(.*?)</ref>", full, t, flags=re.S)
    t = re.sub(r"<ref\s+name\s*=\s*([^>/]+?)\s*/>", short, t)
    t = strip_templates(t)
    t = re.sub(r"\[\[(?:File|Image|Datei|Bild):[^\[\]]*(?:\[\[[^\]]*\]\][^\[\]]*)*\]\]", "", t, flags=re.I)
    t = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[\[([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("'''", "").replace("''", "").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", t).strip()


def named_refs(text):
    out = {}
    for m in re.finditer(r"<ref\s+name\s*=\s*([^>/]+?)\s*>(.*?)</ref>", text, flags=re.S):
        out[m.group(1).strip().strip('"').strip("'")] = ref_summary(m.group(2))
    return out


def window(t, needles, width=520):
    if len(t) <= width:
        return t
    tn = norm(t)
    pos = min([tn.find(norm(n)) for n in needles if norm(n) in tn] or [0])
    a = max(0, pos - width // 2)
    return ("..." if a else "") + t[a:a + width] + "..."


def blocks(text):
    """(section path, raw block): a line outside a table, a row inside."""
    out, path, cur, in_table = [], [], [], False

    def flush():
        if cur and "".join(cur).strip():
            out.append((" > ".join(p for _, p in path), "\n".join(cur)))
        cur.clear()
    for line in text.split("\n"):
        h = re.match(r"^(={2,})\s*(.*?)\s*\1\s*$", line)
        if h:
            flush()
            lvl = len(h.group(1))
            while path and path[-1][0] >= lvl:
                path.pop()
            path.append((lvl, clean(h.group(2), refs=False)))
            continue
        s = line.strip()
        if s.startswith("{|"):
            flush(); in_table = True
            continue
        if s.startswith("|}"):
            flush(); in_table = False
            continue
        if in_table:
            if s.startswith("|-"):
                flush()
            else:
                cur.append(line)
        else:
            flush()
            if s:
                cur.append(line)
                flush()
    flush()
    return out


STALE = re.compile(r"\b(merged|merger|dissolved|defunct|folded|bankrupt\w*|liquidat\w*|ceased|disbanded|"
                   r"no longer|expelled|aufgel\w+|insolven\w+|last (?:competitive |league )?(?:match|meeting|derby)|"
                   r"(?:have|had|has) not (?:met|played|been played|been contested))\b", re.I)
INFO_KEEP = re.compile(r"(team|club|name|locale|city|region|first|latest|last|recent|next|other|total|meetings)", re.I)
INFO_DROP = re.compile(r"(image|caption|logo|stat|win|largest|top|most_?app|scorer|series|broadcast|trophy|stadium|map|alt|size|streak)", re.I)


def article(t, page):
    text = page["text"]
    named = named_refs(text)
    lead_raw = re.split(r"\n==[^=]", text, maxsplit=1)[0]
    out = []
    lead = clean(lead_raw, refs=False)
    out.append("lead: " + lead[:520])
    bold = [clean(b, refs=False) for b in re.findall(r"'''(.+?)'''", re.sub(r"<ref.*?(/>|</ref>)", "", lead_raw, flags=re.S))]
    out.append("bold: " + "; ".join(b[:60] for b in bold[:8]))
    info = []
    for m in re.finditer(r"^\s*\|\s*([\w \-]+?)\s*=[ \t]*(.*)$", lead_raw, flags=re.M):
        k, v = m.group(1), clean(m.group(2), refs=False)
        if v and INFO_KEEP.search(k) and not INFO_DROP.search(k):
            info.append(f"{k}={v[:110]}")
    out.append("infobox: " + " | ".join(info[:12]))
    body = clean(text, refs=False)
    bn, ln = norm(body), norm(lead)
    if t["nameNeedles"]:
        found = [n for n in t["nameNeedles"] if norm(n) in bn]
        s = f"name {t['nameNeedles']}: lead {count(ln, t['nameNeedles'])}, page {count(bn, t['nameNeedles'])}"
        if found and not has(ln, t["nameNeedles"]):
            s += " | first: " + window(body, found, 260)
        out.append(s)
    out.append(f"A {t['a']}: lead {count(ln, t['a'])}, page {count(bn, t['a'])} | "
               f"B {t['b']}: lead {count(ln, t['b'])}, page {count(bn, t['b'])}")
    hits = []
    for sent in re.split(r"(?<=[.!?])\s+", body):
        if STALE.search(sent) and (has(norm(sent), t["a"]) or has(norm(sent), t["b"])):
            hits.append(window(sent, [STALE.search(sent).group(0)], 230))
    if hits:
        out.append(f"ended/merged wording ({len(hits)}): " + " || ".join(hits[:3]))
    return out


def listing(t, page, fragment):
    text = page["text"]
    named = named_refs(text)
    bl = [(sec, raw, norm(clean(raw, refs=False))) for sec, raw in blocks(text)]
    out = []
    frag = norm(fragment.replace("_", " ")) if fragment else ""
    pool = [b for b in bl if frag and frag in norm(b[0])]
    if frag and not pool:
        out.append(f"SECTION '{fragment}' NOT FOUND; whole page searched")
    pool = pool or bl
    a, b, nn = t["a"], t["b"], t["nameNeedles"]
    named_hits = [x for x in pool if has(x[2], nn)]
    both = lambda x: has(x[2], a) and has(x[2], b)
    named_hits.sort(key=lambda x: not both(x))
    if named_hits:
        out.append(f"name {nn}: {len(named_hits)} block(s) in {'section' if frag and pool is not bl else 'page'}")
        for sec, raw, n in named_hits[:3]:
            out.append(f"  [{sec}] A:{'y' if has(n, a) else 'n'} B:{'y' if has(n, b) else 'n'} :: "
                       + window(clean(raw, named), nn + a + b, 560))
    else:
        out.append(f"NAME {nn} NOT FOUND in {'section' if frag and pool is not bl else 'page'}")
        alt = [x for x in pool if both(x)] or [x for x in bl if both(x)]
        if alt:
            out.append(f"blocks naming both clubs: {len(alt)}")
            for sec, raw, n in alt[:3]:
                out.append(f"  [{sec}] :: " + window(clean(raw, named), a + b, 480))
        else:
            one = [x for x in pool if has(x[2], a) or has(x[2], b)]
            out.append(f"NO block names both clubs; blocks naming one: {len(one)}")
            for sec, raw, n in one[:3]:
                out.append(f"  [{sec}] :: " + window(clean(raw, named), a + b, 260))
    return out


def main():
    targets = json.load(open(sys.argv[1], encoding="utf-8"))
    cache, lines = {}, []
    for t in targets:
        u = urllib.parse.urlparse(t["source"])
        lang = u.netloc.split(".")[0]
        title = urllib.parse.unquote(u.path.split("/wiki/", 1)[1]).replace("_", " ")
        fragment = urllib.parse.unquote(u.fragment)
        key = (lang, title)
        if key not in cache:
            cache[key] = fetch(lang, title)
            time.sleep(1.0)
        page = cache[key]
        head = f"### L{t['line']} {t['name']} | {lang}:{title}" + (f"#{fragment}" if fragment else "")
        if "error" in page:
            lines.append(head + f"\nERROR: {page['error']}\n")
            continue
        head += f" (rev {page['revid']}, {page['ts']}, {len(page['text'])} chars)"
        if page["redirects"]:
            head += " REDIRECT " + "; ".join(page["redirects"])
        if page["title"] != title:
            head += f" TITLE NOW '{page['title']}'"
        try:
            body = article(t, page) if t["mode"] == "article" else listing(t, page, fragment)
        except Exception as e:  # one row must not lose the rest
            body = [f"EXTRACT FAILED: {type(e).__name__}: {e}"]
        lines.append(head + "\n" + "\n".join(body) + "\n")
    # comments of at most 60,000 characters
    chunk, n, files = [], 0, []
    for block in lines + [f"requests sent: {REQUESTS}; pages: {len(cache)}; rows: {len(targets)}"]:
        if n + len(block) > 58000:
            files.append("\n".join(chunk)); chunk, n = [], 0
        chunk.append(block); n += len(block) + 1
    files.append("\n".join(chunk))
    for i, body in enumerate(files, 1):
        with open(f"/tmp/probe-comment-{i}.md", "w", encoding="utf-8") as f:
            f.write(f"Derby audit probe, part {i} of {len(files)}\n\n```\n{body}\n```\n")
    print(f"{len(files)} comment file(s); requests {REQUESTS}")


def fetch_old(lang, title, before):
    """The newest revision at or before a timestamp (same rules as fetch)."""
    global REQUESTS
    q = urllib.parse.urlencode({
        "action": "query", "prop": "revisions", "rvprop": "ids|timestamp|content",
        "rvslots": "main", "redirects": "1", "titles": title, "format": "json",
        "formatversion": "2", "maxlag": "5", "rvlimit": "1", "rvstart": before, "rvdir": "older"})
    url = f"https://{lang}.wikipedia.org/w/api.php?{q}"
    for attempt in range(8):
        REQUESTS += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40) as r:
                d = json.load(r)
                retry = r.headers.get("Retry-After")
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}
        if "error" in d:
            if d["error"].get("code") == "maxlag":
                time.sleep(min(int(retry or 5), 120) + 1)
                continue
            return {"error": json.dumps(d["error"])[:200]}
        pg = (d.get("query", {}).get("pages") or [{}])[0]
        rev = (pg.get("revisions") or [{}])[0]
        return {"revid": rev.get("revid"), "ts": rev.get("timestamp"),
                "text": rev.get("slots", {}).get("main", {}).get("content", "")}
    return {"error": "still lagged after 8 tries"}


def extras():
    out = []
    LIST = "List of association football club rivalries in Europe"
    cur = fetch("en", LIST); time.sleep(1)
    old = fetch_old("en", LIST, "2026-10-03T23:59:59Z"); time.sleep(1)
    for label, pg in (("current", cur), ("as of 2026-10-03", old)):
        if "error" in pg:
            out.append(f"### list {label}: ERROR {pg['error']}"); continue
        out.append(f"### en:{LIST} {label} (rev {pg['revid']}, {pg['ts']})")
        for line in pg["text"].split("\n"):
            n = norm(line)
            if "ticino" in n or "derby of love" in n or "klassik" in n:
                out.append("  RAW: " + re.sub(r"<ref.*?(</ref>|/>)", "[ref]", line, flags=re.S)[:420])
    ksc = fetch("de", "Karlsruher SC"); time.sleep(1)
    if "error" in ksc:
        out.append(f"### de:Karlsruher SC: ERROR {ksc['error']}")
    else:
        body = clean(ksc["text"], refs=False)
        bn = norm(body)
        pos = [m.start() for m in re.finditer(r"sudwest|kaiserslautern", bn)]
        out.append(f"### de:Karlsruher SC (rev {ksc['revid']}, {ksc['ts']}): 'suedwest' {bn.count('sudwest')}, 'kaiserslautern' {bn.count('kaiserslautern')}, 'derby' {bn.count('derby')}")
        last = -1000
        shown = 0
        for p_ in [m.start() for m in re.finditer(r"sudwest", bn)] + [m.start() for m in re.finditer(r"derby", bn)]:
            if abs(p_ - last) < 200 or shown >= 10:
                continue
            last = p_; shown += 1
            out.append("  ..." + body[max(0, p_ - 230):p_ + 230] + "...")
    for label, pg in (("current", fetch("en", "South London derby")), ("as of 2026-10-03", fetch_old("en", "South London derby", "2026-10-03T23:59:59Z"))):
        time.sleep(1)
        if "error" in pg:
            out.append(f"### South London derby {label}: ERROR {pg['error']}"); continue
        lead = clean(re.split(r"\n==[^=]", pg["text"], maxsplit=1)[0], refs=False)
        out.append(f"### en:South London derby {label} (rev {pg['revid']}, {pg['ts']})\n  lead: {lead[:420]}")
    out.append(f"requests sent: {REQUESTS}")
    with open("/tmp/probe-comment-1.md", "w", encoding="utf-8") as f:
        f.write("Derby audit probe, run 2 (second look at three rows)\n\n```\n" + "\n".join(out) + "\n```\n")
    print("extras written; requests", REQUESTS)


if __name__ == "__main__":
    extras() if len(sys.argv) > 2 and sys.argv[2] == "extras" else main()
