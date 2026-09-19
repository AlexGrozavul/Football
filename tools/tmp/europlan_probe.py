#!/usr/bin/env python3
"""THROWAWAY probe, phase 5: the seven, through the site's real search.

Phase 4 found the search form and proved five guessed parameter names
wrong. The form is a plain GET to index.php with s=search and the term
in a field called `search`, placeholder "Stadion / Verein suchen".

FSV Optik Rathenow is the control - already settled from a league page,
so a search that cannot find it is broken rather than evidence that the
other seven are absent. Nothing is asked for the seven until the
control comes back.

For each hit the ground page is read for address, capacity and the
Google Maps coordinates, exactly as phase 3 did, so the seven are
judged on the same evidence as the fourteen.
"""
import json, os, re, subprocess, time, urllib.parse as up

BASE = "https://www.europlan-online.de"
UA = ("FootballFixturePlanner/1.0 (personal, non-commercial; "
      "resolving 22 missing German ground coordinates)")
OUT, PAUSE, MAXTIME = "tmp-europlan", 1.2, 40
os.makedirs(OUT, exist_ok=True)

CONTROL = ("FSV Optik Rathenow", "Optik Rathenow")
MISSING = [("Q1378922", "Eutin 08", "Eutin"),
           ("Q720528", "FC Kray", "Essen"),
           ("Q831892", "Lupo Martini Wolfsburg", "Wolfsburg"),
           ("Q566179", "Torgelower FC Greif", "Torgelow"),
           ("Q479306", "VfB Hüls", "Marl"),
           ("Q127275134", "VfR Garching", "Garching bei München"),
           ("Q13426883", "FC Viktoria 1889 Berlin", "Berlin"),
           ("Q21175456", "Teutonia Watzenborn-Steinberg", "Pohlheim")]


def say(s): print(s, flush=True)


def get(path, label):
    url = path if path.startswith("http") else BASE + "/" + path.lstrip("/")
    cmd = ["curl", "-sSL", "--max-time", str(MAXTIME), "--compressed", "-A", UA,
           "-H", "Accept-Language: de,en", "-w", "\n__M__%{http_code}", url]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=MAXTIME + 10)
    except subprocess.TimeoutExpired:
        say(f"  {label}: TIMEOUT"); return None
    raw = p.stdout.decode("utf-8", "replace")
    if "__M__" not in raw:
        say(f"  {label}: NO RESPONSE"); return None
    body, meta = raw.rsplit("\n__M__", 1)
    say(f"  {label}: {meta.strip()} {len(body)}B")
    time.sleep(PAUSE)
    return body


ENT = {"&nbsp;": " ", "&amp;": "&", "&quot;": '"', "&#039;": "'", "&uuml;": "ü",
       "&auml;": "ä", "&ouml;": "ö", "&szlig;": "ß", "&Uuml;": "Ü",
       "&Auml;": "Ä", "&Ouml;": "Ö", "&ndash;": "–"}

def txt(h):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    t = re.sub(r"(?i)<br\s*/?>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    for k, v in ENT.items(): t = t.replace(k, v)
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t).strip()


def search(term):
    return get("index.php?s=search&search=" + up.quote(term), f"search {term!r}")


def hits(html):
    """A search result row: the ground link, and whatever text sits with it."""
    out, seen = [], set()
    for m in re.finditer(r'(?is)<tr[^>]*>(.*?)</tr>', html):
        row = m.group(1)
        a = re.search(r'(?is)<a href="([^"]*stadion-(\d+)\.html)"[^>]*>(.*?)</a>', row)
        if not a or a.group(2) in seen:
            continue
        seen.add(a.group(2))
        out.append({"href": a.group(1), "id": a.group(2),
                    "ground": txt(a.group(3)), "row": txt(row)[:200]})
    if not out:                      # not a table? fall back to bare links
        for m in re.finditer(r'(?is)<a href="([^"]*stadion-(\d+)\.html)"[^>]*>(.*?)</a>', html):
            if m.group(2) in seen:
                continue
            seen.add(m.group(2))
            out.append({"href": m.group(1), "id": m.group(2),
                        "ground": txt(m.group(3)), "row": ""})
    return out


