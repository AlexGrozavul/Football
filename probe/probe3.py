#!/usr/bin/env python3
"""THROWAWAY probe 3, removed in the same branch: every article in each country's
football-rivalry category, its opening paragraph and the Q-ids it links."""
import glob, json, os, re, time, urllib.parse, urllib.request
UA = "football-planner-derby-probe/1.0 (github.com/AlexGrozavul/Football)"
OUT = {}
def save():
    os.makedirs("probe/out", exist_ok=True)
    json.dump(OUT, open("probe/out/probe3.json", "w"), ensure_ascii=False, indent=1)
def get(url, tries=6):
    time.sleep(1.0)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            print("  retry", i, url[:110], e, flush=True); time.sleep(20 * (i + 1))
    raise RuntimeError("failed " + url)
def api(lang, **p):
    p.update(format="json", formatversion="2")
    return get(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(p))
clubs = {}
for f in sorted(glob.glob("data/clubs/??.json")):
    for c in json.load(open(f))["clubs"]:
        clubs[c["id"]] = c.get("name")
def resolve(lang, titles):
    out = {}; titles = sorted(set(t for t in titles if t))
    for i in range(0, len(titles), 50):
        chunk = titles[i:i+50]
        q = api(lang, action="query", titles="|".join(chunk), redirects="1", prop="pageprops", ppprop="wikibase_item").get("query", {})
        norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
        red = {r["from"]: r["to"] for r in q.get("redirects", [])}
        pages = {p["title"]: p for p in q.get("pages", [])}
        for t in chunk:
            t3 = red.get(norm.get(t, t), norm.get(t, t)); p = pages.get(t3, {})
            out[t] = (t3, (p.get("pageprops") or {}).get("wikibase_item"), "missing" in p)
    return out
LINK = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|([^\]]*))?\]\]")
PLACES = {"AT": ["Austria"], "BE": ["Belgium"], "CH": ["Switzerland"], "DE": ["Germany"],
          "ES": ["Spain"], "FR": ["France"], "GB": ["England", "Wales", "the United Kingdom"],
          "GR": ["Greece"], "IT": ["Italy"], "NL": ["the Netherlands"], "RO": ["Romania"], "RS": ["Serbia"]}
cats = {}
for cc, places in PLACES.items():
    for pl in places:
        for pat in ["Category:Football rivalries in {}", "Category:Association football rivalries in {}",
                    "Category:Football derbies in {}", "Category:Association football derbies in {}"]:
            t = pat.format(pl)
            members, cont = [], {}
            while True:
                d = api("en", action="query", list="categorymembers", cmtitle=t, cmlimit="500", **cont)
                members += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
                if "continue" not in d: break
                cont = {"cmcontinue": d["continue"]["cmcontinue"]}
            if members:
                cats[t] = {"cc": cc, "members": members}
OUT["categories"] = cats; save()
print("categories", {k: len(v["members"]) for k, v in cats.items()}, flush=True)
# one level of subcategories
for t, v in list(cats.items()):
    for m in v["members"]:
        if m.startswith("Category:") and m not in cats:
            d = api("en", action="query", list="categorymembers", cmtitle=m, cmlimit="500")
            cats[m] = {"cc": v["cc"], "members": [x["title"] for x in d.get("query", {}).get("categorymembers", [])]}
OUT["categories"] = cats; save()
done = set()
for f in ("probe/out/derbies.json", "probe/out/probe2.json"):
    for k in json.load(open(f)).get("articles", {}):
        done.add(k.split(":", 1)[1] if k.startswith(("en:", "de:", "ro:")) else k)
arts = {}
todo = sorted({(v["cc"], m) for v in cats.values() for m in v["members"]
               if ":" not in m.split(" ")[0] and not m.startswith(("Category:", "List of", "Template:"))})
print("articles to read", len(todo), flush=True)
for cc, title in todo:
    if title in done or title in arts: continue
    try:
        p = api("en", action="parse", page=title, prop="wikitext", redirects="1")["parse"]
    except Exception as e:
        arts[title] = {"cc": cc, "error": str(e)}; continue
    wt = p["wikitext"]; lead = wt.split("\n==", 1)[0]
    ll = [a.strip() for a, b in LINK.findall(lead)]
    try:
        rr = resolve("en", ll[:150])
    except Exception as e:
        arts[title] = {"cc": cc, "error": "resolve " + str(e)}; continue
    lq = sorted({v[1] for v in rr.values() if v[1]})
    plain = re.sub(r"<ref[^>]*/>|<ref.*?</ref>", "", lead, flags=re.S)
    plain = " ".join(re.sub(r"'''?|<[^>]+>", "", LINK.sub(lambda m: m.group(2) or m.group(1), plain)).split())
    arts[title] = {"cc": cc, "title": p["title"], "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(p["title"].replace(" ", "_")),
                   "leadQids": lq, "leadClubsOnMap": [q for q in lq if q in clubs], "lead": plain[:700]}
    if len(arts) % 10 == 0:
        OUT["articles"] = arts; save()
OUT["articles"] = arts; save()
print("articles", len(arts), flush=True)
prev = json.load(open("probe/out/probe2.json")).get("names", {})
qs = sorted({q for v in arts.values() for q in v.get("leadQids", []) if q not in clubs and q not in prev})
names = {}
for i in range(0, len(qs), 50):
    d = get("https://www.wikidata.org/w/api.php?format=json&action=wbgetentities&props=labels|claims|sitelinks&languages=en&sitefilter=enwiki&ids=" + "|".join(qs[i:i+50]))
    for q, e in d.get("entities", {}).items():
        cl = e.get("claims", {})
        val = lambda p: [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in cl.get(p, [])]
        names[q] = {"label": e.get("labels", {}).get("en", {}).get("value"), "P31": val("P31")[:4],
                    "P17": val("P17")[:2], "P118": val("P118")[-3:], "P576": bool(cl.get("P576")),
                    "enwiki": e.get("sitelinks", {}).get("enwiki", {}).get("title")}
OUT["names"] = names; save()
print("names", len(names), flush=True)
