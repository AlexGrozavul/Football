#!/usr/bin/env python3
# THROWAWAY probe #2 - removed in the same branch.
import json, urllib.request, urllib.error
UA = {"User-Agent": "football-fixture-planner probe (personal, non-commercial)"}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None
L = get("https://api.openligadb.de/getavailableleagues")[1]
for l in sorted(L, key=lambda l: (str(l["leagueSeason"]), l["leagueShortcut"])):
    if str(l["leagueSeason"]) in ("2025", "2026", "2027"):
        print("L", l["leagueSeason"], repr(l["leagueShortcut"]), l["leagueId"], repr(l["leagueName"]), (l.get("sport") or {}).get("sportName"))
print("SHORTCUT HISTORY")
for sc in ("rlw", "RLW", "rlsw", "rlb", "rln", "rlno", "regio-bayern", "bl2", "bl3", "dfb"):
    seasons = sorted(str(l["leagueSeason"]) for l in L if l["leagueShortcut"] == sc)
    print("H", sc, seasons[-6:])
s, t = get("https://api.openligadb.de/getavailableteams/regio-bayern/2026")
print("RB TEAMS", [x.get("teamName") for x in (t or [])])
s, m = get("https://api.openligadb.de/getmatchdata/bl3/2026")
nodate = sum(1 for x in m if not x.get("matchDateTime") or str(x.get("matchDateTimeUTC","")).startswith("1970"))
noloc = sum(1 for x in m if not x.get("location"))
print("BL3 nodate", nodate, "noloc", noloc, "of", len(m))
s, m = get("https://api.openligadb.de/getmatchdata/dfb/2026")
print("DFB groups", sorted({(x["group"]["groupOrderID"], x["group"]["groupName"]) for x in m}))
print("DFB dates", sorted({x.get("matchDateTimeUTC","")[:10] for x in m})[-5:])
s, c = get("https://api.openligadb.de/getcurrentgroup/bl2")
print("CURGROUP bl2", s, c)
print("DONE2")
