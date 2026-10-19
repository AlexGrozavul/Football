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
                j = json.loads(f.read().decode())
                if isinstance(j, dict) and "error" in j:
                    print("  API error:", str(j["error"])[:120], "try", t+1, flush=True); time.sleep(10*(t+1)); continue
                return j
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

EU = (37.427929, 24.937678)
print("== Syros: OSM full tags of the unnamed stadium and the nearest pitch, and any name match on the island")
q='[out:json][timeout:90];(way(209001423);way(208927852);way(209001410);way(208927855););out tags center;'
d=overpass(q)
for e in (d or {}).get("elements",[]): print(" ", e["type"]+"/"+str(e["id"]), json.dumps(e.get("tags",{}), ensure_ascii=False), center(e))
q='[out:json][timeout:90];nwr["name"~"Ερμούπ|Ermoupol|Βικελ|Vikelas|Άνω Σύρ|Ανω Συρ|Ano Syr|Ellas|Ελλάς|Hellas",i](37.30,24.85,37.50,25.00);out tags center;'
d=overpass(q)
for e in (d or {}).get("elements",[]):
    t=e.get("tags",{}); c=center(e)
    if c[0] is not None: print("  name-match %s/%s name=%r leisure=%s dist_to_europlan=%.0f m" % (e["type"],e["id"],t.get("name"),t.get("leisure"),hav(*EU,*c)))
print("== Syros: Wikidata")
W = "https://www.wikidata.org/w/api.php?format=json&maxlag=5&"
def srch(term, lang):
    d = req(W + "action=wbsearchentities&limit=7&language=%s&uselang=en&search=%s" % (lang, urllib.parse.quote(term)))
    return [(x["id"], x.get("label"), x.get("description")) for x in (d or {}).get("search", [])] if d else None
found = {}
for term, lang in [("Hellas Syros", "en"), ("Ermoupoli Municipal Stadium", "en"), ("Ermoupoli", "en"), ("Δημοτικό Στάδιο Ερμούπολης", "el"), ("Ermoupoli stadium", "en"), ("Ano Syros", "en"), ("Vikelas", "en")]:
    hits = srch(term, lang); print(" search %r: %s" % (term, hits))
    for h in hits or []: found[h[0]] = h
found["Q12872753"] = ("Q12872753", "Hellas Syros", "club")
d = req(W + "action=wbgetentities&props=labels|aliases|claims|descriptions&languages=en|el&ids=" + "|".join(list(found)[:45]))
ids115 = []
for qid, e in (d or {}).get("entities", {}).items():
    cl = e.get("claims", {})
    co = [(s["mainsnak"]["datavalue"]["value"]["latitude"], s["mainsnak"]["datavalue"]["value"]["longitude"]) for s in cl.get("P625", []) if "datavalue" in s["mainsnak"]]
    p31 = [s["mainsnak"]["datavalue"]["value"]["id"] for s in cl.get("P31", []) if "datavalue" in s["mainsnak"]]
    p115 = [s["mainsnak"]["datavalue"]["value"]["id"] for s in cl.get("P115", []) if "datavalue" in s["mainsnak"]]
    ids115 += p115
    al = {l: [a["value"] for a in v] for l, v in e.get("aliases", {}).items()}
    print(" %s en=%r el=%r P31=%s P115=%s P625=%s d_europlan=%s aliases=%s" % (qid, e.get("labels", {}).get("en", {}).get("value"), e.get("labels", {}).get("el", {}).get("value"), p31, p115, co, ["%.0f m" % hav(*EU, *c) for c in co], al))
if ids115:
    d = req(W + "action=wbgetentities&props=labels|claims&languages=en|el&ids=" + "|".join(ids115))
    for qid, e in (d or {}).get("entities", {}).items():
        co = [(s["mainsnak"]["datavalue"]["value"]["latitude"], s["mainsnak"]["datavalue"]["value"]["longitude"]) for s in e.get("claims", {}).get("P625", []) if "datavalue" in s["mainsnak"]]
        print(" P115 target %s en=%r el=%r P625=%s" % (qid, e.get("labels",{}).get("en",{}).get("value"), e.get("labels",{}).get("el",{}).get("value"), co))
q = """SELECT ?i ?l ?c ?t WHERE { SERVICE wikibase:around { ?i wdt:P625 ?c . bd:serviceParam wikibase:center "Point(24.9370 37.4290)"^^geo:wktLiteral . bd:serviceParam wikibase:radius "3" . } OPTIONAL { ?i wdt:P31 ?t } SERVICE wikibase:label { bd:serviceParam wikibase:language "en,el". ?i rdfs:label ?l } } LIMIT 80"""
d = req("https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q))
print(" SPARQL items with coordinates within 3 km of Ano Syros:", None if d is None else sorted({(b["i"]["value"].rsplit("/",1)[1], b["l"]["value"], b["c"]["value"]) for b in d["results"]["bindings"]}))
