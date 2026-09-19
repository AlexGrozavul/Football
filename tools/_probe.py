#!/usr/bin/env python3
"""TEMPORARY probe. Removed in the same branch once the answers are read."""
import json, re, sys, urllib.parse, urllib.request, html

UA = ("football-fixture-planner/1.0 (personal project; "
      "https://github.com/AlexGrozavul/Football)")
ANS = []

def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.getcode(), r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", 0), str(e)

# ---------------------------------------------------------- StadiumDB
print("### STADIUMDB country page shape")
for slug in ("ger", "germany", "de", "rou", "rom", "romania", "ro"):
    code, body = get(f"https://stadiumdb.com/stadiums/{slug}")
    hit = code == 200 and len(body) > 20000
    print(f"  /stadiums/{slug:8s} -> {code} len={len(body) if code==200 else 0} {'OK' if hit else ''}")
    if hit:
        ANS.append(f"stadiumdb /stadiums/{slug} = {len(body)} bytes")

for slug in ("ger", "rou", "rom", "romania"):
    code, body = get(f"https://stadiumdb.com/stadiums/{slug}")
    if code != 200 or len(body) < 20000:
        continue
    print(f"  --- table shape for /stadiums/{slug}")
    ths = re.findall(r"<th[^>]*>(.*?)</th>", body, re.S)[:8]
    print("      headers:", [re.sub(r"<[^>]+>", "", t).strip() for t in ths])
    trs = re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S)
    print(f"      rows: {len(trs)}")
    for tr in trs[1:4]:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        print("      row:", [html.unescape(re.sub(r"<[^>]+>", " ", t)).strip()[:44] for t in tds])
    # first stadium link shape
    links = re.findall(r'href="(/[^"]*)"', "".join(trs[1:3]))
    print("      links:", links[:6])

# ------------------------------------------------------------ Wikipedia
print()
print("### WIKIPEDIA season articles")
API = "https://en.wikipedia.org/w/api.php"
CAND = [
 "2026–27 Bundesliga", "2026–27 2. Bundesliga", "2026–27 3. Liga",
 "2026–27 Regionalliga",
 "2026–27 Liga I", "2026–27 Liga II", "2026–27 Liga 2 (Romania)",
 "2026–27 Liga III", "2026–27 Liga 3 (Romania)",
 "2026–27 Austrian 2. Liga", "2026–27 2. Liga (Austria)",
]
for title in CAND:
    q = urllib.parse.urlencode({"action":"parse","page":title,"prop":"text",
                                "format":"json","formatversion":"2","redirects":"1"})
    code, body = get(f"{API}?{q}")
    if code != 200:
        print(f"  {title!r:36s} HTTP {code}")
        continue
    try:
        d = json.loads(body)
    except ValueError:
        print(f"  {title!r:36s} bad json"); continue
    if "error" in d:
        print(f"  {title!r:36s} MISSING ({d['error'].get('code')})")
        continue
    txt = d["parse"]["text"]
    real = d["parse"]["title"]
    tables = re.findall(r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>.*?</table>', txt, re.S)
    good = []
    for t in tables:
        hdr = " ".join(re.sub(r"<[^>]+>"," ",h).lower() for h in re.findall(r"<th[^>]*>(.*?)</th>", t, re.S)[:12])
        if ("stadium" in hdr or "venue" in hdr or "ground" in hdr) and "capacit" in hdr:
            rows = len(re.findall(r"<tr[^>]*>", t)) - 1
            good.append(rows)
    print(f"  {title!r:36s} OK as {real!r}  tables={len(tables)} roster-like={good}")
    ANS.append(f"wp {title} -> {real} roster-like tables {good}")

print()
print("### ANSWERS AGAIN")
for a in ANS:
    print("  " + a)
