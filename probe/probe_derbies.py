#!/usr/bin/env python3
"""THROWAWAY probe, removed in the same branch. Reads Wikipedia's list of
European club rivalries and Wikidata's rivalry items, resolves every link to
a Q-id, and writes what it found to probe/out/ so the session can read it."""
import glob, json, re, sys, time, urllib.parse, urllib.request

UA = "football-planner-derby-probe/1.0 (github.com/AlexGrozavul/Football)"
OUT = {}

def get(url, data=None, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA,
                  "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            print("  retry", i, url[:120], e, flush=True)
            time.sleep(5 * (i + 1))
    raise RuntimeError("failed " + url)

def api(lang, **p):
    p.update(format="json", formatversion="2")
    return get(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(p))

clubs = {}
for f in sorted(glob.glob("data/clubs/??.json")):
    for c in json.load(open(f))["clubs"]:
        clubs[c["id"]] = {"name": c.get("name"), "tier": c.get("tier"),
                          "country": c.get("country") or f[-7:-5]}

def resolve(lang, titles):
    """title -> (resolved title, qid or None)"""
    out = {}
    titles = sorted(set(t for t in titles if t))
    for i in range(0, len(titles), 50):
        chunk = titles[i:i+50]
        d = api(lang, action="query", titles="|".join(chunk), redirects="1",
                prop="pageprops", ppprop="wikibase_item")
        q = d.get("query", {})
        norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
        red = {r["from"]: r["to"] for r in q.get("redirects", [])}
        pages = {p["title"]: p for p in q.get("pages", [])}
        for t in chunk:
            t2 = norm.get(t, t); t3 = red.get(t2, t2)
            p = pages.get(t3, {})
            out[t] = (t3, (p.get("pageprops") or {}).get("wikibase_item"),
                      "missing" in p)
        time.sleep(0.5)
    return out

LINK = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|([^\]]*))?\]\]")

def wikitext(lang, title):
    d = api(lang, action="parse", page=title, prop="wikitext", redirects="1")
    if "error" in d:
        return None, d["error"]
    return d["parse"]["wikitext"], d["parse"]["title"]

# ---------------------------------------------------------------- 1. the list
COUNTRIES = ["Austria", "Belgium", "England", "France", "Germany", "Greece",
             "Italy", "Netherlands", "Romania", "Serbia", "Spain", "Switzerland",
             "Wales", "United Kingdom", "Liechtenstein", "Monaco", "Andorra"]
listtitle = "List of association football club rivalries in Europe"
wt, real = wikitext("en", listtitle)
OUT["list_title"] = real
lines = []
section = None; sub = None
for raw in (wt or "").split("\n"):
    m = re.match(r"^(=+)\s*(.*?)\s*\1\s*$", raw)
    if m:
        lvl = len(m.group(1)); name = re.sub(r"\[\[|\]\]|'''", "", m.group(2))
        if lvl == 2: section, sub = name, None
        else: sub = name
        continue
    if section is None: continue
    if not any(c.lower() in section.lower() for c in COUNTRIES): continue
    links = [(a.strip(), (b or a).strip()) for a, b in LINK.findall(raw)]
    links = [l for l in links if not l[0].lower().startswith(("file:", "image:", "category:"))]
    if len(links) >= 2:
        lines.append({"section": section, "sub": sub, "raw": raw.strip()[:600], "links": links})
alltitles = [l[0] for ln in lines for l in ln["links"]]
res = resolve("en", alltitles)
for ln in lines:
    ln["resolved"] = [(t, txt, res[t][0], res[t][1]) for t, txt in ln["links"]]
    qs = [r[3] for r in ln["resolved"]]
    ln["mapClubs"] = [q for q in qs if q in clubs]
    ln["inScope"] = any(clubs[q]["tier"] in (1, 2) for q in ln["mapClubs"])
OUT["list_lines_total"] = len(lines)
OUT["list_lines"] = [ln for ln in lines if ln["inScope"]]
print("list lines", len(lines), "in scope", len(OUT["list_lines"]), flush=True)

