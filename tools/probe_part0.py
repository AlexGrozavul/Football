#!/usr/bin/env python3
"""Temporary probe (Part 0a). Reads Wikipedia only. Summary first and last."""
import json, re, sys, time, urllib.parse, urllib.request, urllib.error

UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
API = "https://en.wikipedia.org/w/api.php"
last = [0.0]
calls = [0]

def get(params):
    params = dict(params, format="json", maxlag="5")
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(1, 5):
        gap = time.time() - last[0]
        if gap < 1.0:
            time.sleep(1.0 - gap)
        last[0] = time.time()
        calls[0] += 1
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                obj = json.loads(r.read().decode("utf-8"))
            if (obj.get("error") or {}).get("code") == "maxlag":
                time.sleep(6); continue
            return obj
        except urllib.error.HTTPError as e:
            ra = int(e.headers.get("Retry-After") or 0) if e.headers else 0
            if e.code in (429, 503) and attempt < 4:
                time.sleep(min(ra or 20 * attempt, 90)); continue
            return {"error": f"HTTP {e.code}"}
        except Exception as e:
            if attempt < 4:
                time.sleep(10 * attempt); continue
            return {"error": str(e)}
    return {"error": "gave up"}

NAT = {
 "Swedish":"SE","Scottish":"GB-SCT","Croatian":"HR","Danish":"DK","Bosnian":"BA","Polish":"PL","Israeli":"IL",
 "Macedonian":"MK","Irish":"IE","Australian":"AU","Portuguese":"PT","English":"GB-ENG","Welsh":"GB-WLS",
 "Italian":"IT","German":"DE","French":"FR","Spanish":"ES","Romanian":"RO","Greek":"GR","Serbian":"RS",
 "Dutch":"NL","Belgian":"BE","Swiss":"CH","Austrian":"AT","Norwegian":"NO","Finnish":"FI","Turkish":"TR",
 "Czech":"CZ","Slovak":"SK","Hungarian":"HU","Bulgarian":"BG","Ukrainian":"UA","Russian":"RU",
 "Cypriot":"CY","Slovenian":"SI","Brazilian":"BR","Argentine":"AR","American":"US","Japanese":"JP",
 "Northern Irish":"GB-NIR","Montenegrin":"ME","Albanian":"AL","Icelandic":"IS","Maltese":"MT","Belarusian":"BY",
 "Moldovan":"MD","Georgian":"GE","Kazakh":"KZ","Luxembourg":"LU","Lithuanian":"LT","Latvian":"LV","Estonian":"EE",
}
NATRE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, NAT), key=len, reverse=True)) + r")\b")

def club_country(name):
    obj = get({"action": "query", "generator": "search", "gsrsearch": f"{name} football club",
               "gsrlimit": "1", "prop": "extracts", "exintro": "1", "explaintext": "1",
               "exsentences": "2", "redirects": "1"})
    pages = ((obj.get("query") or {}).get("pages") or {})
    if not pages:
        return name, None, "UNKNOWN", obj.get("error", "no hit")
    p = next(iter(pages.values()))
    ex = (p.get("extract") or "").replace("\n", " ")
    m = NATRE.search(ex[:300])
    return name, p.get("title"), NAT[m.group(1)] if m else "UNKNOWN", ex[:90]

