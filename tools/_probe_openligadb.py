#!/usr/bin/env python3
# THROWAWAY probe - removed in the same branch. Prints small answers.
import json, re, time, urllib.request, urllib.error
UA = {"User-Agent": "football-fixture-planner probe (personal, non-commercial)", "Accept": "application/json"}
def get(url):
    t = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            body = r.read()
            return r.status, body, dict(r.headers), time.time() - t
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers), time.time() - t
    except Exception as e:
        return None, str(e).encode(), {}, time.time() - t

for base in ("https://api.openligadb.de", "https://www.openligadb.de/api"):
    s, b, h, dt = get(base + "/getavailableleagues")
    print(f"BASE {base}: HTTP {s} {len(b)}B {dt:.1f}s ctype={h.get('Content-Type')}")
s, b, h, dt = get("https://api.openligadb.de/getavailableleagues")
leagues = json.loads(b)
print("TOTAL LEAGUES", len(leagues))
print("SAMPLE ENTRY", json.dumps(leagues[0], ensure_ascii=False))
pat = re.compile(r"bundesliga|3\.? ?liga|pokal|regionalliga|dfb", re.I)
hits = [l for l in leagues if pat.search(l.get("leagueName") or "") and str(l.get("leagueSeason")) in ("2024","2025","2026")]
hits.sort(key=lambda l: (str(l.get("leagueSeason")), l.get("leagueShortcut") or ""))
for l in hits:
    print("LEAGUE", l.get("leagueSeason"), repr(l.get("leagueShortcut")), l.get("leagueId"),
          repr(l.get("leagueName")), "sport=", (l.get("sport") or {}).get("sportName"))
cands = sorted({(l["leagueShortcut"], str(l["leagueSeason"])) for l in hits if str(l["leagueSeason"]) == "2026"})
print("CANDIDATES 2026", cands)
for sc, season in cands:
    s, b, h, dt = get(f"https://api.openligadb.de/getmatchdata/{sc}/{season}")
    try: m = json.loads(b)
    except Exception: m = None
    n = len(m) if isinstance(m, list) else None
    teams = set()
    fin = 0
    if isinstance(m, list):
        for x in m:
            for k in ("team1", "team2"):
                t = x.get(k) or {}
                teams.add(t.get("teamId"))
            fin += bool(x.get("matchIsFinished"))
    s2, b2, _, _ = get(f"https://api.openligadb.de/getavailableteams/{sc}/{season}")
    try: tl = json.loads(b2)
    except Exception: tl = None
    icons = sum(1 for t in tl if t.get("teamIconUrl")) if isinstance(tl, list) else None
    print(f"MATCHES {sc}/{season}: HTTP {s} n={n} finished={fin} teamsInMatches={len(teams)} "
          f"| teams HTTP {s2} n={len(tl) if isinstance(tl, list) else None} withIcon={icons} {dt:.1f}s")
    if isinstance(m, list) and m:
        x = m[0]
        print("  KEYS", sorted(x.keys()))
        print("  TEAMKEYS", sorted((x.get("team1") or {}).keys()))
        print("  GROUP", json.dumps(x.get("group"), ensure_ascii=False), "LOC", json.dumps(x.get("location"), ensure_ascii=False))
        print("  DATES", x.get("matchDateTime"), x.get("matchDateTimeUTC"), x.get("timeZoneID"), "leagueId", x.get("leagueId"), x.get("leagueName"))
        print("  T1", json.dumps(x.get("team1"), ensure_ascii=False))
        print("  RESULTS", json.dumps(x.get("matchResults"), ensure_ascii=False)[:300])
    if isinstance(tl, list) and tl:
        print("  ICONHOSTS", sorted({re.sub(r"^https?://([^/]+)/.*$", r"\1", t.get("teamIconUrl") or "-") for t in tl})[:6])
# unknown league: what does "nothing" look like?
for u in ("https://api.openligadb.de/getmatchdata/zzznotaleague/2026",
          "https://api.openligadb.de/getavailableteams/zzznotaleague/2026",
          "https://api.openligadb.de/getmatchdata/bl2/1999"):
    s, b, h, dt = get(u)
    print(f"UNKNOWN {u}: HTTP {s} body={b[:80]!r}")
print("DONE. candidates again:", cands)
