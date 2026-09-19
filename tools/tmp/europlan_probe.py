#!/usr/bin/env python3
"""THROWAWAY probe, phase 3: ground, coordinates and capacity for the 22.

Phase 1 settled the structure. There is NO /<ground>/verein/<clubId>
link anywhere on the site - that shape came from a search engine's
index, not from the site, and CLAUDE.md already flagged it unverified.
The real club-to-ground link is a league page's table: each row names a
club and the ground it plays at, which is the site's own assertion and
not a name match.

Phase 2 proved the route and exposed a parser bug in itself. This
rereads the same 13 league pages with the cells taken properly:

  club      <span translate="no"> in the club cell
  ground    <td class="liste_stadt"> and its stadion-<id>.html link
  capacity  <td class="kapazitaet">
  position  the row's own zoom control, ol.proj.fromLonLat([lon,lat])

Then it reads the ground page for each candidate, which carries the
address, the capacity and a Google Maps link holding the authoritative
coordinates.

It still decides nothing. Everything is written out with the town from
the ground's address beside the town Wikidata gives the club, so a
false match like Eutin 08 against FC 08 Homburg - which scored 0.5 on
the shared '08' alone - is visible to whoever judges it.
"""
import csv, json, os, re, subprocess, sys, time

BASE = "https://www.europlan-online.de"
UA = ("FootballFixturePlanner/1.0 (personal, non-commercial; "
      "resolving 22 missing German ground coordinates)")
OUT, PAUSE, MAXTIME = "tmp-europlan", 1.2, 40
os.makedirs(OUT, exist_ok=True)

TARGETS = ["Q15972883","Q4545849","Q13397712","Q1378922","Q5424829","Q97927365",
           "Q831887","Q720528","Q3736767","Q13426883","Q566165","Q1514109",
           "Q831892","Q15849956","Q7572134","Q566179","Q2521441","Q479306",
           "Q127275134","Q920263","Q21175456","Q16743331"]

LEAGUES = [("654","NOFV-Regionalliga Nordost"),("640","Regionalliga Bayern"),
           ("2900","Regionalliga Nord"),("24","Regionalliga Südwest"),
           ("23","Regionalliga West"),("30","NOFV-Oberliga Nord"),
           ("55","Oberliga Niederrhein"),("5381","Oberliga Westfalen"),
           ("2901","Oberliga Niedersachsen"),("3010","Schleswig-Holstein-Liga"),
           ("34","Hessenliga"),("641","Bayernliga Nord"),("642","Bayernliga Süd")]


def say(s): print(s, flush=True)


def get(path, label):
    url = path if path.startswith("http") else BASE + "/" + path.lstrip("/")
    cmd = ["curl","-sSL","--max-time",str(MAXTIME),"--compressed","-A",UA,
           "-H","Accept-Language: de,en","-w","\n__M__%{http_code}",url]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=MAXTIME+10)
    except subprocess.TimeoutExpired:
        say(f"  {label}: TIMEOUT"); return None
    raw = p.stdout.decode("utf-8","replace")
    if "__M__" not in raw:
        say(f"  {label}: NO RESPONSE"); return None
    body, meta = raw.rsplit("\n__M__",1)
    say(f"  {label}: {meta.strip()} {len(body)}B")
    time.sleep(PAUSE)
    return body


ENT = {"&nbsp;":" ","&amp;":"&","&quot;":'"',"&#039;":"'","&uuml;":"ü",
       "&auml;":"ä","&ouml;":"ö","&szlig;":"ß","&Uuml;":"Ü","&Auml;":"Ä",
       "&Ouml;":"Ö","&eacute;":"é","&ndash;":"–","&raquo;":"»","&quot":'"'}

def txt(h):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>"," ",h)
    t = re.sub(r"(?i)<br\s*/?>","\n",t)
    t = re.sub(r"<[^>]+>"," ",t)
    for k,v in ENT.items(): t = t.replace(k,v)
    t = re.sub(r"[ \t]+"," ",t)
    return re.sub(r"\n\s*\n+","\n",t).strip()

def norm(s):
    s = s.lower()
    for a,b in [("ä","ae"),("ö","oe"),("ü","ue"),("ß","ss"),("é","e"),("–","-")]:
        s = s.replace(a,b)
    s = re.sub(r"\b(18|19|20)\d{2}\b"," ",s)
    s = re.sub(r"\b\d{2}\s*/\s*\d{2}\b"," ",s)
    s = re.sub(r"[^a-z0-9]+"," ",s)
    return re.sub(r"\s+"," ",s).strip()

NOISE = {"fc","sv","vfb","vfl","vfr","sg","spvgg","tsv","fsv","1","sc","bsc",
         "ii","2","club","verein","berliner","der","bsg","ssv","fsc","spfr",
         "tus","su","svg","08","09","04","05","03","07","06","1900","fsg"}

def reserve(s): return bool(re.search(r"(^|\s)(ii|2)$", norm(s)))

