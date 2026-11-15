#!/usr/bin/env python3
"""TEMPORARY: bucket list audit, phase 3b. Reads Wikipedia articles through
the MediaWiki API (wikitext, or coordinates) and prints, per lead, only the
passages that match the lead's pattern. Removed before the merge."""
import json, math, re, sys, time, urllib.error, urllib.parse, urllib.request

UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
REQUESTS = 0
CACHE = {}


def api(lang, params):
    """One API call. maxlag=5; on a lag refusal wait and retry, never raise it."""
    global REQUESTS
    p = dict(params); p.update({"format": "json", "formatversion": "2", "maxlag": "5"})
    url = f"https://{lang}.wikipedia.org/w/api.php?{urllib.parse.urlencode(p)}"
    for attempt in range(8):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        REQUESTS += 1
        retry = None
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.load(r)
                retry = r.headers.get("Retry-After")
        except urllib.error.HTTPError as e:
            retry = e.headers.get("Retry-After")
            if e.code in (429, 503):
                time.sleep(min(int(retry or 10), 120)); continue
            return {"error": f"HTTP {e.code}"}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}
        if "error" in d:
            if d["error"].get("code") == "maxlag":
                time.sleep(min(int(retry or 5), 120) + 1); continue
            return {"error": json.dumps(d["error"])[:200]}
        time.sleep(0.6)
        return d
    return {"error": "gave up after 8 attempts (maxlag or 429/503)"}


def page(lang, title):
    key = (lang, title)
    if key in CACHE:
        return CACHE[key]
    d = api(lang, {"action": "query", "prop": "revisions|coordinates", "rvprop": "ids|timestamp|content",
                   "rvslots": "main", "redirects": "1", "titles": title})
    if "error" in d:
        out = d
    else:
        qd = d.get("query", {})
        pg = (qd.get("pages") or [{}])[0]
        if pg.get("missing") or pg.get("invalid"):
            out = {"error": "page missing", "title": pg.get("title")}
        else:
            rev = (pg.get("revisions") or [{}])[0]
            out = {"title": pg.get("title"), "revid": rev.get("revid"), "ts": rev.get("timestamp"),
                   "redirects": [f"{x['from']} -> {x['to']}" for x in qd.get("redirects", [])],
                   "coords": pg.get("coordinates"),
                   "text": clean(((rev.get("slots") or {}).get("main") or {}).get("content", ""))}
    CACHE[key] = out
    return out


def clean(t):
    t = re.sub(r"<!--[\s\S]*?-->", "", t)
    t = re.sub(r"<ref[^>/]*/>", "", t)
    t = re.sub(r"<ref[^>]*>[\s\S]*?</ref>", "", t)
    t = re.sub(r"\[\[(?:File|Image|Datei|Bestand|Fișier):[^\]\n]*\]\]", "", t)
    t = re.sub(r"\[\[[^\]|\n]*\|([^\]\n]*)\]\]", r"\1", t)
    t = re.sub(r"\[\[([^\]\n]*)\]\]", r"\1", t)
    t = t.replace("'''", "").replace("''", "").replace("&nbsp;", " ")
    return t


def passages(text, pattern, k, width):
    out, last_end = [], -1
    for m in re.finditer(pattern, text, flags=re.I):
        if m.start() < last_end:
            continue
        a = max(text.rfind("\n", 0, m.start()), text.rfind(". ", 0, m.start()), m.start() - width) + 1
        ends = [x for x in (text.find("\n", m.end()), text.find(". ", m.end())) if x != -1]
        b = min(min(ends) + 1 if ends else len(text), m.end() + width)
        s = " ".join(text[a:b].split())
        if s and s not in out:
            out.append(s)
        last_end = b
        if len(out) >= k:
            break
    return out


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def main():
    targets = json.load(open(sys.argv[1], encoding="utf-8"))
    lines = []
    for t in targets:
        lines.append(f"### {t['n']} `{t['id']}`")
        for lead in t["leads"]:
            if lead[0] == "km":
                _, lang, ta, tb = lead
                pa, pb = page(lang, ta), page(lang, tb)
                ca, cb = (pa.get("coords") or [None])[0], (pb.get("coords") or [None])[0]
                if ca and cb:
                    lines.append(f"**km** {lang}:{pa['title']} ({ca['lat']}, {ca['lon']}; rev {pa['revid']}) to {lang}:{pb['title']} ({cb['lat']}, {cb['lon']}; rev {pb['revid']}): great-circle {km(ca, cb):.1f} km")
                else:
                    lines.append(f"**km** {lang}:{ta} / {tb}: no coordinates ({pa.get('error')}, {pb.get('error')})")
                continue
            lang, title, pattern = lead[0], lead[1], lead[2]
            k = lead[3] if len(lead) > 3 else 4
            width = lead[4] if len(lead) > 4 else 230
            pg = page(lang, title)
            if "error" in pg:
                lines.append(f"**{lang}:{title}** ERROR {pg['error']}")
                continue
            red = f" [{'; '.join(pg['redirects'])}]" if pg["redirects"] else ""
            hits = passages(pg["text"], pattern, k, width)
            lines.append(f"**{lang}:{pg['title']}** rev {pg['revid']} {pg['ts'][:10]}{red} /{pattern}/ {len(hits)} shown")
            lines += [f"- {h}" for h in hits]
        lines.append("")
    lines.append(f"_{REQUESTS} API requests, {len(CACHE)} pages._")
    chunks, cur = [], ""
    for ln in lines:
        if len(cur) + len(ln) + 1 > 58000:
            chunks.append(cur); cur = ""
        cur += ln + "\n"
    chunks.append(cur)
    run = sys.argv[2]
    for i, c in enumerate(chunks, 1):
        open(f"/tmp/probe-comment-{i:02d}.md", "w", encoding="utf-8").write(
            f"**Bucket audit probe, run {run}, part {i} of {len(chunks)}** (matching passages only)\n\n" + c)
    print(f"{REQUESTS} requests, {len(CACHE)} pages, {len(chunks)} comments, {sum(map(len, chunks))} chars")
    print("errors:", sum(1 for v in CACHE.values() if "error" in v))


if __name__ == "__main__":
    main()
