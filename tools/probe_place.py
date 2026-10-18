# TEMPORARY probe for the place-clubs pass 2 (removed before merge)
import json, re, sys, time, urllib.parse, urllib.request
UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
def get(url, data=None, tries=4, timeout=60):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
            time.sleep(1); return body
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(int(e.headers.get("Retry-After", "20")))
            elif e.code in (500, 502, 503, 504): time.sleep(10 * (i + 1))
            else: return f"HTTPERR {e.code}"
        except Exception as e:
            time.sleep(10 * (i + 1)); last = str(e)
    return "FAILED"
def jget(url, data=None):
    b = get(url, data)
    try: return json.loads(b)
    except Exception: return {"_raw": b[:200]}
print("PROBE-SUMMARY-START")
# A. Wikidata
ids = "Q132566856|Q131850818|Q28230311|Q3292651|Q16845757|Q12872753|Q1323373|Q1388917|Q110045992"
d = jget("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&maxlag=5&languages=en|el|ro|sr|sr-el&props=labels|aliases|claims&ids=" + urllib.parse.quote(ids, safe="|"))
ents = d.get("entities", {})
def claim(e, p):
    out = []
    for c in (e.get("claims", {}).get(p) or []):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, dict) and "latitude" in v: out.append(f"{v['latitude']:.6f}/{v['longitude']:.6f}")
        elif isinstance(v, dict) and "id" in v: out.append(v["id"] + "(" + c.get("rank", "")[:1] + ")")
        elif v is not None: out.append(str(v)[:40])
    return out
for q, e in ents.items():
    labs = {k: v["value"] for k, v in e.get("labels", {}).items()}
    al = {k: [x["value"] for x in v] for k, v in e.get("aliases", {}).items()}
    print(f"WD {q} labels={labs} aliases={al} P115={claim(e,'P115')} P625={claim(e,'P625')} P1083={claim(e,'P1083')} P576={claim(e,'P576')}")
# ground items of the four clubs' P115
grounds = sorted({g.split("(")[0] for q in ("Q16845757", "Q12872753", "Q1323373", "Q1388917", "Q3292651") for g in claim(ents.get(q, {}), "P115")})
if grounds:
    d2 = jget("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&maxlag=5&languages=en|el|sr&props=labels|aliases|claims&ids=" + "|".join(grounds))
    for q, e in d2.get("entities", {}).items():
        labs = {k: v["value"] for k, v in e.get("labels", {}).items()}
        al = {k: [x["value"] for x in v] for k, v in e.get("aliases", {}).items()}
        print(f"WDG {q} labels={labs} aliases={al} P625={claim(e,'P625')} P1083={claim(e,'P1083')}")
for term in ("Zakynthians Olympic Champions Ground", "Στάδιο Ζακυνθίων Ολυμπιονικών", "Zakynthos Municipal Stadium", "Stadion Dragan Džajić", "Chrysoupoli Municipal Stadium", "Ermoupoli Municipal Stadium"):
    s = jget("https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&limit=5&language=en&search=" + urllib.parse.quote(term))
    print("WDSEARCH", term, [(x["id"], x.get("label"), x.get("description")) for x in s.get("search", [])])
# B. Overpass
def over(label, q):
    d = jget("https://overpass-api.de/api/interpreter", ("data=" + urllib.parse.quote(q)).encode())
    els = d.get("elements")
    if els is None: print("OVERPASS", label, "FAILED", str(d)[:150]); return
    print("OVERPASS", label, len(els))
    for e in els[:12]:
        c = e.get("center") or {"lat": e.get("lat"), "lon": e.get("lon")}
        t = e.get("tags", {})
        print("   ", e["type"], e["id"], f"{c['lat']:.6f}/{c['lon']:.6f}", {k: t[k] for k in ("name", "name:en", "name:el", "leisure", "sport", "capacity", "building", "operator") if k in t})
