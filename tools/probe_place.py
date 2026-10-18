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
def wd(ids, langs="en|el|ro|sr"):
    q = urllib.parse.urlencode({"action": "wbgetentities", "format": "json", "languages": langs, "props": "labels|aliases|claims", "ids": ids})
    d = jget("https://www.wikidata.org/w/api.php?" + q)
    if "entities" not in d: print("WD FAILED", str(d)[:300])
    return d.get("entities", {})
def claim(e, p):
    out = []
    for c in (e.get("claims", {}).get(p) or []):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, dict) and "latitude" in v: out.append(f"{v['latitude']:.6f}/{v['longitude']:.6f}")
        elif isinstance(v, dict) and "id" in v: out.append(v["id"] + "(" + c.get("rank", "")[:1] + ")")
        elif isinstance(v, dict) and "amount" in v: out.append(v["amount"])
        elif v is not None: out.append(str(v)[:40])
    return out
def show(tag, ents):
    for q, e in ents.items():
        labs = {k: v["value"] for k, v in e.get("labels", {}).items()}
        al = {k: [x["value"] for x in v] for k, v in e.get("aliases", {}).items()}
        print(f"{tag} {q} labels={labs} aliases={al} P115={claim(e,'P115')} P625={claim(e,'P625')} P1083={claim(e,'P1083')} P576={claim(e,'P576')}")
ents = wd("Q132566856|Q131850818|Q28230311|Q24969467")
show("WD", ents)
clubs = wd("Q3292651|Q16845757|Q12872753|Q1323373|Q1388917|Q66424141|Q18539440|Q55593565")
show("WDCLUB", clubs)
gids = sorted({g.split("(")[0] for e in clubs.values() for g in claim(e, "P115")} - set(ents))
if gids: show("WDG", wd("|".join(gids), "en|el|sr"))
for term in ("Ano Syros stadium", "Δημοτικό Γήπεδο Άνω Σύρου", "Ermoupoli stadium", "Ermoupoli Municipal Stadium", "Chrysoupoli stadium"):
    s = jget("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({"action": "wbsearchentities", "format": "json", "limit": 5, "language": "en", "search": term}))
    print("WDSEARCH", term, [(x["id"], x.get("label"), x.get("description")) for x in s.get("search", [])])
def over(label, q):
    d = jget("https://overpass-api.de/api/interpreter", ("data=" + urllib.parse.quote(q)).encode())
    els = d.get("elements")
    if els is None: print("OVERPASS", label, "FAILED", str(d)[:150]); return
    print("OVERPASS", label, len(els))
    for e in els[:14]:
        c = e.get("center") or {"lat": e.get("lat"), "lon": e.get("lon")}
        t = e.get("tags", {})
        print("   ", e["type"], e["id"], f"{c['lat']:.6f}/{c['lon']:.6f}", {k: t[k] for k in ("name", "name:en", "name:el", "leisure", "sport", "capacity", "operator") if k in t})
fb = '["leisure"~"stadium|pitch|sports_centre"]'
for label, lat, lon in (("nestos europlan", 40.990763, 24.688693), ("syros europlan", 37.427929, 24.937678), ("syros sports centre", 37.431348, 24.936195), ("ub Dzajic europlan", 44.453014, 20.071359)):
    over(label + " 500m", f'[out:json][timeout:60];(nwr(around:500,{lat},{lon}){fb};);out center tags;')
print("PROBE-SUMMARY-END")
