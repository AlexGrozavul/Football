"""TEMPORARY probe #2 - removed in the same branch. Reads, writes nothing."""
import json, re, time, urllib.parse, urllib.request
UA = "football-planner-probe/1.0 (github.com/AlexGrozavul/Football)"

def get(url, data=None, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            print(f"   ! attempt {i+1}: {e}"); time.sleep(30)
    return None

def wikitext(site, title):
    time.sleep(4)
    d = get(f"https://{site}.wikipedia.org/w/api.php?action=parse&format=json"
            f"&prop=wikitext&redirects=1&page=" + urllib.parse.quote(title)) or {}
    return (d.get("parse") or {}).get("wikitext", {}).get("*", "")

def coords(site, title):
    time.sleep(4)
    d = get(f"https://{site}.wikipedia.org/w/api.php?action=query&format=json&prop=coordinates|pageprops"
            f"&redirects=1&titles=" + urllib.parse.quote(title)) or {}
    for p in (d.get("query") or {}).get("pages", {}).values():
        return p.get("title"), p.get("coordinates"), (p.get("pageprops") or {}).get("wikibase_item")

print("==== LIGA III 2026-27 CONTEXT")
t = wikitext("en", "2026–27 Liga III")
lines = t.splitlines()
heading = ""
for i, l in enumerate(lines):
    if l.startswith("=="):
        heading = l.strip()
    if any(k in l for k in ("Gilort", "Humor", "Olimpic Zărnești", "Oltul Curti")):
        print(f"\n[{heading}] line {i}: {l.strip()[:600]}")
        if l.lstrip().startswith("*"):
            j = i
            while j > 0 and lines[j-1].lstrip().startswith("*"):
                j -= 1
            print("   list opens after: " + lines[j-1].strip()[:300])

print("\n==== STADIUM ARTICLES")
for site, title in (("en", "Tineretului Stadium (Curtișoara)"), ("en", "Dr. Sinkovits Stadium"),
                    ("en", "Muscelul Stadium"), ("ro", "Stadionul Muscelul"),
                    ("ro", "Stadionul Dr. Sinkovits"), ("en", "Olimpic Zărnești"),
                    ("ro", "Olimpic Zărnești"), ("ro", "ASC Olimpic Zărnești"),
                    ("en", "FC Șoimii Gura Humorului"), ("ro", "Șoimii Gura Humorului")):
    r = coords(site, title)
    print(f"\n{site}:{title} -> {r}")
    if r and r[0]:
        w = wikitext(site, title)
        for l in w.splitlines()[:80]:
            if re.match(r"^\s*\|\s*(location|address|ground|capacity|tenants|opened|coordinates|"
                        r"stadium|stadion|capacitate|chiriași|chiriasi|league|position|season|"
                        r"dissolved|location_map)\w*\s*=", l, re.I):
                print("   " + l.strip()[:200])
        for m in re.finditer(r"[^.\n]*(withdr|retras|dissolv|desființ|Zărnești|Moșteni|Curtișoara)[^.\n]*", w):
            print("   ~ " + m.group(0).strip()[:250])

print("\n==== OVERPASS")
def op(q):
    time.sleep(15)
    return get("https://overpass-api.de/api/interpreter", urllib.parse.urlencode({"data": q}).encode())
for name, lat, lon in (("Zărnești (Brașov), Liga III pin", 45.5611, 25.3152),
                       ("Curtișoara, Wikidata P625", 44.495642, 24.363025),
                       ("Oltul Curtișoara, Liga III pin", 44.5121, 23.9434)):
    d = op(f'[out:json][timeout:120];(nwr["leisure"~"^(pitch|stadium|sports_centre)$"](around:3500,{lat},{lon});'
           f'nwr["building"="stadium"](around:3500,{lat},{lon});node["place"](around:3500,{lat},{lon}););out tags center;')
    print(f"\n  within 3.5 km of {name} {lat},{lon}:")
    for el in (d or {}).get("elements", []):
        tg = el.get("tags", {})
        if tg.get("leisure") == "pitch" and tg.get("sport") and "soccer" not in tg["sport"]:
            continue
        c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        keep = {k: v for k, v in tg.items() if k in ("name", "place", "leisure", "sport", "operator", "wikidata", "capacity", "addr:city")}
        print(f"     {el['type']}/{el['id']} {c.get('lat')},{c.get('lon')} {keep}")
print("\nEND OF PROBE")
