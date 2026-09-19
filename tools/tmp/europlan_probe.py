#!/usr/bin/env python3
"""THROWAWAY probe, phase 2: find each of the 22 clubs on europlan.

Phase 1 settled the structure, and it is not the structure CLAUDE.md
recorded. There is no /<ground>/verein/<clubId> link anywhere - not on
the homepage, the country page, a league page or a ground page. That
URL shape came from a search engine's index and does not exist as
navigation. What does exist is better: a league page is a table whose
every row pairs a CLUB with the GROUND it plays at, as the site's own
assertion. That is the club-to-ground link, and it is what this reads.

This does not match ground names, and it does not decide anything. It
collects candidate rows for the 22 clubs and scores them, and a person
picks. Same shape as propose_coordinates.py: propose, never settle.

Reads at most 13 league pages, chosen locally from a league list
already in hand, and only the ones a target club could plausibly be
in. Rows for clubs that are not one of the 22 are scored and dropped,
not kept.
"""
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time

BASE = "https://www.europlan-online.de"
UA = ("FootballFixturePlanner/1.0 (personal, non-commercial; "
      "resolving 22 missing German ground coordinates)")
OUT = "tmp-europlan"
PAUSE = 1.5
MAXTIME = 40

os.makedirs(OUT, exist_ok=True)

# The 22: the 19 ambiguous and 3 unplaceable rows of coordinate-review.csv.
TARGETS = [
    "Q15972883", "Q4545849", "Q13397712", "Q1378922", "Q5424829",
    "Q97927365", "Q831887", "Q720528", "Q3736767", "Q13426883",
    "Q566165", "Q1514109", "Q831892", "Q15849956", "Q7572134",
    "Q566179", "Q2521441", "Q479306", "Q127275134",
    "Q920263", "Q21175456", "Q16743331",
]

# Tier 4 is read for every target. A tier-5 page is read only if a club
# that could be in it is still missing after tier 4 - these clubs are
# Wikidata-tagged Regionalliga, but several have since gone down.
TIER4 = [("654", "NOFV-Regionalliga Nordost"), ("640", "Regionalliga Bayern"),
         ("2900", "Regionalliga Nord"), ("24", "Regionalliga Südwest"),
         ("23", "Regionalliga West")]
TIER5 = {
    "30": "NOFV-Oberliga Nord", "55": "Oberliga Niederrhein",
    "5381": "Oberliga Westfalen", "2901": "Oberliga Niedersachsen",
    "3010": "Schleswig-Holstein-Liga", "34": "Hessenliga",
    "641": "Bayernliga Nord", "642": "Bayernliga Süd",
}


def say(s):
    print(s, flush=True)


def get(path, label):
    url = path if path.startswith("http") else BASE + path
    cmd = ["curl", "-sSL", "--max-time", str(MAXTIME), "--compressed",
           "-A", UA, "-H", "Accept-Language: de,en",
           "-w", "\n__META__%{http_code}", url]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=MAXTIME + 10)
    except subprocess.TimeoutExpired:
        say(f"  {label}: TIMEOUT")
        return None
    raw = p.stdout.decode("utf-8", "replace")
    if "__META__" not in raw:
        say(f"  {label}: NO RESPONSE ({p.returncode})")
        return None
    body, meta = raw.rsplit("\n__META__", 1)
    say(f"  {label}: {meta.strip()} {len(body)}B {time.time()-t0:.1f}s")
    time.sleep(PAUSE)
    return body


ENT = {"&nbsp;": " ", "&amp;": "&", "&quot;": '"', "&#039;": "'",
       "&uuml;": "ü", "&auml;": "ä", "&ouml;": "ö", "&szlig;": "ß",
       "&Uuml;": "Ü", "&Auml;": "Ä", "&Ouml;": "Ö", "&eacute;": "é",
       "&ndash;": "–", "&raquo;": "»"}


def text_of(h):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    t = re.sub(r"<[^>]+>", " ", t)
    for k, v in ENT.items():
        t = t.replace(k, v)
    return re.sub(r"\s+", " ", t).strip()


def norm(s):
    """Fold a club name to comparable tokens. Founding years go: europlan
    writes 'FC Erzgebirge Aue 1992' where Wikidata writes 'FC Erzgebirge
    Aue'. The reserve-team marker does NOT go - it is the whole
    difference between a first team and its second, and getting it wrong
    puts a club at the wrong ground."""
    s = s.lower()
    for a, b in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"),
                 ("é", "e"), ("–", "-")]:
        s = s.replace(a, b)
    s = re.sub(r"\b(18|19|20)\d{2}\b", " ", s)          # founding years
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


