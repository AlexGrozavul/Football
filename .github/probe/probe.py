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

STOP_RX = re.compile(r"claude|anthropic|footballplanner", re.I)

def raw(url, timeout=40):
    global REQ
    REQ += 1
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
            return r.status, dict((k.lower(), v) for k, v in r.headers.items()), r.read()
    except urllib.error.HTTPError as e:
        return e.code, {}, b""
    except Exception as e:
        return 0, {"error": repr(e)[:120]}, b""

def robots_stop(url):
    """Returns (stop_reason or '', summary). Stops: a robots line naming an Anthropic/Claude crawler or
    this probe, a Disallow for * covering the path, a TDM reservation (header or tdmrep.json)."""
    u = urllib.parse.urlsplit(url)
    base = "%s://%s" % (u.scheme, u.netloc)
    st, hd, body = raw(base + "/robots.txt")
    time.sleep(2)
    txt = body.decode("utf-8", "replace") if st == 200 else ""
    summ = "robots.txt HTTP %s, %d lines" % (st, len(txt.splitlines()))
    if st not in (200, 404):
        return "robots.txt could not be read (HTTP %s %s)" % (st, hd.get("error", "")), summ
    agent, groups = [], {}
    cur = []
    for line in txt.splitlines():
        line = line.split("#")[0].strip()
        if ":" not in line:
            continue
        k, v = [x.strip() for x in line.split(":", 1)]
        k = k.lower()
        if k == "user-agent":
            if STOP_RX.search(v):
                return "robots.txt names '%s'" % v, summ
            cur = groups.setdefault(v.lower(), [])
        elif k == "disallow" and v:
            cur.append(v)
    for rule in groups.get("*", []):
        rx = "^" + re.escape(rule).replace(r"\*", ".*").replace(r"\$", "$")
        if re.search(rx, u.path or "/"):
            return "robots.txt Disallow for *: %s" % rule, summ
    st2, hd2, body2 = raw(base + "/.well-known/tdmrep.json")
    time.sleep(2)
    if st2 == 200 and body2.strip()[:1] in (b"[", b"{"):
        return "tdmrep.json present: %s" % body2[:160].decode("utf-8", "replace"), summ
    summ += "; tdmrep.json HTTP %s" % st2
    return "", summ

def read_url(url):
    stop, summ = robots_stop(url)
    if stop:
        return None, "STOP " + stop + " (" + summ + ")"
    st, hd, body = raw(url, 60)
    time.sleep(2)
    if st != 200:
        return None, "HTTP %s %s (%s)" % (st, hd.get("error", ""), summ)
    if hd.get("tdm-reservation", "0").strip() == "1":
        return None, "STOP TDM-Reservation header (%s)" % summ
    info = "HTTP 200, %d bytes, %s; %s" % (len(body), hd.get("content-type", ""), summ)
    if body[:4] == b"%PDF":
        import subprocess, tempfile
        f = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False); f.write(body); f.close()
        text = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True).stdout.decode("utf-8", "replace")
        return text, info + "; pdf text %d chars" % len(text)
    h = body.decode("utf-8", "replace")
    if re.search(r"text.and.data.mining|TDM.reserv|44b\s*UrhG", h, re.I):
        return None, "STOP page text carries a TDM reservation (%s)" % summ
    meta = re.findall(r"<meta[^>]+name=[\"']robots[\"'][^>]*>", h, re.I)
    h = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"</(p|div|li|h\d|tr|br)>|<br[^>]*>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    import html as _h
    h = _h.unescape(h)
    h = re.sub(r"[ \t\r]+", " ", h)
    return h, info + "; meta robots %s" % (meta[:1] or "none")

def main(cfg):
    blocks = []
    for raw in open(cfg, encoding="utf-8"):
        raw = raw.rstrip("\n")
        if not raw.strip() or raw.startswith("#"):
            continue
        eid, lang, title, pats = (raw.split("\t") + ["", "", "", ""])[:4]
        lines = []
        if lang == "url":
            text, info = read_url(title)
            if text is None:
                blocks.append("### %s | %s | NOT READ: %s\n" % (eid, title, info)); continue
            got = (title, "-", time.strftime("%Y-%m-%d"), text)
            lines_note = info
        else:
            got = fetch(lang, title)
            lines_note = ""
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
        lines.append("### %s | %s:%s | rev %s %s%s %s" % (eid, lang, rt, rev, ts[:10], note, lines_note))
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
