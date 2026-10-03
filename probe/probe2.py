#!/usr/bin/env python3
"""THROWAWAY probe 2, removed in the same branch: the per-country rivalry list
pages, a dewiki search for the Südwestderby, and names for off-map Q-ids."""
import glob, json, os, re, time, urllib.parse, urllib.request
UA = "football-planner-derby-probe/1.0 (github.com/AlexGrozavul/Football)"
OUT = {}
def save():
    os.makedirs("probe/out", exist_ok=True)
    json.dump(OUT, open("probe/out/probe2.json", "w"), ensure_ascii=False, indent=1)
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
        clubs[c["id"]] = {"name": c.get("name"), "tier": c.get("tier"), "country": f[-7:-5]}
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
CANDS = {"DE": ["German football rivalries"], "FR": ["Football rivalries in France"],
         "IT": ["Football derbies in Italy"], "ES": ["Spanish football rivalries"],
         "BE": ["Football rivalries in Belgium"],
         "GB": ["Football rivalries in England", "List of association football rivalries in England",
                "English football rivalries", "List of football rivalries in England"],
         "NL": ["Football rivalries in the Netherlands", "Dutch football rivalries",
                "List of football rivalries in the Netherlands", "Football derbies in the Netherlands"],
         "GR": ["Football rivalries in Greece", "Greek football rivalries", "List of football rivalries in Greece",
                "Football derbies in Greece"]}
alltitles = [t for v in CANDS.values() for t in v]
ex = resolve("en", alltitles)
OUT["candidates"] = {t: ex[t] for t in alltitles}
lists = {}
for cc, ts in CANDS.items():
    for t in ts:
        rt, q, missing = ex[t]
        if not missing and rt not in lists.values():
            lists.setdefault(cc, []).append(rt)
OUT["lists"] = lists; save()
records = []
for cc, ts in lists.items():
    for title in ts:
        wt = api("en", action="parse", page=title, prop="wikitext")["parse"]["wikitext"]
        head = []; block = []
        def flush():
            if block:
                raw = " ".join(block)
                links = [(a.strip(), (b or a).strip()) for a, b in LINK.findall(raw)
                         if not a.lower().startswith(("file:", "image:", "category:"))]
                if len(links) >= 2:
                    records.append({"cc": cc, "list": title, "heading": " / ".join(head), "raw": raw[:500], "links": links})
                block.clear()
        intable = False
        for line in wt.split("\n"):
            m = re.match(r"^(=+)\s*(.*?)\s*\1\s*$", line)
            if m:
                flush(); lvl = len(m.group(1)) - 1
                head[:] = head[:lvl-1] + [re.sub(r"\[\[|\]\]|'''", "", m.group(2))]; continue
            if line.startswith("{|"): flush(); intable = True; continue
            if line.startswith("|}"): flush(); intable = False; continue
            if intable:
                if line.startswith("|-"): flush()
                else: block.append(line)
            elif line.startswith(("*", "#", ":")): flush(); block.append(line); flush()
            else: flush()
        flush()
print("records", len(records), flush=True)
res = resolve("en", [l[0] for r in records for l in r["links"]])
keep = []
for r in records:
    r["resolved"] = [(t, txt, res[t][0], res[t][1]) for t, txt in r["links"]]
    qs = [x[3] for x in r["resolved"]]
    if any(q in clubs and clubs[q]["tier"] in (1, 2) for q in qs):
        keep.append(r)
OUT["records_total"] = len(records); OUT["records"] = keep; save()
print("in scope", len(keep), flush=True)
# verify each rivalry-looking article linked from an in-scope record
done = set(json.load(open("probe/out/derbies.json"))["articles"].keys())
arts = {}
for r in keep:
    for t, txt, rt, q in r["resolved"]:
        if q and q not in clubs and re.search(r"derby|derbi|rival|clásico|classic|klassiker|derby", rt, re.I) and f"en:{rt}" not in done and rt not in arts:
            try:
                wt = api("en", action="parse", page=rt, prop="wikitext")["parse"]["wikitext"]
            except Exception as e:
                arts[rt] = {"error": str(e)}; continue
            lead = wt.split("\n==", 1)[0]
            ll = [a.strip() for a, b in LINK.findall(lead)]
            rr = resolve("en", ll[:150])
            lq = sorted({v[1] for v in rr.values() if v[1]})
            plain = re.sub(r"\{\{[^{}]*\}\}", "", lead); plain = re.sub(r"<ref[^>]*/>|<ref.*?</ref>", "", plain, flags=re.S)
            plain = " ".join(re.sub(r"'''?|<[^>]+>", "", LINK.sub(lambda m: m.group(2) or m.group(1), plain)).split())
            arts[rt] = {"qid": q, "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(rt.replace(" ", "_")),
                        "leadQids": lq, "leadClubsOnMap": [x for x in lq if x in clubs], "lead": plain[:600]}
            if len(arts) % 10 == 0: save()
OUT["articles"] = arts; save()
print("articles", len(arts), flush=True)
# dewiki searches
srch = {}
for s in ["Südwestderby", "Südwest-Derby Karlsruher SC Kaiserslautern", "Karlsruher SC 1. FC Kaiserslautern Rivalität"]:
    d = api("de", action="query", list="search", srsearch=s, srlimit="10")
    srch[s] = [(x["title"], re.sub(r"<[^>]+>", "", x.get("snippet", ""))) for x in d.get("query", {}).get("search", [])]
for s in ["Karlsruher SC Kaiserslautern derby", "Westderby Romania Poli UTA"]:
    d = api("en", action="query", list="search", srsearch=s, srlimit="8")
    srch["en:" + s] = [(x["title"], re.sub(r"<[^>]+>", "", x.get("snippet", ""))) for x in d.get("query", {}).get("search", [])]
OUT["search"] = srch; save()
# names for every off-map Q-id seen in a lead or a record
first = json.load(open("probe/out/derbies.json"))
qs = set()
for v in list(first["articles"].values()) + list(arts.values()):
    qs.update(v.get("leadQids", []))
for r in keep + first["list_lines"]:
    qs.update(x[3] for x in r["resolved"] if x[3])
qs = sorted(q for q in qs if q not in clubs)
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
