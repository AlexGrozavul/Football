"""TEMPORARY probe - removed in the same branch. Reads, writes nothing."""
import json, re, sys, time, urllib.parse, urllib.request

UA = "football-planner-probe/1.0 (github.com/AlexGrozavul/Football)"
QIDS = ["Q24895825", "Q74127553", "Q55864953", "Q7579573", "Q20647345",
        "Q55583717", "Q130234791", "Q113577655", "Q130199486", "Q66424148"]
OSM = ["way/304104666", "way/304104667", "way/337616342", "way/157916749",
       "way/1147687747", "way/1553597347", "way/1153194250", "node/1493556659"]
KEYWORDS = ["Bistri", "Modelu", "Muscel", "Câmpulung", "Cărbune", "Gilort",
            "Secuiesc", "KSE", "Humor", "Șoimii", "Zărne", "Olimpic", "Curti",
            "Oltul", "Lotus", "Felix"]


def get(url, data=None, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            print(f"   ! {url[:70]} attempt {i+1}: {e}")
            time.sleep(20)
    return None


def wd(ids):
    u = ("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
         "&props=labels|claims|sitelinks&languages=en|ro&ids=" + "|".join(ids))
    return (get(u) or {}).get("entities", {})


def val(c):
    dv = c["mainsnak"].get("datavalue")
    if not dv:
        return "<" + c["mainsnak"]["snaktype"] + ">"
    v = dv["value"]
    if isinstance(v, dict):
        return v.get("id") or v.get("time") or (
            f"{v.get('latitude')},{v.get('longitude')}" if "latitude" in v else str(v))
    return str(v)


def wikitext(site, title):
    u = (f"https://{site}.wikipedia.org/w/api.php?action=parse&format=json"
         f"&prop=wikitext&redirects=1&page=" + urllib.parse.quote(title))
    d = get(u) or {}
    return (d.get("parse") or {}).get("wikitext", {}).get("*", "")


print("=" * 30, "WIKIDATA")
ents = wd(QIDS)
refs = set()
for q in QIDS:
    e = ents.get(q, {})
    lab = e.get("labels", {})
    print(f"\n## {q}  en={lab.get('en',{}).get('value')!r} ro={lab.get('ro',{}).get('value')!r}")
    for p in ("P31", "P571", "P576", "P118", "P115", "P159", "P131", "P625", "P1448"):
        cs = e.get("claims", {}).get(p, [])
        if cs:
            print(f"   {p}: " + "; ".join(f"{val(c)}[{c['rank'][:3]}]" for c in cs))
            for c in cs:
                v = val(c)
                if v.startswith("Q"):
                    refs.add(v)
    sl = e.get("sitelinks", {})
    print(f"   sitelinks ({len(sl)}): " + ", ".join(
        f"{k}={v['title']}" for k, v in sl.items() if k in ("enwiki", "rowiki", "huwiki")))
    e["_sl"] = sl

labels = wd(sorted(refs)[:50]) if refs else {}
print("\n   labels: " + "; ".join(
    f"{k}={(v.get('labels',{}).get('en') or v.get('labels',{}).get('ro') or {}).get('value')}"
    f"{' P625=' + val(v['claims']['P625'][0]) if 'P625' in v.get('claims',{}) else ''}"
    for k, v in labels.items()))

print("\n" + "=" * 30, "INFOBOXES")
FIELD = re.compile(r"^\s*\|\s*(ground|stadium|stadion|capacity|capacitate|league|liga|"
                   r"season|sezon|position|dissolved|desființat|desfiintat|founded|"
                   r"înființat|infiintat|fullname|nume|website|clubname|nickname)\w*\s*=",
                   re.I)
for q in QIDS:
    sl = ents.get(q, {}).get("_sl", {})
    for site in ("enwiki", "rowiki"):
        if site in sl:
            t = wikitext(site[:2], sl[site]["title"])
            lines = [l.strip()[:160] for l in t.splitlines()[:120] if FIELD.match(l)]
            print(f"\n## {q} {site} '{sl[site]['title']}' ({len(t)} chars)")
            for l in lines[:14]:
                print("   " + l)
            for m in re.finditer(r"[^.\n]*(dissolv|desființ|desfiint|retras|withdr|merged|fuzion)[^.\n]*",
                                 t, re.I):
                print("   ~ " + m.group(0).strip()[:200])
                break
            time.sleep(2)

print("\n" + "=" * 30, "2026-27 LIGA III / II ARTICLES")
for title in ("2026–27 Liga III", "2026–27 Liga II"):
    t = wikitext("en", title)
    print(f"\n## {title} ({len(t)} chars)")
    for k in KEYWORDS:
        hits = [l.strip()[:170] for l in t.splitlines() if k in l]
        if hits:
            print(f"   [{k}] {len(hits)}x: " + " || ".join(hits[:2]))

print("\n" + "=" * 30, "OVERPASS")
def op(q):
    return get("https://overpass-api.de/api/interpreter",
               urllib.parse.urlencode({"data": q}).encode())

ids = " ".join(f"{t}({i});" for t, i in (r.split("/") for r in OSM))
d = op(f"[out:json][timeout:120];({ids});out tags center;")
for el in (d or {}).get("elements", []):
    c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
    print(f"   {el['type']}/{el['id']} {c.get('lat')},{c.get('lon')} {el.get('tags')}")

time.sleep(15)
d = op('[out:json][timeout:120];area["ISO3166-1"="RO"][admin_level=2]->.a;'
       'node["place"]["name"~"^(Zărnești|Curtișoara|Moșteni|Câmpulung|Târgu Cărbunești|'
       'Târgu Secuiesc|Gura Humorului)$"](area.a);out tags;')
places = []
for el in (d or {}).get("elements", []):
    t = el.get("tags", {})
    places.append((t.get("name"), el["lat"], el["lon"]))
    print(f"   place {t.get('name')} ({t.get('place')}) {el['lat']},{el['lon']} "
          f"is_in={t.get('is_in:county') or t.get('is_in')} wd={t.get('wikidata')}")

for name, lat, lon in places:
    if name not in ("Zărnești", "Curtișoara", "Moșteni"):
        continue
    time.sleep(15)
    d = op(f'[out:json][timeout:120];(nwr["leisure"~"^(pitch|stadium|sports_centre)$"]'
           f'(around:3500,{lat},{lon});nwr["building"="stadium"](around:3500,{lat},{lon}););'
           f'out tags center;')
    print(f"\n   grounds within 3.5 km of {name} {lat},{lon}:")
    for el in (d or {}).get("elements", []):
        t = el.get("tags", {})
        if t.get("sport") and "soccer" not in t.get("sport", "") and t.get("leisure") == "pitch":
            continue
        c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        print(f"     {el['type']}/{el['id']} {c.get('lat')},{c.get('lon')} "
              f"{ {k: v for k, v in t.items() if k in ('name','leisure','sport','operator','wikidata','addr:city','capacity')} }")
print("\nEND OF PROBE")