NOISE = {"fc", "sv", "vfb", "vfl", "vfr", "sg", "spvgg", "tsv", "fsv",
         "1", "sc", "bsc", "ii", "2", "club", "verein", "berliner", "der"}


def reserve(s):
    return bool(re.search(r"(^|\s)(ii|2)$", norm(s)))


def score(a, b):
    ta, tb = set(norm(a).split()), set(norm(b).split())
    if not ta or not tb:
        return 0.0
    if reserve(a) != reserve(b):
        return 0.0                       # first team vs reserve: never a match
    da, db = ta - NOISE, tb - NOISE      # distinctive tokens carry the weight
    if not da or not db:
        da, db = ta, tb
    inter = len(da & db)
    return round(inter / max(len(da), len(db)), 3)


def parse_league(html, liga):
    """Every row of a league table pairs a club with its ground."""
    rows = []
    for rm in re.finditer(r"(?is)<tr[^>]*>(.*?)</tr>", html):
        row = rm.group(1)
        gm = re.search(r'href=["\']([^"\']*stadion-(\d+)\.html)["\']', row, re.I)
        if not gm:
            continue
        cells = [text_of(c) for c in
                 re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", row)]
        cells = [c for c in cells if c]
        if not cells:
            continue
        cap = ""
        for c in cells:
            if re.fullmatch(r"\d{1,3}(\.\d{3})*", c) and len(c) >= 3:
                cap = c
                break
        ground = ""
        gt = re.search(r"(?is)>([^<]{2,80})</a>", gm.group(0) + row[gm.end():])
        for c in cells[1:]:
            if c != cap and not re.fullmatch(r"[NKR]", c):
                ground = c
                break
        rows.append({"club": cells[0], "ground": ground or (gt.group(1).strip()
                     if gt else ""), "cap": cap, "href": gm.group(1),
                     "stadionId": gm.group(2), "liga": liga})
    return rows


# ------------------------------------------------------------------ run
with open("data/clubs/coordinate-review.csv") as f:
    review = {r["clubQid"]: r for r in csv.DictReader(f)}
targets = [{"qid": q, "name": review[q]["name"], "city": review[q]["_city"]}
           for q in TARGETS if q in review]
say(f"targets: {len(targets)}/22 found in coordinate-review.csv")

allrows, fetched = [], []
say("[tier 4]")
for lid, lname in TIER4:
    h = get(f"/index.php?s=liga&id={lid}", lname)
    if h:
        r = parse_league(h, lname)
        allrows += r
        fetched.append({"liga": lname, "id": lid, "rows": len(r)})
        if not fetched[0].get("saved"):
            # Keep one raw page, so a parsing bug can be fixed without
            # asking the site the same question a second time.
            open(f"{OUT}/league-raw.html", "w").write(h)
            fetched[0]["saved"] = True
        with open(f"{OUT}/rows.json", "w") as fh:
            json.dump(allrows, fh, ensure_ascii=False, indent=1)

def best(t):
    c = sorted(((score(t["name"], r["club"]), r) for r in allrows),
               key=lambda x: -x[0])
    return c[0][0] if c else 0.0

say("[tier 5, only for clubs tier 4 did not hold]")
missing = [t for t in targets if best(t) < 0.75]
say(f"  still missing after tier 4: {len(missing)}")
if missing:
    for lid, lname in TIER5.items():
        h = get(f"/index.php?s=liga&id={lid}", lname)
        if h:
            r = parse_league(h, lname)
            allrows += r
            fetched.append({"liga": lname, "id": lid, "rows": len(r)})

# ------------------------------------------------------- candidates only
out = []
for t in targets:
    cands = sorted(((score(t["name"], r["club"]), r) for r in allrows),
                   key=lambda x: -x[0])
    keep = [dict(r, score=s) for s, r in cands[:4] if s > 0.15]
    out.append({"qid": t["qid"], "wikidata_name": t["name"],
                "wikidata_city": t["city"], "candidates": keep})

with open(f"{OUT}/candidates.json", "w") as f:
    json.dump({"leagues_read": fetched, "rows_seen": len(allrows),
               "targets": out}, f, ensure_ascii=False, indent=1)

say("")
say(f"leagues read: {len(fetched)}, rows seen: {len(allrows)}")
for t in out:
    c = t["candidates"]
    top = f'{c[0]["score"]} {c[0]["club"]} -> {c[0]["ground"]}' if c else "NOTHING"
    say(f'  {t["wikidata_name"][:30].ljust(31)} {top[:70]}')
