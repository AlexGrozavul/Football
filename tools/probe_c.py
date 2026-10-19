import json, math, time, sys, urllib.request, urllib.parse, urllib.error
UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
last = [0.0]
def req(url, data=None, tries=4):
    for t in range(tries):
        w = 1.0 - (time.time() - last[0])
        if w > 0: time.sleep(w)
        last[0] = time.time()
        try:
            r = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=120) as f:
                return json.loads(f.read().decode())
        except urllib.error.HTTPError as e:
            ra = e.headers.get("Retry-After")
            print(f"  HTTP {e.code} try {t+1}" + (f" retry-after {ra}" if ra else ""), flush=True)
            time.sleep(min(int(ra), 90) if ra and ra.isdigit() else 15 * (t + 1))
        except Exception as e:
            print(f"  ERR {type(e).__name__} try {t+1}", flush=True); time.sleep(15 * (t + 1))
    return None
def hav(a, b, c, d):
    p = math.pi / 180; x = math.sin((c-a)*p/2)**2 + math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2
    return 12742000 * math.asin(math.sqrt(x))
OVP = "https://overpass-api.de/api/interpreter"
def overpass(q):
    return req(OVP, ("data=" + urllib.parse.quote(q)).encode())
def center(e):
    if "center" in e: return e["center"]["lat"], e["center"]["lon"]
    return e.get("lat"), e.get("lon")
def kind(t):
    l = t.get("leisure"); s = t.get("sport", "")
    if l == "stadium" or t.get("building") == "stadium": return "stadium"
    if l == "pitch" and ("soccer" in s or "football" in s): return "pitch:" + s
    if l == "sports_centre": return "sports_centre"
    return None
CLUBS = [("Nestos Chrysoupoli", 40.990763, 24.688693), ("Zemun/Jedinstvo Ub (Dzajic)", 44.453014, 20.071359),
         ("Selimbar (Magura)", 45.710194, 24.153139), ("Stefanestii de Jos (Matarau)", 44.539250, 26.202917)]
print("== C: OSM within 300 m of the hand-row coordinate")
for n, la, lo in CLUBS:
    q = f'[out:json][timeout:90];(nwr["leisure"~"^(stadium|pitch|sports_centre)$"](around:300,{la},{lo});nwr["building"="stadium"](around:300,{la},{lo}););out tags center;'
    d = overpass(q)
    if d is None: print(n, ": QUERY FAILED"); continue
    rows = []
    for e in d["elements"]:
        k = kind(e.get("tags", {}));
        if not k: continue
        c = center(e)
        if c[0] is None: continue
        rows.append((hav(la, lo, *c), k, e["type"] + "/" + str(e["id"]), e["tags"].get("name"), e["tags"].get("name:en")))
    rows.sort()
    print(n, ":", len(rows), "football-type elements within 300 m;", "named:", sum(1 for r in rows if r[3]))
    for r in rows[:6]: print("   %4.0f m %s %s name=%r en=%r" % r)
print("== Syros: OSM (island bbox) names")
q = '[out:json][timeout:90];(nwr["leisure"~"^(stadium|pitch|sports_centre)$"](37.30,24.85,37.50,25.00);nwr["building"="stadium"](37.30,24.85,37.50,25.00););out tags center;'
d = overpass(q)
EU = (37.427929, 24.937678)
if d:
    rows = []
    for e in d["elements"]:
        k = kind(e.get("tags", {}));
        if not k: continue
        c = center(e); rows.append((k, e["type"] + "/" + str(e["id"]), e["tags"].get("name"), e["tags"].get("name:en"), c, hav(*EU, *c)))
    print(len(rows), "football-type elements on Syros; those within 1.2 km of europlan's Ano Syros point (37.427929, 24.937678):")
    for r in sorted(rows, key=lambda r: r[5]):
        if r[5] < 1200: print("   %4.0f m %s %s name=%r en=%r at %.6f,%.6f" % (r[5], r[0], r[1], r[2], r[3], *r[4]))
else: print("Syros OSM query failed")
print("== Syros: Wikidata")
W = "https://www.wikidata.org/w/api.php?format=json&maxlag=5&"
found = {}
for term, lang in [("Ermoupoli Municipal Stadium", "en"), ("Ermoupoli stadium", "en"), ("Δημοτικό Στάδιο Ερμούπολης", "el"), ("Ανω Σύρος γήπεδο", "el"), ("Ano Syros stadium", "en"), ("Σύρος στάδιο", "el"), ("Vikelas", "en")]:
    d = req(W + "action=wbsearchentities&limit=5&language=%s&uselang=en&search=%s" % (lang, urllib.parse.quote(term)))
    hits = [(x["id"], x.get("label"), x.get("description")) for x in (d or {}).get("search", [])]
    print(" search %r: %s" % (term, hits))
    for h in hits: found[h[0]] = h
if found:
    d = req(W + "action=wbgetentities&props=labels|aliases|claims|descriptions&languages=en|el&ids=" + "|".join(list(found)[:40]))
    for qid, e in (d or {}).get("entities", {}).items():
        cl = e.get("claims", {}); p625 = cl.get("P625", [])
        co = [(s["mainsnak"]["datavalue"]["value"]["latitude"], s["mainsnak"]["datavalue"]["value"]["longitude"]) for s in p625 if "datavalue" in s["mainsnak"]]
        p31 = [s["mainsnak"]["datavalue"]["value"]["id"] for s in cl.get("P31", []) if "datavalue" in s["mainsnak"]]
        al = {l: [a["value"] for a in v] for l, v in e.get("aliases", {}).items()}
        print(" %s en=%r el=%r P31=%s P625=%s dist_to_europlan=%s aliases=%s" % (qid, e.get("labels", {}).get("en", {}).get("value"), e.get("labels", {}).get("el", {}).get("value"), p31, co, ["%.0f m" % hav(*EU, *c) for c in co], al))
# geosearch around Syros on Wikidata
d = req(W + "action=query&list=geosearch&gscoord=37.4290|24.9370&gsradius=3000&gslimit=50")
print(" Wikidata geosearch 3 km around Ano Syros:", [(x["title"], x.get("dist")) for x in (d or {}).get("query", {}).get("geosearch", [])] if d else "failed/none")