# --------------------------------------------- 2. Wikidata rivalry items
top = [q for q, c in clubs.items() if c["tier"] in (1, 2)]
def sparql(q):
    return get("https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q))
wd = []
for i in range(0, len(top), 120):
    vals = " ".join("wd:" + q for q in top[i:i+120])
    q = f"""SELECT ?r ?rLabel ?p ?club ?type ?typeLabel ?article WHERE {{
      VALUES ?club {{ {vals} }}
      VALUES ?p {{ wdt:P710 wdt:P1923 wdt:P527 wdt:P1327 }}
      ?r ?p ?club . ?r wdt:P31 ?type .
      OPTIONAL {{ ?article schema:about ?r; schema:isPartOf <https://en.wikipedia.org/> }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,de,fr,it,es,nl,ro". }} }}"""
    try:
        for b in sparql(q)["results"]["bindings"]:
            wd.append({k: v["value"].rsplit("/", 1)[-1] if v["value"].startswith("http://www.wikidata.org/") else v["value"] for k, v in b.items()})
    except Exception as e:
        OUT.setdefault("wd_errors", []).append(str(e))
    time.sleep(2)
items = {}
for b in wd:
    it = items.setdefault(b["r"], {"label": b.get("rLabel"), "types": set(), "clubs": set(), "article": b.get("article")})
    it["types"].add(b.get("typeLabel")); it["clubs"].add(b["club"])
riv = {k: v for k, v in items.items()
       if any(re.search(r"rival|derby|derbi|clásico|clasico|classico|klassiker|match", t or "", re.I) for t in v["types"])}
OUT["wd_rivalries"] = {k: {"label": v["label"], "types": sorted(filter(None, v["types"])),
                            "clubs": sorted(v["clubs"]), "article": v["article"]} for k, v in riv.items()}
OUT["wd_other_type_counts"] = {}
for k, v in items.items():
    if k in riv: continue
    for t in v["types"]:
        OUT["wd_other_type_counts"][t] = OUT["wd_other_type_counts"].get(t, 0) + 1
print("wikidata rivalry items", len(riv), flush=True)

# ----------------------------------------- 3. each rivalry article, verified
cands = set()
for ln in OUT["list_lines"]:
    for t, txt, rt, q in ln["resolved"]:
        if q and q not in clubs: cands.add(("en", rt))
for k, v in riv.items():
    if v["article"]:
        cands.add(("en", urllib.parse.unquote(v["article"].rsplit("/wiki/", 1)[-1]).replace("_", " ")))
EXTRA = [("en", "Frankenderby"), ("en", "Derby della Madonnina"), ("en", "Südwestderby"),
         ("de", "Frankenderby"), ("de", "Südwestderby"), ("de", "Südwest-Derby"),
         ("en", "Stuttgart derby"), ("de", "Stuttgarter Stadtderby"), ("de", "Baden-Württemberg-Derby"),
         ("en", "Derby-ul Vestului"), ("en", "Western derby (Romania)"), ("ro", "Derby-ul Vestului"),
         ("en", "Revierderby"), ("en", "Eternal derby (Serbia)"), ("en", "Derby du Nord")]
for e in EXTRA: cands.add(e)
arts = {}
for lang, title in sorted(cands):
    try:
        t, realt = wikitext(lang, title)
    except Exception as e:
        arts[f"{lang}:{title}"] = {"error": str(e)}; continue
    if t is None:
        arts[f"{lang}:{title}"] = {"error": str(realt)}; continue
    lead = t.split("\n==", 1)[0]
    leadlinks = [a.strip() for a, b in LINK.findall(lead)]
    alllinks = [a.strip() for a, b in LINK.findall(t)]
    r = resolve(lang, list(set(alllinks))[:2000])
    leadq = sorted({r[x][1] for x in leadlinks if x in r and r[x][1]})
    allq = sorted({v[1] for v in r.values() if v[1]})
    plain = re.sub(r"\{\{[^{}]*\}\}", "", lead)
    plain = re.sub(r"<ref[^>]*/>|<ref.*?</ref>", "", plain, flags=re.S)
    plain = LINK.sub(lambda m: m.group(2) or m.group(1), plain)
    plain = re.sub(r"'''?|\[\[|\]\]|<[^>]+>", "", plain)
    plain = " ".join(plain.split())
    infobox_teams = re.findall(r"\|\s*(?:team|club)\s*\d\s*=\s*([^\n|]+)", t)
    pq = api(lang, action="query", titles=realt, prop="pageprops", ppprop="wikibase_item")
    qid = ((pq["query"]["pages"][0].get("pageprops") or {}).get("wikibase_item"))
    arts[f"{lang}:{title}"] = {"title": realt, "qid": qid,
        "url": f"https://{lang}.wikipedia.org/wiki/" + urllib.parse.quote(realt.replace(' ', '_')),
        "leadClubsOnMap": [q for q in leadq if q in clubs],
        "allClubsOnMap": [q for q in allq if q in clubs],
        "leadQids": leadq[:40], "infoboxTeams": infobox_teams[:6],
        "lead": plain[:700]}
    time.sleep(0.3)
OUT["articles"] = arts
print("articles", len(arts), flush=True)

import os
os.makedirs("probe/out", exist_ok=True)
json.dump(OUT, open("probe/out/derbies.json", "w"), ensure_ascii=False, indent=1, default=list)