def score(a,b):
    ta,tb = set(norm(a).split()), set(norm(b).split())
    if not ta or not tb: return 0.0
    # A first team and its reserve side are never the same club, and
    # putting one at the other's ground is the exact error this whole
    # exercise exists to undo.
    if reserve(a) != reserve(b): return 0.0
    da,db = ta-NOISE, tb-NOISE
    if not da or not db: da,db = ta,tb
    return round(len(da&db)/max(len(da),len(db)),3)


def parse_league(html, liga):
    out = []
    for rm in re.finditer(r"(?is)<tr[^>]*>(.*?)</tr>", html):
        row = rm.group(1)
        gm = re.search(r'(?is)<td class="liste_stadt">\s*<a href="([^"]+stadion-(\d+)\.html)"[^>]*>(.*?)</a>', row)
        if not gm: continue
        cm = re.search(r'(?is)<span translate="no">(.*?)</span>', row)
        cap = re.search(r'(?is)<td class="kapazitaet">\s*([\d.]+)\s*</td>', row)
        ll = re.search(r"fromLonLat\(\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]\)", row)
        out.append({"club": txt(cm.group(1)) if cm else "",
                    "ground": txt(gm.group(3)), "href": gm.group(1),
                    "stadionId": gm.group(2),
                    "cap": cap.group(1) if cap else "",
                    "lon": ll.group(1) if ll else "", "lat": ll.group(2) if ll else "",
                    "liga": liga})
    return out


def parse_ground(html, url):
    t = txt(html)
    g = {"url": url}
    m = re.search(r"maps\.google\.[a-z.]+/maps\?q=\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)", html)
    if m: g["lat"], g["lon"] = m.group(1), m.group(2)
    m = re.search(r"(?i)Kapazität:\s*([\d.]+)", t)
    if m: g["capacity"] = m.group(1)
    m = re.search(r"(?i)Untergrund:\s*(.+)", t)
    if m: g["surface"] = m.group(1).strip()[:40]
    m = re.search(r"(?is)Anschrift\s*\n(.{0,260}?)\n\s*(?:\||Stadiondaten)", t)
    if m:
        g["address"] = re.sub(r"\s*\n\s*", ", ", m.group(1).strip())[:200]
    m = re.search(r"\b(\d{5})\s+([^\n,|]+)", g.get("address", ""))
    if m: g["plz"], g["town"] = m.group(1), m.group(2).strip()
    m = re.search(r"(?is)Vereine, die in diesem Stadion spielen\s*\n(.{0,400}?)\n\s*(?:Weitere Vereine|Bilder|Europlan)", t)
    if m: g["clubs_here"] = re.sub(r"\s*\n\s*", " / ", m.group(1).strip())[:300]
    m = re.search(r"(?is)<title>(.*?)</title>", html)
    if m: g["title"] = txt(m.group(1))[:120]
    return g


# ------------------------------------------------------------------ run
with open("data/clubs/coordinate-review.csv") as f:
    review = {r["clubQid"]: r for r in csv.DictReader(f)}
targets = [{"qid": q, "name": review[q]["name"], "city": review[q]["_city"]}
           for q in TARGETS if q in review]
say(f"targets: {len(targets)}")

rows = []
say("[league pages]")
for lid, lname in LEAGUES:
    h = get(f"index.php?s=liga&id={lid}", lname)
    if h:
        r = parse_league(h, lname)
        rows += r
        say(f"     -> {len(r)} club rows")
json.dump(rows, open(f"{OUT}/rows.json","w"), ensure_ascii=False, indent=1)
say(f"rows: {len(rows)}")

# Candidates per target. Only clubs on the list are kept; every other
# row read is scored and dropped.
picks = []
for t in targets:
    c = sorted(((score(t["name"], r["club"]), r) for r in rows), key=lambda x:-x[0])
    picks.append({"qid": t["qid"], "wikidata_name": t["name"],
                  "wikidata_city": t["city"],
                  "candidates": [dict(r, score=s) for s,r in c[:3] if s >= 0.2]})

# Ground pages for the plausible candidates, deduped.
want = {}
for p in picks:
    for c in p["candidates"][:2]:
        if c["score"] >= 0.25:
            want.setdefault(c["stadionId"], c["href"])
say(f"[ground pages] {len(want)} distinct")
grounds = {}
for sid, href in want.items():
    h = get(href, f"stadion-{sid}")
    if h:
        grounds[sid] = parse_ground(h, BASE + "/" + href.lstrip("/"))

json.dump({"picks": picks, "grounds": grounds},
          open(f"{OUT}/resolved.json","w"), ensure_ascii=False, indent=1)

say("")
say("=== per target: best candidate, and the ground's own town ===")
for p in picks:
    if not p["candidates"]:
        say(f'  {p["wikidata_name"][:30].ljust(31)} NO CANDIDATE'); continue
    c = p["candidates"][0]
    g = grounds.get(c["stadionId"], {})
    say(f'  {p["wikidata_name"][:30].ljust(31)} {c["score"]} {c["club"][:28].ljust(29)}'
        f' {c["ground"][:26].ljust(27)} town={g.get("town","?")[:18].ljust(19)}'
        f' wd_city={p["wikidata_city"][:16]}')