def parse_ground(html, url):
    t = txt(html)
    g = {"url": url}
    m = re.search(r"maps\.google\.[a-z.]+/maps\?q=\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)", html)
    if m: g["lat"], g["lon"] = m.group(1), m.group(2)
    m = re.search(r"(?i)Kapazität:\s*([\d.]+)", t)
    if m: g["capacity"] = m.group(1)
    m = re.search(r"(?is)Anschrift\s*\n(.{0,260}?)\n\s*(?:\||Stadiondaten)", t)
    if m: g["address"] = re.sub(r"\s*\n\s*", ", ", m.group(1).strip())[:200]
    m = re.search(r"\b(\d{5})\s+([^\n,|]+)", g.get("address", ""))
    if m: g["plz"], g["town"] = m.group(1), m.group(2).strip()
    m = re.search(r"(?is)Vereine, die in diesem Stadion spielen\s*\n(.{0,400}?)\n\s*(?:Weitere Vereine|Bilder|Europlan)", t)
    if m: g["clubs_here"] = re.sub(r"\s*\n\s*", " / ", m.group(1).strip())[:300]
    m = re.search(r"(?is)Weitere Vereine[^\n]*\n(.{0,300}?)\n\s*(?:Bilder|Europlan)", t)
    if m: g["clubs_former"] = re.sub(r"\s*\n\s*", " / ", m.group(1).strip())[:300]
    m = re.search(r"(?is)<title>(.*?)</title>", html)
    if m: g["title"] = txt(m.group(1))[:120]
    return g


# --------------------------------------------------------------- control
say("[1] control")
cb = search(CONTROL[1])
ok = bool(cb) and "Rathenow" in cb and re.search(r"stadion-\d+\.html", cb or "")
say(f"  control found: {bool(ok)}")
if cb:
    open(f"{OUT}/search-control.html", "w").write(cb)
result = {"control_ok": bool(ok), "control_hits": hits(cb) if cb else []}
json.dump(result, open(f"{OUT}/seven.json", "w"), ensure_ascii=False, indent=1)
if not ok:
    say("  search does not work; not asking for the seven")
    raise SystemExit(0)

# ------------------------------------------------------------- the seven
say("[2] the seven")
found = {}
for qid, name, town in MISSING:
    b = search(name)
    h = hits(b) if b else []
    if not h and b:                       # try the distinctive word alone
        short = max(name.split(), key=len)
        b2 = search(short)
        h = hits(b2) if b2 else []
    found[qid] = {"name": name, "wikidata_town": town, "hits": h[:6]}
    say(f"    {name}: {len(h)} ground hits")
result["seven"] = found
json.dump(result, open(f"{OUT}/seven.json", "w"), ensure_ascii=False, indent=1)

# ------------------------------------------------------- their ground pages
want = {}
for qid, v in found.items():
    for h in v["hits"][:3]:
        want.setdefault(h["id"], h["href"])
say(f"[3] ground pages: {len(want)}")
grounds = {}
for sid, href in list(want.items())[:30]:
    b = get(href, f"stadion-{sid}")
    if b:
        grounds[sid] = parse_ground(b, BASE + "/" + href.lstrip("/"))
result["grounds"] = grounds
json.dump(result, open(f"{OUT}/seven.json", "w"), ensure_ascii=False, indent=1)

say("")
for qid, v in found.items():
    say(f'{v["name"]}  (wikidata town: {v["wikidata_town"]})')
    for h in v["hits"][:4]:
        g = grounds.get(h["id"], {})
        say(f'   {h["ground"][:34].ljust(35)} town={g.get("town","?")[:22].ljust(23)}'
            f' cap={g.get("capacity","?")}')
say("done")