LEAGUES = {
 "Albania": ("Kategoria Superiore", "Kategoria e Parë"),
 "Andorra": ("Primera Divisió", "Segona Divisió"),
 "Armenia": ("Armenian Premier League", "Armenian First League"),
 "Azerbaijan": ("Azerbaijan Premier League", "Azerbaijan First Division"),
 "Belarus": ("Belarusian Premier League", "Belarusian First League"),
 "Bosnia and Herzegovina": ("Premier League of Bosnia and Herzegovina", "First League of the Federation of Bosnia and Herzegovina"),
 "Bulgaria": ("First Professional Football League (Bulgaria)", "Second Professional Football League (Bulgaria)"),
 "Croatia": ("Croatian Football League", "Croatian First Football League"),
 "Cyprus": ("Cypriot First Division", "Cypriot Second Division"),
 "Czech Republic": ("Czech First League", "Czech National Football League"),
 "Denmark": ("Danish Superliga", "Danish 1st Division"),
 "Estonia": ("Meistriliiga", "Esiliiga"),
 "Faroe Islands": ("Faroe Islands Premier League", "1. deild (Faroe Islands)"),
 "Finland": ("Veikkausliiga", "Ykkösliiga"),
 "Georgia": ("Erovnuli Liga", "Erovnuli Liga 2"),
 "Gibraltar": ("Gibraltar National League", "Gibraltar Second Division"),
 "Hungary": ("Nemzeti Bajnokság I", "Nemzeti Bajnokság II"),
 "Iceland": ("Besta deild karla", "1. deild karla"),
 "Israel": ("Israeli Premier League", "Liga Leumit"),
 "Kazakhstan": ("Kazakhstan Premier League", "Kazakhstan First Division"),
 "Kosovo": ("Football Superleague of Kosovo", "Kosovan First League"),
 "Latvia": ("Latvian Higher League", "Latvian First League"),
 "Liechtenstein": ("Liechtenstein league", "Liechtenstein second league"),
 "Lithuania": ("A Lyga", "I Lyga"),
 "Luxembourg": ("Luxembourg National Division", "Luxembourg Division of Honour"),
 "Malta": ("Maltese Premier League", "Maltese Challenge League"),
 "Moldova": ("Moldovan Super Liga", "Moldovan Liga 1"),
 "Montenegro": ("Montenegrin First League", "Montenegrin Second League"),
 "North Macedonia": ("Macedonian First Football League", "Macedonian Second Football League"),
 "Northern Ireland": ("NIFL Premiership", "NIFL Championship"),
 "Norway": ("Eliteserien", "OBOS-ligaen"),
 "Poland": ("Ekstraklasa", "I liga"),
 "Republic of Ireland": ("League of Ireland Premier Division", "League of Ireland First Division"),
 "Russia": ("Russian Premier League", "Russian First League"),
 "San Marino": ("Campionato Sammarinese di Calcio", "Campionato Sammarinese di Calcio second tier"),
 "Scotland": ("Scottish Premiership", "Scottish Championship"),
 "Slovakia": ("Slovak First Football League", "2. Liga (Slovakia)"),
 "Slovenia": ("Slovenian PrvaLiga", "Slovenian Second League"),
 "Sweden": ("Allsvenskan", "Superettan"),
 "Turkey": ("Süper Lig", "TFF 1. Lig"),
 "Ukraine": ("Ukrainian Premier League", "Ukrainian First League"),
 "Wales": ("Cymru Premier", "Cymru South"),
}
ND = "–"

def season_titles(league):
    return [f"2026{ND}27 {league}", f"2026 {league}"]

def exists(titles):
    out = {}
    for i in range(0, len(titles), 40):
        obj = get({"action": "query", "titles": "|".join(titles[i:i + 40]), "redirects": "1", "prop": "info"})
        q = obj.get("query") or {}
        redir = {r["from"]: r["to"] for r in q.get("redirects") or []}
        norm = {r["from"]: r["to"] for r in q.get("normalized") or []}
        pages = {p["title"]: ("missing" not in p) for p in (q.get("pages") or {}).values()}
        for t in titles[i:i + 40]:
            t1 = norm.get(t, t); t2 = redir.get(t1, t1)
            out[t] = (pages.get(t2, False), t2)
    return out

def search_hint(league):
    obj = get({"action": "query", "list": "search", "srsearch": f"2026 {league} season", "srlimit": "3"})
    return [h["title"] for h in (obj.get("query") or {}).get("search") or []]

def main():
    t0 = time.time()
    names = json.load(open("tools/probe_names.json", encoding="utf-8"))
    print(f"PROBE part0: {len(names)} rival/friend names, {len(LEAGUES)} countries")
    print("=== A. club countries (name | title | country | first words)")
    res = [club_country(n) for n in names]
    for n, t, c, ex in res:
        print(f"{n} | {t} | {c} | {ex}")
    print("=== B. season articles (country | tier1 | tier2)")
    for country, (l1, l2) in LEAGUES.items():
        row = []
        for tier, lg in ((1, l1), (2, l2)):
            ts = season_titles(lg)
            ex = exists(ts)
            hit = [(t, ex[t][1]) for t in ts if ex[t][0]]
            if hit:
                row.append(f"T{tier} YES {hit[0][1]}")
            else:
                row.append(f"T{tier} NO (search: {'; '.join(search_hint(lg))})")
        print(f"{country} | " + " | ".join(row))
    print(f"SUMMARY part0 done: {calls[0]} Wikipedia calls in {time.time()-t0:.0f}s")

main()
