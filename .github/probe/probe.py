#!/usr/bin/env python3
"""Temporary probe (phase 3d): reads Wikipedia wikitext through the MediaWiki
API and posts only the matching sentences as PR comments. Removed before merge."""
import json, os, re, sys, time, urllib.parse, urllib.request, urllib.error

UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
REQ = 0

def api(lang, params):
    global REQ
    params = dict(params, format="json", formatversion="2", maxlag="5")
    url = "https://%s.wikipedia.org/w/api.php?%s" % (lang, urllib.parse.urlencode(params))
    for attempt in range(6):
        REQ += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
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

def fetch(lang, title):
    d = api(lang, {"action": "query", "prop": "revisions", "rvprop": "ids|timestamp|content",
                   "rvslots": "main", "redirects": "1", "titles": title})
    try:
        p = d["query"]["pages"][0]
        if p.get("missing") or "revisions" not in p:
            return None
        rv = p["revisions"][0]
        return p["title"], rv["revid"], rv["timestamp"], rv["slots"]["main"]["content"]
    except Exception:
        return None

def search(lang, title):
    d = api(lang, {"action": "query", "list": "search", "srsearch": title, "srlimit": "3"})
    try:
        return [h["title"] for h in d["query"]["search"]]
    except Exception:
        return []

def clean(w):
    w = re.sub(r"<!--.*?-->", "", w, flags=re.S)
    w = re.sub(r"<ref[^>/]*/>", "", w)
    w = re.sub(r"<ref[^>]*>.*?</ref>", "", w, flags=re.S)
    w = re.sub(r"\[\[(?:File|Datei|Image|Bild|Fichier|Fișier|Archivo):[^\]]*\]\]", "", w)
    w = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", w)
    w = re.sub(r"\[\[([^\]]*)\]\]", r"\1", w)
    w = re.sub(r"'{2,}", "", w)
    w = w.replace("&nbsp;", " ")
    return w

def units(w):
    out = []
    for line in w.split("\n"):
        line = line.strip()
        if len(line) < 4:
            continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ÝȘȚ0-9\"„«])", line):
            s = s.strip()
            if s:
                out.append(s)
    return out

def snip(u, m, width=270):
    if len(u) <= width:
        return u
    a = max(0, m.start() - width // 2)
    return ("…" if a else "") + u[a:a + width] + "…"

def main(cfg):
    blocks = []
    for raw in open(cfg, encoding="utf-8"):
        raw = raw.rstrip("\n")
        if not raw.strip() or raw.startswith("#"):
            continue
        eid, lang, title, pats = (raw.split("\t") + ["", "", "", ""])[:4]
        lines = []
        got = fetch(lang, title)
        note = ""
        if got is None:
            cands = search(lang, title)
            note = " SEARCH-FALLBACK from '%s' candidates=%s" % (title, cands)
            got = fetch(lang, cands[0]) if cands else None
        if got is None:
            blocks.append("### %s | %s:%s | MISSING%s\n" % (eid, lang, title, note))
            continue
        rt, rev, ts, text = got
        us = units(clean(text))
        lines.append("### %s | %s:%s | rev %s %s%s" % (eid, lang, rt, rev, ts[:10], note))
        lead = next((u for u in us if re.match(r"[A-Za-zÀ-ÿ0-9„\"]", u) and len(u) > 40 and "=" not in u[:30]), "")
        lines.append("[lead] " + lead[:230])
        seen = set()
        for gi, g in enumerate([x.strip() for x in pats.split(";;") if x.strip()], 1):
            cap = 2
            mm = re.match(r"(\d)@(.*)", g)
            if mm:
                cap, g = int(mm.group(1)), mm.group(2)
            try:
                rx = re.compile(g, re.I)
            except re.error as e:
                lines.append("[g%d] BAD REGEX %s" % (gi, e)); continue
            n = 0
            for i, u in enumerate(us):
                m = rx.search(u)
                if m and i not in seen:
                    seen.add(i); n += 1
                    lines.append("[g%d] %s" % (gi, snip(u, m)))
                    if n >= cap:
                        break
            if n == 0:
                lines.append("[g%d] NO MATCH /%s/" % (gi, g))
        blocks.append("\n".join(lines) + "\n")
    blocks.append("requests made: %d\n" % REQ)
    return blocks

def post(blocks):
    repo, pr, tok = os.environ.get("REPO"), os.environ.get("PR"), os.environ.get("GITHUB_TOKEN")
    chunks, cur = [], ""
    for b in blocks:
        if len(cur) + len(b) > 58000:
            chunks.append(cur); cur = ""
        cur += b + "\n"
    if cur:
        chunks.append(cur)
    run = os.environ.get("RUN_LABEL", "?")
    for i, c in enumerate(chunks, 1):
        body = "PROBE %s part %d/%d\n\n%s" % (run, i, len(chunks), c)
        if not (repo and pr and tok):
            sys.stdout.write(body); continue
        req = urllib.request.Request(
            "https://api.github.com/repos/%s/issues/%s/comments" % (repo, pr),
            data=json.dumps({"body": body}).encode(), method="POST",
            headers={"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json", "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            print("comment", i, r.status, len(body))
        time.sleep(1)

if __name__ == "__main__":
    post(main(sys.argv[1]))
