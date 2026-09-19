#!/usr/bin/env python3
"""TEMPORARY probe 2. Removed in the same branch once the answers are read."""
import json, re, urllib.parse, urllib.request, html

UA = ("football-fixture-planner/1.0 (personal project; "
      "https://github.com/AlexGrozavul/Football)")
TAG = re.compile(r"<[^>]+>")

def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.getcode(), r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", 0), str(e)

def txt(f):
    return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", f))).strip()

print("### 1. STADIUMDB parsed rows (name | city | clubs | capacity)")
for slug in ("ger", "rou"):
    code, body = get(f"https://stadiumdb.com/stadiums/{slug}")
    print(f"--BEGIN {slug} ({code})")
    tables = re.findall(r"<table[^>]*>(.*?)</table>", body, re.S | re.I)
    print(f"  tables on page: {len(tables)}")
    n = 0
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S | re.I):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(tds) < 4:
            continue
        n += 1
        href = re.search(r'href="([^"]+)"', tds[0])
        print(f"R\t{txt(tds[0])}\t{txt(tds[1])}\t{txt(tds[2])}\t{txt(tds[3])}\t{href.group(1) if href else ''}")
    print(f"--END {slug} rows={n}")

print()
print("### 2. RAW HTML of two rows, to see what the Clubs cell really holds")
code, body = get("https://stadiumdb.com/stadiums/ger")
rows = [tr for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S | re.I)
        if len(re.findall(r"<td", tr)) >= 4]
for tr in rows[:2]:
    print("  RAW:", re.sub(r"\s+", " ", tr)[:600])

print()
print("### 3. WIKIPEDIA table headers on the two pages that found nothing")
API = "https://en.wikipedia.org/w/api.php"
def parse(title):
    q = urllib.parse.urlencode({"action":"parse","page":title,"prop":"text",
                                "format":"json","formatversion":"2","redirects":"1"})
    c, b = get(f"{API}?{q}")
    if c != 200: return None, f"HTTP {c}"
    d = json.loads(b)
    if "error" in d: return None, d["error"].get("code")
    return d["parse"], None

for title in ("2026–27 Regionalliga", "2026–27 Liga III"):
    p, err = parse(title)
    if err: print(f"  {title}: {err}"); continue
    tables = re.findall(r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>.*?</table>', p["text"], re.S)
    print(f"  {title}: {len(tables)} wikitables")
    for i, t in enumerate(tables[:14]):
        hdr = [txt(h)[:22] for h in re.findall(r"<th[^>]*>(.*?)</th>", t, re.S)[:8]]
        nrows = len(re.findall(r"<tr[^>]*>", t)) - 1
        print(f"    [{i}] rows={nrows:3d} hdr={hdr}")

print()
print("### 4. Candidate per-division / alternative titles")
for title in ("2026–27 Regionalliga Bayern", "2026–27 Regionalliga West",
              "2026–27 Regionalliga Nord", "2026–27 Regionalliga Nordost",
              "2026–27 Regionalliga Südwest", "2026–27 2. Liga",
              "2026–27 Austrian Football Second League"):
    p, err = parse(title)
    if err:
        print(f"  {title!r:40s} MISSING ({err})"); continue
    tables = re.findall(r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>.*?</table>', p["text"], re.S)
    good = []
    for t in tables:
        hdr = " ".join(txt(h).lower() for h in re.findall(r"<th[^>]*>(.*?)</th>", t, re.S)[:12])
        if ("stadium" in hdr or "venue" in hdr or "ground" in hdr) and "capacit" in hdr:
            good.append(len(re.findall(r"<tr[^>]*>", t)) - 1)
    print(f"  {title!r:40s} OK as {p['title']!r} roster-like={good}")