fb = '["leisure"~"stadium|pitch|sports_centre"]'
over("zakynthos 400m", f'[out:json][timeout:60];(nwr(around:400,37.770997,20.886793){fb};);out center tags;')
over("cisnadie Magura 400m", f'[out:json][timeout:60];(nwr(around:400,45.710194,24.153139){fb};);out center tags;')
over("clinceni stadium 400m", f'[out:json][timeout:60];(nwr(around:400,44.377778,25.940833){fb};);out center tags;')
over("stefanestii Dumitru Matarau 400m", f'[out:json][timeout:60];(nwr(around:400,44.539250,26.202917){fb};);out center tags;')
over("popesti inter gaz 400m", f'[out:json][timeout:60];(nwr(around:400,44.376750,26.203917){fb};);out center tags;')
# C. StadiumDB
for slug, keys in (("rou", r"Șelimbăr|Selimbar|Cisnădie|Cisnadie|Magura|Ștefăneștii|Stefanestii|Matarau|Mătărău|Clinceni|Popești|Popesti"), ("ser", r"Ub\b|Zemun|Džaji|Dzaji|Dragan"), ("gre", r"Chrysoup|Nestos|Syros|Ermoup|Zakynth")):
    b = get(f"https://stadiumdb.com/stadiums/{slug}")
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", b, re.S)
    hits = []
    for r in rows:
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r)).strip()
        if re.search(keys, t, re.I): hits.append(t[:160])
    print("STADIUMDB", slug, len(rows), "rows;", hits[:8] or "no matching row")
# D. Popesti second source
for label, url, pat in (
    ("calciomercato Popesti-Steaua", "https://www.calciomercato.com/partita/popesti-leordeni-steaua-bucuresti/Ay1GRwsA77PC-ezEuneNd", r"Clinceni|Inter Gaz|[Ss]tadio|Stadion"),
    ("calciomercato Popesti-Bacau", "https://www.calciomercato.com/partita/popesti-leordeni-fc-bacau/ipBJEa0LyCQ7yT3ca6W0w", r"Clinceni|Inter Gaz|[Ss]tadio|Stadion"),
    ("newsweek", "https://newsweek.ro/sport/poli-timisoara-a-castigat-spectaculos-cu-cs-popesti-leordeni-in-liga-a-ii-a", r"Clinceni|Inter Gaz|stadion"),
    ("club site", "https://scpopestileordeni.com/", r"Clinceni|Inter Gaz|stadion|Stadion"),
    ("soccerway", "https://ro.soccerway.com/echipa/popesti-leordeni/jZwqBI0S", r"Clinceni|Inter Gaz")):
    b = get(url)
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b))
    ms = [txt[max(0, m.start() - 70): m.end() + 90] for m in re.finditer(pat, txt)][:4]
    print("POP2", label, len(b), ms or "no match")
# E. europlan
EU = "https://www.europlan-online.de/"
pages = 0
found = {}
for term in ("Chrysoupoli", "Ermoupoli", "Ub"):
    b = get(EU + "index.php?s=search&search=" + urllib.parse.quote(term)); pages += 1
    links = re.findall(r'<a[^>]+href="([^"]*stadion-\d+\.html)"[^>]*>(.*?)</a>', b, re.S)
    clean = [(h, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip()) for h, t in links]
    print("EUROPLAN search", term, len(clean), [c for c in clean][:12])
    found[term] = clean
KEY = re.compile(r"chrysoup|nestos|syros|ermoup|\bub\b|dzaji|džaji|zemun|jedinstvo|dragan", re.I)
todo = []
for term, clean in found.items():
    for h, t in clean:
        if KEY.search(h) or KEY.search(t): todo.append((h, t))
seen = []
for h, t in todo:
    if h in seen or pages >= 10: continue
    seen.append(h); pages += 1
    url = h if h.startswith("http") else EU + h.lstrip("/")
    b = get(url)
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b))
    co = re.findall(r"maps\.google\.de/maps\?q=\(([-\d., ]+)\)", b)[:1]
    cap = re.findall(r"Kapazit[äa]t:?\s*([\d.]+)", txt)[:1]
    vv = re.search(r"Vereine, die in diesem Stadion spielen(.{0,300})", txt)
    ttl = re.search(r"<title>(.*?)</title>", b, re.S)
    print("EUROPLAN ground", url, "|", (ttl.group(1).strip()[:90] if ttl else ""), "| coord", co, "| cap", cap, "| clubs:", (vv.group(1)[:260] if vv else "n/a"))
print("EUROPLAN pages used:", pages)
print("PROBE-SUMMARY-END")
